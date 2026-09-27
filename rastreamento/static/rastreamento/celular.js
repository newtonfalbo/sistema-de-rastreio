"use strict";
(async () => {
  let token = window.location.hash.slice(1);
  window.history.replaceState(null, "", window.location.pathname);
  const status = document.getElementById("status");
  const form = document.getElementById("envio");
  const button = document.getElementById("enviar");
  const consent = document.getElementById("autorizacao");
  const section = document.getElementById("vinculo");
  let busy = false;
  async function post(path, data) {
    const response = await fetch(path, {method: "POST", credentials: "same-origin", headers: {"Content-Type": "application/json", "X-CSRFToken": form.querySelector('[name="csrfmiddlewaretoken"]').value}, body: JSON.stringify({token, ...data})});
    const uncertain = "Não foi possível confirmar a resposta. Consulte o responsável antes de tentar novamente.";
    let result;
    try {result = await response.json();} catch (_) {throw new Error(uncertain);}
    if (!result || typeof result !== "object" || Array.isArray(result)) throw new Error(uncertain);
    if (!response.ok) throw new Error(typeof result.detail === "string" ? result.detail : "Envio recusado.");
    const verifying = path === "/celular/verificar/";
    if (response.status !== (verifying ? 200 : 201)) throw new Error(uncertain);
    if (verifying) {
      if (typeof result.pessoa !== "string" || typeof result.dispositivo !== "string" ||
          typeof result.expira_em !== "string" || !Number.isFinite(Date.parse(result.expira_em))) throw new Error(uncertain);
    } else if (typeof result.detail !== "string") {throw new Error(uncertain);}
    return result;
  }
  if (!token) {status.textContent = "Abra o link completo enviado pelo responsável ou leia novamente o QR Code.";return;}
  try {
    const result = await post("/celular/verificar/", {});
    document.getElementById("pessoa").textContent = result.pessoa;
    document.getElementById("dispositivo").textContent = result.dispositivo;
    document.getElementById("validade").textContent = new Date(result.expira_em).toLocaleString("pt-BR");
    section.hidden = false;
    status.textContent = "Confira o vínculo. A posição só será obtida após sua autorização e o toque no botão.";
  } catch (error) {status.textContent = error.message;return;}
  form.addEventListener("submit", async event => {
    event.preventDefault();
    if (busy || !token || !consent.checked || !form.reportValidity()) return;
    if (!window.isSecureContext || !navigator.geolocation) {status.textContent = "Abra este link HTTPS em um navegador compatível com localização.";return;}
    busy = true;button.disabled = true;
    status.textContent = "Aguardando sua permissão e a posição do aparelho…";
    try {
      const position = await new Promise((resolve,reject) => navigator.geolocation.getCurrentPosition(resolve,reject,{enableHighAccuracy:true,maximumAge:0,timeout:20000}));
      if (!consent.checked) throw new Error("Autorização retirada. Nenhuma posição foi enviada.");
      const result = await post("/celular/enviar/", {autorizado:true,aviso_versao:document.getElementById("aviso-versao").value,latitude:position.coords.latitude.toFixed(7),longitude:position.coords.longitude.toFixed(7),precisao_metros:position.coords.accuracy,capturado_em:new Date(position.timestamp).toISOString()});
      token = "";section.hidden = true;status.textContent = result.detail + " Você pode fechar esta página.";
    } catch (error) {
      const errors = {1:"Permissão negada. Nenhuma posição foi enviada.",2:"Localização indisponível. Confira o GPS e tente novamente.",3:"O aparelho demorou a obter a posição. Tente novamente."};
      status.textContent = errors[error.code] || error.message;
    } finally {busy=false;button.disabled=false;}
  });
})();
