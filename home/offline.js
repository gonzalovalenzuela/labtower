// ES: Página «Sin conexión»: idioma y tema de LabTower, y reintento solo cada 10 s (o con el botón). Al volver el servidor, recarga la página pedida.
// EN: "No connection" page: LabTower's language and theme, and an automatic retry every 10 s (or with the button). When the server is back, it reloads the requested page.
(function () {
  var d = document.documentElement, t = null, lang = null;
  try { t = localStorage.getItem("pi-theme"); lang = localStorage.getItem("pi-lang"); } catch (e) { /* sin almacenamiento / no storage */ }
  if (t === "light" || t === "dark") d.setAttribute("data-theme", t);
  if (!lang) lang = (navigator.language || "es").slice(0, 2) === "es" ? "es" : "en";
  var TX = {
    es: { t: "Sin conexión con LabTower", m: "No se pudo llegar al servidor. Si estás fuera de casa, conéctate a la VPN.", a: "Se vuelve a intentar solo.", r: "Reintentar" },
    en: { t: "No connection to LabTower", m: "The server could not be reached. If you are away from home, connect to the VPN.", a: "It retries on its own.", r: "Retry" }
  }[lang === "en" ? "en" : "es"];
  d.lang = lang === "en" ? "en" : "es";
  ["t", "m", "a", "r"].forEach(function (k) { document.getElementById(k).textContent = TX[k]; });
  var btn = document.getElementById("r"), busy = false;
  function retry() {
    if (busy) return; busy = true; btn.disabled = true;
    fetch("/manifest.webmanifest", { cache: "no-store" })
      .then(function (r) { if (r.ok) location.reload(); })
      .catch(function () { /* sigue sin conexión / still offline */ })
      .then(function () { busy = false; btn.disabled = false; });
  }
  btn.addEventListener("click", retry);
  setInterval(retry, 10000);
  window.addEventListener("online", retry);
})();
