"use strict";
(() => {
  const form = document.getElementById("capture-form");
  const button = document.getElementById("capture-button");
  const status = document.getElementById("capture-status");
  let sending = false;
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (sending || button.disabled || !form.reportValidity()) return;
    if (!window.isSecureContext || !navigator.geolocation) {
      status.textContent = "Localização indisponível. Use HTTPS ou localhost em um navegador compatível.";
      return;
    }
    const device = document.getElementById("capture-device").value;
    if (!device || !document.getElementById("capture-consent").checked) return;
    sending = true;
    button.disabled = true;
    status.textContent = "Aguardando sua permissão e a localização do navegador…";
    try {
      const position = await new Promise((resolve, reject) => navigator.geolocation.getCurrentPosition(resolve, reject, {enableHighAccuracy: true, timeout: 15000, maximumAge: 0}));
      const response = await fetch("/api/localizacoes/", {
        method: "POST", credentials: "same-origin",
        headers: {"Content-Type": "application/json", "X-CSRFToken": form.querySelector('[name="csrfmiddlewaretoken"]').value},
        body: JSON.stringify({dispositivo: device, latitude: position.coords.latitude.toFixed(7), longitude: position.coords.longitude.toFixed(7), precisao_metros: position.coords.accuracy, capturado_em: new Date(position.timestamp).toISOString()}),
      });
      if (!response.ok) {
        if (response.status === 401 || response.status === 403) throw new Error("Sua sessão expirou ou o envio não foi autorizado. Entre novamente e confira o compartilhamento.");
        if (response.status === 429) throw new Error("Muitos envios. Aguarde um minuto antes de tentar novamente.");
        if (response.status === 400) throw new Error("Envio recusado. Confira se o dispositivo e o compartilhamento continuam ativos.");
        throw new Error("Não foi possível confirmar o envio. Consulte o histórico antes de tentar novamente.");
      }
      status.textContent = "Localização registrada com sucesso. ";
      const refresh = document.createElement("a");
      refresh.href = window.location.href;
      refresh.textContent = "Atualizar o painel";
      status.append(refresh);
      document.getElementById("capture-consent").checked = false;
    } catch (error) {
      const errors = {1: "Permissão negada. Nenhuma localização foi enviada.", 2: "O navegador não conseguiu obter sua posição. Tente em um local com melhor sinal.", 3: "O tempo para obter a posição terminou. Tente novamente."};
      status.textContent = errors[error.code] || error.message || "Falha ao obter a localização.";
    } finally {
      sending = false;
      button.disabled = false;
    }
  });

  const loadMap = document.getElementById("load-map");
  const mapStatus = document.getElementById("map-status");
  loadMap.addEventListener("click", async () => {
    if (loadMap.disabled) return;
    loadMap.disabled = true;
    mapStatus.textContent = "Carregando mapa externo…";
    try {
      const points = JSON.parse(document.getElementById("map-points").textContent);
      const config = JSON.parse(document.getElementById("map-config").textContent);
      if (!points.length) throw new Error("Ainda não existem posições nesta página.");
      await Promise.race([new Promise((_, reject) => setTimeout(() => reject(new Error("O provedor demorou a responder. Tente novamente.")), 15000)), Promise.all([
        new Promise((resolve, reject) => {
          const css = document.createElement("link");
          css.rel = "stylesheet"; css.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
          css.onload = resolve; css.onerror = () => reject(new Error("Não foi possível carregar o estilo do mapa."));
          document.head.append(css);
        }),
        new Promise((resolve, reject) => {
          if (window.L) { resolve(); return; }
          const script = document.createElement("script");
          script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
          script.integrity = "sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=";
          script.crossOrigin = "anonymous";
          script.onload = resolve; script.onerror = () => reject(new Error("Não foi possível carregar o mapa. O histórico continua disponível abaixo."));
          document.head.append(script);
        }),
      ])]);
      document.getElementById("map-intro").remove();
      const map = L.map("map");
      const tiles = L.tileLayer(config.tile_url, {maxZoom: 19, attribution: config.attribution, referrerPolicy: "origin"}).addTo(map);
      tiles.on("tileerror", () => { mapStatus.textContent = "Algumas imagens do mapa não carregaram. As coordenadas permanecem no histórico."; });
      const bounds = [];
      points.forEach((point, index) => {
        const latlng = [point.latitude, point.longitude]; bounds.push(latlng);
        const popup = document.createElement("div");
        popup.textContent = `${point.dispositivo} · ${new Date(point.capturado_em).toLocaleString("pt-BR", {timeZone: "America/Fortaleza"})}`;
        L.circleMarker(latlng, {radius: index === 0 ? 9 : 6, color: "#146a58", fillOpacity: index === 0 ? 0.9 : 0.45}).addTo(map).bindPopup(popup);
        if (index === 0 && point.precisao !== null && Number.isFinite(point.precisao)) {
          L.circle(latlng, {radius: point.precisao, weight: 1, color: "#146a58", fillOpacity: 0.08}).addTo(map);
        }
      });
      map.fitBounds(bounds, {padding: [35, 35], maxZoom: 16});
      mapStatus.textContent = `${points.length} posição(ões) desta página. O ponto maior é o mais recente da página; o círculo indica a precisão informada. Se as imagens forem bloqueadas pelo provedor, consulte as coordenadas no histórico.`;
    } catch (error) {
      mapStatus.textContent = error.message;
      loadMap.disabled = false;
    }
  });
})();
