const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync('rastreamento/static/rastreamento/celular.js','utf8');
async function setup({token='segredo-link', verifyOK=true, geoError=null, consent=true}={}) {
  const elements = {};
  for(const id of ['status','envio','enviar','autorizacao','vinculo','pessoa','dispositivo','validade']) {
    elements[id]={textContent:'',checked:consent,disabled:false,hidden:true,handlers:{},addEventListener(n,f){this.handlers[n]=f;},reportValidity(){return true;},querySelector(){return {value:'csrf-test'};}};
  }
  const sent=[];let captures=0,cleaned=false;
  const context={document:{getElementById:id=>elements[id]},window:{isSecureContext:true,location:{hash:token?'#'+token:'',pathname:'/celular/'},history:{replaceState(){cleaned=true;}}},navigator:{geolocation:{getCurrentPosition(resolve,reject){captures++;if(geoError)reject(geoError);else resolve({coords:{latitude:1.234567891,longitude:2.3,accuracy:9},timestamp:1780000000000});}}},fetch:async(path,options)=>{sent.push({path,options});return {ok:path.includes('verificar')?verifyOK:true,json:async()=>path.includes('verificar')?{pessoa:'Teste',dispositivo:'Celular',expira_em:'2026-09-25T20:00:00Z',detail:'Link indisponível'}:{detail:'Registrada'}};}};
  await vm.runInNewContext(source,context);
  return {elements,sent,captures:()=>captures,cleaned:()=>cleaned,submit:()=>elements.envio.handlers.submit({preventDefault(){}})};
}
test('link ausente nao solicita dados ou localizacao',async()=>{const x=await setup({token:''});assert.equal(x.sent.length,0);assert.equal(x.captures(),0);});
test('remove fragmento e verifica vinculo sem coletar localizacao',async()=>{const x=await setup();assert.equal(x.cleaned(),true);assert.equal(x.captures(),0);assert.equal(x.sent[0].path,'/celular/verificar/');assert.equal(x.sent[0].options.headers['X-CSRFToken'],'csrf-test');assert.equal(x.elements.pessoa.textContent,'Teste');});
test('link recusado nao habilita envio',async()=>{const x=await setup({verifyOK:false});assert.equal(x.elements.vinculo.hidden,true);assert.equal(x.elements.envio.handlers.submit,undefined);});
test('sem autorizacao nao coleta',async()=>{const x=await setup({consent:false});await x.submit();assert.equal(x.captures(),0);assert.equal(x.sent.length,1);});
test('envio autorizado consome token na interface e nao repete',async()=>{const x=await setup();await x.submit();await x.submit();assert.equal(x.sent.length,2);const body=JSON.parse(x.sent[1].options.body);assert.equal(body.latitude,'1.2345679');assert.equal(body.autorizado,true);assert.equal(body.token,'segredo-link');assert.equal(x.elements.vinculo.hidden,true);});
test('permissao negada nao transmite posicao',async()=>{const x=await setup({geoError:{code:1}});await x.submit();assert.equal(x.sent.length,1);assert.match(x.elements.status.textContent,/Permissão negada/);});
