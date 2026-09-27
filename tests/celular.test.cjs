const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync('rastreamento/static/rastreamento/celular.js','utf8');
async function setup({token='segredo-link', verifyOK=true, geoError=null, consent=true, deferred=false, malformed=false, sendStatus=201, verifyResult=undefined}={}) {
  const elements = {};
  for(const id of ['status','envio','enviar','autorizacao','vinculo','pessoa','dispositivo','validade','aviso-versao']) {
    elements[id]={textContent:'',checked:consent,disabled:false,hidden:true,handlers:{},addEventListener(n,f){this.handlers[n]=f;},reportValidity(){return true;},querySelector(){return {value:'csrf-test'};}};
  }
  elements["aviso-versao"].value = "2026-09-26.1";
  const sent=[];let captures=0,cleaned=false,finish;
  const context={document:{getElementById:id=>elements[id]},window:{isSecureContext:true,location:{hash:token?'#'+token:'',pathname:'/celular/'},history:{replaceState(){cleaned=true;}}},navigator:{geolocation:{getCurrentPosition(resolve,reject){captures++;if(geoError)reject(geoError);else {const position={coords:{latitude:1.234567891,longitude:2.3,accuracy:9},timestamp:1780000000000};if(deferred)finish=()=>resolve(position);else resolve(position);}}}},fetch:async(path,options)=>{sent.push({path,options});return {ok:path.includes('verificar')?verifyOK:true,status:path.includes('verificar')?(verifyOK?200:410):sendStatus,json:async()=>{if(malformed && path.includes('enviar'))throw new SyntaxError('HTML');return path.includes('verificar')?(verifyResult === undefined ? {pessoa:'Teste',dispositivo:'Celular',expira_em:'2026-09-25T20:00:00Z',detail:'Link indisponível'} : verifyResult):{detail:'Registrada'};}};}};
  await vm.runInNewContext(source,context);
  return {elements,sent,finish:()=>finish(),captures:()=>captures,cleaned:()=>cleaned,submit:()=>elements.envio.handlers.submit({preventDefault(){}})};
}
test('link ausente nao solicita dados ou localizacao',async()=>{const x=await setup({token:''});assert.equal(x.sent.length,0);assert.equal(x.captures(),0);});
test('remove fragmento e verifica vinculo sem coletar localizacao',async()=>{const x=await setup();assert.equal(x.cleaned(),true);assert.equal(x.captures(),0);assert.equal(x.sent[0].path,'/celular/verificar/');assert.equal(x.sent[0].options.headers['X-CSRFToken'],'csrf-test');assert.equal(x.elements.pessoa.textContent,'Teste');});
test('link recusado nao habilita envio',async()=>{const x=await setup({verifyOK:false});assert.equal(x.elements.vinculo.hidden,true);assert.equal(x.elements.envio.handlers.submit,undefined);});
test('sem autorizacao nao coleta',async()=>{const x=await setup({consent:false});await x.submit();assert.equal(x.captures(),0);assert.equal(x.sent.length,1);});
test('envio autorizado consome token na interface e nao repete',async()=>{const x=await setup();await x.submit();await x.submit();assert.equal(x.sent.length,2);const body=JSON.parse(x.sent[1].options.body);assert.equal(body.latitude,'1.2345679');assert.equal(body.autorizado,true);assert.equal(body.token,'segredo-link');assert.equal(x.elements.vinculo.hidden,true);});
test('permissao negada nao transmite posicao',async()=>{const x=await setup({geoError:{code:1}});await x.submit();assert.equal(x.sent.length,1);assert.match(x.elements.status.textContent,/Permissão negada/);});

test('envia a versao do aviso apresentado',async()=>{const x=await setup();await x.submit();assert.equal(JSON.parse(x.sent[1].options.body).aviso_versao,'2026-09-26.1');});


test('retirada de autorizacao enquanto aguarda GPS nao envia posicao',async()=>{const x=await setup({deferred:true});const pending=x.submit();x.elements.autorizacao.checked=false;x.finish();await pending;assert.equal(x.sent.length,1);assert.equal(x.elements.enviar.disabled,false);assert.match(x.elements.status.textContent,/Autorização retirada/);});

test('cliques simultaneos no celular nao duplicam captura ou envio',async()=>{const x=await setup({deferred:true});const pending=x.submit();await x.submit();assert.equal(x.captures(),1);x.finish();await pending;assert.equal(x.sent.length,2);});

test('resposta malformada ou status inesperado nao confirma registro',async()=>{for(const options of [{malformed:true},{sendStatus:200}]){const x=await setup(options);await x.submit();assert.equal(x.elements.vinculo.hidden,false);assert.doesNotMatch(x.elements.status.textContent,/Você pode fechar/);assert.match(x.elements.status.textContent,/confirmar/);}});

test('vinculo incompleto ou invalido nao habilita captura',async()=>{for(const verifyResult of [null,[],{}, {pessoa:'Teste',dispositivo:'Celular',expira_em:'invalid'}]){const x=await setup({verifyResult});assert.equal(x.elements.vinculo.hidden,true);assert.equal(x.elements.envio.handlers.submit,undefined);assert.equal(x.captures(),0);assert.match(x.elements.status.textContent,/confirmar/);}});
