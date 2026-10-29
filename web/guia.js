// v494 — LA GUÍA DE LA APP. El usuario: «una guía interactiva de cómo se usa la app: una ventana que
// indica dónde picar para hacer cada cosa, que sólo le vas picando Siguiente para que avance, o se le puede
// dar Omitir; breve, simple y que explique muy fácil el uso de la app». Cada paso ilumina una parte de la
// pantalla; si esa parte no está a la vista (p. ej. no hay Destacados hoy), el paso se salta.
// v495 — «falta la guía para Combinadas, En vivo y las demás secciones… se lanza 1 vez: cuando se abre
// la app se hace la guía de TODAS las secciones, no por separado». Una sola guía que recorre las secciones
// ella misma (cambia de pantalla en cada parte) y al final vuelve a Picks. Sale sola la primera vez; la
// casilla «No volver a mostrar» la apaga para siempre, y la ayuda («?» → Ver la guía) la repite.
// v498 — sale CADA VEZ que se abre la app hasta que se marca esa casilla.
(function () {
  'use strict';
  const CLAVE = 'sp_guia_v1';
  const NUNCA = CLAVE + '_nunca';
  const NOMBRE = { picks: 'Picks', vivo: 'En vivo', combinadas: 'Combinadas', mios: 'Mis picks', historial: 'Historial', planes: 'Planes' };
  const PASOS = [
    { v: 'picks', sel: null, t: 'Bienvenido a SharPicks', d: 'Te enseñamos la app en un minuto. Toca «Siguiente» para avanzar.' },
    { v: 'picks', sel: '#destacados:not([hidden])', t: 'Los mejores del día', d: 'Los 💎 Diamante: nuestros picks más probables. Toca uno para verlo.' },
    { v: 'picks', sel: '#pestanas', t: 'Elige el día', d: 'Hoy, mañana, pasado o ayer.' },
    { v: 'picks', sel: '.busca-caja', t: 'Busca tu equipo', d: 'Escribe cualquier equipo y te salen sus partidos de todos los días.' },
    { v: 'picks', sel: '#tarjetas .partido-fila, #tarjetas .liga-cab', t: 'Abre un partido', d: 'Toca un partido: el pick, sus estadísticas, la tabla y el marcador en vivo.' },
    { v: 'vivo', sel: '#tarjetas .partido-fila, #nav [data-vista-ir="vivo"]', t: 'En vivo', d: 'Lo que se juega ahora, con su minuto, y si tu pick ya se cumplió.' },
    { v: 'combinadas', sel: '#armador:not([hidden])', t: 'Arma tu combinada', d: 'Elige los niveles y cuántas patas, y toca «Armar».' },
    { v: 'combinadas', sel: '#combinadas-lista .dest, #combinadas-lista', t: 'Combinadas del día', d: 'Cuota y probabilidad de que se cumplan TODAS las patas.' },
    { v: 'mios', sel: '#tarjetas, #aviso, #nav [data-vista-ir="mios"]', t: 'Mis picks', d: 'En cualquier partido toca «☆ Seguir» y aparece aquí, con su resultado.' },
    { v: 'historial', sel: '#historial, #marcadores', t: 'Historial', d: 'Todas las verdes y las rojas, sin esconder ninguna: el acierto real de cada nivel.' },
    { v: 'planes', sel: '.planes-grid', t: 'Planes', d: 'Gratis, monedas por pick (si sale roja, te las regresamos) o VIP con todo.' },
    { v: 'picks', sel: '.ayuda-btn', t: '¿Dudas?', d: 'Aquí está la ayuda con lo que significa cada cosa. Desde ahí repites esta guía.' },
  ];
  let i = 0, capa = null, luz = null, caja = null, nunca = false, desde = 'picks';
  const visible = (el) => { if (!el) return false; const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const objetivo = (p) => (p.sel ? [...document.querySelectorAll(p.sel)].find(visible) || null : null);
  const vista = () => (window.SP && SP.estado && SP.estado.vista) || 'picks';
  const espera = (ms) => new Promise((r) => setTimeout(r, ms));
  function irA(v) {
    if (vista() === v) return Promise.resolve(false);
    const b = document.querySelector('#nav [data-vista-ir="' + v + '"]');
    if (b) b.click();
    return espera(700).then(() => true);
  }
  // v498 — el usuario: «cada que se abra la app, en cualquier usuario, debe aparecer, a menos que ya haya picado
  // la casilla de no volver a mostrar». Sólo la casilla la apaga (terminarla u omitirla ya no).
  function yaVista() { try { return !!localStorage.getItem(NUNCA); } catch (e) { return false; } }

  function cerrar(hecho) {
    try { localStorage.setItem(CLAVE, hecho ? 'hecha' : 'omitida'); if (nunca) localStorage.setItem(NUNCA, '1'); } catch (e) { /* sin almacenamiento: no pasa nada */ }
    [capa, luz, caja].forEach((x) => x && x.remove());
    capa = luz = caja = null;
    window.removeEventListener('resize', colocar);
    irA(desde);                       // vuelve a donde estaba (la primera vez, Picks)
    window.scrollTo({ top: 0 });
  }
  // v514 — el alto de la barra de estado del iPhone (app instalada): la caja nunca queda debajo de la hora
  let _seguro = null;
  function seguro() {
    if (_seguro == null) {
      const d = document.createElement('div');
      d.style.cssText = 'position:fixed;top:0;height:env(safe-area-inset-top);visibility:hidden;pointer-events:none';
      document.body.appendChild(d); _seguro = d.offsetHeight || 0; d.remove();
    }
    return _seguro;
  }
  function colocar() {
    if (!caja) return;
    const el = objetivo(PASOS[i]);
    const m = 8, sup = seguro() + 8;
    if (el) {
      const r = el.getBoundingClientRect(), alto = Math.min(r.height + 2 * m, window.innerHeight * 0.5);
      Object.assign(luz.style, { display: 'block', top: (r.top - m) + 'px', left: Math.max(4, r.left - m) + 'px',
        width: Math.min(window.innerWidth - 8, r.width + 2 * m) + 'px', height: alto + 'px' });
      capa.classList.add('con-luz');
      const ch = caja.offsetHeight, abajo = r.top - m + alto + 12, arriba = r.top - m - 12 - ch;
      caja.style.top = Math.max(sup, abajo + ch < window.innerHeight - 8 || arriba < sup ? Math.min(abajo, window.innerHeight - ch - 8) : arriba) + 'px';
    } else {
      luz.style.display = 'none';
      capa.classList.remove('con-luz');
      caja.style.top = Math.max(sup + 8, (window.innerHeight - caja.offsetHeight) / 2) + 'px';
    }
  }
  let ocupado = false;
  async function paso(n) {
    if (ocupado || !caja) return;
    ocupado = true;
    try {
      // cada paso en su pantalla; si su parte no está a la vista, se salta
      for (; n < PASOS.length; n++) {
        if (await irA(PASOS[n].v)) { if (!caja) return; }
        if (!PASOS[n].sel || objetivo(PASOS[n])) break;
      }
      if (n >= PASOS.length) { cerrar(true); return; }
      i = n;
      const p = PASOS[i], el = objetivo(p), ultimo = i === PASOS.length - 1;
      caja.innerHTML = '<div class="guia-num">' + NOMBRE[p.v] + ' · ' + (i + 1) + ' de ' + PASOS.length + '</div><div class="guia-t">' + p.t + '</div><p class="guia-d">' + p.d + '</p>' +
        '<label class="guia-nunca"><input type="checkbox"' + (nunca ? ' checked' : '') + '> No volver a mostrar la guía</label>' +
        '<div class="guia-bot"><button type="button" class="guia-omitir">' + (ultimo ? 'Cerrar' : 'Omitir') + '</button>' +
        '<button type="button" class="guia-sig">' + (ultimo ? 'Listo' : 'Siguiente') + '</button></div>';
      if (el) el.scrollIntoView({ block: el.getBoundingClientRect().height > window.innerHeight * 0.5 ? 'start' : 'center' });
      requestAnimationFrame(colocar);
    } finally { ocupado = false; }
  }
  function empezar() {
    if (caja) return;
    desde = vista();
    capa = document.createElement('div'); capa.className = 'guia-capa';
    luz = document.createElement('div'); luz.className = 'guia-luz';
    caja = document.createElement('div'); caja.className = 'guia-caja'; caja.setAttribute('role', 'dialog'); caja.setAttribute('aria-label', 'Guía de la app');
    document.body.append(capa, luz, caja);
    caja.addEventListener('change', (e) => { if (e.target.closest('.guia-nunca')) nunca = !!e.target.checked; });
    caja.addEventListener('click', (e) => {
      if (e.target.closest('.guia-sig')) paso(i + 1);
      else if (e.target.closest('.guia-omitir')) cerrar(false);
    });
    capa.addEventListener('click', () => paso(i + 1));   // tocar fuera también avanza
    window.addEventListener('resize', colocar);
    paso(0);
  }
  window.SPGuia = { empezar, PASOS };
  // desde la ayuda: la guía completa otra vez
  document.addEventListener('click', (e) => {
    if (!e.target.closest('[data-guia]')) return;
    const a = document.getElementById('ayuda'); if (a) a.hidden = true;
    empezar();
  });
  // la primera vez, sola (cuando ya cargaron los picks, para que haya qué señalar)
  if (!yaVista()) {
    const t0 = Date.now();
    const esperar = setInterval(() => {
      const listo = document.querySelector('#tarjetas .partido-fila, #tarjetas .liga-cab');
      if (listo || Date.now() - t0 > 15000) { clearInterval(esperar); if (!document.querySelector('.ficha:not([hidden])')) empezar(); }
    }, 500);
  }
})();
