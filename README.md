# AI言いにくいこと変換局 Ver.1.0

Flask + Gemini API で動作するローカル向け初期版です。

## 機能
- 入力した文章を4種類（丁寧・ビジネス向け／やさしい断り方／短く率直／ちょっとユーモラス）に変換
- 結果ごとのコピーと「コピーしました！」表示
- PCは2列、スマートフォンは1列のレスポンシブ表示
- 入力・結果をアプリのデータベースなどに保存しない
- バージョン表示と「アプリについて」
- 著作開発者：小澤保則

## 起動手順（Windows / PowerShell）
1. Python 3.11 以降を推奨。フォルダー内で PowerShell を開く。
2. 仮想環境を作成して有効化する。

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. 必要なパッケージを入れる。

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. `.env.example` を `.env` にコピーし、`GEMINI_API_KEY` を自分のAPIキーに置き換える。`.env` は公開・共有しない。
5. 起動する。

   ```powershell
   python -c "from dotenv import load_dotenv; load_dotenv()"
   python app.py
   ```

   上の `python -c` はそのコマンド実行中だけの設定なので、通常は次の起動方法がおすすめです。

   ```powershell
   python -m dotenv run -- python app.py
   ```

6. ブラウザーで `http://127.0.0.1:5000` を開く。

## メモ
- Gemini APIキーはサーバー側の環境変数だけで扱い、ブラウザーには送信しません。
- このアプリは入力内容や変換結果を保存しませんが、変換のために入力文はGemini APIへ送信されます。個人情報や機密情報を入力しないでください。
- 初回はAPIキー設定と通信環境が必要です。


## Androidホーム画面に追加
1. HTTPSで公開したアプリURLをAndroid版Chromeで開きます。
2. Chromeのメニューから「ホーム画面に追加」または「アプリをインストール」を選びます（表示名は端末・Chromeの版で異なる場合があります）。
3. 追加済みのアイコンが古い場合は、古いショートカットを削除してから再追加します。

この対応で追加したファイルは `manifest.webmanifest`、`static/icon-192.png`、`static/icon-512.png` です。画面の変換処理と `static/app.js` は変更していません。

## 公開環境の注意
このZIPは既存の最終微調整版を基準に、ホーム画面アイコン対応だけを加えたものです。公開先で変換APIが正常に動くかは、公開先の環境変数 `GEMINI_API_KEY`、デプロイ先設定、サーバーログにも依存します。ZIP内だけのテストで、公開URL上の動作まで保証することはできません。


## 変換時にサーバーエラーが表示される場合

この版では、変換APIがHTMLなどJSON以外を返した場合に、画面が `Unexpected token '<'` で止まらず、HTTPステータスを表示します。HTTP 5xx が表示された場合はブラウザー側だけでは復旧できず、Renderのサービスログにある `/api/convert` の例外またはワーカー終了原因を確認する必要があります。
