const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync('rastreamento/static/rastreamento/painel.js', 'utf8');

function setup({failCSS = false} = {}) {
  const elements = {};
  for (const id of ['capture-form', 'capture-button', 'capture-status', 'load-map', 'map-status', 'map-points', 'map-config', 'map-intro']) {
    elements[id] = {handlers: {}, disabled: false, textContent: '', addEventListener(name, fn) {this.handlers[name] = fn;}, remove() {this.removed = true;}};
  }
  const untrusted = '<img src=x onerror=alert(1)>';
  elements['map-points'].textContent = JSON.stringify([{latitude: 0, longitude: 0, precisao: null, dispositivo: untrusted, capturado_em: '2026-01-01T00:00:00Z'}]);
  elements['map-config'].textContent = JSON.stringify({tile_url: 'https://tiles.example.invalid/{z}/{x}/{y}', attribution: 'Teste'});
  const resources = [], popups = [], tiles = [];
  const L = {
    map() {return {fitBounds() {}};},
    tileLayer(url, options) {tiles.push({url, options}); return {addTo() {return this;}, on() {}};},
    circleMarker() {return {addTo() {return this;}, bindPopup(node) {popups.push(node);}};},
  };
  const context = {L, window: {}, setTimeout() {}, document: {
    getElementById: id => elements[id],
    createElement(tag) {return {tag, set innerHTML(_) {throw new Error('HTML dinâmico proibido no teste');}};},
    head: {append(node) {resources.push(node); if (node.tag === 'link' && failCSS) node.onerror(); else node.onload();}},
  }};
  vm.runInNewContext(source, context);
  return {elements, resources, popups, tiles, untrusted, load: () => elements['load-map'].handlers.click()};
}

test('mapa solicita recursos somente apos clique e usa integridade e CORS anonimo', async () => {
  const state = setup();
  assert.equal(state.resources.length, 0);
  await state.load();
  const css = state.resources.find(item => item.tag === 'link');
  const js = state.resources.find(item => item.tag === 'script');
  assert.equal(css.integrity, 'sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=');
  assert.equal(js.integrity, 'sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=');
  assert.equal(css.crossOrigin, 'anonymous');
  assert.equal(js.crossOrigin, 'anonymous');
  assert.equal(state.popups[0].textContent.startsWith(state.untrusted), true);
  assert.equal(state.tiles[0].options.referrerPolicy, 'origin');
});

test('falha do CSS informa erro e permite nova tentativa sem criar mapa', async () => {
  const state = setup({failCSS: true});
  await state.load();
  assert.equal(state.tiles.length, 0);
  assert.equal(state.elements['load-map'].disabled, false);
  assert.match(state.elements['map-status'].textContent, /estilo do mapa/);
  assert.equal(state.elements['map-intro'].removed, undefined);
});
