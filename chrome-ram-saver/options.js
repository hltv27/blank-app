import { getSettings, setSettings } from "./lib/storage.js";
import { hostnameOf } from "./lib/rules.js";

const enabledEl = document.getElementById("enabled");
const idleMinutesEl = document.getElementById("idleMinutes");
const excludePinnedEl = document.getElementById("excludePinned");
const excludeAudioEl = document.getElementById("excludeAudio");
const whitelistForm = document.getElementById("whitelistForm");
const whitelistInput = document.getElementById("whitelistInput");
const whitelistListEl = document.getElementById("whitelistList");
const statusEl = document.getElementById("status");

let statusTimer = null;
function showStatus(text) {
  statusEl.textContent = text;
  statusEl.style.opacity = "1";
  clearTimeout(statusTimer);
  statusTimer = setTimeout(() => { statusEl.style.opacity = "0"; }, 1500);
}

function renderWhitelist(whitelist) {
  whitelistListEl.innerHTML = "";
  if (!whitelist || whitelist.length === 0) {
    const li = document.createElement("li");
    li.className = "empty";
    li.textContent = "A lista branca está vazia.";
    whitelistListEl.appendChild(li);
    return;
  }
  for (const host of whitelist) {
    const li = document.createElement("li");
    const span = document.createElement("span");
    span.textContent = host;
    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.textContent = "Remover";
    removeBtn.addEventListener("click", async () => {
      const settings = await getSettings();
      const next = settings.whitelist.filter((h) => h !== host);
      await setSettings({ whitelist: next });
      renderWhitelist(next);
      showStatus("Guardado ✓");
    });
    li.append(span, removeBtn);
    whitelistListEl.appendChild(li);
  }
}

async function load() {
  const settings = await getSettings();
  enabledEl.checked = settings.enabled;
  idleMinutesEl.value = settings.idleMinutes;
  excludePinnedEl.checked = settings.excludePinned;
  excludeAudioEl.checked = settings.excludeAudio;
  renderWhitelist(settings.whitelist);
}

enabledEl.addEventListener("change", async () => {
  await setSettings({ enabled: enabledEl.checked });
  showStatus("Guardado ✓");
});

idleMinutesEl.addEventListener("change", async () => {
  const value = Math.max(1, Math.min(1440, Number(idleMinutesEl.value) || 15));
  idleMinutesEl.value = value;
  await setSettings({ idleMinutes: value });
  showStatus("Guardado ✓");
});

excludePinnedEl.addEventListener("change", async () => {
  await setSettings({ excludePinned: excludePinnedEl.checked });
  showStatus("Guardado ✓");
});

excludeAudioEl.addEventListener("change", async () => {
  await setSettings({ excludeAudio: excludeAudioEl.checked });
  showStatus("Guardado ✓");
});

whitelistForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const raw = whitelistInput.value.trim();
  if (!raw) return;
  const host = hostnameOf(raw.includes("://") ? raw : `https://${raw}`) || raw.toLowerCase();
  const settings = await getSettings();
  if (!settings.whitelist.includes(host)) {
    const next = [...settings.whitelist, host];
    await setSettings({ whitelist: next });
    renderWhitelist(next);
    showStatus("Guardado ✓");
  }
  whitelistInput.value = "";
});

load();
