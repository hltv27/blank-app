export const DEFAULT_SETTINGS = {
  enabled: true,
  idleMinutes: 15,
  excludePinned: true,
  excludeAudio: true,
  whitelist: [],
};

const SETTINGS_KEY = "settings";

export async function getSettings() {
  const stored = await chrome.storage.local.get(SETTINGS_KEY);
  return { ...DEFAULT_SETTINGS, ...(stored[SETTINGS_KEY] || {}) };
}

export async function setSettings(patch) {
  const current = await getSettings();
  const next = { ...current, ...patch };
  await chrome.storage.local.set({ [SETTINGS_KEY]: next });
  return next;
}

export function onSettingsChanged(callback) {
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area === "local" && changes[SETTINGS_KEY]) {
      callback(changes[SETTINGS_KEY].newValue || DEFAULT_SETTINGS);
    }
  });
}

// Última vez que cada separador esteve em primeiro plano. Guardado em
// storage.session porque o service worker é reciclado a qualquer momento
// e uma variável em memória perder-se-ia entre acordares.
const ACTIVITY_KEY = "lastActive";

export async function getLastActiveMap() {
  const stored = await chrome.storage.session.get(ACTIVITY_KEY);
  return stored[ACTIVITY_KEY] || {};
}

export async function touchTab(tabId) {
  const map = await getLastActiveMap();
  map[tabId] = Date.now();
  await chrome.storage.session.set({ [ACTIVITY_KEY]: map });
}

export async function forgetTab(tabId) {
  const map = await getLastActiveMap();
  if (tabId in map) {
    delete map[tabId];
    await chrome.storage.session.set({ [ACTIVITY_KEY]: map });
  }
}
