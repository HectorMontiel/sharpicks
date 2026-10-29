// v512 — LA MUDANZA DE sharpicks.pages.dev A sharpicksapp.com, SIN PERDER LA SESIÓN.
// La sesión de Supabase y las preferencias viven en localStorage, que es de cada dominio. En el dominio viejo
// se empacan (sólo las claves de SharPicks) en el fragmento # y se va al nuevo; en el nuevo se desempacan
// ANTES de que cuenta.js cree el cliente de Supabase (este script va primero en index.html).
// Candados: en el nuevo sólo se acepta si se llega DESDE el dominio viejo (referrer), nunca se pisa una
// sesión que ya exista, y el fragmento se borra de la barra en el acto. Así un enlace preparado por otro no
// puede meterte en su cuenta.
(function () {
  var VIEJO = 'sharpicks.pages.dev', NUEVO = 'https://sharpicksapp.com';
  var nuestra = function (k) { return /^(sb-|sp_|sharpicks-)/.test(k || ''); };
  try {
    if (location.hostname === VIEJO) {
      var d = {};
      for (var i = 0; i < localStorage.length; i++) {
        var k = localStorage.key(i);
        if (nuestra(k)) d[k] = localStorage.getItem(k);
      }
      var h = Object.keys(d).length ? '#mudanza=' + encodeURIComponent(btoa(unescape(encodeURIComponent(JSON.stringify(d))))) : '';
      location.replace(NUEVO + location.pathname + location.search + h);
      return;
    }
    var m = location.hash.match(/^#mudanza=([^&]+)/);
    if (!m) return;
    history.replaceState(null, '', location.pathname + location.search);
    if ((document.referrer || '').indexOf('https://' + VIEJO + '/') !== 0) return;
    var datos = JSON.parse(decodeURIComponent(escape(atob(decodeURIComponent(m[1])))));
    Object.keys(datos).forEach(function (k) {
      if (nuestra(k) && typeof datos[k] === 'string' && localStorage.getItem(k) == null) localStorage.setItem(k, datos[k]);
    });
    try { sessionStorage.setItem('sp_mudado', '1'); } catch (e) { /* sin sessionStorage */ }
  } catch (e) { /* sin localStorage: se entra sin sesión, igual que antes */ }
})();
