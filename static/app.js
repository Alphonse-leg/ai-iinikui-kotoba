const phrase = document.getElementById("phrase");
const charCount = document.getElementById("char-count");
const convertButton = document.getElementById("convert-button");
const statusBox = document.getElementById("status");
const resultsSection = document.getElementById("results-section");
const toast = document.getElementById("toast");
let toastTimer;

phrase.addEventListener("input", () => {
  charCount.textContent = `${phrase.value.length} / 2000`;
});

function showStatus(message, isError = false) {
  statusBox.textContent = message;
  statusBox.classList.toggle("error", isError);
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 1800);
}

convertButton.addEventListener("click", async () => {
  const text = phrase.value.trim();
  if (!text) {
    showStatus("言い換えたい文章を入力してね。", true);
    phrase.focus();
    return;
  }

  convertButton.disabled = true;
  convertButton.textContent = "考え中… 🐾";
  showStatus("言い換え名人の猫が考えています…");
  resultsSection.hidden = true;

  try {
    const response = await fetch("/api/convert", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "変換に失敗しました。");

    for (const key of ["business", "gentle", "direct", "humorous"]) {
      document.getElementById(`result-${key}`).textContent = data.results[key];
    }
    resultsSection.hidden = false;
    showStatus("できたよ！しっくりくる言い方を選んでね。");
    resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    showStatus(error.message || "通信に失敗しました。もう一度お試しください。", true);
  } finally {
    convertButton.disabled = false;
    convertButton.innerHTML = '<span aria-hidden="true">✨</span> やさしく言い換える';
  }
});

document.querySelectorAll(".copy-button").forEach((button) => {
  button.addEventListener("click", async () => {
    const key = button.dataset.copy;
    const text = document.getElementById(`result-${key}`).textContent;
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      showToast("コピーしました！");
    } catch (_error) {
      // Clipboard API may be unavailable on non-secure origins.
      const temporary = document.createElement("textarea");
      temporary.value = text;
      temporary.setAttribute("readonly", "");
      temporary.style.position = "fixed";
      temporary.style.opacity = "0";
      document.body.appendChild(temporary);
      temporary.select();
      const copied = document.execCommand("copy");
      temporary.remove();
      if (copied) showToast("コピーしました！");
      else showToast("コピーできませんでした。文章を選択してコピーしてください。");
    }
  });
});
