import { getSettings, getLastActiveMap, touchTab, forgetTab } from "./lib/storage.js";
import { isEligible } from "./lib/rules.js";

const ALARM_NAME = "check-idle-tabs";

chrome.runtime.onInstalled.addListener(async () => {
  chrome.alarms.create(ALARM_NAME, { periodInMinutes: 1 });
  const tabs = await chrome.tabs.query({});
  await Promise.all(tabs.map((tab) => touchTab(tab.id)));
  await updateBadge();
});

chrome.runtime.onStartup.addListener(() => {
  chrome.alarms.create(ALARM_NAME, { periodInMinutes: 1 });
});

chrome.tabs.onCreated.addListener((tab) => touchTab(tab.id));

chrome.tabs.onActivated.addListener(({ tabId }) => touchTab(tabId));

chrome.tabs.onUpdated.addListener((tabId, changeInfo) => {
  if (changeInfo.status === "loading") touchTab(tabId);
  if ("discarded" in changeInfo || "status" in changeInfo) updateBadge();
});

chrome.tabs.onRemoved.addListener((tabId) => forgetTab(tabId));

chrome.windows.onFocusChanged.addListener(async (windowId) => {
  if (windowId === chrome.windows.WINDOW_ID_NONE) return;
  const [active] = await chrome.tabs.query({ active: true, windowId });
  if (active) touchTab(active.id);
});

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === ALARM_NAME) suspendIdleTabs();
});

chrome.commands.onCommand.addListener(async (command) => {
  if (command === "suspend-current-tab") {
    const [active] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (active) await discardTab(active.id);
  } else if (command === "suspend-all-inactive") {
    await suspendAllInactiveNow();
  }
});

async function getActiveTabIds() {
  const activeTabs = await chrome.tabs.query({ active: true });
  return new Set(activeTabs.map((t) => t.id));
}

// Corre a cada minuto (via chrome.alarms — setInterval não sobrevive à
// reciclagem do service worker). Só suspende separadores que já ultrapassaram
// o limiar de inactividade configurado pelo utilizador.
async function suspendIdleTabs() {
  const settings = await getSettings();
  if (!settings.enabled) return;

  const [lastActive, tabs, activeTabIds] = await Promise.all([
    getLastActiveMap(),
    chrome.tabs.query({}),
    getActiveTabIds(),
  ]);

  const now = Date.now();
  const thresholdMs = settings.idleMinutes * 60 * 1000;

  for (const tab of tabs) {
    if (!isEligible(tab, settings, activeTabIds)) continue;
    const last = lastActive[tab.id] ?? now;
    if (now - last >= thresholdMs) {
      await discardTab(tab.id);
    }
  }
  await updateBadge();
}

// Suspende imediatamente todos os separadores elegíveis, ignorando o
// temporizador de inactividade — usado pelo botão "Suspender agora".
export async function suspendAllInactiveNow() {
  const settings = await getSettings();
  const [tabs, activeTabIds] = await Promise.all([chrome.tabs.query({}), getActiveTabIds()]);
  let count = 0;
  for (const tab of tabs) {
    if (!isEligible(tab, settings, activeTabIds)) continue;
    await discardTab(tab.id);
    count++;
  }
  await updateBadge();
  return count;
}

export async function discardTab(tabId) {
  try {
    await chrome.tabs.discard(tabId);
  } catch {
    // alguns separadores (ex: já em primeiro plano numa janela minimizada,
    // ou o próprio separador do gestor de extensões) recusam ser suspensos
  }
}

export async function updateBadge() {
  const tabs = await chrome.tabs.query({});
  const discardedCount = tabs.filter((t) => t.discarded).length;
  await chrome.action.setBadgeText({ text: discardedCount > 0 ? String(discardedCount) : "" });
  await chrome.action.setBadgeBackgroundColor({ color: "#0f9d58" });
}

// Chamado pelo popup para forçar uma actualização de contadores.
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type === "suspend-all-inactive") {
    suspendAllInactiveNow().then((count) => sendResponse({ count }));
    return true; // resposta assíncrona
  }
  if (message?.type === "discard-tab") {
    discardTab(message.tabId).then(() => {
      updateBadge();
      sendResponse({ ok: true });
    });
    return true;
  }
});
