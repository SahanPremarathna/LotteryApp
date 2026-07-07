const lotterySelect = document.querySelector("#lotterySelect");
const dateInput = document.querySelector("#dateInput");
const searchButton = document.querySelector("#searchButton");
const message = document.querySelector("#message");
const resultPanel = document.querySelector("#resultPanel");
const lotteryLogo = document.querySelector("#lotteryLogo");
const lotteryName = document.querySelector("#lotteryName");
const drawMeta = document.querySelector("#drawMeta");
const resultGroups = document.querySelector("#resultGroups");
const imageArea = document.querySelector("#imageArea");

function yesterdayIso() {
  const date = new Date();
  date.setDate(date.getDate() - 1);
  return date.toISOString().slice(0, 10);
}

function showMessage(text, kind = "info") {
  message.textContent = text;
  message.className = `message ${kind}`;
  message.hidden = false;
}

function hideMessage() {
  message.hidden = true;
}

function valueGroup(title, values) {
  if (!values || values.length === 0) return "";

  return `
    <div class="value-group">
      <p>${title}</p>
      <div class="balls">
        ${values.map((value) => `<span>${value}</span>`).join("")}
      </div>
    </div>
  `;
}

function renderResult(result) {
  lotteryLogo.src = result.logo || "https://www.dlb.lk/assets/frontend/eng/images/logo.jpg";
  lotteryLogo.alt = result.lottery;
  lotteryName.textContent = result.lottery;
  drawMeta.textContent = `Draw ${result.draw_number} | ${result.draw_date}`;

  const groups = [];
  if (result.letter) groups.push(valueGroup("Special letter", [result.letter]));
  if (result.numbers) groups.push(valueGroup("Winning numbers", result.numbers));
  if (result.special_number) groups.push(valueGroup("Special number", [result.special_number]));
  if (result.raw_result) groups.push(valueGroup("Raw result", result.raw_result));

  resultGroups.innerHTML = groups.join("");
  imageArea.innerHTML = "";

  const image = result.lagna || result.special_image;
  if (image && image.src) {
    imageArea.innerHTML = `
      <p>${result.lagna ? "Lagna image" : "Special draw image"}</p>
      <img src="${image.src}" alt="${image.alt || result.lottery}">
    `;
  }

  resultPanel.hidden = false;
}

async function loadLotteries() {
  const response = await fetch("/api/lotteries");
  const data = await response.json();

  lotterySelect.innerHTML = data.lotteries
    .map((lottery) => `<option value="${lottery.key}">${lottery.name}</option>`)
    .join("");
}

async function searchResult() {
  hideMessage();
  resultPanel.hidden = true;

  const lottery = lotterySelect.value;
  const date = dateInput.value;
  if (!lottery || !date) {
    showMessage("Select a lottery and date first.", "error");
    return;
  }

  searchButton.disabled = true;
  searchButton.textContent = "Loading";
  showMessage("Fetching result from DLB...", "info");

  try {
    const response = await fetch(
      `/api/result?lottery=${encodeURIComponent(lottery)}&date=${encodeURIComponent(date)}`
    );
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Result not found.");
    }

    hideMessage();
    renderResult(data.result);
  } catch (error) {
    showMessage(error.message, "error");
  } finally {
    searchButton.disabled = false;
    searchButton.textContent = "Get result";
  }
}

dateInput.value = yesterdayIso();
searchButton.addEventListener("click", searchResult);
loadLotteries().catch(() => showMessage("Could not load lottery list.", "error"));
