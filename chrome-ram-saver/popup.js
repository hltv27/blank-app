import { getSettings, setSettings } from "./lib/storage.js";
import { hostnameOf, isWhitelisted } from "./lib/rules.js";

const enabledToggle = document.getElementById("enabledToggle");
const totalCountEl = document.getElementById("totalCount");
const discardedCountEl = document.getElementById("discardedCount");
const suspendAllBtn = document.getElementById("suspendAllBtn");
const suspendCurrentBtn = document.getElementById("suspendCurrentBtn");
const whitelistBtn = document.getElementById("whitelistBtn");
const discardedListEl = document.getElementById("discardedList");
const openOptionsBtn = document.getElementById("openOptionsBtn");

let currentTab = null;

async function refresh() {
  const [settings, tabs, [activeTab]] = await Promise.all([
    getSettings(),
    chrome.tabs.query({}),
    chrome.tabs.query({ active: true, currentWindow: true }),
  ]);

  currentTab = activeTab || null;
  enabledToggle.checked = settings.enabled;

  const discarded = tabs.filter((t) => t.discarded);
  totalCountEl.textContent = String(tabs.length);
  discardedCountEl.textContent = String(discarded.length);

  renderDiscardedList(discarded);
  renderWhitelistButton(settings);
  renderCurrentTabButton(activeTab);
}

function renderDiscardedList(discarded) {
  discardedListEl.innerHTML = "";
  if (discarded.length === 0) {
    const li = document.createElement("li");
    li.className = "empty";
    li.textContent = "Nenhum separador suspenso de momento.";
    discardedListEl.appendChild(li);
    return;
  }
  for (const tab of discarded) {
    const li = document.createElement("li");
    li.title = "Clica para reactivar";
    const img = document.createElement("img");
    img.src = tab.favIconUrl || "icons/icon16.png";
    img.alt = "";
    img.onerror = () => { img.src = "icons/icon16.png"; };
    const span = document.createElement("span");
    span.textContent = tab.title || tab.url || "Separador";
    li.append(img, span);
    li.addEventListener("click", async () => {
      await chrome.tabs.update(tab.id, { active: true });
      await chrome.windows.update(tab.windowId, { focused: true });
      window.close();
    });
    discardedListEl.appendChild(li);
  }
}

function renderCurrentTabButton(activeTab) {
  const discardable = activeTab && activeTab.url && !activeTab.discarded &&
    /^https?:/.test(activeTab.url);
  suspendCurrentBtn.disabled = !discardable;
  suspendCurrentBtn.title = discardable
    ? ""
    : "Este separador não pode ser suspenso";
}

function renderWhitelistButton(settings) {
  if (!currentTab || !currentTab.url || !/^https?:/.test(currentTab.url)) {
    whitelistBtn.disabled = true;
    whitelistBtn.textContent = "Adicionar site à lista branca";
    return;
  }
  const host = hostnameOf(currentTab.url);
  if (!host) {
    whitelistBtn.disabled = true;
    return;
  }
  whitelistBtn.disabled = false;
  const listed = isWhitelisted(currentTab.url, settings.whitelist);
  whitelistBtn.textContent = listed
    ? `Remover ${host} da lista branca`
    : `Adicionar ${host} à lista branca`;
  whitelistBtn.dataset.host = host;
  whitelistBtn.dataset.listed = String(listed);
}

enabledToggle.addEventListener("change", async () => {
  await setSettings({ enabled: enabledToggle.checked });
});

suspendAllBtn.addEventListener("click", async () => {
  suspendAllBtn.disabled = true;
  suspendAllBtn.textContent = "A suspender…";
  await chrome.runtime.sendMessage({ type: "suspend-all-inactive" });
  suspendAllBtn.disabled = false;
  suspendAllBtn.textContent = "Suspender inactivos agora";
  await refresh();
});

suspendCurrentBtn.addEventListener("click", async () => {
  if (!currentTab) return;
  await chrome.runtime.sendMessage({ type: "discard-tab", tabId: currentTab.id });
  window.close();
});

whitelistBtn.addEventListener("click", async () => {
  const host = whitelistBtn.dataset.host;
  const listed = whitelistBtn.dataset.listed === "true";
  const settings = await getSettings();
  const whitelist = listed
    ? settings.whitelist.filter((h) => h !== host)
    : [...settings.whitelist, host];
  await setSettings({ whitelist });
  await refresh();
});

openOptionsBtn.addEventListener("click", () => {
  chrome.runtime.openOptionsPage();
});

refresh();
