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
  const CLAVE = 'sp_guia_v3';      // v532 — enseña CÓMO funciona: abre un partido (cancha, Pulso, campana), el morado de la IA y Mi cuenta
  const NUNCA = CLAVE + '_nunca';
  const NOMBRE = { picks: 'Picks', vivo: 'En vivo', combinadas: 'Combinadas', mios: 'Mis picks', historial: 'Historial', planes: 'Planes' };
  // v532 — el usuario: «agrégale a la guía el morado de la IA… si es gratis, todo censurado pero que se sepa qué se
  // puede tener sin el VIP… la personalización de Telegram, ver el partido en vivo con la cancha, el Pulso… mostrar
  // cómo funciona». La guía ABRE un partido (cancha, Pulso, campana) y Mi cuenta; al gratis le enseña el morado con
  // candado. Sigue breve (15 pasos, una línea cada uno: test_v494).
  const PASOS = [
    { v: 'picks', sel: null, t: 'Bienvenido a SharPicks', d: 'Te enseñamos la app en un minuto. Toca «Siguiente» para avanzar.' },
    { v: 'picks', sel: '#destacados:not([hidden])', t: 'Los mejores del día', d: 'Los 💎 Diamante: nuestros picks más probables. Toca uno para verlo.' },
    { v: 'picks', sel: '#destacados .dest.ia-2, #destacados .dest.guia-demo', t: '✨ El morado de la IA', d: 'Los que la IA ve con mayor probabilidad brillan en morado: aciertan 91 % (medido).' },
    { v: 'picks', sel: '.busca-caja', t: 'Busca tu equipo', d: 'Elige el día arriba o escribe cualquier equipo: te salen sus partidos.' },
    { v: 'vivo', sel: null, t: '⚽ Mira el partido', d: 'La cancha en vivo: tiros, goles, presión y el minuto exacto.' },
    { v: 'vivo', sel: null, t: '⚡ Pulso en vivo', d: 'En el 2.º tiempo: lo más probable que pase ahora y lo que salió en el historial.' },
    { v: 'vivo', sel: '.ficha:not([hidden]) .campana, .ficha:not([hidden]) .equipos', t: '🔔 Avísame de este partido', d: 'Toca la campana y te avisamos por Telegram de lo que pase en este partido.' },
    { v: 'combinadas', sel: '#armador:not([hidden])', t: 'Arma tu combinada', d: 'Días (hoy a pasado), deportes, partidos y niveles. Las moradas de la IA van primero.' },
    { v: 'combinadas', sel: null, t: '🪙 Tu combinada paga', d: 'Si acierta, ganas monedas: 2 desde cuota 2,00, 3 desde 3,00 y 5 desde 5,00 (una al día).' },
    { v: 'combinadas', sel: '#combinadas-lista .dest, #combinadas-lista', t: 'Combinadas del día', d: 'Cuota y probabilidad de que se cumplan TODAS las patas.' },
    { v: 'mios', sel: '#tarjetas, #aviso, #nav [data-vista-ir="mios"]', t: 'Mis picks', d: 'En cualquier partido toca «☆ Seguir» y aparece aquí, con su resultado.' },
    { v: 'historial', sel: '#historial, #marcadores', t: 'Historial', d: 'Día, semana, mes, año o todo: todas las verdes y las rojas, sin esconder ninguna.' },
    { v: 'picks', sel: '#micuenta:not([hidden]) #caja-tg, #cuenta', t: '🔔 Avisos por Telegram', d: 'Conecta tu Telegram y elige qué te avisamos: tus deportes, el ⚡ Pulso o tus partidos.' },
    { v: 'planes', sel: '.planes-grid', t: 'Planes', d: 'Gratis, monedas por pick (si sale roja, te las regresamos) o VIP con todo.' },
    { v: 'picks', sel: '.ayuda-btn', t: '¿Dudas?', d: 'Aquí está la ayuda con lo que significa cada cosa. Desde ahí repites esta guía.' },
  ];
  // lo que cambia para quien NO es VIP: se le enseña qué tendría (con candado) y qué sí tiene gratis
  const D_GRATIS = {
    '✨ El morado de la IA': '🔒 VIP: la IA ilumina en morado los de mayor probabilidad (91 % medido).',
    '⚡ Pulso en vivo': 'Gratis: «otro gol» y «2 córners». Con VIP o 🪙 monedas, todo el Pulso al minuto.',
    'Arma tu combinada': 'Elige días, deportes y partidos. 🥇 Oro gratis; otros niveles, con 🪙 según su cuota.',
    '🔔 Avisos por Telegram': 'Entra y conecta tu Telegram: te avisamos de tus partidos (lo VIP, con candado).',
  };
  const esVip = () => !!(window.SPX && SPX.esVip && SPX.esVip());
  const conCuenta = () => !!(window.SPX && SPX.yo && SPX.yo.user);
  // abrir lo que el paso enseña (y cerrarlo al salir de él)
  // la cancha y el Pulso sólo existen con partido en vivo (y el Pulso, en el 2.º tiempo): se enseñan SIEMPRE con una
  // captura real (Atlético-MG–Cruzeiro, 29-oct), para que se vea igual a cualquier hora. La campana, en un partido real.
  const IMG = { '⚽ Mira el partido': 'marca/guia-cancha.jpg', '⚡ Pulso en vivo': 'marca/guia-pulso.jpg' };
  const FICHA = new Set(['🔔 Avísame de este partido']);
  function abrirFicha() {
    if (document.querySelector('.ficha:not([hidden]) .cancha')) return Promise.resolve();
    const est = window.SP && SP.estado; if (!est) return Promise.resolve();
    const todos = est.picks.concat(est.analisis || []).filter((p) => p.deporte === 'Fútbol' && p.espn);
    const vivo = (p) => { const v = est.vivo && est.vivo[p.espn]; return v && v.fase === 'in'; };
    const fin = (p) => { const v = est.vivo && est.vivo[p.espn]; return v && v.fase === 'post'; };
    const p = todos.find(vivo) || todos.find((x) => !fin(x) && x.estado === 'pendiente') || todos[0];
    if (!p) return Promise.resolve();
    const b = document.createElement('button'); b.hidden = true; b.dataset.ficha = p.id;
    document.body.appendChild(b); b.click(); b.remove();
    return espera(1500);
  }
  function cerrarFicha() { const x = document.querySelector('.ficha:not([hidden]) [data-cerrar]'); if (x) x.click(); }
  function abrirCuenta() {
    if (!conCuenta()) return Promise.resolve();
    const b = document.querySelector('[data-mi-cuenta]'); if (b) b.click();
    return espera(1800);
  }
  function cerrarCuenta() { const m = document.getElementById('micuenta'); if (m && !m.hidden) { const x = m.querySelector('[data-cerrar-cuenta]'); if (x) x.click(); } }
  // al gratis: el primer destacado con el morado «de muestra» y candado (se quita al seguir)
  function demoMorado() {
    if (esVip() || document.querySelector('#destacados .dest.ia-2')) return;
    const d = document.querySelector('#destacados .dest'); if (!d) return;
    d.classList.add('ia-2', 'guia-demo');
    const f = d.querySelector('.fila');
    if (f && !d.querySelector('.ia-sello')) f.insertAdjacentHTML('afterend', '<span class="ia-sello s2 guia-demo-sello">🔒 Modelo + IA: mayor probabilidad · VIP</span>');
  }
  function quitarDemo() {
    document.querySelectorAll('.guia-demo').forEach((d) => d.classList.remove('ia-2', 'guia-demo'));
    document.querySelectorAll('.guia-demo-sello').forEach((x) => x.remove());
  }
  let cambioDia = false;
  function destacadosDeManana() {
    if (document.querySelector('#destacados:not([hidden]) .dest')) return Promise.resolve();
    const b = document.querySelector('[data-dia="manana"]'); if (b) { b.click(); cambioDia = true; }
    return espera(600);
  }
  async function preparar(p) {
    if (!FICHA.has(p.t)) cerrarFicha();
    if (p.t !== '🔔 Avisos por Telegram') cerrarCuenta();
    if (p.t !== '✨ El morado de la IA') quitarDemo();
    if (FICHA.has(p.t)) await abrirFicha();
    if (p.t === 'Los mejores del día') await destacadosDeManana();      // sin destacados hoy, los de mañana
    if (p.t === '✨ El morado de la IA') demoMorado();
    if (p.t === '🔔 Avisos por Telegram') await abrirCuenta();
  }
  const texto = (p) => (!esVip() && D_GRATIS[p.t] && !(p.t === '🔔 Avisos por Telegram' && conCuenta()) ? D_GRATIS[p.t] : p.d);
  let i = 0, capa = null, luz = null, caja = null, nunca = false, desde = 'picks';
  const visible = (el) => { if (!el) return false; const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  // v532 — con varias opciones, la PRIMERA de la lista que esté a la vista (no la primera de la página): la campana antes que el marcador
  const objetivo = (p) => {
    if (!p.sel) return null;
    for (const s of p.sel.split(/,(?![^(]*\))/)) { const el = [...document.querySelectorAll(s.trim())].find(visible); if (el) return el; }
    return null;
  };
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
    cerrarFicha(); cerrarCuenta(); quitarDemo();
    if (cambioDia) { cambioDia = false; const h = document.querySelector('[data-dia="hoy"]'); if (h) h.click(); }
    window.removeEventListener('resize', colocar);
    window.removeEventListener('scroll', colocar);
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
    const m = 8, sup = seguro() + 8, techo = cabecera();
    if (el) {
      const r0 = el.getBoundingClientRect(), arriba0 = Math.max(r0.top, techo + m);
      const r = { top: arriba0, left: r0.left, width: r0.width, height: Math.max(40, r0.bottom - arriba0) };
      const alto = Math.min(r.height + 2 * m, window.innerHeight * 0.5);
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
  // v540 — el usuario: «la guía se traba un poco» y «un botón de regresar». Antes un toque mientras la guía cambiaba de
  // pantalla (0,7-1,8 s) se tiraba y parecía congelada: ahora el último toque se guarda y se cumple al terminar, y el
  // botón dice «…» mientras tanto. «Atrás» va al paso anterior que se pueda enseñar.
  let ocupado = false, pendiente = null;
  async function paso(n, dir) {
    if (!caja) return;
    dir = dir || 1;
    if (ocupado) { pendiente = [n, dir]; return; }
    ocupado = true;
    const b = caja.querySelector('.guia-sig'); if (b) { b.disabled = true; b.textContent = '…'; }
    try {
      // cada paso en su pantalla; si su parte no está a la vista, se salta (hacia donde se iba)
      for (; n >= 0 && n < PASOS.length; n += dir) {
        if (await irA(PASOS[n].v)) { if (!caja) return; }
        await preparar(PASOS[n]);                                   // v532 — abre lo que el paso enseña
        if (!caja) return;
        if (!PASOS[n].sel || objetivo(PASOS[n])) break;
      }
      if (n >= PASOS.length) { cerrar(true); return; }
      if (n < 0) n = 0;
      i = n;
      const p = PASOS[i], el = objetivo(p), ultimo = i === PASOS.length - 1;
      caja.innerHTML = '<div class="guia-num">' + NOMBRE[p.v] + ' · ' + (i + 1) + ' de ' + PASOS.length + '</div><div class="guia-t">' + p.t + '</div><p class="guia-d">' + texto(p) + '</p>' +
        (IMG[p.t] ? '<img class="guia-img" src="' + IMG[p.t] + '?v=532" alt="Así se ve: ' + p.t + '" loading="eager">' : '') +
        '<label class="guia-nunca"><input type="checkbox"' + (nunca ? ' checked' : '') + '> No volver a mostrar la guía</label>' +
        '<div class="guia-bot"><button type="button" class="guia-omitir">' + (ultimo ? 'Cerrar' : 'Omitir') + '</button>' +
        (i > 0 ? '<button type="button" class="guia-atras">Atrás</button>' : '') +
        '<button type="button" class="guia-sig">' + (ultimo ? 'Listo' : 'Siguiente') + '</button></div>';
      const img = caja.querySelector('.guia-img'); if (img) img.addEventListener('load', colocar);   // se recoloca al cargar
      if (el) llevar(el);
      requestAnimationFrame(colocar);
      setTimeout(colocar, 350);                                      // por si la página aún se acomodaba
    } finally {
      ocupado = false;
      if (pendiente && caja) { const [pn, pd] = pendiente; pendiente = null; if (pn !== i) paso(pn, pd); }   // un toque repetido no salta dos pasos
      else pendiente = null;
    }
  }
  // el alto de la cabecera fija (lo iluminado y el scroll quedan debajo de ella)
  function cabecera() { const t = document.querySelector('header.top'); return t ? t.getBoundingClientRect().bottom : 0; }
  // lleva lo que se enseña a la vista, sin animación (la luz se mide justo después) y debajo de la cabecera
  function llevar(el) {
    const r = el.getBoundingClientRect(), techo = cabecera(), alto = window.innerHeight - techo;
    const y = r.height > alto * 0.6 ? r.top - techo - 12 : r.top - techo - (alto - r.height) / 2;
    window.scrollTo({ top: Math.max(0, window.scrollY + y), behavior: 'instant' });
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
      if (e.target.closest('.guia-sig')) paso(i + 1, 1);
      else if (e.target.closest('.guia-atras')) paso(i - 1, -1);
      else if (e.target.closest('.guia-omitir')) cerrar(false);
    });
    capa.addEventListener('click', () => paso(i + 1, 1));   // tocar fuera también avanza
    window.addEventListener('resize', colocar);
    window.addEventListener('scroll', colocar, { passive: true });   // si se mueve la página, la luz la sigue
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
