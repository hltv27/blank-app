const NON_DISCARDABLE_SCHEMES = ["chrome:", "chrome-extension:", "edge:", "about:", "devtools:", "file:"];

export function hostnameOf(url) {
  try {
    return new URL(url).hostname.toLowerCase();
  } catch {
    return null;
  }
}

export function isDiscardableUrl(url) {
  if (!url) return false;
  try {
    const parsed = new URL(url);
    return !NON_DISCARDABLE_SCHEMES.includes(parsed.protocol);
  } catch {
    return false;
  }
}

export function isWhitelisted(url, whitelist) {
  const host = hostnameOf(url);
  if (!host || !whitelist || whitelist.length === 0) return false;
  return whitelist.some((entry) => {
    const w = entry.toLowerCase().trim();
    if (!w) return false;
    return host === w || host.endsWith(`.${w}`);
  });
}

// Decide se um separador é elegível para suspensão, independentemente do
// tempo de inactividade (usado tanto pelo temporizador automático como
// pelas acções manuais "suspender tudo agora").
export function isEligible(tab, settings, activeTabIds) {
  if (!tab.id || tab.discarded) return false;
  if (activeTabIds.has(tab.id)) return false;
  if (settings.excludePinned && tab.pinned) return false;
  if (settings.excludeAudio && tab.audible) return false;
  if (!isDiscardableUrl(tab.url)) return false;
  if (isWhitelisted(tab.url, settings.whitelist)) return false;
  return true;
}
