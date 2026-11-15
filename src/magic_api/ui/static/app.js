// MagicGPT chat UI. Plain JS, no build step.
// Card display rules (README): 1-4 cards -> image grid; 5-20 -> bulleted list
// with hover image; more than 20 -> list truncated to 20 + hint.
const GRID_MAX = 4;
const LIST_MAX = 20;

const chat = document.getElementById("chat");
const form = document.getElementById("composer");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");
const preview = document.getElementById("hover-preview");
const previewImg = preview.querySelector("img");

const history = []; // [{role, content}] sent to the backend each turn
let backendUrl = null;

async function getBackendUrl() {
  if (!backendUrl) {
    const res = await fetch("/config.json");
    backendUrl = (await res.json()).backend_url;
  }
  return backendUrl;
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function cardImage(card) {
  const face = card.card_faces && card.card_faces[0];
  const uris = card.image_uris || (face && face.image_uris) || {};
  return uris.normal || uris.large || uris.small || null;
}

function addMessage(role, text, extraClass = "") {
  const wrap = el("div", `msg ${role}`);
  const bubble = el("div", `bubble ${extraClass}`.trim(), text);
  wrap.appendChild(bubble);
  chat.appendChild(wrap);
  chat.scrollTop = chat.scrollHeight;
  return { wrap, bubble };
}

function renderCards(wrap, cards) {
  if (!cards.length) return;
  if (cards.length <= GRID_MAX) {
    const grid = el("div", "card-grid");
    for (const card of cards) {
      const src = cardImage(card);
      if (!src) continue;
      const img = el("img");
      img.src = src;
      img.alt = card.name;
      img.loading = "lazy";
      grid.appendChild(img);
    }
    wrap.appendChild(grid);
    return;
  }
  const list = el("ul", "card-list");
  for (const card of cards.slice(0, LIST_MAX)) {
    const li = el("li");
    const link = el("a", "", card.name);
    link.href = card.scryfall_uri || "#";
    link.target = "_blank";
    link.rel = "noopener";
    const src = cardImage(card);
    if (src) {
      link.addEventListener("mouseenter", () => { previewImg.src = src; preview.hidden = false; });
      link.addEventListener("mousemove", (e) => {
        preview.style.left = `${Math.min(e.clientX + 16, window.innerWidth - 260)}px`;
        preview.style.top = `${Math.max(8, Math.min(e.clientY - 120, window.innerHeight - 340))}px`;
      });
      link.addEventListener("mouseleave", () => { preview.hidden = true; });
    }
    li.append(link, document.createTextNode(card.type_line ? ` — ${card.type_line}` : ""));
    list.appendChild(li);
  }
  wrap.appendChild(list);
  if (cards.length > LIST_MAX) {
    wrap.appendChild(el("div", "card-more", `Showing ${LIST_MAX} of ${cards.length} cards. Narrow your question to see more.`));
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  sendBtn.disabled = true;

  addMessage("user", text);
  history.push({ role: "user", content: text });
  const pending = addMessage("assistant", "Thinking…", "pending");

  try {
    const base = await getBackendUrl();
    const res = await fetch(`${base}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: history, mode: "cards" }),
    });
    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      throw new Error(detail.detail || `Request failed (${res.status})`);
    }
    const data = await res.json();
    pending.bubble.textContent = data.reply;
    pending.bubble.classList.remove("pending");
    history.push({ role: "assistant", content: data.reply });
    renderCards(pending.wrap, data.cards || []);
  } catch (err) {
    pending.bubble.textContent = `Sorry, something went wrong: ${err.message}`;
    pending.bubble.className = "bubble error";
    history.pop(); // let the user retry the same question
  } finally {
    sendBtn.disabled = false;
    input.focus();
    chat.scrollTop = chat.scrollHeight;
  }
});
