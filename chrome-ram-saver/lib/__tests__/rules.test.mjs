import assert from "node:assert/strict";
import { isDiscardableUrl, isWhitelisted, isEligible, hostnameOf } from "../rules.js";

let passed = 0;
function test(name, fn) {
  fn();
  passed++;
  console.log("OK:", name);
}

test("isDiscardableUrl aceita http/https", () => {
  assert.equal(isDiscardableUrl("https://exemplo.com/pagina"), true);
  assert.equal(isDiscardableUrl("http://127.0.0.1:8080/"), true);
});

test("isDiscardableUrl rejeita esquemas internos do browser", () => {
  assert.equal(isDiscardableUrl("chrome://extensions"), false);
  assert.equal(isDiscardableUrl("chrome-extension://abc123/popup.html"), false);
  assert.equal(isDiscardableUrl("about:blank"), false);
  assert.equal(isDiscardableUrl("devtools://devtools/x"), false);
  assert.equal(isDiscardableUrl("file:///home/user/x.html"), false);
});

test("isDiscardableUrl rejeita undefined/vazio/malformado", () => {
  assert.equal(isDiscardableUrl(undefined), false);
  assert.equal(isDiscardableUrl(""), false);
  assert.equal(isDiscardableUrl("nem-um-url"), false);
});

test("hostnameOf extrai o hostname em minúsculas", () => {
  assert.equal(hostnameOf("https://Exemplo.COM/pagina"), "exemplo.com");
  assert.equal(hostnameOf("http://sub.dominio.org:9000/x"), "sub.dominio.org");
  assert.equal(hostnameOf("não-é-um-url"), null);
});

test("isWhitelisted faz match exacto de domínio", () => {
  assert.equal(isWhitelisted("https://exemplo.com/x", ["exemplo.com"]), true);
  assert.equal(isWhitelisted("https://outro.com/x", ["exemplo.com"]), false);
});

test("isWhitelisted cobre subdomínios do domínio na lista", () => {
  assert.equal(isWhitelisted("https://mail.exemplo.com/x", ["exemplo.com"]), true);
  assert.equal(isWhitelisted("https://naoexemplo.com/x", ["exemplo.com"]), false, "não deve fazer match parcial de sufixo sem ponto");
});

test("isWhitelisted é case-insensitive e ignora lista vazia", () => {
  assert.equal(isWhitelisted("https://Exemplo.com/x", ["exemplo.com"]), true);
  assert.equal(isWhitelisted("https://exemplo.com/x", []), false);
  assert.equal(isWhitelisted("https://exemplo.com/x", undefined), false);
});

const baseSettings = { excludePinned: true, excludeAudio: true, whitelist: [] };

test("isEligible exclui separador activo", () => {
  const tab = { id: 1, url: "https://exemplo.com" };
  assert.equal(isEligible(tab, baseSettings, new Set([1])), false);
});

test("isEligible exclui separador já discarded", () => {
  const tab = { id: 1, url: "https://exemplo.com", discarded: true };
  assert.equal(isEligible(tab, baseSettings, new Set()), false);
});

test("isEligible exclui pinned quando excludePinned=true", () => {
  const tab = { id: 1, url: "https://exemplo.com", pinned: true };
  assert.equal(isEligible(tab, baseSettings, new Set()), false);
});

test("isEligible permite pinned quando excludePinned=false", () => {
  const tab = { id: 1, url: "https://exemplo.com", pinned: true };
  assert.equal(isEligible(tab, { ...baseSettings, excludePinned: false }, new Set()), true);
});

test("isEligible exclui separador com áudio quando excludeAudio=true", () => {
  const tab = { id: 1, url: "https://exemplo.com", audible: true };
  assert.equal(isEligible(tab, baseSettings, new Set()), false);
});

test("isEligible exclui separadores de esquemas internos", () => {
  const tab = { id: 1, url: "chrome://extensions" };
  assert.equal(isEligible(tab, baseSettings, new Set()), false);
});

test("isEligible exclui sites na lista branca", () => {
  const tab = { id: 1, url: "https://exemplo.com/pagina" };
  assert.equal(isEligible(tab, { ...baseSettings, whitelist: ["exemplo.com"] }, new Set()), false);
});

test("isEligible aceita um separador normal em segundo plano", () => {
  const tab = { id: 1, url: "https://exemplo.com/pagina", pinned: false, audible: false };
  assert.equal(isEligible(tab, baseSettings, new Set([999])), true);
});

test("isEligible exclui separador sem id", () => {
  const tab = { url: "https://exemplo.com" };
  assert.equal(isEligible(tab, baseSettings, new Set()), false);
});

console.log(`\n${passed} testes unitários passaram`);
