import json
import os
import re

from flask import Flask, jsonify, render_template, request, send_from_directory
from dotenv import load_dotenv
from google import genai
from google.genai import types, errors

load_dotenv()

APP_VERSION = "Ver.1.0"
app = Flask(__name__)


@app.get("/service-worker.js")
def service_worker():
    # A minimal no-cache worker endpoint prevents stale browser registrations
    # from receiving a 404; it does not cache pages or API responses.
    response = send_from_directory(
        app.root_path,
        "service-worker.js",
        mimetype="application/javascript",
        max_age=0,
    )
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


@app.get("/manifest.webmanifest")
def static_manifest():
    return send_from_directory(
        app.root_path,
        "manifest.webmanifest",
        mimetype="application/manifest+json",
    )
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024  # 32 KB request limit

STYLE_INSTRUCTIONS = {
    "business": "丁寧・ビジネス向け。礼儀正しく、失礼のない自然な表現。",
    "gentle": "やさしい断り方。相手への配慮を示しつつ、無理なことは明確に伝える。",
    "direct": "短く率直。余計な説明を省き、冷たくなりすぎない簡潔な表現。",
    "humorous": "軽いユーモアを交える。相手を傷つけたり、皮肉や攻撃になったりしない表現。",
}


def convert_phrase(user_text: str) -> dict:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY が設定されていません。.env または環境変数を確認してください。")

    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    prompt = f"""
あなたは「言い換え名人の猫」です。
ユーザーの本音や言いにくい言葉を否定せず受け止め、相手に伝わりやすい自然な日本語に言い換えてください。
意味や大事な境界線を勝手に変えず、過度にへりくだったり、攻撃的にしたりしないでください。
ユーザーが入力した文に対し、次の4種類をそれぞれ1つずつ作ってください。

1. business: {STYLE_INSTRUCTIONS["business"]}
2. gentle: {STYLE_INSTRUCTIONS["gentle"]}
3. direct: {STYLE_INSTRUCTIONS["direct"]}
4. humorous: {STYLE_INSTRUCTIONS["humorous"]}

入力文:
<user_text>
{user_text}
</user_text>

必ずJSONオブジェクトだけを返してください。形式:
{{
  "business": "丁寧・ビジネス向けの言い換え",
  "gentle": "やさしい断り方の言い換え",
  "direct": "短く率直な言い換え",
  "humorous": "軽いユーモアのある言い換え"
}}
""".strip()

    client = genai.Client(api_key=api_key)
    try:
        config = types.GenerateContentConfig(
            temperature=0.7,
            response_mime_type="application/json",
        )
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )
        except errors.ServerError as exc:
            # Gemini may temporarily return 503 when a model is overloaded.
            # Try the currently recommended Flash-Lite model once, unless it was already selected.
            if getattr(exc, "code", None) != 503 or model_name == "gemini-3.5-flash-lite":
                raise
            app.logger.warning(
                "Gemini model %s returned 503; retrying once with gemini-3.5-flash-lite",
                model_name,
            )
            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt,
                config=config,
            )
        raw = (response.text or "").strip()
        # Defensive cleanup in case a model returns fenced JSON despite the JSON mode.
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE)
        data = json.loads(raw)
        result = {}
        for key in STYLE_INSTRUCTIONS:
            value = data.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError("AIからの返答形式が正しくありません。もう一度お試しください。")
            result[key] = value.strip()
        return result
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            close()


@app.get("/")
def index():
    return render_template("index.html", app_version=APP_VERSION)


@app.post("/api/convert")
def api_convert():
    payload = request.get_json(silent=True) or {}
    user_text = payload.get("text", "")
    if not isinstance(user_text, str):
        return jsonify({"error": "文章を入力してください。"}), 400

    user_text = user_text.strip()
    if not user_text:
        return jsonify({"error": "言い換えたい文章を入力してください。"}), 400
    if len(user_text) > 2000:
        return jsonify({"error": "入力は2,000文字以内にしてください。"}), 400

    try:
        results = convert_phrase(user_text)
        return jsonify({"results": results})
    except json.JSONDecodeError:
        app.logger.exception("Gemini returned invalid JSON")
        return jsonify({"error": "返答をうまく読み取れませんでした。少し表現を変えて、もう一度お試しください。"}), 502
    except errors.ServerError as exc:
        app.logger.exception("Gemini service error")
        if getattr(exc, "code", None) == 503:
            return jsonify({"error": "Gemini側が一時的に混雑しています。少し待ってから、もう一度お試しください。"}), 503
        return jsonify({"error": "Gemini側でエラーが発生しました。少し待ってから、もう一度お試しください。"}), 502
    except Exception as exc:
        app.logger.exception("Conversion failed")
        message = str(exc)
        if "GEMINI_API_KEY" in message:
            safe_message = message
        else:
            safe_message = "変換に失敗しました。通信状況やAPI設定を確認して、もう一度お試しください。"
        return jsonify({"error": safe_message}), 500


@app.errorhandler(413)
def request_too_large(_error):
    return jsonify({"error": "送信データが大きすぎます。入力を短くしてください。"}), 413


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
