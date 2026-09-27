const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync('rastreamento/static/rastreamento/painel.js', 'utf8');
function setup({secure = true, checked = true, error = null, response = {ok:true,status:201}, deferred = false} = {}) {
  const elements = {};
  for (const id of ['capture-form','capture-button','capture-status','capture-device','capture-consent','capture-aviso','load-map','map-status']) {
    elements[id] = {disabled:false, checked, value: 'device-123', textContent:'', handlers:{},
      addEventListener(name, fn) {this.handlers[name] = fn;}, reportValidity() {return true;},
      querySelector() {return {value:'csrf-test'};}, append() {}};
  }
  elements["capture-aviso"].value = "2026-09-26.1";
  let calls = 0, sent = [], resolvePosition;
  const context = {document: {getElementById:id=>elements[id], createElement:()=>({})},
    window: {isSecureContext:secure, location:{href:'http://localhost/'}},
    navigator:{geolocation:{getCurrentPosition(resolve,reject) {calls++; if(deferred){resolvePosition=resolve;return;} if(error) reject(error); else resolve({coords:{latitude:-3.731912345,longitude:-38.526712345,accuracy:10},timestamp:1780000000000});}}},
    fetch:async(url,options)=>{sent.push({url,options});return response;}};
  vm.runInNewContext(source, context);
  return {elements, submit:()=>elements['capture-form'].handlers.submit({preventDefault(){}}), calls:()=>calls, sent,
    resolve:()=>resolvePosition({coords:{latitude:0,longitude:0,accuracy:0},timestamp:1780000000000})};
}
test('nao coleta automaticamente e exige consentimento', async()=>{const x=setup({checked:false}); assert.equal(x.calls(),0);await x.submit();assert.equal(x.calls(),0);});
test('contexto inseguro nao coleta',async()=>{const x=setup({secure:false});await x.submit();assert.equal(x.calls(),0);assert.match(x.elements['capture-status'].textContent,/HTTPS/);});
test('envia uma posicao com CSRF e sete casas decimais',async()=>{const x=setup();await x.submit();assert.equal(x.sent.length,1);assert.equal(x.sent[0].options.headers['X-CSRFToken'],'csrf-test');const body=JSON.parse(x.sent[0].options.body);assert.equal(body.latitude,'-3.7319123');assert.equal(body.dispositivo,'device-123');assert.equal(x.elements['capture-consent'].checked,false);assert.match(x.elements['capture-status'].textContent,/sucesso/);});
test('permissao negada nao envia e reabilita botao',async()=>{const x=setup({error:{code:1}});await x.submit();assert.equal(x.sent.length,0);assert.match(x.elements['capture-status'].textContent,/Permissão negada/);assert.equal(x.elements['capture-button'].disabled,false);});
test('erro da API nao e apresentado como sucesso',async()=>{const x=setup({response:{ok:false,status:400}});await x.submit();assert.match(x.elements['capture-status'].textContent,/Envio recusado/);});

test('sucesso HTTP inesperado nao confirma criacao nem repete envio',async()=>{for(const status of [200,202,204]){const x=setup({response:{ok:true,status}});await x.submit();assert.match(x.elements['capture-status'].textContent,/Não foi possível confirmar/);assert.doesNotMatch(x.elements['capture-status'].textContent,/sucesso/);assert.equal(x.elements['capture-consent'].checked,true);assert.equal(x.elements['capture-button'].disabled,false);assert.equal(x.sent.length,1);}});
test('cliques simultaneos nao duplicam coleta',async()=>{const x=setup({deferred:true});const first=x.submit();await x.submit();assert.equal(x.calls(),1);x.resolve();await first;assert.equal(x.sent.length,1);});

test('retirar autorizacao enquanto aguarda GPS impede envio', async()=>{const x=setup({deferred:true});const pending=x.submit();x.elements['capture-consent'].checked=false;x.resolve();await pending;assert.equal(x.sent.length,0);assert.match(x.elements['capture-status'].textContent,/Nenhuma/);});

test('trocar dispositivo enquanto aguarda GPS impede envio', async()=>{const x=setup({deferred:true});const pending=x.submit();x.elements['capture-device'].value='other-device';x.resolve();await pending;assert.equal(x.sent.length,0);});

test('envia a versao do aviso apresentado com autorizacao', async()=>{const x=setup();await x.submit();const body=JSON.parse(x.sent[0].options.body);assert.equal(body.autorizado,true);assert.equal(body.aviso_versao,'2026-09-26.1');});
