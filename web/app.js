// v377-v378 — El sitio sólo LEE: los picks de Supabase (o de datos/hoy.json)
// y, EN VIVO, el marcador y las estadísticas directo de ESPN (permite leerlo
// desde la página), cada 30 s, sólo de los partidos que se están jugando.
(function () {
  const C = window.CONFIG || {};
  const ZONA = 'America/Mexico_City';
  const ESPN = 'https://site.api.espn.com/apis/site/v2/sports/';
  const $ = (id) => document.getElementById(id);
  const estado = { pfm: {}, dia: 'hoy', deporte: 'Todos', nivel: 'Todos', soloElige: false, orden: 'hora', picks: [], vivo: {}, vivoCursor: 0, errorPicks: false, respaldoPicks: false, errorCombinadas: false };

  // v483 — «cuando busco algún equipo la aplicación se traba»: cada repintado creaba miles de
  // Intl.DateTimeFormat (uno por llamada, y `diaDe` se llama varias veces por pick). Los formateadores se
  // crean UNA vez y el día de cada instante se recuerda: pintar bajó de ~620 ms a lo que se mide en test_v483.
  const FMT = (o) => new Intl.DateTimeFormat(o.loc || 'es-MX', Object.assign({ timeZone: ZONA }, o.op));
  const F_DIA = FMT({ loc: 'en-CA', op: {} }), F_HORA = FMT({ op: { hour: '2-digit', minute: '2-digit' } }),
    F_DIAHORA = FMT({ op: { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' } }),
    F_FECHA = FMT({ op: { weekday: 'short', day: 'numeric', month: 'short' } });
  const _MEMO_DIA = new Map();
  const diaCdmx = (d) => {
    const t = d.getTime(); let r = _MEMO_DIA.get(t);
    if (r === undefined) { r = F_DIA.format(d); if (_MEMO_DIA.size > 20000) _MEMO_DIA.clear(); _MEMO_DIA.set(t, r); }
    return r;
  };
  // v402 — parser ISO aislado y cubierto por test_web_v402.cjs. Reconoce Z y offsets ±HH:MM/±HHMM.
  const aFecha = window.SharPicksFechas.aFecha;
  const horaCdmx = (d) => d ? F_DIAHORA.format(d) : '';
  const pct = (x) => x == null ? '—' : Math.round(100 * x) + ' %';
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));   // v508: también '
  // v454 — ÍCONOS EN VEZ DE EMOJIS (el usuario: «los emojis hacen que se vea hecha con IA»).
  // Lucide (ISC) y Tabler (MIT) en un solo archivo propio, `iconos.svg` (v517: con versión, si no el navegador guarda el viejo 4 h y faltan los íconos nuevos).
  const ico = (n, extra) => '<svg class="ic' + (extra ? ' ' + extra : '') + '" aria-hidden="true"><use href="iconos.svg?v=517#i-' + n + '"/></svg>';
  const DEP_ICO = { 'Fútbol': 'ball-football', Tenis: 'ball-tennis', NFL: 'ball-american-football', NBA: 'ball-basketball', NHL: 'ice-skating',
    MLB: 'ball-baseball', KBO: 'ball-baseball', 'Béisbol': 'ball-baseball', Mixta: 'link-2' };
  const icoDep = (d) => (DEP_ICO[d] ? ico(DEP_ICO[d], 'dep') : '');
  const OK = () => ico('circle-check'), MAL = () => ico('circle-x');
  // v456 — EL RESTO DE LOS EMOJIS, de una vez: lo que se pinta en pantalla pasa por
  // aquí y cada emoji se cambia por su ícono (con su color). No toca los avisos del
  // navegador (alert), ni los atributos, ni el dibujo de la cancha (SVG); en las
  // listas desplegables sólo se quita el emoji (ahí no cabe un ícono).
  const EMOJI_ICO = {
    '✅': ['circle-check', 'ok'], '❌': ['circle-x', 'mal'], '✓': ['circle-check', 'ok'], '✔': ['circle-check', 'ok'],
    '⚽': ['ball-football', 'dep'], '🎾': ['ball-tennis', 'dep'], '🏀': ['ball-basketball', 'dep'], '🏈': ['ball-american-football', 'dep'],
    '⚾': ['ball-baseball', 'dep'], '🏒': ['ice-skating', 'dep'],
    '💎': ['gem', 'nv-diamante'], '🔷': ['award', 'nv-platino'], '🥇': ['medal', 'nv-oro'], '🥈': ['medal', 'nv-plata'],
    '💰': ['coins', 'nv-error'], '🪙': ['coins', 'moneda'], '💳': ['credit-card'],
    '🤖': ['bot', 'acento'], '🧠': ['lightbulb', 'acento'], '🔗': ['link-2'], '⚠': ['triangle-alert', 'aviso'], '🐞': ['bug', 'aviso'],
    '⏳': ['hourglass'], '🕒': ['clock'], '⏰': ['timer'], '🔁': ['refresh-cw'], '♻': ['recycle'], '🌙': ['moon'],
    '🎯': ['target'], '📊': ['chart-column'], '📒': ['book-open'], '📖': ['book-open'], '📋': ['book-open'], '📰': ['newspaper'],
    '🔒': ['lock', 'candado'], '🔓': ['lock-open', 'candado'], '🔑': ['key-round'], '➕': ['plus'], '➖': ['minus'], '✕': ['x'],
    '★': ['star', 'estrella'], '⭐': ['star', 'estrella'], '☆': ['star'], '👍': ['thumbs-up'], '👎': ['thumbs-down'], '🙌': ['thumbs-up'],
    '🏆': ['trophy', 'nv-oro'], '🏅': ['trophy', 'nv-oro'], '👑': ['crown', 'nv-oro'], '🔴': ['circle-dot', 'vivo'],
    '✨': ['sparkles', 'acento'], '🎉': ['party-popper', 'acento'], '🎁': ['gift', 'acento'], '💡': ['lightbulb', 'aviso'],
    '🗑': ['trash-2'], '🏁': ['flag'], '🚩': ['flag'], '🥅': ['target'], '⚖': ['scale'], '📡': ['radio'], '🔀': ['link-2'],
    '🧱': ['shield-check'], '✋': ['hand'], '↗': ['trending-up'], '👤': ['user'], '👥': ['users'], '📢': ['megaphone'],
    '💬': ['message-circle'], '❓': ['circle-help'], '🔍': ['search'],
    '🟨': ['square', 'amarilla'], '🟥': ['square', 'roja-t'],
    '⚡': ['zap', 'acento'], '🔔': ['bell'], '🔕': ['bell'],   // v527
    '📈': ['activity', 'acento'], '↩': ['undo-2'], '↔': ['arrow-left-right'], '🧩': ['puzzle'],   // v517
  };
  const RE_EMOJI = new RegExp('(' + Object.keys(EMOJI_ICO).map((e) => e.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|') + ')\uFE0F?', 'g');
  function iconizar(raiz) {
    if (!raiz || raiz.nodeType !== 1 && raiz.nodeType !== 9) return;
    const andador = document.createTreeWalker(raiz, NodeFilter.SHOW_TEXT, {
      acceptNode: (t) => {
        const p = t.parentNode;
        if (!p || !t.nodeValue || !RE_EMOJI.test(t.nodeValue)) { RE_EMOJI.lastIndex = 0; return NodeFilter.FILTER_REJECT; }
        RE_EMOJI.lastIndex = 0;
        if (p instanceof SVGElement || /^(SCRIPT|STYLE|TEXTAREA|TITLE)$/.test(p.nodeName)) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      } });
    const nodos = [];
    while (andador.nextNode()) nodos.push(andador.currentNode);
    nodos.forEach((t) => {
      if (t.parentNode && t.parentNode.nodeName === 'OPTION') { t.nodeValue = t.nodeValue.replace(RE_EMOJI, '').replace(/^\s+/, ''); return; }
      const frag = document.createDocumentFragment(), txt = t.nodeValue;
      let ultimo = 0;
      txt.replace(RE_EMOJI, (m, e, i) => {
        if (i > ultimo) frag.appendChild(document.createTextNode(txt.slice(ultimo, i)));
        const [n, c] = EMOJI_ICO[e];
        const tmp = document.createElement('span');
        tmp.innerHTML = ico(n, c);
        frag.appendChild(tmp.firstChild);
        ultimo = i + m.length;
        return m;
      });
      if (ultimo < txt.length) frag.appendChild(document.createTextNode(txt.slice(ultimo)));
      t.parentNode.replaceChild(frag, t);
    });
  }
  // sólo lo que cambió (el reloj cambia cada segundo: revisar toda la página sería caro)
  const porIconizar = new Set();
  new MutationObserver((cambios) => {
    cambios.forEach((c) => {
      if (c.type === 'characterData') { if (c.target.parentNode) porIconizar.add(c.target.parentNode); }
      else c.addedNodes.forEach((n) => porIconizar.add(n.nodeType === 3 ? n.parentNode : n));
    });
    if (porIconizar.size && !porIconizar._pend) {
      porIconizar._pend = true;
      requestAnimationFrame(() => { porIconizar._pend = false; const xs = [...porIconizar]; porIconizar.clear(); xs.forEach((n) => n && n.isConnected && iconizar(n)); });
    }
  }).observe(document.documentElement, { childList: true, subtree: true, characterData: true });
  document.addEventListener('DOMContentLoaded', () => iconizar(document.body));
  if (document.body) iconizar(document.body);
  const lados = (p) => { const t = String(p.partido || ''); const i = t.indexOf(' vs '); return i < 0 ? [t, ''] : [t.slice(0, i), t.slice(i + 4)]; };

  const _MEMO_DIADE = new WeakMap();           // v483 — el día de cada pick, sin tocar el objeto
  function diaDe(p) {
    const m = _MEMO_DIADE.get(p);
    if (m && m.i === p.inicio && m.f === p.fecha) return m.r;
    const d = aFecha(p.inicio), r = d ? diaCdmx(d) : String(p.fecha || '');
    _MEMO_DIADE.set(p, { i: p.inicio, f: p.fecha, r });
    return r;
  }
  function diaPestana(n) { const d = new Date(); d.setUTCDate(d.getUTCDate() + n); return diaCdmx(d); }
  const OFFS = { ayer: -1, hoy: 0, manana: 1, pasado: 2 };

  // Niveles (como los «stakes» de BetFlipAi), pero con lo MEDIDO de verdad
  function nivel(p) {
    // v455 — íconos en vez de emojis; Platino lleva la escarapela (el usuario: la gema y el diamante se confundían)
    if (p.solo_analisis) return { n: 'Sólo análisis', c: 'analisis', i: ico('chart-column', 'nv-analisis') };   // v418
    if (p.tipo === 'error') return { n: 'Cuota alta', c: 'error', i: ico('coins', 'nv-error') };
    if (p.elige) return { n: 'Diamante', c: 'diamante', i: ico('gem', 'nv-diamante') };
    if ((p.prob || 0) >= 0.85) return { n: 'Platino', c: 'platino', i: ico('award', 'nv-platino') };
    if ((p.prob || 0) >= 0.80) return { n: 'Oro', c: 'oro', i: ico('medal', 'nv-oro') };
    return { n: 'Plata', c: 'plata', i: ico('medal', 'nv-plata') };
  }

  // v396 — el nivel en palabras: probabilidad, nunca «segura» ni «se cumplen 9 de 10»
  function grado(p) {
    const n = nivel(p).n;
    return { Diamante: 'Muy alta', Platino: 'Muy alta', Oro: 'Alta', Plata: 'Buena' }[n] || '—';
  }

  // v466 — LA BASE ENTREGA COMO MÁXIMO 1000 FILAS POR CONSULTA, aunque se pida «limit=5000».
  // Con 1157 picks en la ventana, los 157 últimos (los de pasado mañana, el Barcelona-Real Madrid)
  // no llegaban y nadie lo notaba. Ahora se piden por páginas hasta tener TODAS las que la base
  // dice que hay; si faltara alguna, falla y se usa el respaldo completo (datos/hoy.json).
  async function todasLasFilas(url) {
    const H = { apikey: C.SUPABASE_ANON_KEY, Authorization: 'Bearer ' + C.SUPABASE_ANON_KEY };
    const pagina = (desde, n, extra) => fetch(url + '&offset=' + desde + '&limit=' + n, { headers: Object.assign({}, H, extra || {}) })
      .then((r) => { if (!r.ok) throw new Error('base de datos ' + r.status); return Promise.all([r.json(), r.headers.get('content-range')]); });
    const [filas, rango] = await pagina(0, 1000, { Prefer: 'count=exact' });
    if (!Array.isArray(filas)) throw new Error('respuesta de la base no es una lista');
    const total = Number(String(rango || '').split('/')[1]);
    const paso = filas.length;
    if (!paso) return filas;
    if (Number.isFinite(total)) {
      const resto = [];
      for (let i = paso; i < total; i += paso) resto.push(pagina(i, paso).then(([d]) => d));
      (await Promise.all(resto)).forEach((d) => { if (Array.isArray(d)) filas.push(...d); });
      if (filas.length < total) throw new Error('faltan filas: ' + filas.length + ' de ' + total);
      return filas;
    }
    for (let i = paso, d = filas; d.length === paso && i < 100000; i += paso) {   // sin el total: hasta una página incompleta
      [d] = await pagina(i, paso);
      if (!Array.isArray(d)) throw new Error('respuesta de la base no es una lista');
      filas.push(...d);
    }
    return filas;
  }

  async function cargar() {
    // v384 — datos de apoyo (deportes con partidos pero sin pick)
    fetch('combinadas_simuladas.json?v=528').then((r) => r.ok ? r.json() : null).then((d) => { estado.combSim = d; }).catch(() => {});   // v421
    fetch('datos/meta.json?t=' + Date.now()).then((r) => r.ok ? r.json() : null).then((m) => { estado.meta = m || {}; }).catch(() => {});
    // v418 — los partidos SIN pick, para analizarlos (no cuentan en ningún marcador)
    fetch('datos/analisis.json?t=' + Date.now()).then((r) => r.ok ? r.json() : null)
      .then((d) => { estado.analisis = (d && Array.isArray(d.analisis)) ? d.analisis : []; pintar(); }).catch(() => {});
    try {
      if (C.SUPABASE_URL && C.SUPABASE_ANON_KEY) {
        const desde = diaPestana(-2);
        const pedirPicks = () => todasLasFilas(C.SUPABASE_URL.replace(/\/$/, '') + '/rest/v1/picks?select=*&fecha=gte.' + desde + '&order=inicio.asc,id.asc');
        // v515 — un tropiezo de la base (un 500 suelto) no manda a nadie al respaldo: se reintenta una vez
        let datos;
        try { datos = await pedirPicks(); } catch (e1) { await new Promise((r) => setTimeout(r, 1500)); datos = await pedirPicks(); }
        estado.picks = datos;
        estado.errorPicks = false;
        estado.respaldoPicks = false;
        $('actualizado').textContent = 'Datos de la base · ' + horaCdmx(new Date());
      } else { throw new Error('sin base'); }
    } catch (e) {
      console.warn('[sharpicks] falló la consulta principal de picks', e);
      try {
        const r = await fetch('datos/hoy.json?t=' + Date.now());
        if (!r.ok) throw new Error('respaldo HTTP ' + r.status);
        const d = await r.json();
        if (!d || !Array.isArray(d.picks)) throw new Error('respaldo sin lista de picks');
        estado.picks = d.picks;
        estado.errorPicks = false;
        estado.respaldoPicks = true;
        const generada = aFecha(d.generado);
        $('actualizado').textContent = generada ? 'Respaldo local · ' + horaCdmx(generada) : 'Respaldo local · fecha de generación no verificable';
        // v515 — en cuanto la base vuelva a responder, se regresa a los datos vivos (sin esperar a que el usuario recargue)
        setTimeout(() => { if (estado.respaldoPicks) cargar().then(() => pintar()).catch(() => {}); }, 20000);
      } catch (e2) {
        console.error('[sharpicks] falló también el respaldo local de picks', e2);
        estado.picks = [];
        estado.errorPicks = true;
        estado.respaldoPicks = false;
        $('aviso').textContent = 'No se pudieron consultar los pronósticos. La fuente y el respaldo fallaron; reintenta en un momento.';
      }
    }
    // v396 — las combinadas (tabla pública `combinadas`)
    try {
      if (C.SUPABASE_URL && C.SUPABASE_ANON_KEY) {
        const datosCombinadas = await todasLasFilas(C.SUPABASE_URL.replace(/\/$/, '') + '/rest/v1/combinadas?select=*&fecha=gte.' + diaPestana(-30) + '&order=inicio.asc,id.asc');
        estado.combinadas = datosCombinadas;
        estado.errorCombinadas = false;
      } else {
        estado.combinadas = [];
        estado.errorCombinadas = true;
      }
    } catch (e) {
      console.warn('[sharpicks] no se pudieron consultar las combinadas', e);
      estado.combinadas = [];
      estado.errorCombinadas = true;
    }
    pintar();
    vivo();
  }

  // ---------- EN VIVO (ESPN) ----------
  const STATS_FUT = [['totalShots', 'Tiros'], ['shotsOnTarget', 'A puerta'], ['wonCorners', 'Córners'],
    ['possessionPct', 'Posesión %'], ['foulsCommitted', 'Faltas'], ['yellowCards', 'Amarillas'], ['redCards', 'Rojas'],
    ['offsides', 'Fueras de lugar'], ['saves', 'Paradas'], ['accuratePasses', 'Pases buenos']];

  const TRAD = { 'Shots': 'Tiros', 'Shots on Goal': 'Tiros a puerta', 'Saves': 'Paradas', 'Hits': 'Golpes', 'Blocked Shots': 'Tiros bloqueados',
    'Penalty Minutes': 'Minutos de castigo', 'Power Play Goals': 'Goles en power play', 'Faceoffs Won': 'Saques ganados', 'Takeaways': 'Robos',
    'Giveaways': 'Pérdidas', 'Rebounds': 'Rebotes', 'Assists': 'Asistencias', 'Turnovers': 'Pérdidas', 'Steals': 'Robos', 'Blocks': 'Tapones',
    'Field Goal %': '% de tiro', 'Three Point %': '% de triples', 'Free Throw %': '% de libres', 'Total Yards': 'Yardas', 'Passing': 'Pase',
    'Rushing': 'Carrera', '1st Downs': 'Primeros downs', 'Turnovers ': 'Pérdidas', 'Possession': 'Posesión' };

  // v378 — LOS COLORES DE CADA EQUIPO (los da ESPN: principal y secundario).
  // Sobre el fondo oscuro, un color casi negro no se ve: se usa el secundario
  // o se aclara. Si los dos equipos quedan casi iguales, el visitante va con
  // su secundario (o con el rosa de la página).
  const hex = (h) => { h = String(h || '').replace('#', ''); return /^[0-9a-f]{6}$/i.test(h) ? h : null; };
  const rgb = (h) => [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
  const luz = (h) => { const [r, g, b] = rgb(h).map((x) => { x /= 255; return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); }); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
  const dist = (a, b) => { const x = rgb(a), y = rgb(b); return Math.hypot(x[0] - y[0], x[1] - y[1], x[2] - y[2]); };
  const aclarar = (h) => rgb(h).map((x) => Math.round(x + (255 - x) * 0.45).toString(16).padStart(2, '0')).join('');
  function visible(c, alt) {
    if (c && luz(c) >= 0.06) return c;
    if (alt && luz(alt) >= 0.06) return alt;
    return c ? aclarar(c) : null;
  }
  function coloresEquipos(t1, t2) {
    let a = visible(hex(t1.color), hex(t1.alternateColor)) || '7c5cff';
    let b = visible(hex(t2.color), hex(t2.alternateColor)) || 'ff5ca8';
    if (dist(a, b) < 90) {
      const alt = visible(hex(t2.alternateColor), null);
      b = alt && dist(a, alt) >= 90 ? alt : (dist(a, 'ff5ca8') >= 90 ? 'ff5ca8' : '7c5cff');
    }
    const txt = (c) => (luz(c) > 0.45 ? '#111' : '#fff');
    return { l: '#' + a, r: '#' + b, tl: txt(a), tr: txt(b) };
  }
  const varsColor = (v) => v && v.colores ? '--c-l:' + v.colores.l + ';--c-r:' + v.colores.r + ';--t-l:' + v.colores.tl + ';--t-r:' + v.colores.tr : '';

  // v436 — el puesto de ESPN («CD-L», «AM», «F»…) en la misma escala que 365Scores:
  // prof 0 = portería propia … 100 = media cancha; ancho 0 = su izquierda … 100 = su derecha
  const PUESTO = { G: [0, 50], GK: [0, 50], SW: [14, 50], CD: [20, 50], CB: [20, 50], LB: [24, 10], RB: [24, 90], LWB: [40, 8], RWB: [40, 92],
    DM: [38, 50], CDM: [38, 50], CM: [50, 50], LM: [58, 10], RM: [58, 90], AM: [70, 50], CAM: [70, 50], LW: [80, 12], RW: [80, 88], SS: [80, 50],
    LF: [86, 25], RF: [86, 75], CF: [90, 50], F: [92, 50], ST: [92, 50] };
  function puestoEspn(a) {
    const m = String(a || '').toUpperCase().match(/^([A-Z]+)(?:-([LR]))?$/), b = PUESTO[m && m[1]] || [50, 50];
    return [b[0], Math.max(4, Math.min(96, b[1] + (m && m[2] ? (m[2] === 'L' ? -16 : 16) : 0)))];
  }
  // v503 — PRÓRROGA Y PENALES. El usuario: «el Hoffenheim se fue a tiempos extra y me lo mandaste como
  // finalizado… quiero saber el estatus del tiempo extra, de los penales, cómo se van marcando cada uno».
  // ESPN dice en qué parte va (`status.type.name`) y en el resumen trae la tanda (`shootout`: cada tiro con
  // su jugador y si entró). Medido en vivo con Holstein Kiel–Hoffenheim (DFB-Pokal, 28-oct).
  const ESTADO_ESPN = {
    STATUS_END_OF_REGULATION: 'Fin de los 90 · va a prórroga', STATUS_FIRST_HALF_EXTRA_TIME: 'Prórroga · 1.ª parte',
    STATUS_EXTRA_TIME: 'Prórroga', STATUS_HALFTIME_ET: 'Descanso de la prórroga', STATUS_SECOND_HALF_EXTRA_TIME: 'Prórroga · 2.ª parte',
    STATUS_END_OF_EXTRATIME: 'Fin de la prórroga · penales', STATUS_SHOOTOUT: 'Penales',
    STATUS_FINAL_PEN: 'Final (penales)', STATUS_FINAL_AET: 'Final (prórroga)',
  };
  const PAUSA_ESPN = ['STATUS_END_OF_REGULATION', 'STATUS_HALFTIME_ET', 'STATUS_END_OF_EXTRATIME', 'STATUS_SHOOTOUT'];
  function penalesDe(d, comp, nos1) {
    const tanda = Array.isArray(d.shootout) ? d.shootout : [];
    const st = ((comp.status || {}).type || {}).name || '';
    if (!tanda.length && !/SHOOTOUT|FINAL_PEN|END_OF_EXTRATIME/.test(st)) return null;
    const tiros = [[], []];
    tanda.forEach((t) => {
      const lado = String(t.id) === String((nos1.team || {}).id) || t.team === (nos1.team || {}).displayName ? 0 : 1;
      (t.shots || []).slice().sort((a, b) => (a.shotNumber || 0) - (b.shotNumber || 0)).forEach((x) => tiros[lado].push({ ok: !!x.didScore, j: x.player || '' }));
    });
    const g = tiros.map((l) => l.filter((x) => x.ok).length);
    return { g, tiros };
  }
  function leerResumen(d, p) {
    const comp = ((d.header || {}).competitions || [])[0] || {};
    const st = (comp.status || {}).type || {};
    const cs = comp.competitors || [];
    const ch = cs.find((c) => c.homeAway === 'home') || {}, ca = cs.find((c) => c.homeAway === 'away') || {};
    const [nos1, nos2] = p.girado ? [ca, ch] : [ch, ca];        // en el orden de NUESTRO «A vs B»
    const stats = {};
    for (const t of ((d.boxscore || {}).teams || [])) {
      const lado = String((t.team || {}).id) === String((nos1.team || {}).id) ? 0 : 1;
      for (const s of t.statistics || []) {
        const k = s.name || s.label; if (!k) continue;
        stats[k] = stats[k] || { label: s.label || s.name, v: [null, null] };
        stats[k].v[lado] = s.displayValue;
      }
    }
    const eventos = ((d.keyEvents && d.keyEvents.length ? d.keyEvents : d.scoringPlays) || []).map((e) => {
      const tipo = ((e.type || {}).text) || '';
      const ico = /goal|penalty - scored/i.test(tipo) || e.scoringPlay ? '⚽' : /yellow/i.test(tipo) ? '🟨' : /red card/i.test(tipo) ? '🟥' : /substitution/i.test(tipo) ? '' : '•';
      let texto = String(e.text || e.shortText || '').replace(/\s+(Goal|Own Goal|Penalty - Scored|Yellow Card|Red Card|Substitution)[^]*$/i, '').replace(/^(Goal|Yellow Card|Red Card)!?\s*/i, '');
      // v518 — «Xerez 1, Cadiz 3. Borja Vázquez (Cadiz) left footed shot…»: sólo «Borja Vázquez (Cadiz)»
      const quien = ico === '⚽' && texto.match(/\d+\.\s*([^.]+?\([^)]+\))/);
      if (quien) texto = quien[1];
      return { min: ((e.clock || {}).displayValue) || '', ico, texto,
        lado: String((e.team || {}).id) === String((nos1.team || {}).id) ? 0 : 1, gol: ico === '⚽' };
    }).filter((e) => e.texto && e.ico);
    // v427 — las jugadas con su lugar en la cancha. ESPN las da en la dirección de
    // ataque de quien la hizo (los dos atacan hacia X=100): el visitante se refleja.
    const n1 = ((nos1.team || {}).displayName) || '';
    const jugadas = (d.commentary || []).map((c) => c.play).filter((x) => x && x.fieldPositionX != null).map((x) => ({
      t: ((x.type || {}).type) || '', min: ((x.clock || {}).displayValue) || '', seg: Number((x.clock || {}).value || 0), per: Number((x.period || {}).number || 0),
      lado: ((x.team || {}).displayName) === n1 ? 0 : 1, equipo: ((x.team || {}).displayName) || '',
      x: Number(x.fieldPositionX), y: Number(x.fieldPositionY),
      x2: x.fieldPosition2X != null ? Number(x.fieldPosition2X) : null, y2: x.fieldPosition2Y != null ? Number(x.fieldPosition2Y) : null,
    })).sort((a, b) => a.seg - b.seg);
    // v436 — la alineación de ESPN (formación y puesto de cada titular): el respaldo cuando 365Scores no la trae
    const once = [];
    for (const r of d.rosters || []) {
      const lado = String((r.team || {}).id) === String((nos1.team || {}).id) ? 0 : 1;
      (r.roster || []).filter((j) => j.starter).forEach((j) => {
        const [prof, ancho] = puestoEspn((j.position || {}).abbreviation);
        once.push({ lado, n: j.jersey || '', nombre: (j.athlete || {}).shortName || (j.athlete || {}).displayName || '', prof, ancho, nota: null });
      });
    }
    return {
      jugadas, once, formacion: [0, 1].map((l) => ((d.rosters || []).find((r) => (String((r.team || {}).id) === String((nos1.team || {}).id) ? 0 : 1) === l) || {}).formation || ''),
      fase: st.state || 'pre', terminado: !!st.completed, est: st.name || '', pen: penalesDe(d, comp, nos1),
      detalle: ESTADO_ESPN[st.name] || ({ FT: 'Final', HT: 'Medio tiempo', AET: 'Final (prórroga)', 'FT-Pens': 'Final (penales)', Final: 'Final' })[st.shortDetail] || st.shortDetail || st.detail || '',
      reloj: (comp.status || {}).displayClock || '', g: [Number(nos1.score || 0), Number(nos2.score || 0)],
      stats, eventos, nombres: [((nos1.team || {}).displayName) || '', ((nos2.team || {}).displayName) || ''],
      colores: coloresEquipos(nos1.team || {}, nos2.team || {}),
    };
  }

  async function vivo() {
    const ahora = Date.now();
    const ids = {};
    for (const p of estado.picks.concat(estado.analisis || [])) {     // v424: también las de sólo análisis
      const ini = aFecha(p.inicio);
      if (!p.espn || !ini) continue;
      const desde = ini.getTime() - 10 * 60e3, hasta = ini.getTime() + 4 * 3600e3;
      const yaFin = (estado.vivo[p.espn] || {}).terminado;
      // v463 — el usuario: «salen partidos de ayer como en juego». Lo que ya terminó y el servidor aún no
      // cerró (hasta 10 días) se pide UNA vez a ESPN y se pone verde o rojo al momento, sin esperar
      const atrasado = p.estado === 'pendiente' && !p.solo_analisis && ahora > hasta && ahora - ini.getTime() < 10 * 864e5 && !estado.vivo[p.espn];
      if ((ahora >= desde && ahora <= hasta && !yaFin) || atrasado) ids[p.espn] = p;
    }
    const entradas = Object.entries(ids);
    // v518 — un candado de una vuelta que el iPhone congeló al salir de la app no frena la de al volver
    if ((estado.vivoCorriendo && Date.now() - (estado.vivoDesde || 0) < 10000) || !entradas.length) return;
    // v465 — el usuario: «se traba y se calienta el teléfono». Se pedían hasta 40 resúmenes de ESPN
    // (cientos de KB cada uno) cada 20 s, aunque la app estuviera en segundo plano. Ahora: nada en
    // segundo plano; los partidos ABIERTOS siempre; de los demás, 8 por vuelta (se turnan).
    if (document.hidden && estado.vivoPrimera) return;
    estado.vivoPrimera = true;
    const visibles = new Set([...estado.abiertos].concat(fichaId ? [clavePartido(estado.picks.concat(estado.analisis || []).find((x) => x.id === fichaId) || {})] : []));
    const abiertos = entradas.filter(([, p]) => visibles.has(clavePartido(p)));
    // v503 — primero los que aún no tienen dato en vivo (al abrir la app, si no, esperaban más de un minuto)
    const resto = entradas.filter(([, p]) => !visibles.has(clavePartido(p))).sort((a, b) => (!!estado.vivo[a[0]]) - (!!estado.vivo[b[0]]));
    const n = Math.min(8, resto.length);
    const cursor = resto.length ? estado.vivoCursor % resto.length : 0;
    const lista = abiertos.concat(Array.from({ length: n }, (_, i) => resto[(cursor + i) % resto.length]));
    estado.vivoCursor = resto.length ? (cursor + n) % resto.length : 0;
    estado.vivoCorriendo = true; estado.vivoDesde = Date.now();
    let cambio = false;
    try {
      for (let i = 0; i < lista.length; i += 8) {
        await Promise.all(lista.slice(i, i + 8).map(async ([k, p]) => {
          const [ruta, id] = k.split(':');
          try {
            const ctl = new AbortController(); const to = setTimeout(() => ctl.abort(), 8000);
            const r = await fetch(ESPN + ruta + '/summary?event=' + id, { signal: ctl.signal });
            clearTimeout(to);
            if (r.ok) {
              const nuevo = leerResumen(await r.json(), p), viejo = estado.vivo[k];
              if (!viejo || viejo.reloj !== nuevo.reloj || String(viejo.g) !== String(nuevo.g) || viejo.fase !== nuevo.fase) cambio = true;
              estado.vivo[k] = nuevo;
            }
          } catch (e) { /* sin red: se reintenta en 30 s */ }
        }));
      }
    } finally { estado.vivoCorriendo = false; }
    // v486 — los que van en tiempo agregado («45'+2'»): cuántos minutos anunció el árbitro (FotMob, 30 s)
    try {
      const enAgregado = entradas.map(([k, p]) => p).filter((p) => { const v = estado.vivo[p.espn]; return v && v.fase === 'in' && /\+/.test(String(v.reloj || '')); }).slice(0, 6);
      const r = await Promise.all(enAgregado.map((p) => presionFM(p).catch(() => false)));
      if (enAgregado.some((p) => { const c = estado.pfm[clavePartido(p)]; return c && c.compensacion; }) || r.some(Boolean)) cambio = true;
    } catch (e) { /* sin FotMob: sólo el reloj de ESPN */ }
    if (cambio && !document.hidden) { pintar(); refrescarFicha(); }
  }

  // v424 — EL MARCADOR DE TODOS: lo que ESPN no cubre (Tercera RFEF, Sub-21…)
  // sale de Flashscore por nuestra función `/vivo` (functions/vivo.js). Se
  // empareja por los nombres de los dos equipos; cuando la tarjeta está abierta
  // se piden también sus estadísticas del momento.
  const DEP_FS = { 'Fútbol': 'futbol', Tenis: 'tenis', NBA: 'basquet', NHL: 'hockey', MLB: 'beisbol', KBO: 'beisbol', 'Béisbol': 'beisbol' };
  const GENERICAS = new Set(['fc', 'cf', 'cd', 'sc', 'ac', 'club', 'the', 'afc', 'de', 'del', 'and', 'sad']);
  const fichas = (s) => String(s || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9 ]/g, ' ')
    .split(/\s+/).filter((w) => w.length >= 3 && !GENERICAS.has(w));
  const casan = (a, b) => { const x = fichas(a), y = new Set(fichas(b)); return x.length && y.size && x.some((w) => y.has(w)); };
  // v429 — el MÁS parecido, no el primero: «Bayern Munich» con «Bayern Munich»
  // gana a «Bayern Munich Sub19» (la Youth League juega el mismo día)
  const parecido = (a, b) => { const x = new Set(fichas(a)), y = new Set(fichas(b)); if (!x.size || !y.size) return 0;
    let c = 0; x.forEach((w) => { if (y.has(w)) c++; }); return c / (x.size + y.size - c); };
  function mejorCruce(L, V, lista, kh, ka) {
    let mejor = null, pm = 0;
    for (const x of lista) {
      for (const gir of [false, true]) {
        const a = parecido(L, gir ? x[ka] : x[kh]), b = parecido(V, gir ? x[kh] : x[ka]);
        if (a > 0 && b > 0 && a + b > pm) { pm = a + b; mejor = { m: x, girado: gir }; }
      }
    }
    return mejor;
  }
  const STATS_FS = { 'Ball possession': 'possessionPct', 'Total shots': 'totalShots', 'Shots on target': 'shotsOnTarget', 'Corner kicks': 'wonCorners',
    'Yellow cards': 'yellowCards', 'Red cards': 'redCards', 'Fouls': 'foulsCommitted', 'Offsides': 'offsides', 'Goalkeeper saves': 'saves',
    'Expected goals (xG)': 'xg', 'Passes': 'totalPasses' };
  estado.fsPor = {}; estado.fsStats = {}; estado.fsPedido = {};
  async function vivoFs() {
    if (document.hidden) return;
    const ahora = Date.now();
    const sin = estado.picks.concat(estado.analisis || []).filter((p) => {
      if (p.espn && estado.vivo[p.espn]) return false;          // ESPN ya lo da
      const ini = aFecha(p.inicio);
      return ini && DEP_FS[p.deporte] && ahora >= ini - 10 * 60e3 && ahora <= ini.getTime() + duracion(p.deporte) + 30 * 60e3;
    });
    if (!sin.length) return;
    let cambio = false;
    for (const dep of [...new Set(sin.map((p) => DEP_FS[p.deporte]))]) {
      let lista = [];
      try { const r = await fetch('vivo?dep=' + dep); if (r.ok) lista = (await r.json()).partidos || []; } catch (e) { continue; }
      for (const p of sin.filter((x) => DEP_FS[x.deporte] === dep)) {
        const [L, V] = lados(p);
        const cr = mejorCruce(L, V, lista, 'home', 'away'), m = cr && cr.m, girado = !!(cr && cr.girado);
        if (!m || m.estado === 'pre') continue;
        const k = clavePartido(p), viejo = estado.fsPor[k];
        const g = [m.gh == null ? 0 : m.gh, m.ga == null ? 0 : m.ga];
        const st = estado.fsStats[m.id] || {};
        estado.fsPor[k] = { fase: m.estado, terminado: m.estado === 'post', detalle: m.detalle, reloj: m.detalle, g: girado ? [g[1], g[0]] : g,
          stats: Object.fromEntries(Object.entries(st).map(([n, v]) => [STATS_FS[n] || n, { label: n, v: girado ? [v[1], v[0]] : v }])),
          eventos: [], nombres: [L, V], colores: null, fuente: 'flashscore', fsId: m.id };
        if (!viejo || String(viejo.g) !== String(estado.fsPor[k].g) || viejo.fase !== m.estado) cambio = true;
        // las estadísticas, sólo de las tarjetas abiertas (una vez por minuto)
        if (estado.abiertos.has(k) && m.estado === 'in' && dep === 'futbol' && !(estado.fsPedido[m.id] > ahora - 60e3)) {
          estado.fsPedido[m.id] = ahora;
          fetch('vivo?id=' + encodeURIComponent(m.id)).then((r) => (r.ok ? r.json() : null)).then((d) => {
            if (d && d.stats && Object.keys(d.stats).length) { estado.fsStats[m.id] = d.stats; vivoFs(); }
          }).catch(() => {});
        }
      }
    }
    if (cambio) pintar();
    if (cambio) minutos365().catch(() => {});      // v493 — el minuto real de lo que llegó sin minuto
  }

  // ¿Cómo va la apuesta? (sólo para enseñarlo; lo oficial lo liquida el modelo)
  function progreso(p, v) {
    if (!v || v.fase === 'pre') return null;
    // v381 — el premium se sigue en vivo con su texto real (si el usuario lo ve)
    const [L, V] = lados(p), a = String((window.SPX && SPX.yo.desbloqueados[p.id]) || p.apuesta || '');
    const sv = (k) => { const s = v.stats[k]; return s ? s.v.map((x) => Number(x || 0)) : null; };
    let m, cuenta = null, lado = null, linea = null, tipo = null;
    if ((m = a.match(/^(Goles|Puntos|Córners|Tarjetas): (Más|Menos) de ([\d.]+)/))) {
      linea = Number(m[3]); lado = m[2];
      // v489 — el usuario: «Parma-Udinese ya hay 4 tarjetas en la presión pero no pones como cumplido el
      // pick»: las estadísticas de ESPN iban atrasadas (decían 1). Tarjetas y córners no se borran: se toma
      // la cuenta MÁS ALTA de las fuentes (estadísticas de ESPN, sus incidencias y las de FotMob).
      const fm = estado.pfm[clavePartido(p)] || {};
      const mx = (...xs) => { const ok = xs.filter((x) => x != null && !isNaN(x)); return ok.length ? Math.max(...ok) : null; };
      const suma = (x) => (Array.isArray(x) ? Number(x[0] || 0) + Number(x[1] || 0) : null);
      if (m[1] === 'Córners') { const c = sv('wonCorners'); cuenta = mx(c ? c[0] + c[1] : null, suma((fm.todo || {}).corners)); tipo = 'córners'; }
      else if (m[1] === 'Tarjetas') {
        const y = sv('yellowCards'), rr = sv('redCards');
        cuenta = mx(y ? y[0] + y[1] + (rr ? rr[0] + rr[1] : 0) : null,
          (v.eventos || []).some((e) => /🟨|🟥/.test(e.ico)) ? (v.eventos || []).filter((e) => /🟨|🟥/.test(e.ico)).length : null,
          Array.isArray(fm.eventos) && fm.eventos.some((e) => e.tipo !== 'gol') ? fm.eventos.filter((e) => e.tipo !== 'gol').length : null,
          suma((fm.todo || {}).amarillas));
        tipo = 'tarjetas';
      }
      else { cuenta = v.g[0] + v.g[1]; tipo = m[1].toLowerCase(); }
    } else if ((m = a.match(/^Goles (.+): (Más|Menos) de ([\d.]+)/))) {
      linea = Number(m[3]); lado = m[2]; cuenta = m[1] === V ? v.g[1] : v.g[0]; tipo = 'goles de ' + m[1];
    }
    if (cuenta != null) {
      const txt = 'Van ' + cuenta + ' ' + tipo + ' (línea ' + linea + ')';
      if (lado === 'Menos') return cuenta > linea ? { e: 'roja', t: txt + ' · ya se pasó' } : v.terminado ? { e: 'verde', t: txt } : { e: 'va', t: txt + ' · aguanta ' + Math.floor(linea - cuenta) + ' más' };
      return cuenta > linea ? { e: 'verde', t: txt + ' · ¡ya se cumplió!' } : v.terminado ? { e: 'roja', t: txt } : { e: 'va', t: txt + ' · faltan ' + Math.floor(linea - cuenta + 1) };
    }
    const dif = v.g[0] - v.g[1];
    let ok = null;
    if ((m = a.match(/^Gana (.+)/))) ok = m[1] === V ? dif < 0 : dif > 0;
    else if ((m = a.match(/^(.+) o empate$/))) ok = m[1] === V ? dif <= 0 : dif >= 0;
    else if ((m = a.match(/^Handicap: (.+) ([+-][\d.]+)/))) { const h = Number(m[2]); ok = m[1] === V ? (v.g[1] + h > v.g[0]) : (v.g[0] + h > v.g[1]); }
    if (ok == null) return null;
    return { e: v.terminado ? (ok ? 'verde' : 'roja') : 'va', t: v.terminado ? (ok ? 'Se cumplió' : 'No se cumplió') : (ok ? 'Ahorita se está cumpliendo' : 'Ahorita no se cumple') };
  }

  // ---------- MARCADORES ----------
  function cuenta(lista) {
    const v = lista.filter((p) => p.estado === 'verde').length, r = lista.filter((p) => p.estado === 'roja').length;
    const din = lista.reduce((s, p) => s + (p.estado === 'verde' ? (p.cuota || 1) - 1 : p.estado === 'roja' ? -1 : 0), 0);
    return { v, r, pct: v + r ? v / (v + r) : null, din };
  }
  function cajaMarcador(titulo, todo) {
    // v386 — los errores de cuota (💰) con su propio marcador, aparte
    const lista = todo.filter((p) => p.tipo !== 'error');
    const t = cuenta(lista), e = cuenta(lista.filter((p) => p.elige)), er = cuenta(todo.filter((p) => p.tipo === 'error'));
    const pend = lista.filter((p) => p.estado === 'pendiente' || p.estado === 'vivo').length;
    return '<div class="caja"><div class="tit">' + titulo + '</div>' +
      '<div class="num">✅ ' + t.v + ' &nbsp;❌ ' + t.r + ' <span class="pct">' + pct(t.pct) + '</span></div>' +
      '<div class="barra"><i style="width:' + (t.pct == null ? 0 : 100 * t.pct) + '%"></i></div>' +
      '<div class="sub">💎 Diamante: ✅ ' + e.v + ' ❌ ' + e.r + (e.pct == null ? '' : ' · ' + pct(e.pct)) + ' · por jugar ' + pend + '</div>' +
      (er.v + er.r ? '<div class="sub">💰 Cuota alta: ✅ ' + er.v + ' ❌ ' + er.r + ' · ' + pct(er.pct) + '</div>' : '') + '</div>';
  }

  // ---------- TARJETAS ----------
  // v467 — sin escudo (o si la imagen no carga) va una silueta neutra, nunca una letra suelta:
  // el usuario veía «A» y «L» en el Atlético-Deportivo. El tenista sin foto lleva la persona.
  const SILUETA = (dep) => '<span class="escudo silueta">' + ico(dep === 'Tenis' ? 'user' : 'ball-football') + '</span>';
  function escudo(url, nombre, dep) {
    return url ? '<img class="escudo" loading="lazy" src="' + esc(url) + '" alt="" data-silueta="' + esc(dep || '') + '">' : SILUETA(dep);   // v490: no `data-dep` (es el del filtro de deportes)
  }
  document.addEventListener('error', (e) => {
    const im = e.target;
    if (im && im.tagName === 'IMG' && im.classList.contains('escudo')) im.outerHTML = SILUETA(im.dataset.silueta);
  }, true);
  function cuentaAtras(ini) {
    const s = Math.floor((ini - Date.now()) / 1000);
    if (s <= 0) return '';
    const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60);
    return h > 23 ? Math.floor(h / 24) + ' d ' + (h % 24) + ' h' : h + ' h ' + String(m).padStart(2, '0') + ' min';
  }
  function etiquetaEstado(p, v) {
    const ini = aFecha(p.inicio);
    if (p.estado === 'verde') return '<span class="et verde">' + OK() + ' Verde</span>';
    if (p.estado === 'roja') return '<span class="et roja">' + MAL() + ' Roja</span>';
    if (p.estado === 'nula') return '<span class="et">Nula</span>';
    if (v && v.fase === 'in') {
      const rv = relojVivo(v, p);
      const txt = rv.minuto && !/EXTRA_TIME/.test(v.est || '') ? rv.t + ' (minuto ' + rv.minuto + ')' + (rv.agregado ? ' · +' + rv.agregado + ' de compensación' : '')
        : PAUSA_ESPN.includes(v.est) || /EXTRA_TIME/.test(v.est || '') ? (v.detalle || rv.t) + (v.pen && (v.est === 'STATUS_SHOOTOUT' || v.est === 'STATUS_END_OF_EXTRATIME') ? ' ' + v.pen.g[0] + '-' + v.pen.g[1] : '') + (/EXTRA_TIME/.test(v.est || '') && v.reloj ? ' · ' + v.reloj : '')
          : (rv.t && rv.t !== 'Vivo' ? rv.t : (v.detalle || v.reloj || 'En vivo'));
      return '<span class="et vivo"><i class="punto"></i>' + esc(txt) + '</span>';
    }
    if (v && v.terminado) return '<span class="et">Terminado · liquidando</span>';
    if (ini && ini <= new Date()) return '<span class="et vivo"><i class="punto"></i>En juego</span>';
    return '<span class="et">⏳ ' + esc(cuentaAtras(ini)) + '</span>';
  }
  // ---------- ESTADÍSTICAS VISUALES (como SofaScore) ----------
  // Cada fila: número del local | nombre | número del visitante; el que va
  // adelante en su color, y dos barras que crecen desde el centro.
  const num = (x) => { const n = parseFloat(String(x == null ? '' : x).replace('%', '')); return isNaN(n) ? 0 : n; };
  function filaStat(etq, va, vb, chica) {
    const a = num(va), b = num(vb), m = Math.max(a, b) || 1;
    const ga = a > b, gb = b > a;
    return '<div class="st' + (chica ? ' chica' : '') + '">' +
      '<div class="st-nums"><span class="pill l' + (ga ? ' gana' : '') + '">' + esc(va ?? '-') + '</span>' +
      '<span class="st-etq">' + esc(etq) + '</span>' +
      '<span class="pill r' + (gb ? ' gana' : '') + '">' + esc(vb ?? '-') + '</span></div>' +
      '<div class="st-barras"><div class="mitad izq"><i class="' + (ga ? 'gana' : '') + '" style="width:' + (100 * a / m) + '%"></i></div>' +
      '<div class="mitad der"><i class="' + (gb ? 'gana' : '') + '" style="width:' + (100 * b / m) + '%"></i></div></div></div>';
  }
  function posesion(v) {
    const s = v.stats.possessionPct; if (!s) return '';
    const a = num(s.v[0]), b = num(s.v[1]), t = a + b || 1;
    if (!a || !b) return '';           // 0 % - 100 %: ESPN aún no la calcula
    return '<div class="posesion"><div class="pos-etq">Posesión</div><div class="pos-barra">' +
      '<i class="l" style="width:' + (100 * a / t) + '%">' + Math.round(a) + '%</i>' +
      '<i class="r" style="width:' + (100 * b / t) + '%">' + Math.round(b) + '%</i></div></div>';
  }
  // v394 — si ESPN todavía no manda las estadísticas (ligas chicas: llegan con
  // retraso o sólo al final) se dice, en vez de pintar barras en cero
  const AVISO_SIN_STATS = '<div class="mini sin-stats">📡 Las estadísticas en vivo de este partido aún no llegan: ' +
    'ESPN las publica con retraso en esta liga. El marcador sí va al minuto y esto se actualiza solo.</div>';
  function statsVacias(v) {
    const vals = Object.values(v.stats || {}).flatMap((s) => (s.v || []).map((x) => num(x)));
    return !vals.length || vals.every((x) => x === 0);
  }
  // v518 — el usuario: «así no tengan pick tienen que tener bien sus estadísticas». ESPN a veces manda
  // sólo faltas y tarjetas (Copa del Rey: tiros y córners en 0 con 1-3 en el marcador al 90'). Eso es
  // no tenerlas: se toma el respaldo entero (365Scores / FotMob) o se avisa, nunca barras en cero.
  function statsHueco(v, p) {
    if (statsVacias(v)) return true;
    if (!p || p.deporte !== 'Fútbol') return false;
    const s = v.stats || {};
    const ceros = ['totalShots', 'shotsOnTarget', 'wonCorners'].every((k) => !s[k] || (s[k].v || []).every((x) => !num(x)));
    const g = v.g || [0, 0], min = parseInt(String(v.reloj || ''), 10) || 0;
    return ceros && (g[0] + g[1] > 0 || min >= 30 || v.fase === 'post');
  }
  // v429 — LA CANCHA, «LO MEJOR DE CADA FUENTE». El usuario: «junta lo mejor
  // de cada una… que se vea como el partido; simple pero moderno e innovador».
  //   · 365Scores (abierto a cualquier página): la alineación de los 22 en su
  //     formación con número y calificación, y TODOS los tiros con su xG, xGOT,
  //     pie/cabeza y por dónde fueron al arco.
  //   · ESPN: las jugadas con lugar (faltas, córners, fueras de lugar…).
  //   · un balón que recorre las últimas jugadas en orden, para que se vea como
  //     el partido; y la «ola» de presión minuto a minuto (tiros por su xG,
  //     córners y jugadas de ataque).
  // Coordenadas: las dos fuentes dan cada jugada en la dirección de ataque de
  // quien la hizo (hacia 100); el local ataca a la derecha, el visitante se refleja.
  const API365 = 'https://webws.365scores.com/web/';
  const P365 = 'appTypeId=5&langId=29&timezoneName=America/Mexico_City&userCountryId=31';
  estado.d365 = {}; estado.g365 = {}; estado.p365 = {};
  async function dia365(dia, vivo) {
    const c = estado.g365[dia];
    if (c && Date.now() - c.ts < (vivo ? 55e3 : 3 * 60e3)) return c.juegos;
    const [a, m, d] = dia.split('-');
    try {
      const r = await fetch(API365 + 'games/allscores/?' + P365 + '&sports=1&showOdds=false&startDate=' + d + '/' + m + '/' + a + '&endDate=' + d + '/' + m + '/' + a);
      const j = r.ok ? await r.json() : null;
      estado.g365[dia] = { ts: Date.now(), juegos: ((j && j.games) || []).map((g) => ({ id: g.id, home: g.homeCompetitor.name, away: g.awayCompetitor.name,
        gt: g.statusGroup === 3 && Number(g.gameTime) > 0 ? Number(g.gameTime) : null })) };      // v493: el minuto en vivo
    } catch (e) { estado.g365[dia] = { ts: Date.now(), juegos: (c && c.juegos) || [] }; }
    return estado.g365[dia].juegos;
  }
  // v493 — el minuto de los partidos en vivo que no lo traen (sólo Flashscore: «1.ª parte»)
  estado.m365 = {};
  async function minutos365() {
    if (document.hidden || !estado.grupos) return;
    const rel = /\d+\s*['’]|^\d+$/;
    const sin = [...estado.grupos.values()].map((g) => g[0]).filter((p) => {
      const v = vivoDe([p]); return p.deporte === 'Fútbol' && v && v.fase === 'in' && !enPausa(v) && !rel.test(String(v.reloj || '').trim());
    });
    if (!sin.length) return;
    let cambio = false;
    for (const dia of [...new Set(sin.map(diaDe))]) {
      const juegos = await dia365(dia, true);
      sin.filter((p) => diaDe(p) === dia).forEach((p) => {
        const k = clavePartido(p);
        let gid = estado.p365[k];
        if (gid === undefined) { const [L, V] = lados(p), cr = mejorCruce(L, V, juegos, 'home', 'away'); gid = estado.p365[k] = cr ? cr.m.id : null; if (cr && cr.girado) estado.p365[k + '|girado'] = true; }
        const j = gid && juegos.find((x) => x.id === gid);
        if (j && j.gt) { const prev = estado.m365[gid]; if (!prev || prev.gt !== j.gt) { estado.m365[gid] = { gt: j.gt, ts: Date.now() }; cambio = true; } }
      });
    }
    if (cambio) pintar();
  }
  async function detalle365(p) {
    if (p.deporte !== 'Fútbol') return null;
    const k = clavePartido(p);
    let gid = estado.p365[k];
    // v436 — si no se encontró, se vuelve a buscar cada 2 minutos (antes quedaba sin cancha para siempre)
    if (gid === undefined || (gid === null && Date.now() - (estado.p365[k + '|t'] || 0) > 120e3)) {
      estado.p365[k + '|t'] = Date.now();
      const [L, V] = lados(p), cr = mejorCruce(L, V, await dia365(diaDe(p)), 'home', 'away');
      gid = estado.p365[k] = cr ? cr.m.id : null;
      if (cr && cr.girado) estado.p365[k + '|girado'] = true;
    }
    if (!gid) return null;
    const viejo = estado.d365[gid];
    if (viejo && Date.now() - viejo.ts < 15e3) return viejo;
    try {
      const r = await fetch(API365 + 'game/?' + P365 + '&gameId=' + gid);
      const g = r.ok ? (await r.json()).game : null;
      if (!g) return viejo || null;
      const gir = !!estado.p365[k + '|girado'];
      const nombres = Object.fromEntries((g.members || []).map((m) => [m.id, m]));
      const once = (comp, lado) => ((comp.lineups || {}).members || []).filter((m) => m.status === 1 && m.yardFormation).map((m) => ({
        lado, n: (nombres[m.id] || {}).jerseyNumber || '', nombre: (nombres[m.id] || {}).shortName || (nombres[m.id] || {}).name || '',
        prof: Number(m.yardFormation.fieldLine), ancho: Number(m.yardFormation.fieldSide), nota: m.ranking || null }));
      const lh = gir ? 1 : 0, la = gir ? 0 : 1;
      const tiros = (((g.chartEvents || {}).events) || []).map((e) => ({
        lado: e.competitorNum === 1 ? lh : la, x: Number(e.side), y: Number(e.line), xg: Number(e.xg || 0), xgot: Number(e.xgot || 0),
        min: e.time || '', gol: ((e.outcome || {}).name) === 'Gol', resultado: ((e.outcome || {}).name) || '', cuerpo: e.bodyPart || '',
        jugador: (nombres[e.playerId] || {}).shortName || '', arco: e.outcome && e.outcome.y != null ? { y: Number(e.outcome.y), z: Number(e.outcome.z) } : null }));
      estado.d365[gid] = { ts: Date.now(), once: once(g.homeCompetitor, lh).concat(once(g.awayCompetitor, la)), tiros,
        minuto: Number(g.gameTime) > 0 ? Number(g.gameTime) : null, minutoTxt: g.gameTimeDisplay || '',      // v489
        formacion: [gir ? g.awayCompetitor.lineups && g.awayCompetitor.lineups.formation : g.homeCompetitor.lineups && g.homeCompetitor.lineups.formation,
          gir ? g.homeCompetitor.lineups && g.homeCompetitor.lineups.formation : g.awayCompetitor.lineups && g.awayCompetitor.lineups.formation] };
      return estado.d365[gid];
    } catch (e) { return viejo || null; }
  }
  // sólo de los partidos cuya cancha está a la vista (tarjeta abierta o ficha)
  // v460 — la presión de FotMob (por /presion, nuestra función de Cloudflare): cada 30 s en vivo; al terminar, una vez
  async function presionFM(p) {
    const k = clavePartido(p), prev = estado.pfm[k], v = vivoDe([p]);
    if (!v || v.fase === 'pre') return false;
    if (prev && ((prev.terminado && prev.momentum !== undefined) || Date.now() - prev.ts < 30e3)) return false;
    const ini = aFecha(p.inicio); if (!ini) return false;
    const f = ini.toISOString().slice(0, 10).replace(/-/g, ''), [L, V] = lados(p);
    let j = null;
    try { const r = await fetch('/presion?f=' + f + '&l=' + encodeURIComponent(L) + '&v=' + encodeURIComponent(V)); j = r.ok ? await r.json() : null; } catch (e) { /* sin red */ }
    estado.pfm[k] = Object.assign({}, j || {}, { ts: Date.now() });
    return !!(j && (j.momentum || j.mitades)) && JSON.stringify([j.momentum, j.mitades, j.eventos]) !== JSON.stringify(prev ? [prev.momentum, prev.mitades, prev.eventos] : null);
  }
  async function vivo365() {
    if (document.hidden) return;
    const vistos = new Set([...estado.abiertos].concat(fichaId ? [clavePartido(estado.picks.find((x) => x.id === fichaId) || {})] : []));
    const ps = estado.picks.concat(estado.analisis || []).filter((p) => vistos.has(clavePartido(p)) && p.deporte === 'Fútbol');
    const hechos = new Set();
    let cambio = false;
    for (const p of ps) {
      const k = clavePartido(p); if (hechos.has(k)) continue; hechos.add(k);
      const previo = estado.d365[estado.p365[k]], antes = JSON.stringify((previo || {}).tiros || []) + ((previo || {}).once || []).length;
      const d = await detalle365(p);
      if (d && (!previo || JSON.stringify(d.tiros) + (d.once || []).length !== antes)) cambio = true;   // v436: también si llega la alineación      // v431: también al llegar por 1.ª vez
      const v = vivoDe([p]);
      if (estado.p365[k] && v && v.fase === 'in') await stats365(estado.p365[k]);      // v431 — quién ataca ahora
      if (await presionFM(p)) cambio = true;                                           // v460
    }
    if (cambio) { pintar(); refrescarFicha(); }
  }

  const JUGADA = { goal: ['⚽', 'Gol', 5], 'penalty---scored': ['⚽', 'Gol de penal', 5], 'shot-on-target': ['🎯', 'Tiro a puerta', 3],
    'shot-off-target': ['↗️', 'Tiro desviado', 2], 'shot-blocked': ['🧱', 'Tiro bloqueado', 1.5], 'corner-awarded': ['🚩', 'Córner', 1],
    foul: ['✋', 'Falta', 0], offside: ['🚩', 'Fuera de lugar', 0.5], 'yellow-card': ['🟨', 'Amarilla', 0], 'red-card': ['🟥', 'Roja', 0] };
  // v517 — ESPN también manda «goal---header», «goal---left-footed»…: son goles (antes salía el texto crudo y no contaba como gol)
  const jugada = (t) => JUGADA[t] || (/^goal/.test(t || '') ? JUGADA.goal : /^penalty.*scored/.test(t || '') ? JUGADA['penalty---scored'] : null);
  const BASE_442 = [[0, 50], [24, 10], [20, 36], [20, 64], [24, 90], [58, 10], [50, 38], [50, 62], [58, 90], [90, 38], [90, 62]];
  const minuto = (s) => { const m = String(s || '').match(/(\d+)(?:'\s*\+\s*(\d+))?/); return m ? Number(m[1]) + (m[2] ? Number(m[2]) / 10 : 0) : 0; };
  function cancha(v, p) {
    const k = p ? clavePartido(p) : '';
    const d = p ? estado.d365[estado.p365[k]] : null;
    // v436 — UNA FUENTE POR COSA, SIN MEZCLAR (el usuario: «cuando uno no funciona,
    // agarrar el otro, pero no combinarlos»). Si la primera no trae nada, la siguiente:
    //   · alineación: 365Scores → ESPN → (sin ninguna) puntitos en 4-4-2, sin nombres;
    //   · jugadas: ESPN con su lugar → tiros de 365Scores → goles y tarjetas de ESPN.
    const espnJ = (v && v.jugadas) || [], t365 = (d && d.tiros) || [], evE = ((v && v.eventos) || []).filter((e) => e.gol || /🟨|🟥/.test(e.ico));
    const fuente = espnJ.length ? 'espn' : t365.length ? '365' : evE.length ? 'eventos' : '';
    const js = fuente === 'espn' ? espnJ : [], todos = t365;
    const onceReal = d && d.once && d.once.length >= 18 ? d.once : v && v.once && v.once.length >= 18 ? v.once : null;
    const pfm = k ? estado.pfm[k] : null;                     // v460 — la presión de FotMob
    if (!fuente && !onceReal && !(pfm && (pfm.momentum || pfm.mitades))) return '';
    const once = onceReal || BASE_442.flatMap(([prof, ancho], i) => [0, 1].map((lado) => ({ lado, n: '', nombre: '', i, prof, ancho, nota: null })));
    const dibujo = fuente === '365' ? t365 : fuente === 'espn' ? espnJ.filter((j) => /goal|scored|shot/.test(j.t)).map((j) => ({ lado: j.lado, x: j.x, y: j.y,
      xg: /goal|scored/.test(j.t) ? 0.35 : /on-target/.test(j.t) ? 0.2 : 0.1, min: j.min, gol: /goal|scored/.test(j.t), resultado: (jugada(j.t) || ['', ''])[1], cuerpo: j.equipo, jugador: '' })) : [];
    const c = (v && v.colores) || { l: '#22c55e', r: '#e879f9' };
    const col = (lado) => (lado === 0 ? c.l : c.r);
    const X = (lado, x) => ((lado === 0 ? x : 100 - x) * 1.05).toFixed(2), Y = (lado, y) => ((lado === 0 ? y : 100 - y) * 0.68).toFixed(2);
    // v489 — sin minuto real («2.ª parte» de Flashscore se leía como minuto 2): el de 365Scores
    const relojTxt = String((v && (v.reloj || v.detalle)) || '').trim();
    const reloj = /\d+\s*['’]|^\d+$/.test(relojTxt) ? minuto(relojTxt) : ((d && d.minuto) || minuto(relojTxt));
    const ahora = Math.max(reloj, ...js.map((j) => j.seg / 60), ...dibujo.map((t) => minuto(t.min)), ...evE.map((e) => minuto(e.min)), 0);
    const pausa = !v || v.fase !== 'in' || enPausa(v);
    const letrero = !v || v.fase === 'pre' ? '' : v.terminado || v.fase === 'post' ? 'FINAL'
      : v.est === 'STATUS_SHOOTOUT' || v.est === 'STATUS_END_OF_EXTRATIME' ? 'PENALES' : v.est === 'STATUS_END_OF_REGULATION' ? 'VA A PRÓRROGA'
        : v.est === 'STATUS_HALFTIME_ET' ? 'DESCANSO' : pausa ? 'MEDIO TIEMPO' : '';
    // sin ruido: los goles siempre; los demás tiros, sólo los de los últimos 15 minutos
    const tiros = dibujo.filter((t) => t.gol || minuto(t.min) >= ahora - 15);
    // las jugadas REALES para el motor, de la fuente elegida
    const enTiempo = (m, per) => (per === 1 ? Math.min(m, 45.5) : per === 2 ? Math.max(m, 45.5) : m);   // v460
    const reales = (fuente === 'espn' ? js.map((j) => ({ id: 'e' + j.seg + j.t, t: j.t, src: 'espn', m: enTiempo(j.seg / 60, j.per), lado: j.lado, x: X(j.lado, j.x), y: Y(j.lado, j.y),
      w: (jugada(j.t) || [0, 0, 0])[2], txt: (jugada(j.t) || ['•', ''])[0] + ' <b>' + esc((jugada(j.t) || ['', 'Jugada'])[1]) + '</b> · ' + esc(j.equipo) + ' · ' + esc(j.min) }))
      : fuente === '365' ? t365.map((t) => ({ id: 't' + t.min + t.x + t.y, t: t.gol ? 'goal' : /ataj/i.test(t.resultado) ? 'shot-on-target' : 'shot-off-target', src: '365',
        m: minuto(t.min), lado: t.lado, x: X(t.lado, t.x), y: Y(t.lado, t.y),
        w: 1.5 + 8 * t.xg, txt: (t.gol ? '⚽ <b>Gol</b>' : '🎯 <b>Tiro</b>') + ' · ' + esc(t.jugador) + ' · ' + esc(t.min) }))
      : evE.map((e) => ({ id: 'k' + e.min + e.lado + e.ico, t: e.gol ? 'goal' : '', src: 'eventos', m: minuto(e.min), lado: e.lado,
        x: X(e.lado, 95), y: Y(e.lado, 50), w: e.gol ? 5 : 0, txt: e.ico + ' <b>' + (e.gol ? 'Gol' : 'Tarjeta') + '</b> · ' + esc(e.texto) + ' · ' + esc(e.min) })))
      .sort((a, b) => a.m - b.m);
    if (k) {
      // v434 — el usuario: al abrir una tarjeta en vivo, la cancha va EN EL MINUTO
      // QUE CORRE, no desde el saque inicial. Lo ya pasado no se repite (antes, si
      // las jugadas llegaban después de abrir, se volvían a jugar desde el minuto 1).
      const m = estado.motor[k] = Object.assign(estado.motor[k] || { vistas: new Set() }, { gid: estado.p365[k] || null, pausa, minuto: ahora, reales });
      if (!m.ini && reales.length) {
        m.ini = true; m.pos = {}; m.portador = null; m.escena = null; m.cola = [];
        reales.forEach((q) => m.vistas.add(q.id));
        const u = reales[reales.length - 1], h = m.gid ? estado.s365[m.gid] || [] : [];
        if (h.length) m.statsVisto = h[h.length - 1].t;
        if (u && !pausa) {
          const reciente = ahora - u.m <= 3, dir = u.lado === 0 ? 1 : -1;
          m.bx = reciente ? Math.max(6, Math.min(99, Number(u.x) - dir * 8)) : 52.5 + dir * 14;
          m.by = reciente ? Math.max(6, Math.min(62, Number(u.y))) : 34;
        }
      }
    }
    let s = '<svg class="cancha-svg" viewBox="0 0 105 68" role="img" aria-label="Cancha en vivo"' + (k ? ' data-motor="' + esc(k) + '"' : '') + '>' +
      '<defs><pattern id="franjas" width="10.5" height="68" patternUnits="userSpaceOnUse"><rect width="5.25" height="68" fill="rgba(255,255,255,.025)"/></pattern>' +
      '<radialGradient id="luz" cx="50%" cy="40%" r="75%"><stop offset="0" stop-color="#1c7a45"/><stop offset="1" stop-color="#0d3b22"/></radialGradient>' +
      '<filter id="brillo"><feGaussianBlur stdDeviation=".7" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>' +
      '<rect width="105" height="68" rx="2.5" fill="url(#luz)"/><rect width="105" height="68" rx="2.5" fill="url(#franjas)"/><g class="lineas">' +
      '<rect x=".6" y=".6" width="103.8" height="66.8" rx="1.6"/><line x1="52.5" y1=".6" x2="52.5" y2="67.4"/><circle cx="52.5" cy="34" r="9.15"/><circle cx="52.5" cy="34" r=".5" class="punto"/>' +
      '<rect x=".6" y="13.85" width="16.5" height="40.3"/><rect x="87.9" y="13.85" width="16.5" height="40.3"/>' +
      '<rect x=".6" y="24.85" width="5.5" height="18.3"/><rect x="98.9" y="24.85" width="5.5" height="18.3"/>' +
      '<path d="M17.1 26.7 A9.15 9.15 0 0 1 17.1 41.3"/><path d="M87.9 26.7 A9.15 9.15 0 0 0 87.9 41.3"/></g>';
    tiros.forEach((t) => {
      const r = (0.8 + 2.6 * Math.min(1, t.xg)).toFixed(2);
      s += '<g class="tiro' + (t.gol ? ' gol' : '') + '"><title>' + esc((t.gol ? '⚽ Gol de ' : 'Tiro de ') + t.jugador + ' · ' + t.min + ' · xG ' + t.xg.toFixed(2) + ' · ' + t.cuerpo + (t.gol ? '' : ' · ' + t.resultado)) + '</title>' +
        '<circle cx="' + X(t.lado, t.x) + '" cy="' + Y(t.lado, t.y) + '" r="' + r + '" stroke="' + col(t.lado) + '" fill="' + (t.gol ? col(t.lado) : 'none') + '"/>' +
        (t.gol ? '<text x="' + X(t.lado, t.x) + '" y="' + (Number(Y(t.lado, t.y)) + 0.9).toFixed(2) + '" class="bal">⚽</text>' : '') + '</g>';
    });
    // los 22 en su formación; el motor los mueve con el juego (data-bx/by = su lugar)
    once.forEach((j) => {
      const x = j.lado === 0 ? 3 + j.prof * 0.45 : 102 - j.prof * 0.45, y = j.lado === 0 ? 5 + j.ancho * 0.58 : 63 - j.ancho * 0.58;
      const key = j.lado + '|' + (j.n || j.nombre || 'p' + j.i), mo = estado.motor[k], pm = (mo && mo.pos || {})[key];
      let tx = pm ? pm[0] : x, ty = pm ? pm[1] : y;
      if (!pm && mo && mo.bx != null) {
        // v434 — al abrir: cada quien ya corrido hacia donde va el balón ahora
        const gk = j.prof <= 5;
        tx = Math.max(2, Math.min(103, x + (mo.bx - 52.5) * (gk ? 0.08 : 0.42))); ty = Math.max(3, Math.min(65, y + (mo.by - 34) * (gk ? 0.15 : 0.28)));
        (mo.pos = mo.pos || {})[key] = [tx, ty];
      }
      s += '<g class="jug' + (estado.motor[k] && estado.motor[k].portador === key ? ' portador' : '') + '" data-key="' + esc(key) + '" data-bx="' + x.toFixed(2) + '" data-by="' + y.toFixed(2) +
        '" data-prof="' + j.prof + '" data-lado="' + j.lado + '" style="transform: translate(' + tx.toFixed(2) + 'px,' + ty.toFixed(2) + 'px)">' +
        '<title>' + esc(j.n + ' ' + j.nombre + (j.nota ? ' · ' + j.nota : '')) + '</title>' +
        '<circle class="aro" r="2.4" fill="' + col(j.lado) + '"/><circle class="pto" r="1.05" fill="' + col(j.lado) + '"/>' +
        '<text y=".75" class="num">' + esc(j.n) + '</text><text y="5" class="nom">' + esc(j.nombre) + '</text></g>';
    });
    s += '<line class="pase" x1="0" y1="0" x2="0" y2="0"/>';
    const mb = k && estado.motor[k] && estado.motor[k].bx != null ? [estado.motor[k].bx, estado.motor[k].by] : [52.5, 34];
    s += '<g class="balon" style="transform: translate(' + mb[0].toFixed(2) + 'px,' + mb[1].toFixed(2) + 'px)"><ellipse cx=".35" cy=".75" rx="1.25" ry=".55" class="sombra"/><circle r="2" class="halo"/>' +
      '<circle r="1.25" class="bola"/><path d="M0,-.55 L.52,-.17 L.32,.45 L-.32,.45 L-.52,-.17Z" class="penta"/></g>';
    if (letrero) s += '<g class="letrero"><rect x="32.5" y="27" width="40" height="14" rx="3"/><text x="52.5" y="36.2">' + letrero + '</text></g>';
    s += '</svg>';
    const ult = reales.length ? reales[reales.length - 1] : null;
    const xg = [0, 1].map((l) => todos.filter((t) => t.lado === l).reduce((a, t) => a + t.xg, 0));
    const cab = '<div class="cancha-ult"><span class="chip-ult">' + (ult ? ult.txt : '⚽ <b>En vivo</b>') + '</span>' +
      (todos.length ? '<span class="xg"><i style="background:' + c.l + '"></i>xG ' + xg[0].toFixed(2) + ' · ' + xg[1].toFixed(2) + '<i style="background:' + c.r + '"></i></span>' : '') + '</div>';
    // la ola de presión: minuto a minuto, suavizada
    // v460 — LA PRESIÓN DE TODOS LOS PARTIDOS (el usuario: «todos tienen que tener su barra,
    // dividida en 1.er y 2.º tiempo, con sus goles y tarjetas, también al terminar»). En este
    // orden y SIEMPRE con datos reales: 1) FotMob minuto a minuto («momentum»); 2) las jugadas
    // de ESPN o los tiros de 365Scores; 3) FotMob por tiempo: quién dominó el 1T y el 2T (tiros,
    // a puerta, córners, ocasiones claras y toques en el área); 4) si no hay nada, la línea.
    const mom = pfm && Array.isArray(pfm.momentum) && pfm.momentum.length >= 5 ? pfm.momentum : null;
    const fin = Math.max(90, ahora, mom ? mom.length - 1 : 0), xm = (m) => Math.max(0, Math.min(100, 100 * m / fin));
    const pocasJugadas = reales.filter((q) => q.w > 0).length < 4;
    const dominio = (x) => { if (!x) return null; const t = (i) => (x.tiros || [0, 0])[i] + 2 * (x.puerta || [0, 0])[i] + (x.corners || [0, 0])[i] + 3 * (x.ocasiones || [0, 0])[i] + 0.3 * (x.area || [0, 0])[i];
      const a = t(0), b = t(1); return a + b > 0 ? (a - b) / (a + b) : null; };
    const mits = pfm && pfm.mitades ? pfm.mitades.map(dominio) : null;
    const modo = mom ? 'momentum' : !pocasJugadas ? 'jugadas' : mits && mits.some((x) => x != null) ? 'mitades' : 'linea';
    const barra = (x0, x1, valor, tope) => { const h = 11 * Math.abs(valor) / tope; return h < 0.2 ? '' : '<rect x="' + x0.toFixed(2) + '" y="' + (valor > 0 ? 12 - h : 12).toFixed(2) +
      '" width="' + Math.max(0.3, x1 - x0).toFixed(2) + '" height="' + h.toFixed(2) + '" fill="' + (valor > 0 ? c.l : c.r) + '"/>'; };
    let barras = '';
    if (modo === 'momentum') {
      const tope = Math.max(1, ...mom.map(Math.abs)), W = 100 / fin;
      barras = mom.map((x, i) => barra(xm(i) - W * 0.38, xm(i) + W * 0.38, x, tope)).join('');
    } else if (modo === 'jugadas') {
      const val = new Array(Math.ceil(fin) + 1).fill(0);
      reales.forEach((q) => { const m = Math.floor(q.m); if (val[m] != null) val[m] += (q.lado === 0 ? 1 : -1) * q.w; });
      const suave = val.map((_, i) => val.slice(Math.max(0, i - 3), i + 1).reduce((a, b, kk, arr) => a + b * (kk + 1) / arr.length, 0));
      const tope = Math.max(1, ...suave.map(Math.abs)), W = 100 / fin;
      barras = suave.map((x, i) => barra(xm(i) - W * 0.38, xm(i) + W * 0.38, x, tope)).join('');
    } else if (modo === 'mitades') {
      // una barra ancha por tiempo, hasta el minuto que va
      const hasta = Math.min(ahora || fin, fin);
      barras = [[0, 45, mits[0]], [45.5, fin, mits[1]]].map(([a, b, x]) => (x == null || hasta <= a ? '' : barra(xm(a) + 0.4, xm(Math.min(b, hasta)) - 0.4, x || 0.05, 1))).join('');
    }
    const ola = '<svg class="presion-svg' + (modo === 'linea' ? ' linea' : '') + '" viewBox="0 0 100 24" preserveAspectRatio="none" aria-label="' +
      ({ momentum: 'Presión minuto a minuto', jugadas: 'Presión minuto a minuto', mitades: 'Presión por tiempo', linea: 'El partido minuto a minuto' }[modo]) + '">' +
      (modo === 'linea' ? '<line x1="0" y1="12" x2="100" y2="12" class="pista"/><line x1="0" y1="12" x2="' + xm(ahora).toFixed(1) + '" y2="12" class="va"/>' : barras) +
      '<line x1="' + xm(45.5).toFixed(2) + '" y1="1" x2="' + xm(45.5).toFixed(2) + '" y2="23" class="eje medio"/>' + (modo === 'linea' ? '' : '<line x1="0" y1="12" x2="100" y2="12" class="eje"/>') + '</svg>';
    const tiempos = '<div class="ola-tiempos"><span style="width:' + xm(45.5).toFixed(1) + '%">1.er tiempo</span><span>2.º tiempo</span></div>';
    // v432/v460 — un ⚽ en el minuto de cada gol y las tarjetas (arriba el local, abajo el visitante):
    // de la fuente elegida y, si ésta no los trae, de FotMob
    const deReales = reales.filter((q) => /Gol|Tarjeta/.test(q.txt)).map((q) => ({ m: q.m, lado: q.lado, tipo: /Tarjeta/.test(q.txt) ? q.txt.slice(0, 2) : 'gol', txt: q.txt.replace(/<[^>]+>/g, '') }));
    const deFotmob = pfm && Array.isArray(pfm.eventos) ? pfm.eventos.map((e) => ({ m: e.m <= 45 && e.extra ? 45 : e.m, lado: e.local ? 0 : 1,
      tipo: e.tipo === 'gol' ? 'gol' : e.tipo === 'roja' ? '🟥' : '🟨', txt: (e.tipo === 'gol' ? 'Gol' : 'Tarjeta') + ' · ' + e.m + (e.extra ? '+' + e.extra : '') + "'" })) : [];
    // v487 — el usuario: «Milan-Bologna van 2-3 y en la presión sólo aparecen 4 balones; pasa cuando hay
    // muchos goles». Los goles salían sólo de las jugadas de la fuente elegida (a esa le faltaba el del 60')
    // y FotMob sólo entraba si no había NINGUNO. Ahora gana la fuente cuyos goles cuadran con el marcador
    // (jugadas, eventos de ESPN o FotMob); si ninguna cuadra, la que trae más.
    const totalGoles = v && Array.isArray(v.g) ? Number(v.g[0] || 0) + Number(v.g[1] || 0) : null;
    const golesE = evE.filter((e) => e.gol).map((e) => ({ m: minuto(e.min), lado: e.lado, tipo: 'gol', txt: 'Gol · ' + String(e.min || '') }));
    const fuentesGol = [deReales.filter((q) => q.tipo === 'gol'), golesE, deFotmob.filter((q) => q.tipo === 'gol')];
    const golesM = fuentesGol.find((f) => totalGoles != null && f.length === totalGoles) || fuentesGol.reduce((a, b) => (b.length > a.length ? b : a));
    const tarjetasR = deReales.filter((q) => q.tipo !== 'gol');
    const marcas = golesM.concat(tarjetasR.length ? tarjetasR : deFotmob.filter((q) => q.tipo !== 'gol'));
    const vistoGol = new Set();
    const goles = marcas.filter((q) => { const g = Math.round(q.m) + '|' + q.lado + '|' + q.tipo; if (vistoGol.has(g)) return false; vistoGol.add(g); return true; })
      .map((q) => '<span class="ola-gol ' + (q.lado === 0 ? 'arriba' : 'abajo') + '" style="left:' + Math.min(98, xm(q.m)).toFixed(1) + '%" title="' + esc(q.txt) + '">' + (q.tipo === 'gol' ? '⚽' : q.tipo) + '</span>').join('');
    const pocas = modo === 'linea';
    const fm = onceReal && d && onceReal === d.once ? d.formacion : onceReal && v ? v.formacion : null;
    const form = fm && (fm[0] || fm[1]) ? '<small class="tenue">' + esc(fm[0] || '') + ' vs ' + esc(fm[1] || '') + '</small>' : '';
    // v434 — el usuario: «el menos texto posible»; lo demás queda en el tooltip
    const leyenda = '<div class="cancha-ley" title="Tamaño del tiro = peligro (xG). Animación aproximada según el juego."><span><i class="l-tiro"></i>tiro</span><span><i class="l-gol"></i>gol</span></div>';
    return '<div class="cancha">' + cab + s + leyenda + '<div class="cancha-tit"><span>' + ({ momentum: 'Presión', jugadas: 'Presión', mitades: 'Presión por tiempo', linea: 'Sin datos de presión en esta liga' }[modo]) + '</span>' + form + '</div><div class="ola">' + ola + goles + '</div>' + tiempos + '</div>';
  }
  // v431 — EL MOTOR: QUE LA CANCHA SE VEA COMO EL PARTIDO. El usuario: «no me
  // gusta que las bolitas se queden estáticas… no se entienden las circunferencias
  // blancas… en el medio tiempo el balón se sigue moviendo». Ninguna fuente gratis
  // da la posición de los 22 en vivo (Sofascore la paga y bloquea su API), así que
  // la animación se ARMA con lo que sí hay, y lo dice:
  //   · quién ataca AHORA: lo que cambió en el último minuto en 365Scores (pases
  //     en el último tercio, posesiones ganadas arriba, remates, grandes ocasiones,
  //     córners) y, si no, la posesión y las jugadas de ESPN;
  //   · el balón anda por esa zona y, cuando llega una jugada REAL con lugar (tiro,
  //     córner, falta…), salta ahí con su etiqueta;
  //   · los 22 se mueven con el balón (el bloque sube o baja, se cierran a su lado);
  //   · en el medio tiempo y al final, todo se detiene y la cancha lo dice.
  const STATS_ATAQUE = { 80: 1, 84: 1.5, 3: 2.5, 4: 3, 24: 4, 8: 2 };     // id de 365Scores → peso
  estado.s365 = {}; estado.motor = {};
  async function stats365(gid) {
    try {
      const r = await fetch(API365 + 'game/stats/?' + P365 + '&games=' + gid);
      const j = r.ok ? await r.json() : null;
      const comp = ((j && j.competitors) || []).map((c) => c.id);
      const fila = {};
      ((j && j.statistics) || []).filter((s) => s.filterId == null || s.filterId === -1).forEach((s) => {
        const lado = comp.indexOf(s.competitorId);
        if (lado < 0) return;
        fila[s.id] = fila[s.id] || [0, 0];
        fila[s.id][lado] = parseFloat(String(s.value).replace('%', '')) || 0;
      });
      const h = estado.s365[gid] = (estado.s365[gid] || []).concat([{ t: Date.now(), v: fila }]).slice(-6);
      return h;
    } catch (e) { return estado.s365[gid] || []; }
  }
  // dominio: de −1 (ataca el visitante) a +1 (ataca el local), con lo del último minuto
  function dominio(k) {
    const m = estado.motor[k] || {};
    const h = m.gid ? estado.s365[m.gid] || [] : [];
    let a = 0, b = 0;
    if (h.length >= 2) {
      const x = h[h.length - 1].v, y = h[Math.max(0, h.length - 3)].v;
      for (const [id, w] of Object.entries(STATS_ATAQUE)) {
        const n = x[id], o = y[id] || [0, 0];
        if (n) { a += w * Math.max(0, n[0] - o[0]); b += w * Math.max(0, n[1] - o[1]); }
      }
    }
    // y las jugadas reales de los últimos 4 minutos
    const ahora = m.minuto || 0;
    (m.reales || []).filter((q) => q.m >= ahora - 4).forEach((q) => { if (q.lado === 0) a += q.w; else b += q.w; });
    if (a + b > 0) return Math.max(-1, Math.min(1, (a - b) / (a + b + 2)));
    const pos = (h.length && h[h.length - 1].v[10]) || null;
    return pos ? Math.max(-0.6, Math.min(0.6, (pos[0] - 50) / 40)) : 0;
  }
  const azar = () => (Math.random() + Math.random() + Math.random() - 1.5) / 1.5;   // ~normal, de −1 a 1
  // v432 — «que los jugadores se muevan conforme se mueve el balón, con lógica:
  // no un defensa hasta el fondo». Cada puesto tiene su franja (en la dirección
  // de ataque de su equipo, de 0 = su portería a 105 = la contraria):
  const FRANJA = (prof) => (prof <= 5 ? [2, 13] : prof <= 35 ? [7, 66] : prof <= 65 ? [16, 88] : [34, 97]);   // v435: nadie pegado a la línea
  // v433 — LAS JUGADAS A BALÓN PARADO. El usuario: «que tengan la lógica de cuando
  // hay un tiro de esquina, un tiro directo, un penal, cuando festejan, un saque
  // de banda». Cada jugada REAL (ESPN o 365Scores) o lo que suben las estadísticas
  // de 365Scores (córners, faltas, saques de banda) arma una ESCENA de unos
  // segundos: dónde va el balón y dónde se pone cada quien.
  const TICKS = { corner: 5, libre: 4, penal: 5, gol: 7, banda: 3, tiro: 3, saque: 3 };
  function escenaDe(q) {
    // q.t de ESPN o de 365Scores; q.lado = quien la hizo (en la falta, el que la cometió)
    const otro = q.lado === 0 ? 1 : 0;
    if (q.t === 'corner-awarded') return { tipo: 'corner', atk: q.lado, y: Number(q.y) };
    if (q.t === 'foul' || q.t === 'offside') return { tipo: 'libre', atk: otro, x: Number(q.x), y: Number(q.y) };
    if (/penalty/.test(q.t)) return { tipo: 'penal', atk: q.lado, luego: /scored/.test(q.t) ? 'gol' : null };
    if (q.t === 'goal') return { tipo: 'gol', atk: q.lado, x: Number(q.x), y: Number(q.y) };
    if (/shot/.test(q.t)) return { tipo: 'tiro', atk: q.lado, x: Number(q.x), y: Number(q.y), puerta: q.t === 'shot-on-target' };
    if (q.t === 'banda') return { tipo: 'banda', atk: q.lado };
    return null;
  }
  // lo que suben las estadísticas (cuando ESPN no da jugadas con lugar)
  function escenasDeStats(m) {
    const h = m.gid ? estado.s365[m.gid] || [] : [];
    if (h.length < 2 || m.statsVisto === h[h.length - 1].t) return [];
    m.statsVisto = h[h.length - 1].t;
    const x = h[h.length - 1].v, y = h[h.length - 2].v, out = [];
    const sube = (id, lado) => ((x[id] || [0, 0])[lado] - (y[id] || [0, 0])[lado]);
    [0, 1].forEach((lado) => {
      if (!(m.reales || []).some((q) => /^e/.test(q.id))) {          // sin ESPN: córners y faltas de las estadísticas
        for (let i = 0; i < sube(8, lado); i++) out.push({ t: 'corner-awarded', lado, y: Math.random() < 0.5 ? 10 : 58, txt: '🚩 <b>Córner</b>' });
        for (let i = 0; i < sube(12, lado); i++) out.push({ t: 'foul', lado, x: 30 + Math.random() * 45, y: 8 + Math.random() * 52, txt: '✋ <b>Falta</b>' });
      }
      for (let i = 0; i < Math.min(2, sube(15, lado)); i++) out.push({ t: 'banda', lado, txt: '↔️ <b>Saque de banda</b>' });
    });
    return out;
  }
  // dónde va cada quien en la escena; d = jugadores {lado, prof, x0, y0}
  function ponerEscena(e, js, m) {
    const dirA = e.atk === 0 ? 1 : -1, gx = dirA > 0 ? 104.4 : 0.6, propia = dirA > 0 ? 0.6 : 104.4;
    const hacia = (x, dx) => x - dirA * dx;                          // dx metros antes de la portería contraria
    const atk = js.filter((q) => q.lado === e.atk), def = js.filter((q) => q.lado !== e.atk);
    const pt = (lista) => lista.find((q) => q.prof <= 5), campo = (lista) => lista.filter((q) => q.prof > 5);
    const cerca = (lista, x, y) => campo(lista).sort((a, b) => Math.hypot(a.x0 - x, a.y0 - y) - Math.hypot(b.x0 - x, b.y0 - y));
    const ptDef = pt(def), ptAtk = pt(atk);
    if (ptDef) { ptDef.x = dirA > 0 ? 103.2 : 1.8; ptDef.y = 34; }
    if (ptAtk) { ptAtk.x = dirA > 0 ? 6 : 99; ptAtk.y = 34; }
    let bx = m.bx, by = m.by;
    if (e.tipo === 'corner') {
      by = e.y < 34 ? 0.9 : 67.1; bx = gx;
      const a = cerca(atk, bx, by), t = a.shift(); if (t) { t.x = hacia(gx, 0.8); t.y = by + (by < 34 ? 0.8 : -0.8); }
      a.slice(0, 5).forEach((q, i) => { q.x = hacia(gx, 4 + (i % 3) * 3.5); q.y = 26 + i * 4; });
      a.slice(5, 7).forEach((q, i) => { q.x = hacia(gx, 19); q.y = 28 + i * 12; });
      a.slice(7).forEach((q, i) => { q.x = 52.5 - dirA * 4; q.y = 20 + i * 28; });
      campo(def).forEach((q, i) => { if (i < 6) { q.x = hacia(gx, 3 + (i % 3) * 3.5) + dirA * 0.9; q.y = 26.5 + i * 4; } else { q.x = hacia(gx, 22 + (i - 6) * 8); q.y = 24 + (i % 3) * 10; } });
    } else if (e.tipo === 'libre') {
      bx = e.x; by = e.y;
      const vx = gx - bx, vy = 34 - by, n = Math.hypot(vx, vy) || 1, ux = vx / n, uy = vy / n;
      const a = cerca(atk, bx, by), t = a.shift(); if (t) { t.x = bx - ux * 1.6; t.y = by - uy * 1.6; }
      const cercaArco = Math.abs(gx - bx) < 35;
      const d = cerca(def, bx, by);
      d.slice(0, cercaArco ? 4 : 2).forEach((q, i) => { q.x = bx + ux * 9.15 - uy * (i - 1.5) * 0.9; q.y = by + uy * 9.15 + ux * (i - 1.5) * 0.9; });   // la barrera
      a.slice(0, 5).forEach((q, i) => { q.x = cercaArco ? hacia(gx, 7 + (i % 2) * 4) : bx + dirA * (6 + i * 3); q.y = cercaArco ? 24 + i * 5 : 10 + i * 12; });
      d.slice(cercaArco ? 4 : 2).forEach((q, i) => { q.x = cercaArco ? hacia(gx, 6 + (i % 2) * 4) + dirA * 0.8 : q.x0; q.y = cercaArco ? 25 + i * 4.5 : q.y0; });
    } else if (e.tipo === 'penal') {
      bx = hacia(gx, 11); by = 34;
      const a = campo(atk).sort((p, q) => q.prof - p.prof), t = a.shift(); if (t) { t.x = hacia(gx, 13); t.y = 34.5; }
      a.concat(campo(def)).forEach((q, i) => { q.x = hacia(gx, 18.5 + (i % 3) * 2); q.y = 14 + (i * 3.3) % 40; });
    } else if (e.tipo === 'gol') {
      if (e.paso === 0) { bx = gx + dirA * 0.3; by = 34 + (Math.random() - 0.5) * 5; }                 // ¡adentro!
      const esquina = { x: hacia(gx, 3), y: (e.y || 34) < 34 ? 5 : 63 };
      campo(atk).forEach((q, i) => { q.x = esquina.x - dirA * (i % 3) * 1.6; q.y = esquina.y + (esquina.y < 34 ? 1 : -1) * Math.floor(i / 3) * 1.6; });   // el festejo
      campo(def).forEach((q) => { q.x = (q.x0 + 52.5 * 0.4) / 1.4; q.y = q.y0; });                    // los otros, de regreso
      if (ptAtk) { ptAtk.x = dirA > 0 ? 14 : 91; }
    } else if (e.tipo === 'banda') {
      by = m.by < 34 ? 0.6 : 67.4; bx = Math.max(10, Math.min(95, m.bx));
      const a = cerca(atk, bx, by), t = a.shift(); if (t) { t.x = bx; t.y = by + (by < 34 ? -0.2 : 0.2); }
      a.slice(0, 3).forEach((q, i) => { q.x = bx + dirA * (i - 1) * 6; q.y = by + (by < 34 ? 1 : -1) * (5 + i * 3); });
      cerca(def, bx, by).slice(0, 3).forEach((q, i) => { q.x = bx + dirA * (i - 0.5) * 5 + dirA * 1.5; q.y = by + (by < 34 ? 1 : -1) * (6 + i * 3); });
    } else if (e.tipo === 'tiro') {
      if (e.paso === 0) { bx = e.x; by = e.y; }
      else if (e.paso === 1) { bx = e.puerta ? gx - dirA * 1.2 : gx + dirA * 0.4; by = 34 + (e.puerta ? (Math.random() - 0.5) * 4 : (Math.random() < 0.5 ? -6 : 6)); }
      else if (!e.puerta) { bx = hacia(gx, 5.5) + dirA * 0; by = 30; if (ptDef) { ptDef.x = bx + dirA * 1; ptDef.y = by; } }   // saque de meta
      else if (ptDef) { bx = ptDef.x; by = ptDef.y; }                                                   // la tiene el portero
      campo(atk).slice(0, 3).forEach((q, i) => { q.x = hacia(gx, 10 + i * 5); q.y = 26 + i * 8; });
    }
    return [bx, by];
  }
  // v434 — EL MOTOR COMO SOFASCORE. El usuario mandó dos videos: el nuestro «se
  // mueve muy rígido, todos a la par»; el de Sofascore, «más fluido y sólo van
  // ciertos jugadores al balón». Lo que hace Sofascore y aquí se copia:
  //   · el balón SIEMPRE lo tiene alguien (sale grande, con número y nombre); los
  //     demás son puntitos;
  //   · el portador conduce o PASA a un compañero bien colocado (la línea del
  //     pase se dibuja); a veces se la roban (el que domina la pierde menos);
  //   · cada jugador va hacia su lugar con INERCIA (nadie salta) y sólo los que
  //     están cerca del balón se mueven de verdad: el rival más cercano presiona
  //     entre el portador y su portería y otro cubre; los lejanos sólo se acomodan.
  function moverCanchas() {
    if (document.hidden) return;                       // v465 — en segundo plano no se mueve nada
    document.querySelectorAll('.cancha-svg[data-motor]').forEach((svg) => {
      const rc = svg.getBoundingClientRect();
      if (rc.bottom < 0 || rc.top > window.innerHeight || !rc.height) return;   // v465 — fuera de la pantalla, quieta
      const k = svg.dataset.motor, m = estado.motor[k];
      if (!m) return;
      const quieto = m.pausa;
      const d = quieto ? 0 : dominio(k);
      m.pos = m.pos || {};
      const anunciar = (txt) => {
        const et = svg.parentElement && svg.parentElement.querySelector('.chip-ult');
        if (et && txt) { et.innerHTML = txt; et.classList.remove('nuevo'); void et.offsetWidth; et.classList.add('nuevo'); }
      };
      // los 22, con su lugar actual (persiste entre repintados) y su lugar de formación
      const js = [...svg.querySelectorAll('.jug[data-bx]')].map((j) => {
        const lado = Number(j.dataset.lado), prof = Number(j.dataset.prof), key = j.dataset.key;
        const x0 = Number(j.dataset.bx), y0 = Number(j.dataset.by), p = m.pos[key] || [x0, y0];
        return { j, key, lado, dir: lado === 0 ? 1 : -1, prof, x0, y0, cx: p[0], cy: p[1], x: x0, y: y0 };
      });
      if (!js.length) return;
      const equipo = (l) => js.filter((q) => q.lado === l), campo = (l) => equipo(l).filter((q) => q.prof > 5);
      const dist = (a, x, y) => Math.hypot(a.cx - x, a.cy - y);
      let bx = m.bx == null ? 52.5 : m.bx, by = m.by == null ? 34 : m.by, pase = null;
      let port = js.find((q) => q.key === m.portador) || null;
      if (quieto) { m.escena = null; port = null; bx = 52.5; by = 34; }
      else if (!m.escena) {
        const hayEspn = (m.reales || []).some((q) => q.src === 'espn');
        // lo que llega tarde pero ya pasó (más de 2 minutos atrás) no se juega: la cancha va en el minuto que corre
        (m.reales || []).filter((q) => !m.vistas.has(q.id) && ((hayEspn && q.src === '365') || q.m < (m.minuto || 0) - 2)).forEach((q) => m.vistas.add(q.id));
        const nueva = (m.reales || []).find((q) => q.id && !m.vistas.has(q.id));
        m.cola = (m.cola || []).concat(escenasDeStats(m));
        const ev = nueva || m.cola.shift();
        if (nueva) m.vistas.add(nueva.id);
        if (ev) { const e = escenaDe(ev); if (e) { m.escena = Object.assign(e, { paso: 0 }); anunciar(ev.txt); } }
      }
      if (m.escena) {
        // balón parado: la escena dice dónde va el balón y cada quien; lo tiene quien la cobra
        [bx, by] = ponerEscena(m.escena, js.map((q) => Object.assign(q, { x0: q.x0, y0: q.y0 })), m);
        js.forEach((q) => { q.tx = q.x; q.ty = q.y; });
        port = campo(m.escena.atk).sort((a, b) => Math.hypot(a.x - bx, a.y - by) - Math.hypot(b.x - bx, b.y - by))[0] || null;
        const e = m.escena; e.paso++;
        if (e.paso >= TICKS[e.tipo]) {
          if (e.luego) m.escena = { tipo: e.luego, atk: e.atk, paso: 0 };
          else { if (e.tipo === 'gol') { bx = 52.5; by = 34; port = campo(e.atk === 0 ? 1 : 0).sort((a, b) => a.prof - b.prof).pop() || null; } m.escena = null; }
        }
      } else if (!quieto) {
        // juego corrido: ¿quién la tiene?, ¿la pierde?, ¿conduce o pasa?
        if (!port) port = campo(d >= 0 ? 0 : 1).sort((a, b) => dist(a, bx, by) - dist(b, bx, by))[0];
        const contra = port.lado === 0 ? -d : d;                        // si su equipo va perdiendo el dominio, la pierde más
        if (Math.random() < 0.08 + 0.12 * Math.max(0, contra)) {
          const rival = campo(port.lado === 0 ? 1 : 0).sort((a, b) => dist(a, port.cx, port.cy) - dist(b, port.cx, port.cy))[0];
          if (rival) { port = rival; anunciar(''); }
        } else if (Math.random() < 0.55) {
          // el pase: a un compañero a 6-28 m, de preferencia hacia adelante
          const cands = campo(port.lado).filter((q) => q !== port).map((q) => {
            const dd = dist(q, port.cx, port.cy), avance = (q.cx - port.cx) * port.dir;
            return { q, w: dd < 6 || dd > 28 ? 0 : Math.max(0.2, (avance + 12) / dd) };
          }).filter((c) => c.w > 0);
          const tot = cands.reduce((a, c) => a + c.w, 0);
          if (tot > 0) {
            let r = Math.random() * tot; const elegido = cands.find((c) => (r -= c.w) <= 0) || cands[0];
            pase = [port.cx, port.cy, elegido.q.cx, elegido.q.cy]; port = elegido.q;
          }
        } else {
          // conduce: unos metros hacia la portería contraria
          port.cx = Math.max(7, Math.min(98, port.cx + port.dir * (2 + Math.random() * 3.5)));
          port.cy = Math.max(5, Math.min(63, port.cy + (Math.random() - 0.5) * 3));
        }
        bx = port.cx + port.dir * 2.8; by = port.cy + 0.6;
        // el lugar al que va cada uno: su formación corrida hacia el balón (poco) + lo cercano (mucho)
        js.forEach((q) => {
          const gk = q.prof <= 5;
          let tx = q.x0 + (bx - 52.5) * (gk ? 0.08 : 0.42) + q.dir * (q.lado === port.lado ? 3 : -1.5);
          let ty = q.y0 + (by - 34) * (gk ? 0.15 : 0.28);
          if (q.lado !== port.lado && !gk) ty = 34 + (ty - 34) * 0.78;
          const [mn, mx] = FRANJA(q.prof), t = q.dir > 0 ? tx : 105 - tx, tc = Math.max(mn, Math.min(mx, t));
          tx = q.dir > 0 ? tc : 105 - tc;
          q.tx = tx; q.ty = Math.max(3, Math.min(65, ty));
        });
        // los cercanos: dos compañeros se ofrecen, el rival más cercano presiona y otro cubre
        campo(port.lado).filter((q) => q !== port).sort((a, b) => dist(a, bx, by) - dist(b, bx, by)).slice(0, 2).forEach((q, i) => {
          q.tx = bx + q.dir * (i === 0 ? 7 : 3) ; q.ty = by + (i === 0 ? 9 : -9) * (by > 34 ? -1 : 1) * 0.8;
        });
        campo(port.lado === 0 ? 1 : 0).sort((a, b) => dist(a, bx, by) - dist(b, bx, by)).slice(0, 2).forEach((q, i) => {
          q.tx = bx - port.dir * (i === 0 ? 2.2 : 7); q.ty = by + (i === 0 ? 0.6 : (by > 34 ? -6 : 6));
        });
        port.tx = port.cx; port.ty = port.cy;
      } else {
        js.forEach((q) => { q.tx = q.x0; q.ty = q.y0; });
      }
      // con inercia: cada quien avanza una parte hacia su lugar (y la transición lo suaviza)
      js.forEach((q) => {
        const f = q === port ? 1 : quieto ? 0.5 : m.escena ? 0.6 : 0.38;
        q.cx += ((q.tx == null ? q.x0 : q.tx) - q.cx) * f; q.cy += ((q.ty == null ? q.y0 : q.ty) - q.cy) * f;
        const bd = q === port ? 3.2 : m.escena ? 1.2 : 2.2;               // v435: nadie fuera de la cancha (v438: el portador, con su aro, tampoco)
        q.cx = Math.max(bd, Math.min(105 - bd, q.cx)); q.cy = Math.max(bd, Math.min(68 - bd, q.cy));
        m.pos[q.key] = [q.cx, q.cy];
        q.j.style.transform = 'translate(' + q.cx.toFixed(2) + 'px,' + q.cy.toFixed(2) + 'px)';
        q.j.classList.toggle('portador', q === port);
      });
      m.portador = port ? port.key : null;
      if (port && !m.escena) { bx = port.cx + port.dir * 2.8; by = port.cy + 0.6; }
      // v438 — el balón nunca fuera de la cancha (sólo en el gol entra a la red)
      const bb = m.escena && m.escena.tipo === 'gol' ? 0.2 : 1.2;
      bx = Math.max(bb, Math.min(105 - bb, bx)); by = Math.max(bb, Math.min(68 - bb, by));
      m.bx = bx; m.by = by;
      const b = svg.querySelector('.balon');
      if (b) b.style.transform = 'translate(' + bx.toFixed(2) + 'px,' + by.toFixed(2) + 'px)';
      const ln = svg.querySelector('.pase');
      if (ln) {
        if (pase) { ln.setAttribute('x1', pase[0].toFixed(1)); ln.setAttribute('y1', pase[1].toFixed(1)); ln.setAttribute('x2', pase[2].toFixed(1)); ln.setAttribute('y2', pase[3].toFixed(1)); ln.classList.remove('ve'); void ln.getBBox(); ln.classList.add('ve'); }
        else ln.classList.remove('ve');
      }
    });
  }
  setInterval(moverCanchas, 1000);

  // v462 — el usuario: «a veces las barras de estadísticas en vivo no se muestran (Al Nassr)»:
  // ESPN no las publica en vivo en algunas ligas. Respaldo, en este orden: 365Scores (se
  // pide cada 20 s para los partidos abiertos) y FotMob (por /presion). Nunca se mezclan.
  function statsRespaldo(p) {
    if (!p || p.deporte !== 'Fútbol') return null;
    const k = clavePartido(p), gid = estado.p365[k], h = gid ? estado.s365[gid] : null, gir = !!estado.p365[k + '|girado'];
    const u = h && h.length ? h[h.length - 1].v : null;
    const par = (a, voltea) => (a ? { v: (voltea ? [a[1], a[0]] : [a[0], a[1]]).map(String) } : null);
    const limpia = (o) => { const r = Object.fromEntries(Object.entries(o).filter(([, x]) => x)); return Object.keys(r).length ? r : null; };
    if (u && (u[3] || u[10])) return limpia({ possessionPct: par(u[10], gir), totalShots: par(u[3], gir), shotsOnTarget: par(u[4], gir), wonCorners: par(u[8], gir) });
    const t = estado.pfm[k] && estado.pfm[k].todo;
    if (t) return limpia({ possessionPct: par(t.pos), totalShots: par(t.tiros), shotsOnTarget: par(t.puerta), wonCorners: par(t.corners),
      yellowCards: par(t.amarillas), foulsCommitted: par(t.faltas) });
    return null;
  }
  const conRespaldo = (v, p) => {
    if (!v || (v.stats && Object.keys(v.stats).length && !statsHueco(v, p))) return v;
    const r = statsRespaldo(p);
    return r ? Object.assign({}, v, { stats: r }) : v;
  };
  // v486 — EL RELOJ EN VIVO. El usuario: «en medio tiempo sigue saliendo 45+3 y debería decir medio
  // tiempo… quiero que se vea el tiempo exacto en el que van y cuánto agregó el árbitro». ESPN deja
  // congelado `displayClock` («45'+3'») durante el descanso; y «45'+3'» quiere decir el minuto 3 DE LA
  // compensación (minuto 48), no los minutos que se agregaron: ésos los da FotMob (`compensacion`).
  const PAUSA_RE = /medio|descanso|half|^ht$|et-ht|pausa/i;
  const enPausa = (v) => !!v && (PAUSA_ESPN.includes(v.est) || PAUSA_RE.test(String(v.detalle || '')));
  function relojVivo(v, p) {
    if (!v) return { t: 'Vivo', sub: '' };
    // v503 — prórroga y penales con su nombre (y la tanda, «2-1», debajo)
    const pen = v.pen ? v.pen.g[0] + '-' + v.pen.g[1] : '';
    if (v.est === 'STATUS_SHOOTOUT' || v.est === 'STATUS_END_OF_EXTRATIME') return { t: 'Penales', sub: pen };
    if (v.est === 'STATUS_HALFTIME_ET') return { t: 'Descanso', sub: 'de la prórroga' };
    if (v.est === 'STATUS_END_OF_REGULATION') return { t: "90'", sub: 'va a prórroga' };
    if (/EXTRA_TIME/.test(v.est || '')) { const rx = String(v.reloj || '').trim(); return { t: rx ? rx.replace(/'\+/, '+') : 'Prórroga', sub: 'prórroga' }; }
    if (enPausa(v)) return { t: 'Medio tiempo', sub: '' };
    // v489 — sólo Flashscore («2.ª parte», sin minuto): el minuto de 365Scores si ya se pidió
    const d3 = p && estado.p365 && estado.d365[estado.p365[clavePartido(p)]];
    const sinMinuto = !/\d+\s*['’]|^\d+$/.test(String(v.reloj || '').trim());
    if (sinMinuto && d3 && d3.minutoTxt && Date.now() - d3.ts < 60e3) return { t: d3.minutoTxt, sub: '' };
    // v493 — el usuario: «sale primera parte o segunda parte y al picar la tarjeta ya se actualiza el tiempo
    // real; debería mostrar el tiempo real desde que carga». El minuto de la lista del día de 365Scores
    // (una consulta para todos, cada minuto), y entre consulta y consulta corre solo.
    const m3 = sinMinuto && p && estado.p365 && estado.m365[estado.p365[clavePartido(p)]];
    if (m3) {
      const t = m3.gt + Math.floor((Date.now() - m3.ts) / 60e3), tope = m3.gt <= 45 ? 45 : m3.gt <= 90 ? 90 : 120;
      return { t: t > tope ? tope + '+' + (t - tope) + "'" : t + "'", sub: '' };
    }
    if (sinMinuto && d3 && d3.minutoTxt) return { t: d3.minutoTxt, sub: '' };
    const r = String(v.reloj || v.detalle || 'Vivo'), m = /^(\d+)'?\s*\+\s*(\d+)'?$/.exec(r.trim());
    if (!m) return { t: r, sub: '' };
    const base = Number(m[1]), extra = Number(m[2]);
    const c = p && estado.pfm[clavePartido(p)] && estado.pfm[clavePartido(p)].compensacion;
    const deC = c && (base <= 45 ? c.tiempo === 1 : c.tiempo === 2) && c.min ? c.min : null;
    return { t: base + '+' + extra + "'", sub: deC ? 'de +' + deC : '', minuto: base + extra, agregado: deC };
  }
  // v503 — la tanda de penales: un círculo por tiro (verde entró, rojo falló), con el jugador al tocarlo
  function penalesHtml(v, L, V) {
    if (!v || !v.pen) return '';
    const fila = (n, l) => '<div class="pen-f"><span class="pen-n">' + esc(n) + '</span><span class="pen-t">' +
      (v.pen.tiros[l].map((x) => '<i class="pen-' + (x.ok ? 'si' : 'no') + '" title="' + esc(x.j + (x.ok ? ': gol' : ': falló')) + '"></i>').join('') || '<small class="tenue">—</small>') +
      '</span><b>' + v.pen.g[l] + '</b></div>';
    return '<div class="penales"><div class="pen-tit">Penales' + (v.terminado ? '' : ' · en vivo') + '</div>' + fila(L, 0) + fila(V, 1) + '</div>';
  }
  // v462 — la compensación anunciada (FotMob): «+4 min de compensación»
  function compensacion(p, v) {
    const c = p && estado.pfm[clavePartido(p)] && estado.pfm[clavePartido(p)].compensacion;
    return c && v && v.fase === 'in' ? '<div class="compen">' + ico('timer') + ' +' + c.min + ' min de compensación' + (c.tiempo === 1 ? ' en el 1.er tiempo' : '') + '</div>' : '';
  }
  function miniStats(v, p) {
    v = conRespaldo(v, p);
    if (!v || !v.stats) return '';
    if ((v.fase === 'in' || v.fase === 'post') && statsHueco(v, p)) return AVISO_SIN_STATS;
    const q = [['totalShots', 'Tiros'], ['shotsOnTarget', 'A puerta'], ['wonCorners', 'Córners']].filter(([k]) => v.stats[k]);
    if (!q.length && !v.stats.possessionPct) return '';
    return '<div class="mini" style="' + varsColor(v) + '">' + posesion(v) + q.map(([k, n]) => filaStat(n, v.stats[k].v[0], v.stats[k].v[1], true)).join('') + '</div>';
  }
  const SECCIONES_FUT = [
    ['Lo principal', [['totalShots', 'Tiros totales'], ['shotsOnTarget', 'Tiros a puerta'], ['wonCorners', 'Córners'], ['saves', 'Paradas del portero']]],
    ['Ataque y pases', [['accuratePasses', 'Pases buenos'], ['totalPasses', 'Pases'], ['totalCrosses', 'Centros'], ['offsides', 'Fueras de lugar']]],
    ['Disciplina', [['foulsCommitted', 'Faltas'], ['yellowCards', 'Amarillas'], ['redCards', 'Rojas']]],
  ];
  function estadisticas(p, v) {
    if ((v.fase === 'in' || v.fase === 'post') && statsHueco(v, p)) return AVISO_SIN_STATS;
    let h = posesion(v);
    if (p.deporte === 'Fútbol') {
      for (const [tit, filas] of SECCIONES_FUT) {
        const f = filas.filter(([k]) => v.stats[k]);
        if (!f.length) continue;
        h += '<div class="seccion"><div class="sec-tit">' + tit + '</div>' + f.map(([k, n]) => filaStat(n, v.stats[k].v[0], v.stats[k].v[1])).join('') + '</div>';
      }
    } else {
      h += '<div class="seccion">' + Object.keys(v.stats).slice(0, 10).map((k) =>
        filaStat(TRAD[v.stats[k].label] || v.stats[k].label, v.stats[k].v[0], v.stats[k].v[1])).join('') + '</div>';
    }
    return h;
  }
  // v379 — UNA TARJETA POR PARTIDO. El usuario: «que no haya partidos
  // repetidos, ni de tenis ni de fútbol ni de ningún deporte». Antes iba una
  // tarjeta por apuesta: un partido con dos apuestas salía dos veces. Ahora
  // el partido sale una vez y sus apuestas van dentro (la mejor primero); si
  // la misma apuesta llegara dos veces, se queda una.
  // los dos nombres en cualquier orden («A vs B» y «B vs A» son el mismo partido)
  const clavePartido = (p) => [p.deporte || '', lados(p).map((x) => x.toLowerCase().trim()).sort().join(' / '), diaDe(p)].join('|');
  function agrupar(lista) {
    const g = new Map();
    for (const p of lista) {
      const k = clavePartido(p);
      if (!g.has(k)) g.set(k, []);
      const ya = g.get(k);
      if (!ya.some((x) => String(x.apuesta).trim() === String(p.apuesta).trim())) ya.push(p);
    }
    for (const ps of g.values()) ps.sort((a, b) => (b.elige - a.elige) || ((b.prob || 0) - (a.prob || 0)));
    return [...g.values()];
  }
  // v430 — «que cada pick tenga su verde o rojo en cuanto acaba el partido».
  // Lo oficial lo pone el servidor al liquidar (cada 1-2 h); mientras, la página
  // lo califica con el marcador en vivo (ESPN / Flashscore) en cuanto se decide
  // (un «Más de» ya cumplido, un «Menos de» ya pasado o el partido terminado).
  // Los marcadores del día siguen contando sólo lo oficial.
  function estadoVisto(p, v) {
    if (['verde', 'roja', 'nula'].includes(p.estado)) return p.estado;
    const pr = progreso(p, v || vivoDe([p]));
    return pr && (pr.e === 'verde' || pr.e === 'roja') ? pr.e : p.estado;
  }
  function estadoPick(p, v) {
    const e = estadoVisto(p, v);
    if (e !== p.estado) return e === 'verde' ? '<span class="et verde" title="Al pitazo; el servidor lo confirma">' + OK() + ' Verde</span>' : '<span class="et roja" title="Al pitazo; el servidor lo confirma">' + MAL() + ' Roja</span>';
    if (p.estado === 'verde') return '<span class="et verde">' + OK() + ' Verde</span>';
    if (p.estado === 'roja') return '<span class="et roja">' + MAL() + ' Roja</span>';
    if (p.estado === 'nula') return '<span class="et">Nula</span>';
    return '';
  }
  // v391 — lo que la IA opina de ESTE pick (sólo si está en contra se avisa en la fila)
  function iaDelPick(p) {
    const a = window.SPX && SPX.yo.ia ? SPX.yo.ia[p.partido] : null;
    const v = a && (a.veredictos || []).find((x) => String(x.apuesta).trim() === String((SPX.yo.desbloqueados || {})[p.id] || p.apuesta).trim());
    return v && v.opinion === 'en_contra' ? '<div class="ia-aviso">🤖 La IA lo ve en contra: ' + esc(v.motivo) + '</div>' : '';
  }
  // v453 — EL DATO REAL de cada pick terminado (sale del marcador final): «Quedó 2-1 ·
  // 3 goles (línea 2.5)». En córners y tarjetas sólo el marcador (no se guardan por pick).
  function realDe(p) {
    if (!p || !p.marcador || !['verde', 'roja'].includes(p.estado)) return '';
    const g = String(p.marcador).split('-').map((x) => Number(String(x).trim()));
    if (g.length !== 2 || g.some((x) => Number.isNaN(x))) return '';
    const V = lados(p)[1], a = String((window.SPX && SPX.yo.desbloqueados[p.id]) || p.apuesta || '');
    const U = { NBA: 'puntos', NFL: 'puntos', MLB: 'carreras', KBO: 'carreras', 'Béisbol': 'carreras', Tenis: 'sets' }[p.deporte] || 'goles';
    let m, t = 'Quedó ' + g[0] + '-' + g[1];
    if ((m = a.match(/^(Goles|Puntos|Carreras|Sets): (Más|Menos) de ([\d.]+)/))) t += ' · ' + (g[0] + g[1]) + ' ' + U + ' (línea ' + m[3] + ')';
    else if ((m = a.match(/^Goles (.+): (Más|Menos) de ([\d.]+)/))) t += ' · ' + m[1] + ': ' + (m[1] === V ? g[1] : g[0]) + ' (línea ' + m[3] + ')';
    return t;
  }
  function filaPick(p, v, varias) {
    if (p.solo_analisis) {
      return '<div class="pick-fila analisis"><small class="tenue">📊 Sin pick sugerido' +
        (p.apuesta ? ' · ' + (p.fuente === 'casa' ? 'la casa ve' : 'el modelo ve') + ' <b>' + esc(p.apuesta) + '</b>' + (p.prob ? ' (' + pct(p.prob) + ')' : '') : '') + '</small></div>';
    }
    const pr = progreso(p, v);
    const nv = nivel(p);
    const ev = estadoVisto(p, v);
    // v530 — el usuario: «la tarjeta está muy larga… que se muestre muy bien lo que se tiene que mostrar, pero quita
    // mucho espacio». Dos renglones por pick: nivel + apuesta + estado; y cuota · probabilidad · grado, cómo va y Seguir.
    const prog = pr ? '<span class="progreso pk-prog ' + pr.e + '">' + esc(pr.t) + '</span>'
      : realDe(p) ? '<span class="progreso pk-prog ' + p.estado + '">' + esc(realDe(p)) + '</span>' : '';
    return '<div class="pick-fila compacta ' + (ev === 'verde' ? 'verde' : ev === 'roja' ? 'roja' : '') + '">' +
      '<div class="pk-top"><span class="et nivel ' + nv.c + '">' + nv.i + ' ' + nv.n + '</span>' +
      '<div class="apuesta">' + (window.SPX ? SPX.apuesta(p) : esc(p.apuesta)) + '</div>' + estadoPick(p, v) + '</div>' +
      '<div class="pk-meta"><span class="pk-dato"><small>cuota</small><b>' + (p.cuota ? Number(p.cuota).toFixed(2) : '—') + '</b></span>' +
      '<span class="pk-dato"><small>prob.</small><b>' + pct(p.prob) + '</b></span>' +
      '<span class="pk-dato"><small>' + (p.tipo === 'error' ? 'paga de más' : 'nivel') + '</small><b>' +
      (p.tipo === 'error' ? '+' + Math.round(100 * (p.ventaja || 0)) + ' %' : grado(p)) + '</b></span>' +
      (window.SPX ? SPX.extra(p) : '') + '</div>' + prog + iaDelPick(p) +
      (p.tipo === 'error' && p.porque ? '<div class="porque">' + esc(p.porque) + ' · riesgo alto: apuesta poco</div>' : '') + '</div>';
  }
  // ---------- v396: COMBINADAS ----------
  const ICONO_DEP = new Proxy({}, { get: (_, d) => icoDep(d) });   // v455 — íconos en vez de emojis
  const porId = () => { if (!estado._porId || estado._porIdN !== estado.picks.length) { estado._porId = new Map(estado.picks.map((p) => [p.id, p])); estado._porIdN = estado.picks.length; } return estado._porId; };
  function faseCombinada(c) {
    if (c.estado === 'verde' || c.estado === 'roja' || c.estado === 'nula') return 'terminado';
    const empezo = (c.patas || []).some((x) => { const d = aFecha(x.inicio); return d && d <= new Date(); });
    return empezo ? 'vivo' : 'proximo';
  }
  function tarjetaCombinada(c) {
    const m = porId();
    const patas = (c.patas || []).map((x) => {
      const p = m.get(x.id) || x;
      const ev = m.get(x.id) ? estadoVisto(p) : p.estado;          // v430 — al pitazo
      const e = ev === 'verde' ? '✅' : ev === 'roja' ? '❌' : ev === 'nula' ? '➖' : '⏳';
      const txt = window.SPX && m.get(x.id) ? SPX.apuesta(p) : esc(x.apuesta);
      // v491 — si la pata no está en la lista (retirada), igual abre la ficha de su partido (otro pick o su análisis)
      const kp = !m.get(x.id) && x.partido ? clavePartido(x) : null;
      const alt = kp ? estado.picks.concat(estado.analisis || []).find((q) => clavePartido(q) === kp) : null, ir = alt ? alt.id : null;
      return '<div class="comb-pata"' + (m.get(x.id) || ir ? ' data-ficha="' + esc(m.get(x.id) ? x.id : ir) + '" role="button" tabindex="0"' : '') + '><span>' + e + '</span><div><b>' + txt + '</b><small>' + (ICONO_DEP[x.deporte] || '') + ' ' + esc(x.partido || '') +
        ' · ' + Number(x.cuota || 0).toFixed(2) + ' · ' + pct(x.prob) + (x.ia === 'a_favor' ? ' · 🤖 a favor' : '') + '</small></div>' +
        (m.get(x.id) || ir ? '<i class="comb-ir">›</i>' : '') + '</div>';
    }).join('');
    const evs = (c.patas || []).map((x) => (m.get(x.id) ? estadoVisto(m.get(x.id)) : x.estado));
    const ce = c.estado !== 'pendiente' && c.estado !== 'vivo' ? c.estado
      : evs.includes('roja') ? 'roja' : evs.length && evs.every((e) => e === 'verde' || e === 'nula') && evs.includes('verde') ? 'verde' : c.estado;
    c = Object.assign({}, c, { estado: ce });
    const est = c.estado === 'verde' ? '<span class="et verde">' + OK() + ' Verde</span>' : c.estado === 'roja' ? '<span class="et roja">' + MAL() + ' Roja</span>'
      : faseCombinada(c) === 'vivo' ? '<span class="et vivo"><i class="punto"></i>En juego</span>' : '<span class="et">⏳ ' + esc(horaCdmx(aFecha(c.inicio))) + '</span>';
    return '<div class="dest comb ' + (c.estado === 'verde' ? 'verde' : c.estado === 'roja' ? 'roja' : '') + '">' +
      '<div class="fila"><span class="et nivel">' + (c.alcance === 'IA' ? ico('sparkles', 'acento') : ICONO_DEP[c.alcance] || ico('link-2')) + ' ' + esc(c.alcance === 'IA' ? 'IA + modelo' : c.alcance) + (c.tipo === 'alta' ? ' · 3 patas' : '') + '</span>' + est + '</div>' +
      patas + '<div class="dest-pie"><b>' + Number(c.cuota || 0).toFixed(2) + '</b><span>probabilidad ' + pct(c.prob) + '</span></div>' +
      (window.SPX && SPX.extraComb ? SPX.extraComb(c) : '') + '</div>';
  }
  // v421 — «actualiza el historial de las combinadas con la mejora, desde la misma
  // fecha que las demás». Las de 2 patas hasta el 21-oct son la SIMULACIÓN del
  // método nuevo (v420) con esos partidos reales (`combinadas_simuladas.json`);
  // desde el 22-oct, las publicadas. Las de 3 patas, todas reales.
  const DESDE_NUEVO = '2026-10-22';
  // v528 — las de 3 patas, con la regla nueva (💎/🔷 por acierto real por banda de cuota, 1,30-2,60): del 15 al 29-oct
  // rehechas sobre esos partidos reales (`combinadas_simuladas.json` → «tres»); desde el 30, las publicadas
  const DESDE_TRES = '2026-10-30';
  function histCombinadas() {
    const sim = (estado.combSim && estado.combSim.combinadas) || [];
    const tres = (estado.combSim && estado.combSim.tres) || null;
    const t = (estado.combinadas || []).filter((c) => (c.estado === 'verde' || c.estado === 'roja') &&
        (c.tipo === 'alta' ? !tres || c.fecha >= DESDE_TRES : c.fecha >= DESDE_NUEVO))
      .concat(sim.filter((c) => c.estado === 'verde' || c.estado === 'roja'))
      .concat(tres ? tres.combinadas : []);
    if (!t.length) return '<p class="tenue">Aún no termina ninguna combinada. Aquí se van a ver sus verdes y rojas, sin quitar nada.</p>';
    const fila = (titulo, xs) => { const v = xs.filter((c) => c.estado === 'verde').length, r = xs.length - v;
      return '<div class="ia-fila"><span>' + titulo + '</span><b>✅ ' + v + ' ❌ ' + r + '</b><small>' + (xs.length ? pct(v / xs.length) : '—') + '</small></div>'; };
    return fila('🔗 Combinadas (2 patas)', t.filter((c) => c.tipo !== 'alta' && c.alcance !== 'IA')) + fila('🔗 Combinadas (3 patas)', t.filter((c) => c.tipo === 'alta' && c.alcance !== 'IA')) +
      fila('✨ IA + modelo (3 patas)', t.filter((c) => c.alcance === 'IA')) +
      fila('🔀 Mixtas', t.filter((c) => c.alcance === 'Mixta')) +
      (sim.length ? '<p class="tenue chico">Las de 2 patas del ' + esc(estado.combSim.desde.slice(8)) + ' al ' + esc(estado.combSim.hasta.slice(8)) +
        ' de oct. y las de 3 patas hasta el 29 son el método nuevo con esos partidos reales; después, las publicadas.</p>' : '');
  }
  function tarjeta(ps) {
    const p = ps[0];
    const v = vivoDe(ps);
    const nv = nivel(p);
    const [L, V] = lados(p);
    const marc = v && v.fase !== 'pre' ? v.g[0] + ' - ' + v.g[1] : (p.marcador || '');
    const est = ps.map((x) => estadoVisto(x, v));
    const todas = est.every((e) => e === 'verde' || e === 'roja' || e === 'nula');
    const clase = ['tarjeta', nv.c, todas && est.every((e) => e !== 'roja') ? 'verde' : '', todas && est.every((e) => e === 'roja') ? 'roja' : ''].join(' ');
    const cab = todas && !(v && v.fase === 'in') ? '<span class="et">Terminado</span>' : etiquetaEstado(dict(p, { estado: 'pendiente' }), v);
    return '<article class="' + clase + '" data-id="' + esc(p.id) + '">' +
      '<div class="fila"><div class="etiquetas"><span class="et nivel ' + nv.c + '">' + nv.i + ' ' + nv.n + '</span>' +
      '<span class="et">' + esc(p.deporte || '') + '</span>' + (ps.length > 1 ? '<span class="et">' + ps.length + ' apuestas</span>' : '') + '</div>' + cab + '</div>' +
      '<div class="equipos"><div class="eq">' + escudo(p.logo_h, L, p.deporte) + '<span>' + esc(L) + '</span></div>' +
      '<div class="marc">' + (marc ? esc(marc) : 'vs') + '</div>' +
      '<div class="eq der"><span>' + esc(V) + '</span>' + escudo(p.logo_a, V, p.deporte) + '</div></div>' +
      '<div class="liga">' + esc(p.liga || '') + ' · ' + esc(horaCdmx(aFecha(p.inicio))) + '</div>' +
      contextoHtml((ps.find((x) => x.ctx) || {}).ctx, L, V, p.liga) +
      iaBloque(p, L, V, conVip(ps).ctx, conVip(ps).jug, ps.some((x) => x.vip_hay)) +
      // v517 — «la tarjeta principal ya se hizo larga»: a la vista la cancha y el Pulso; las estadísticas, plegadas
      penalesHtml(v, L, V) + (v && (v.fase === 'in' || v.fase === 'post') ? cancha(v, p) : '') + pulsoChip(p, v) +   // v460: también al terminar
      seccionStats(compensacion(p, v) + miniStats(v, p)) +
      ps.map((x) => filaPick(x, v, ps.length > 1)).join('') +
      (ps.some((x) => x.espn) ? '<button class="ver" data-ficha="' + esc((ps.find((x) => x.espn) || p).id) + '">Ver partido →</button>' : '') +
      '</article>';
  }
  // v513 — en la tarjeta en vivo, el Pulso gratis: «otro gol» en su tramo medido (lo demás, en «Ver partido»)
  function pulsoChip(p, v) {
    if (!window.PULSO || !v || v.fase !== 'in' || (p.deporte && p.deporte !== 'Fútbol')) return '';
    if (PULSO.enPrimerTiempo(v)) return '<div class="pulso-chip espera">' + ico('activity', 'acento') + ' Pulso · se abre en el 2.º tiempo</div>';
    const ms = PULSO.mercados(p, v, conRespaldo(v, p));
    const m = PULSO.mejor(ms, pulsoAbierto(p)) || ms.find((x) => x.k === 'gol' && x.tramo);
    if (!m || !m.tramo) return '';
    const t = m.tramo, [L, V] = lados(p);
    return '<div class="pulso-chip ' + (m.p >= 0.7 ? 'alta' : m.p >= 0.6 ? 'media' : 'baja') + '" title="Pulso SharPicks: lo medido en el historial">' +
      ico('activity', 'acento') + ' Pulso · ' + esc(PULSO.nombre(m.k, L, V).toLowerCase()) + ' <b>' + Math.round(100 * t.desde) + '-' + Math.round(100 * t.hasta) + '%</b> <small>salió ' + Math.round(100 * t.fue) + '%</small></div>';
  }
  // v517 — «CANDIDATOS PULSO» arriba de En vivo: los partidos donde lo medido dice que hay algo bueno que meter
  // ahora (lo más probable que aún paga, 70 %+). Se tocan y abren «Ver partido».
  function candidatosPulso(grupos) {
    if (!window.PULSO || !PULSO.listo()) return '';
    const c = [];
    for (const g of grupos) {
      const p = g.find((x) => x.espn) || g[0], v = vivoDe(g);
      if (!v || v.fase !== 'in' || (p.deporte && p.deporte !== 'Fútbol')) continue;
      const m = PULSO.mejor(PULSO.mercados(p, v, conRespaldo(v, p)), pulsoAbierto(p));
      if (m && m.p >= 0.7 && m.tramo) c.push({ p, v, m });
    }
    if (!c.length) return '';
    c.sort((a, b) => b.m.p - a.m.p);
    return '<div class="pulso-cand"><div class="pc-tit">' + ico('target') + ' Candidatos Pulso<small>lo más probable ahora</small></div>' + c.slice(0, 4).map(({ p, v, m }) => {
      const [L, V] = lados(p), abierto = pulsoAbierto(p), t = m.tramo;
      return '<button class="pc-fila" data-ficha="' + esc(p.id) + '"><span class="pc-min">' + esc(String(v.reloj || '')) + '</span>' +
        '<span class="pc-par">' + esc(L) + ' ' + v.g[0] + '-' + v.g[1] + ' ' + esc(V) + '<small>' + esc(PULSO.nombre(m.k, L, V)) + ' · salió ' + Math.round(100 * t.fue) + '%' +
        (iaPulso(p, v).hay || iaPulso(p, v).rec ? ' · <span class="pc-ia">' + ico('sparkles', 'acento') + ' IA</span>' : '') + '</small></span>' +
        '<span class="pc-p">' + (abierto ? Math.round(100 * m.p) + '%' : Math.round(100 * t.desde) + '-' + Math.round(100 * t.hasta) + '%') + '</span></button>';
    }).join('') + '</div>';
  }
  // v517 — las estadísticas en vivo de la tarjeta, en su pestaña (como «Antes del partido»)
  function seccionStats(html) {
    return html ? '<details class="ctx"><summary>' + ico('chart-column') + ' Estadísticas en vivo</summary>' + html + '</details>' : '';
  }
  const dict = (a, b) => Object.assign({}, a, b);
  // v384 — «un H2H en las tarjetas por si la gente quiere analizar el partido»
  // v387 — el análisis y la predicción de la IA (Gemini), medida aparte
  const pp = (x) => (x == null ? '' : ' <span class="ia-prob">(' + Math.round(100 * x) + ' %)</span>');
  // v417 — quien no es VIP VE que el partido tiene análisis de la IA, pero
  // bloqueado: al tocarlo va a Planes, al VIP. Sólo se enseña si de verdad hay
  // análisis (`ia_disponibles`: nombre del partido, nunca el contenido).
  // v469 — QUIÉN PUEDE ANOTAR Y TIRAR A PUERTA (dentro del análisis IA, como pidió el usuario).
  // Nuestro modelo con la base de FotMob, medido en 121 mil jugador-partido y calibrado: «anota»,
  // «1+» y «2+» a puerta ganan a la media de su posición en las dos mitades (p5>0). Ya cuentan
  // que el jugador puede no salir. El 3+ no ganó: no se enseña.
  function jugadoresHtml(jug, L, V) {
    if (!jug || !((jug.h || []).length || (jug.a || []).length)) return '';
    const pc = (x) => Math.round(100 * (x || 0)) + '%';
    // en el teléfono no caben nombres largos: «Lamine Yamal» → «L. Yamal»
    const corto = (n) => { const w = String(n || '').trim().split(/\s+/); return n.length > 11 && w.length > 1 ? w[0][0] + '. ' + w.slice(1).join(' ') : n; };
    const eq = (n, xs) => !(xs || []).length ? '' : '<div class="jug-eq"><div class="jug-nom">' + esc(n) + '</div>' +
      xs.map((j) => '<div class="jug-fila"><span class="jug-n" title="' + esc(j.n) + '">' + esc(corto(j.n)) + '</span><b>' + pc(j.gol) + '</b><b>' + pc(j.p1) + '</b><b>' + pc(j.p2) + '</b></div>').join('') + '</div>';
    return '<div class="ia-jug"><div class="jug-cab"><span>' + ico('ball-football') + ' Jugadores</span><small>Anota</small><small>A puerta 1+</small><small>2+</small></div>' +
      eq(L, jug.h) + eq(V, jug.a) + '</div>';
  }
  // v470 — LÍNEAS POR ESTADÍSTICA (el usuario: «si un equipo promedia 7 córners, que me diga córners de
  // ese equipo +5, +4, +6…»). Salen de los mismos promedios de «Antes del partido» con el rival, y la
  // probabilidad está medida y calibrada (exportar_web → lineas_stats). ctx.lin = {stat: {h, a, t}}.
  // (sólo las que ganaron a la media de la liga: las amarillas, los goles totales y los córners totales no)
  const LIN_NOM = { goles: 'Goles', corners: 'Córners', tiros: 'Tiros', tiros_puerta: 'Tiros a puerta' };
  function lineasHtml(ctx, L, V) {
    const lin = ctx && ctx.lin;
    if (!lin) return '';
    const fila = (n, xs) => !(xs || []).length ? '' : '<div class="lin-fila"><span class="lin-n">' + esc(n) + '</span><span class="lin-chips">' +
      xs.map(([t, l, p, cu]) => '<span class="lin-x">' + (t === 'mas' ? 'Más ' : 'Menos ') + l + ' <b>' + Math.round(100 * p) + '%</b>' +
        (cu ? '<i>' + Number(cu).toFixed(2) + '</i>' : '') + '</span>').join('') + '</span></div>';
    const html = Object.keys(LIN_NOM).filter((k) => lin[k]).map((k) =>
      '<div class="lin-st"><div class="lin-tit">' + LIN_NOM[k] + '</div>' + fila(L, lin[k].h) + fila(V, lin[k].a) + fila('Total', lin[k].t) + '</div>').join('');
    // v474 — sincronizado con lo que se puede meter: con Playdoit, sólo SUS líneas (y su cuota)
    // v475 — también dice que el favorito (el precio de la casa) ya está metido
    // v476 — medido: en las líneas de la casa, su probabilidad (sin margen) es la más certera
    return html ? html + '<p class="tenue chico">' + (lin.casa ? 'Las líneas que ofrece Playdoit, con su cuota y su probabilidad sin margen (medido: es la más certera). '
      : 'Playdoit no cotiza estas estadísticas en este partido: líneas de referencia de nuestro modelo (promedios, rival y favorito). ') +
      'Información, no un pick.</p>' : '';
  }
  // v472 — «ARMA TU PARLEY DE ESTE PARTIDO»: con las líneas que Playdoit SÍ ofrece, la más alta de cada
  // estadística con nuestra probabilidad >= 75 %. Las patas del mismo partido van juntas: el producto se
  // queda corto y se corrige con lo medido (2 patas ×1,04 · 3 ×1,067 · 4 ×1,13; 29.571 partidos).
  const PAR_CORR = { 2: 1.02, 3: 1.067, 4: 1.13 };   // v476 — con la prob. de la casa (2 patas: 1.041 parleys)
  // v474 — el usuario: «¿dónde está el botón para que la IA arme el parley?». Siempre sale el botón; el
  // pozo son las líneas de Playdoit (la más alta de cada estadística con >= 75 %, o >= 60 %).
  estado.parley = estado.parley || {};
  function parleyHtml(ctx, L, V) {
    const lin = ctx && ctx.lin;
    if (!lin) return '';
    const k = L + '|' + V, n = estado.parley[k];
    if (!lin.casa) return '<p class="tenue">Playdoit no tiene este partido en su catálogo ahorita: no hay líneas que se puedan meter.</p>';
    const par = lin.par || [];
    if (!n) return '<button class="vip-btn par-ir" data-par-k="' + esc(k) + '" data-par-n="3">' + ico('target') + ' Armar parley</button>';
    const chips = '<div class="par-chips">' + [2, 3, 4].map((x) => '<button class="chip' + (x === n ? ' activa' : '') + '" data-par-k="' + esc(k) + '" data-par-n="' + x + '">' + x + ' patas</button>').join('') + '</div>';
    if (par.length < 2) return chips + '<p class="aviso">Playdoit no ofrece líneas con buena probabilidad para armar un parley en este partido.</p>';
    return chips + parleyDe(par, Math.min(n, par.length), L, V) + (par.length < n ? '<p class="tenue chico">Sólo hay ' + par.length + ' líneas de la casa que valgan.</p>' : '') +
      '<p class="tenue chico">Líneas y cuotas de Playdoit. En combinadas del mismo partido la casa puede ajustar la cuota.</p>';
  }
  function parleyDe(par, n, L, V) {
    const nom = (lado) => (lado === 'h' ? L : lado === 'a' ? V : 'Total');
    // v477 — también los mercados principales de la casa (doble oportunidad, goles del partido, ambos anotan)
    const patTxt = (st, lado, lin) => st === 'doble' ? 'Doble oportunidad: <b>' + esc({ '1X': L + ' o empate', X2: V + ' o empate', 12: L + ' o ' + V }[lado] || lado) + '</b>'
      : st === 'goles_total' ? 'Goles del partido: <b>' + (lado === 'mas' ? 'más de ' : 'menos de ') + lin + '</b>'
        : st === 'btts' ? 'Ambos anotan: <b>' + (lado === 'si' ? 'sí' : 'no') + '</b>'
          : esc(LIN_NOM[st] || st) + ' ' + esc(nom(lado)) + ': <b>más de ' + lin + '</b>';
    const una = (n) => {
      const ps = par.slice(0, n), prod = ps.reduce((x, y) => x * y[3], 1), cuota = ps.reduce((x, y) => x * y[4], 1);
      const prob = Math.min(Math.min(...ps.map((x) => x[3])), prod * (PAR_CORR[n] || 1));
      return '<div class="par-caja"><div class="par-cab"><b>' + n + ' patas</b><span>se cumplen todas ~<b>' + Math.round(100 * prob) + '%</b> · cuota ~' + cuota.toFixed(2) + '</span></div>' +
        ps.map(([st, lado, lin, pr, cu]) => '<div class="par-pata"><span>' + patTxt(st, lado, lin) + '</span>' +
          '<span class="par-n"><b>' + Math.round(100 * pr) + '%</b><small>' + Number(cu).toFixed(2) + '</small></span></div>').join('') + '</div>';
    };
    return una(n);
  }
  // v482 — los jugadores y las líneas ya no vienen en lo público (se veían con las herramientas del
  // navegador): al VIP se los da la base (`picks_vip`, es_pro()); a los demás sólo `vip_hay` para el 🔒
  function conVip(ps) {
    const p = ps[0], ctx = (ps.find((x) => x.ctx) || {}).ctx;
    const v = window.SPX && SPX.yo.vip ? SPX.yo.vip[p.fecha + '|' + p.partido] : null;
    return { ctx: v && v.lin ? Object.assign({}, ctx, { lin: v.lin }) : ctx, jug: (v && v.jug) || (ps.find((x) => x.jug) || {}).jug };
  }
  function iaBloque(p, L, V, ctx, jug, vipHay) {
    const a = window.SPX && SPX.yo.ia ? SPX.yo.ia[p.partido] : null;
    const vip = window.SPX && SPX.esVip && SPX.esVip();
    if (a) return iaHtml(a, L, V, ctx, jug);
    // VIP y aún sin análisis de la IA: el apartado sale igual, con los jugadores
    if (vip && (jugadoresHtml(jug, L, V) || lineasHtml(ctx, L, V))) return '<details class="ctx ia"><summary>🤖 Análisis IA</summary>' +
      sub('Jugadores', jugadoresHtml(jug, L, V)) + sub('Líneas por estadística', lineasHtml(ctx, L, V)) + sub('Arma tu parley de este partido', parleyHtml(ctx, L, V)) + '</details>';
    const hay = (window.SPX && SPX.yo.iaHay && SPX.yo.iaHay.has(p.partido)) || !!vipHay || !!jugadoresHtml(jug, L, V) || !!lineasHtml(ctx, L, V);
    if (!hay || vip) return '';
    return '<button class="ctx ia ia-bloq" data-vista-ir="planes" data-foco="plan-vip">🤖 Análisis IA <span class="candado">🔒 VIP</span></button>';
  }
  // v448 — PRIMER GOL Y PA1 (pago anticipado: el equipo llega a ir ganando por un gol)
  // con los goles esperados de cada equipo: los goles caen como Poisson y cada uno es
  // de un equipo según su parte. Medido en 237 partidos con el orden real de goles
  // (ESPN): los dos informan (p5>0); el favorito sale algo MÁS de lo que dice.
  const memoPa1 = new Map();
  function primerYPa1(lh, la) {
    const clave = lh + '|' + la;
    if (memoPa1.has(clave)) return memoPa1.get(clave);
    const L = Math.max(0.05, Number(lh) + Number(la)), p0 = Math.exp(-L), q = Number(la) / L;
    const algunaVez = (qq) => {
      let tot = 0, pn = p0;
      for (let n = 1; n < 20; n++) {
        pn *= L / n;
        let f = new Map([[0, 1]]), toco = 0;
        for (let i = 0; i < n; i++) {
          const g = new Map();
          f.forEach((pr, st) => { [[1, qq], [-1, 1 - qq]].forEach(([d, pd]) => { const t = st + d; if (t >= 1) toco += pr * pd; else g.set(t, (g.get(t) || 0) + pr * pd); }); });
          f = g;
        }
        tot += pn * toco;
      }
      return tot;
    };
    const r = { h: (1 - q) * (1 - p0), a: q * (1 - p0), nadie: p0, pa1h: algunaVez(1 - q), pa1a: algunaVez(q) };
    memoPa1.set(clave, r);
    return r;
  }
  function pa1Html(lh, la, L, V) {
    const r = primerYPa1(lh, la), pc = (x) => Math.round(100 * x) + ' %';
    const fila = (n, x) => '<span><em>' + esc(n) + '</em><b>' + pc(x) + '</b></span>';
    return '<div class="ia-pa1"><div><small>🥇 Anota primero</small>' + fila(L, r.h) + fila(V, r.a) + '</div>' +
      '<div><small title="Pago anticipado: llega a ir ganando por un gol">🏁 PA1</small>' + fila(L, r.pa1h) + fila(V, r.pa1a) + '</div></div>';
  }
  function iaHtml(a, L, V, ctx, jug) {
    if (!a) return '';
    const res = { local: 'gana ' + L, empate: 'empate', visita: 'gana ' + V }[a.pred_resultado] || '';
    // v407 — el mismo template para todos los deportes, con su unidad
    const dep = a.deporte || 'Fútbol', fut = dep === 'Fútbol';
    const U = { 'Fútbol': 'goles', NHL: 'goles', NBA: 'puntos', NFL: 'puntos', MLB: 'carreras', KBO: 'carreras', Tenis: 'sets' }[dep] || 'puntos';
    const lin = (x) => (x > 0 ? '+' : '') + x;
    const hand = a.linea_handicap == null || !a.pred_handicap ? null
      : (a.pred_handicap === 'local' ? L + ' ' + lin(a.linea_handicap) : V + ' ' + lin(-a.linea_handicap));
    const est = a.evaluado ? (a.ok_resultado ? ' · <b class="txt-verde">✅ acertó</b>' : ' · <b class="txt-rojo">❌ falló</b>') : '';
    return '<details class="ctx ia"><summary>🤖 Análisis IA' + est + '</summary>' +
      '<p class="ia-txt">' + esc(a.analisis || '') + '</p>' +
      '<div class="ia-pred">La IA ve: <b>' + esc(res) + '</b> · ' + L.slice(0, 14) + ' ' + Math.round(100 * (a.p_local || 0)) + ' %' +
      (a.p_empate ? ' · empate ' + Math.round(100 * a.p_empate) + ' %' : '') + ' · ' + V.slice(0, 14) + ' ' + Math.round(100 * (a.p_visita || 0)) + ' %</div>' +
      '<div class="ia-pred">' + (fut && a.pred_goles ? 'Goles: <b>' + (a.pred_goles === 'mas' ? 'más de 2.5' : 'menos de 2.5') + '</b>' + pp(a.prob_goles) + ' · ' : '') +
      'confianza ' + '★'.repeat(a.confianza || 0) + '☆'.repeat(5 - (a.confianza || 0)) + '</div>' +
      // v470 — lo principal a la vista; lo demás en pestañas que se abren
      // v533 — si la IA la rehízo ~2 h antes (con noticias frescas), se enseña ésa: acertó +20 pts (barrido 29-oct)
      (a.mejor_2h ? '<div class="ia-meter">🧠 Lo que metería la IA: <b>' + esc(a.mejor_2h) + '</b>' +
        (a.prob_mejor_2h != null ? ' · ' + Math.round(100 * a.prob_mejor_2h) + ' %' : '') + ' <small>(2 h antes)</small></div>'
      : a.mejor_apuesta ? '<div class="ia-meter">🧠 Lo que metería la IA: <b>' + esc(a.mejor_apuesta) + '</b>' +
        (a.prob_mejor_apuesta != null ? ' · ' + Math.round(100 * a.prob_mejor_apuesta) + ' %' : '') + '</div>' : '') +
      // v392 — más precisa: marcador, goles esperados, ambos anotan, córners, tarjetas (con ✅/❌ al terminar)
      sub('Predicciones', '<div class="ia-grid">' + [
        // v396 — con la probabilidad que le da la IA a cada predicción
        a.marcador_ia ? ['⚽ Marcador', a.marcador_ia, a.ok_marcador, a.prob_marcador] : null,
        a.goles_esperados != null ? ['🥅 Goles esperados', String(a.goles_esperados), null, null] : null,
        // v407 — el total y el hándicap, en todos los deportes
        a.linea_total != null && a.pred_total ? ['📊 Total de ' + U, (a.pred_total === 'mas' ? 'Más' : 'Menos') + ' de ' + a.linea_total +
          (a.total_esperado != null ? ' (~' + a.total_esperado + ')' : ''), a.ok_total, a.prob_total] : null,
        hand ? ['⚖️ Hándicap', hand, a.ok_handicap, a.prob_handicap] : null,
        a.btts ? ['🎯 Ambos anotan', a.btts === 'si' ? 'Sí' : 'No', a.ok_btts, a.prob_ambos == null ? null : (a.btts === 'si' ? a.prob_ambos : 1 - a.prob_ambos)] : null,
        a.linea_corners != null ? ['🚩 Córners', (a.pred_corners === 'mas' ? 'Más' : 'Menos') + ' de ' + a.linea_corners + (a.corners_esperados != null ? ' (~' + a.corners_esperados + ')' : ''), a.ok_corners, a.prob_corners] : null,
        a.linea_tarjetas != null ? ['🟨 Tarjetas', (a.pred_tarjetas === 'mas' ? 'Más' : 'Menos') + ' de ' + a.linea_tarjetas + (a.tarjetas_esperadas != null ? ' (~' + a.tarjetas_esperadas + ')' : ''), a.ok_tarjetas, a.prob_tarjetas] : null,
      ].filter(Boolean).map(([t, v, ok, pr]) => '<div><small>' + t + '</small><b>' + esc(v) + (ok === true ? ' ✅' : ok === false ? ' ❌' : '') + '</b>' +
        (pr != null ? '<span class="ia-prob">probabilidad ' + Math.round(100 * pr) + ' %</span>' : '') + '</div>').join('') + '</div>' +
        // v394 — los goles de cada equipo
        (a.goles_local_esperados != null && a.goles_visita_esperados != null
          ? filaStat(U.charAt(0).toUpperCase() + U.slice(1) + ' esperados', a.goles_local_esperados, a.goles_visita_esperados, true) : '')) +
      // v468 — el bloque de promedios de la IA se quitó: eran los MISMOS de «Antes del partido» (redundante)
      // v448 — primer gol y PA1 de cada equipo (sólo fútbol: es lo que se midió)
      (fut && a.goles_local_esperados != null && a.goles_visita_esperados != null ? sub('Primer gol y PA1', pa1Html(a.goles_local_esperados, a.goles_visita_esperados, L, V)) : '') +
      (fut ? sub('Jugadores', jugadoresHtml(jug, L, V)) : '') +
      (fut ? sub('Líneas por estadística', lineasHtml(ctx, L, V)) : '') +
      (fut ? sub('Arma tu parley de este partido', parleyHtml(ctx, L, V)) : '') +
      sub('Nuestros picks según la IA',
        (a.pick_ia && a.pick_ia !== 'ninguno' ? '<div class="ia-pred">Su pick favorito: <b>' + esc(a.pick_ia) + '</b> ' + (a.coincide ? '✅ coincide con nuestro análisis' : '⚠️ ve el partido distinto') + '</div>' : '') +
        (a.veredictos && a.veredictos.length ? '<div class="ia-ver">' + a.veredictos.map((v) =>
          '<div class="' + (v.opinion === 'en_contra' ? 'contra' : 'favor') + '">' + (v.opinion === 'en_contra' ? '❌ En contra' : '✅ A favor') +
          ': <b>' + esc(v.apuesta) + '</b> — ' + esc(v.motivo) + (v.estado === 'verde' ? ' · salió ✅' : v.estado === 'roja' ? ' · salió ❌' : '') + '</div>').join('') + '</div>' : '')) +
      // v446 — lo que encontró en la web (bajas, alineaciones) y «¿te sirvió?» (sólo se mide)
      (a.noticias ? sub('Noticias', '<div class="ia-noti">' + String(a.noticias).split(' | ').map((n) => '<div>· ' + esc(n) + '</div>').join('') + '</div>') : '') +
      (window.SPX && SPX.votoIA ? SPX.votoIA(a.id) : '') +
      '<p class="tenue chico">Experimental: la medimos aparte en Historial y nuestros picks no dependen de ella.</p></details>';
  }
  function formaHtml(f) {
    return String(f || '').split('').map((c) => '<i class="fr ' + ({ G: 'g', E: 'e', P: 'p' }[c] || '') + '">' + c + '</i>').join('');
  }
  // v470 — una pestaña plegada dentro de otra (Antes del partido, Análisis IA)
  const sub = (titulo, cuerpo) => !cuerpo ? '' : '<details class="sub"><summary>' + titulo + '</summary><div class="sub-c">' + cuerpo + '</div></details>';
  // v492 — LOS ÚLTIMOS 5 DE VERDAD (no el promedio) y LA TABLA. El usuario: «las estadísticas más
  // importantes de sus últimos 5 partidos, las reales, pero que no se haga tan largo» y «una pestaña
  // para saber en qué lugar van: toda la tabla, resaltados esos equipos». Cada equipo de «Forma» se toca
  // y despliega sus 5 partidos (el más reciente arriba): marcador y, a favor-en contra, córners, tiros a
  // puerta y amarillas; «—» si ese partido no tiene la estadística real.
  const par = (x) => (Array.isArray(x) ? x[0] + '-' + x[1] : '—');
  function ultimosHtml(u) {
    if (!u || !u.length) return '';
    return '<div class="u5"><div class="u5-f u5-cab"><span></span><span>Rival</span><span>Res.</span><span>Córn.</span><span>A puerta</span><span>Amar.</span></div>' +
      u.map((x) => { const r = x[3] > x[4] ? 'G' : x[3] === x[4] ? 'E' : 'P';
        return '<div class="u5-f"><i class="fr ' + r.toLowerCase() + '">' + r + '</i><span class="u5-r" title="' + esc(x[0] + ' · ' + x[1]) + '">' +
          (x[2] ? 'vs ' : '@ ') + esc(x[1]) + '</span><b>' + x[3] + '-' + x[4] + '</b><span>' + par(x[5]) + '</span><span>' + par(x[6]) + '</span><span>' + par(x[7]) + '</span></div>'; }).join('') + '</div>';
  }
  function formaEquipo(nombre, f, u) {
    if (!u || !u.length) return '<div class="ctx-f"><span>' + esc(nombre) + '</span><span>' + formaHtml(f) + '</span></div>';
    return '<details class="ctx-eq"><summary class="ctx-f"><span>' + esc(nombre) + '</span><span>' + formaHtml(f) + '<i class="ctx-mas">▾</i></span></summary>' + ultimosHtml(u) + '</details>';
  }
  // la tabla (web/datos/tablas.json, del exportador): se pide una vez, al primer partido que la necesita
  estado.tablas = null;
  let pidiendoTablas = false;
  function pedirTablas() {
    if (estado.tablas || pidiendoTablas) return;
    pidiendoTablas = true;
    fetch('datos/tablas.json?x=' + Math.floor(Date.now() / 6e5)).then((r) => (r.ok ? r.json() : null))
      .then((j) => { estado.tablas = (j && j.ligas) || {}; pintar(); }).catch(() => { estado.tablas = {}; });
  }
  const fichasEq = (t) => normBusca(t).replace(/\b(fc|cf|sc|cd|ud|club|afc|sd|ac|as|ss|calcio|de|the)\b/g, ' ').split(/[^a-z0-9]+/).filter(Boolean);
  function filaDe(grupos, nombre) {
    const a = fichasEq(nombre); let mejor = null, pts = 0;
    grupos.forEach((g) => g.filas.forEach((f) => { const b = fichasEq(f[1]); const com = a.filter((x) => b.includes(x)).length;
      const sc = com / Math.max(1, Math.min(a.length, b.length)); if (sc > pts) { pts = sc; mejor = f; } }));
    return pts >= 0.5 ? mejor : null;
  }
  const zona = (t) => (/relegat|descens/i.test(t) ? 'baja' : /europa|conference|sudamericana|play-?in|promotion play/i.test(t) ? 'media' : t ? 'alta' : '');
  function tablaHtml(liga, L, V) {
    if (!liga) return '';
    if (!estado.tablas) { pedirTablas(); return ''; }
    const t = estado.tablas[liga];
    if (!t || !t.grupos || !t.grupos.length) return '';
    const yoL = filaDe(t.grupos, L), yoV = filaDe(t.grupos, V);
    const dg = (x) => (x == null ? '' : x > 0 ? '+' + x : String(x));
    const v = (x) => (x == null ? '' : x);
    return t.grupos.map((g) => (t.grupos.length > 1 ? '<div class="ctx-tit">' + esc(g.nombre) + '</div>' : '') +
      '<div class="tabla-liga"><div class="tl-f tl-cab"><span>#</span><span>Equipo</span><span>PJ</span><span>DG</span><span>Pts</span></div>' +
      g.filas.map((f) => '<div class="tl-f' + (f === yoL || f === yoV ? ' yo' : '') + (zona(f[8]) ? ' z-' + zona(f[8]) : '') + '"' + (f[8] ? ' title="' + esc(f[8]) + '"' : '') + '>' +
        '<span>' + f[0] + '</span><span class="tl-n">' + esc(f[1]) + '</span><span>' + v(f[2]) + '</span><span>' + dg(f[6]) + '</span><b>' + v(f[7]) + '</b></div>').join('') + '</div>').join('') +
      '<p class="tenue chico">Resaltados ' + esc(L) + ' y ' + esc(V) + '. Fuente: ESPN.</p>';
  }
  function contextoHtml(ctx, L, V, liga) {
    if (!ctx) return '';
    // v470 — el usuario: «está muy grande; que tenga secciones que yo pueda abrir». Cada parte es
    // una pestaña plegada dentro de la general (se recuerdan abiertas al repintar: memoriaVista).
    let h = '<details class="ctx"><summary>📋 Antes del partido</summary>';
    if (ctx.fl || ctx.fv) {
      h += sub('Forma · últimos 5', '<div class="ctx-tit">El más reciente a la derecha' + (ctx.ul || ctx.uv ? ' · toca un equipo para ver sus partidos' : '') + '</div>' +
        formaEquipo(L, ctx.fl, ctx.ul) + formaEquipo(V, ctx.fv, ctx.uv) +
        '<p class="tenue chico">G = ganó · E = empató · P = perdió.' + (ctx.ul || ctx.uv ? ' En cada partido, a favor-en contra.' : '') + '</p>');
    }
    // v391 — promedios de los últimos 10 de cada uno, con barras (como SofaScore)
    if (ctx.sl && ctx.sv) {
      const pc = (x) => (x == null ? '-' : Math.round(100 * x) + ' %');
      const filas = [['gf', 'Goles a favor', (x) => x], ['gc', 'Goles en contra', (x) => x], ['o25', 'Partidos con +2.5 goles', pc],
        ['btts', 'Ambos anotan', pc], ['tir', 'Tiros', (x) => x], ['cor', 'Córners', (x) => x], ['tap', 'Tiros a puerta', (x) => x], ['tar', 'Amarillas', (x) => x], ['pos', 'Posesión %', (x) => x]]
        .filter(([k]) => ctx.sl[k] != null && ctx.sv[k] != null);
      h += sub('Promedios · últimos ' + Math.min(ctx.sl.n, ctx.sv.n), '<div class="leyenda"><span class="l">' + esc(L) + '</span><span class="r">' + esc(V) + '</span></div>' +
        filas.map(([k, et, f]) => filaStat(et, f(ctx.sl[k]), f(ctx.sv[k]), true)).join(''));
    }
    if (ctx.h2h && ctx.h2h.length) {
      h += sub('Enfrentamientos · ' + ctx.h2h.length, ctx.h2h.map((x) =>
        '<div class="ctx-h"><small>' + esc(x[0]) + '</small><span>' + esc(x[1]) + '</span><b>' + esc(x[2]) + '</b><span>' + esc(x[3]) + '</span></div>').join(''));
    } else if (ctx.sl || ctx.sv) {
      // v415 — sin H2H se dice (antes la sección desaparecía y parecía un fallo)
      h += sub('Enfrentamientos', '<p class="tenue">No se han enfrentado en nuestros registros.</p>');
    }
    // v492 — la tabla de su liga, entera, con los dos resaltados
    const tb = tablaHtml(liga, L, V);
    if (tb) h += sub('Clasificación', tb);
    if (ctx.bl || ctx.bv) {
      h += sub('Bajas', (ctx.bl ? '<div class="ctx-b"><b>' + esc(L) + ':</b> ' + ctx.bl.map(esc).join(', ') + '</div>' : '') +
        (ctx.bv ? '<div class="ctx-b"><b>' + esc(V) + ':</b> ' + ctx.bv.map(esc).join(', ') + '</div>' : ''));
    }
    return h + '<p class="tenue chico">Es información para que analices; el pick ya la toma en cuenta a través del mercado.</p></details>';
  }

  // ---------- FICHA DEL PARTIDO (tipo SofaScore) ----------
  let fichaId = null;
  // v380 — el usuario: «en los terminados, al picarle en Ver partido no se
  // ven las estadísticas». Lo en vivo sólo pide los partidos en juego; uno
  // terminado se pide a ESPN al abrir su ficha (una vez) y se pinta igual.
  async function pedirResumen(p) {
    if (!p.espn || estado.vivo[p.espn]) return;
    const [ruta, id] = p.espn.split(':');
    try {
      const r = await fetch(ESPN + ruta + '/summary?event=' + id);
      if (r.ok) estado.vivo[p.espn] = leerResumen(await r.json(), p);
    } catch (e) { /* sin red: la ficha queda sin estadísticas */ }
  }
  // v513 — PULSO SHARPICKS en «Ver partido». Gratis: «otro gol» y «2 córners más» en su tramo medido; VIP
  // (o el partido abierto con monedas): todos los mercados, % exacto, cuota justa y tus picks en vivo.
  // v520 — la recomendación «IA + modelo» de este partido, sólo si es del marcador de ahora (tras un gol, se espera la nueva)
  function iaPulso(p, v) {
    const yo = (window.SPX && SPX.yo) || {}, c = clavePartido(p), marc = v && v.g ? v.g[0] + '-' + v.g[1] : '';
    const r = (yo.pulsoIA || {})[c], h = (yo.pulsoHay || {})[c];
    return { rec: r && r.marcador === marc && r.acierto == null ? r : null, hay: !!(h && h.marcador === marc) };
  }
  // v522 — LAS SEÑALES DEL PULSO DE ESTE PARTIDO (70 %+ y que aún pagan), medidas: la nube las apunta al cruzar el
  // umbral y las califica (✅ en cuanto se cumplen, ❌ al pitido). Aquí, además, el estado de ahora con el marcador y
  // los córners en vivo. El mercado de las que siguen en juego sólo con VIP o con el Pulso abierto.
  function senalVa(s, v, vs) {
    if (!s.mercado || !v || !v.g) return null;
    const [gh, ga] = String(s.marcador).split('-').map(Number), g = v.g, k = s.mercado;
    if (k.startsWith('cor')) {
      const c = ((vs && vs.stats) || {}).wonCorners, n = c && c.v ? num(c.v[0]) + num(c.v[1]) : null;
      if (n == null || s.corners == null) return null;
      const meta = s.corners + Number(k[3]);
      return { ok: n >= meta, falta: meta - n, base: s.corners, meta, van: n, que: 'cor' };
    }
    const tot = g[0] + g[1];
    // v524 — cada señal con sus números: lo que había al apuntarla, la meta y lo que va ahora
    const r = (base, meta, van) => ({ ok: van >= meta, falta: meta - van, base, meta, van, que: 'gol' });
    return k === 'gol' ? r(gh + ga, gh + ga + 1, tot) : k === 'gol2' ? r(gh + ga, gh + ga + 2, tot)
      : k === 'gol_l' ? r(gh, gh + 1, g[0]) : k === 'gol_v' ? r(ga, ga + 1, g[1]) : null;
  }
  function senalesHtml(p, v, vs, L, V) {
    const ss = ((window.SPX && SPX.yo.pulsoSen) || {})[clavePartido(p)] || [];
    if (!ss.length || !window.PULSO) return '';
    const fin = v && v.fase === 'post';
    const fila = (s) => {
      const va = s.acierto == null ? senalVa(s, v, vs) : null, nums = senalVa(s, v, vs);
      const ok = s.acierto === true || (va && va.ok), mal = s.acierto === false || (fin && va && !va.ok);
      const est = ok ? '<span class="sn-e ok">' + OK() + (s.cumplida_min ? ' ' + s.cumplida_min + "'" : ' sí') + '</span>'
        : mal ? '<span class="sn-e mal">' + MAL() + ' no</span>'
        : '<span class="sn-e va">' + ico('hourglass') + (va && va.falta > 0 ? ' falta' + (va.falta > 1 ? 'n ' : ' ') + va.falta : '') + '</span>';
      const que = s.mercado ? esc(PULSO.nombre(s.mercado, L, V)) + ' <b>' + Math.round(100 * Number(s.prob)) + '%</b>' : ico('lock', 'candado') + ' VIP';
      // «4 → 7 · van 6»: con cuántos se apuntó, a cuántos tiene que llegar y cuántos van (córners o goles)
      const cuenta = s.mercado && nums ? '<small class="sn-n">' + ico(nums.que === 'cor' ? 'flag' : 'ball-football') + ' ' + nums.base + ' → ' + nums.meta +
        (ok || mal ? '' : ' · van ' + nums.van) + '</small>' : '';
      return '<div class="sn-fila"><span class="sn-m">' + s.minuto + "'</span><span class=\"sn-q\">" + que +
        (s.ia ? ' <span class="pc-ia">' + ico('sparkles', 'acento') + '</span>' : '') + cuenta + '</span>' + est + '</div>';
    };
    // v524 — el usuario: «si ya se cumplió, se quita y se pone en la sección de las que ya se cumplieron»
    const cumple = (s) => s.acierto === true || (s.acierto == null && (senalVa(s, v, vs) || {}).ok);
    const falla = (s) => s.acierto === false || (s.acierto == null && fin && senalVa(s, v, vs) && !senalVa(s, v, vs).ok);
    const orden = ss.slice().sort((a, b) => a.minuto - b.minuto);
    const enJuego = orden.filter((s) => !cumple(s) && !falla(s)), hechas = orden.filter(cumple), fallas = orden.filter(falla);
    const grupo = (tit, xs) => (xs.length ? '<div class="sn-sub">' + tit + '</div>' + xs.map(fila).join('') : '');
    return '<div class="senales"><div class="sn-cab"><span>' + ico('target') + ' Señales 70 %+</span><small>' + hechas.length + ' de ' + ss.length + ' ' + OK() + '</small></div>' +
      grupo('En juego', enJuego) + grupo('Ya se cumplieron', hechas) + grupo('No se cumplieron', fallas) + '</div>';
  }
  function pulsoAbierto(p) {
    return !!(window.SPX && (SPX.esVip() || (SPX.yo.pulso || {})[clavePartido(p)]));
  }
  function pulsoHtml(p, v, vs, L, V, abierto) {
    if (!window.PULSO || !v || v.fase !== 'in' || p.deporte && p.deporte !== 'Fútbol') return '';
    // v517 — sólo en el 2.º tiempo (lo medido); en el 1.º, un aviso corto en vez del bloque
    if (PULSO.enPrimerTiempo(v)) return '<div class="pulso pulso-espera">' + ico('activity', 'acento') + ' <b>Pulso</b> · se abre en el 2.º tiempo</div>';
    const ms = PULSO.mercados(p, v, vs);
    if (!ms.length) return PULSO.listo() ? '' : '<div class="pulso pulso-espera">' + ico('activity', 'acento') + ' Cargando el Pulso…</div>';
    const top = PULSO.mejor(ms, abierto);
    // v517 — compacto: burbujas en rejilla; la mejor (la más probable que aún paga algo) arriba y destacada
    const burbuja = (m) => {
      const t = m.tramo, nom = esc(PULSO.nombre(m.k, L, V));
      if (!abierto && !m.gratis) return '<div class="pt bloq"><span class="pt-n">' + nom + '</span><span class="pt-s">' + ico('lock', 'candado') + ' VIP</span></div>';
      const pr = abierto ? Math.round(100 * m.p) + '%' : (t ? Math.round(100 * t.desde) + '-' + Math.round(100 * t.hasta) + '%' : '');
      return '<div class="pt ' + (m.p >= 0.7 ? 'alta' : m.p >= 0.6 ? 'media' : 'baja') + '" title="' + (t ? 'Salió ' + Math.round(100 * t.fue) + ' % en ' + t.n.toLocaleString('es-MX') + ' casos' : '') + '">' +
        '<span class="pt-n">' + nom + '</span><span class="pt-p">' + pr + '</span>' +
        '<span class="pt-s">' + (abierto ? 'justa ' + m.justa.toFixed(2) : t ? 'salió ' + Math.round(100 * t.fue) + '%' : '') + '</span></div>';
    };
    const dest = top ? '<div class="pulso-top"><span class="pulso-top-et">' + ico('star', 'estrella') + ' Mejor ahora</span><b>' + esc(PULSO.nombre(top.k, L, V)) + '</b>' +
      '<span class="pulso-top-p">' + (abierto ? Math.round(100 * top.p) + '%' : Math.round(100 * top.tramo.desde) + '-' + Math.round(100 * top.tramo.hasta) + '%') + '</span>' +
      '<small>' + (abierto ? 'valor si paga más de ' + top.justa.toFixed(2) : 'salió ' + Math.round(100 * top.tramo.fue) + '% en el historial') + '</small></div>' : '';
    const precio = Number((window.SPX && SPX.yo.precios.precio_pulso) || 2);
    // v520 — «IA + MODELO»: Gemini elige la mejor jugada SÓLO entre estos mercados de 70 %+ (en la nube, medida como señal)
    const ia = iaPulso(p, v);
    // v522 — el usuario: «¿por qué 2 córners más tiene 83 % y 1 córner más 67 %? no tiene sentido». El 83 % era el
    // de cuando se recomendó (al 63'), no el de ahora. Ahora dice de qué minuto es, si ya se cumplió y, si no, cuánto
    // falta y qué probabilidad le da el Pulso a eso AHORA.
    const iaEstado = (r) => {
      const va = r.acierto === true ? { ok: true } : senalVa(r, v, vs);
      if (va && va.ok) return { cl: 'hecha', txt: OK() + ' Se cumplió' + (r.acierto === true ? '' : ' (el servidor la confirma)') };
      if (!va) return { cl: '', txt: ico('hourglass') + ' En curso' };
      const k = r.mercado.startsWith('cor') ? 'cor' + Math.min(3, Math.max(1, va.falta)) : r.mercado === 'gol2' && va.falta === 1 ? 'gol' : r.mercado;
      const ahora = ms.find((m) => m.k === k);
      const falta = r.mercado.startsWith('cor') ? 'faltan ' + va.falta + (va.falta === 1 ? ' córner' : ' córners') : r.mercado === 'gol2' && va.falta === 1 ? 'falta 1 gol' : 'falta el gol';
      return { cl: '', txt: ico('hourglass') + ' ' + falta + (ahora ? ' · ahora ' + Math.round(100 * ahora.p) + '%' : '') };
    };
    // v524 — cumplida, deja la caja (pasa a «Ya se cumplieron» en las señales) y la IA da una nueva con lo de ahora
    if (ia.rec && iaEstado(ia.rec).cl === 'hecha') ia.rec = null;
    const iaE = ia.rec ? iaEstado(ia.rec) : null;
    const iaH = ia.rec ? '<div class="pulso-ia ' + iaE.cl + '"><span class="pulso-ia-et">' + ico('sparkles', 'acento') + ' IA + modelo · al ' + ia.rec.minuto + "' (" + esc(ia.rec.marcador) + ')</span><b>' + esc(PULSO.nombre(ia.rec.mercado, L, V)) + '</b>' +
        '<span class="pulso-top-p">' + Math.round(100 * Number(ia.rec.prob)) + '%</span>' + '<small class="ia-va">' + iaE.txt + '</small>' +
        (ia.rec.motivo ? '<small>' + esc(ia.rec.motivo) + '</small>' : '') + '</div>'
      : ia.hay && !abierto ? '<div class="pulso-ia bloq"><span class="pulso-ia-et">' + ico('sparkles', 'acento') + ' IA + modelo</span><b>Ya tiene su recomendación</b><small>' + ico('lock', 'candado') + ' VIP o abre el Pulso de este partido</small></div>' : '';
    return '<div class="pulso"><div class="pulso-cab"><span>' + ico('activity', 'acento') + ' Pulso SharPicks</span><small>en vivo</small></div>' + iaH + dest +
      '<div class="pulso-grid">' + ms.filter((m) => m !== top).map(burbuja).join('') + '</div>' +
      (abierto ? '' : '<button class="btn pulso-abrir" data-pulso-abrir="' + esc(clavePartido(p)) + '">' + ico('lock-open', 'candado') + ' Todo el Pulso · ' + precio + ' monedas</button>') + '</div>';
  }

  function ficha(id) {
    // v461 — el usuario: «a veces le pongo Ver partido y no me lleva a ningún lado»: sólo buscaba en
    // los picks; las tarjetas de «sólo análisis» viven aparte. Ahora busca en las dos.
    const todos = estado.picks.concat(estado.analisis || []);
    const p = todos.find((x) => x.id === id); if (!p) return;
    fichaId = id;
    if (p.espn && !estado.vivo[p.espn]) { pedirResumen(p).then(() => { if (fichaId === id) ficha(id); pintar(); }); }
    const v = estado.vivo[p.espn];
    const [L, V] = lados(p);
    const otras = (agrupar(todos.filter((x) => clavePartido(x) === clavePartido(p) && !x.solo_analisis))[0]) || [];
    // v527 — la campana: avisarme por Telegram de ESTE partido (señales del Pulso y sus picks)
    const kAl = clavePartido(p), alOn = window.SPX && (SPX.yo.alertas || []).some((x) => x.tipo === 'partido' && x.valor === kAl);
    // v530 — el usuario: «el botón de avisarme está muy escondido… ponlo de otro color y que cambie al picarlo»: su
    // propio renglón bajo el marcador, ámbar; prendido, verde
    const campana = window.SPX && !(v && v.fase === 'post') ? '<div class="campana-fila"><button class="campana' + (alOn ? ' on' : '') + '" data-tg-partido="' + esc(kAl) + '">' +
      ico('bell') + '<span>' + (alOn ? 'Te aviso por Telegram' : 'Avisarme por Telegram') + '</span>' + (alOn ? ico('circle-check') : '') + '</button></div>' : '';
    let h = '<button class="cerrar" data-cerrar>✕</button>' +
      '<div class="equipos grande"><div class="eq">' + escudo(p.logo_h, L, p.deporte) + '<span>' + esc(L) + '</span></div>' +
      '<div class="marc">' + (v && v.fase !== 'pre' ? v.g[0] + ' - ' + v.g[1] : 'vs') + '<small>' + esc(v ? v.detalle : horaCdmx(aFecha(p.inicio))) + '</small></div>' +
      '<div class="eq der"><span>' + esc(V) + '</span>' + escudo(p.logo_a, V, p.deporte) + '</div></div>' + campana;
    h += penalesHtml(v, L, V);           // v503
    h += cancha(v, p);                   // v427/v429 — la cancha en vivo
    h += '<!--PULSO-->';                 // v517 — el Pulso justo debajo de la cancha, a la vista
    setTimeout(vivo365, 50);
    const vs = conRespaldo(v, p);                                      // v462 — con respaldo si ESPN no las trae
    const abierto = pulsoAbierto(p);
    h += (otras.length ? '<h3>Nuestras apuestas en este partido</h3>' : '') + otras.map((x) => {
      const pr = progreso(x, v);
      // v513 — la probabilidad EN VIVO de que el pick quede verde (Pulso; VIP o con el partido abierto)
      const real = (window.SPX && SPX.yo.desbloqueados[x.id]) || (x.premium ? '' : x.apuesta);
      const ahora = abierto && window.PULSO && v && v.fase === 'in' && !(pr && /verde|roja/.test(pr.e)) ? PULSO.delPick(real, p, v, vs) : null;
      return '<div class="linea-ap"><span>' + nivel(x).i + ' ' + (window.SPX ? SPX.apuesta(x) : esc(x.apuesta)) + ' · ' + (x.cuota ? Number(x.cuota).toFixed(2) : '') + '</span>' +
        (pr ? '<span class="progreso ' + pr.e + '">' + esc(pr.t) + '</span>' : '<span class="tenue">' + pct(x.prob) + '</span>') +
        (ahora != null ? '<span class="pulso-pick" title="Probabilidad en vivo (Pulso)">ahora ' + Math.round(100 * ahora) + ' %</span>' : '') + '</div>';
    }).join('');
    // v517 — el usuario: «la tarjeta de Ver partido ya es muy grande, hay que seccionarla». A la vista: el
    // marcador, la cancha, el Pulso y nuestras apuestas; las estadísticas y lo que ha pasado, plegados (y se
    // quedan como el usuario los dejó al repintarse cada minuto).
    const yaAbiertas = new Set([...document.querySelectorAll('#ficha-cuerpo details[data-sec][open]')].map((d) => d.dataset.sec));
    const seccion = (k, tit, cuerpo) => '<details class="ctx ficha-sec" data-sec="' + k + '"' + (yaAbiertas.has(k) ? ' open' : '') + '><summary>' + tit + '</summary>' + cuerpo + '</details>';
    const pulsoArriba = pulsoHtml(p, v, vs, L, V, abierto) + senalesHtml(p, v, vs, L, V);
    h = h.replace('<!--PULSO-->', pulsoArriba);
    if (vs && Object.keys(vs.stats || {}).length) {
      h += seccion('stats', ico('chart-column') + ' Estadísticas', compensacion(p, v) + '<div class="leyenda"><span class="l">' + esc(L) + '</span><span class="r">' + esc(V) + '</span></div>' + estadisticas(p, vs));
    } else {
      h += '<p class="tenue">Las estadísticas aparecen aquí en cuanto empieza el partido.</p>';
    }
    if (v && v.eventos.length) {
      h += seccion('eventos', ico('clock') + ' Lo que ha pasado', v.eventos.slice().reverse().slice(0, 25).map((e) =>
        '<div class="evento ' + (e.lado ? 'der' : '') + '"><b>' + esc(e.min) + '</b> ' + e.ico + ' ' + esc(e.texto) + '</div>').join(''));
    }
    // v446 — «⚠️ Reportar un error» (resultado mal, equipo equivocado, dato raro): si es real, +5 🪙
    h += '<button class="reportar" data-reportar="' + esc(p.partido) + '" data-pick="' + esc(p.id) + '">⚠️ Reportar un error</button>';
    $('ficha-cuerpo').innerHTML = h;
    $('ficha-cuerpo').setAttribute('style', varsColor(v));
    $('ficha').hidden = false;
  }
  function refrescarFicha() { if (fichaId && !$('ficha').hidden) ficha(fichaId); }

  // ---------- PINTAR ----------
  // ---------- v380: LA PÁGINA COMO APP ----------
  // El usuario: «está muy larga de scrollear, tiene un buen de partidos, es
  // mucho escanear… que sea más fácil, más intuitiva, que no sea aburrida».
  // Antes: una tira con 120 tarjetas grandes. Ahora: barra de abajo con
  // pantallas (Picks · En vivo · Mis picks · Historial · Planes), 💎 Destacados
  // en carrusel, y la lista COMPACTA POR LIGA (una línea por partido, como
  // SofaScore) que se abre al tocarla con la tarjeta completa.
  estado.vista = 'picks';
  estado.fase = 'todos';
  estado.busca = '';
  estado.liga = '';
  estado.abiertos = new Set();
  estado.ligasCerradas = new Set();
  estado.ligasAbiertas = new Set();
  try { estado.porHora = localStorage.getItem('sp_orden') === 'hora'; } catch (e) { estado.porHora = false; }   // v468
  try { estado.ligasFav = new Set(JSON.parse(localStorage.getItem('sp_ligas_fav') || '[]')); } catch (e) { estado.ligasFav = new Set(); }   // v470     // v461 — el usuario: «que cada liga salga minimizada para que no ocupe tanto»
  estado.verFinales = false;
  estado.verSinPick = false;                    // v484 — el bloque «Sin pick» de «Por hora», plegado

  function vivoDe(ps) {
    const x = ps.find((q) => q.espn);
    return (x && estado.vivo[x.espn]) || estado.fsPor[clavePartido(ps[0])] || null;      // v424: o Flashscore
  }
  const DURA = { 'Fútbol': 2.1, NBA: 2.6, NHL: 2.7, NFL: 3.5, MLB: 3.4, KBO: 3.4, 'Béisbol': 3.4, Tenis: 3 };
  const duracion = (dep) => (DURA[dep] || 3) * 3600e3;
  function faseDe(ps) {
    const v = vivoDe(ps);
    const fin = ps.every((x) => ['verde', 'roja', 'nula'].includes(x.estado) || (v && v.terminado && ['verde', 'roja'].includes(estadoVisto(x, v))));
    if (v && v.fase === 'in') return 'vivo';
    // v431 — «datos raros en la hora de la MLS»: ESPN dice que aún NO empieza
    // (su hora real es otra); manda ESPN y se enseña nuestra hora, no su texto
    if (v && v.fase === 'pre' && !fin) return 'proximo';
    if (fin || (v && v.terminado)) return 'terminado';
    const ini = aFecha(ps[0].inicio);
    // v421 — empezado sin dato en vivo: en juego lo que dura ESE deporte; después,
    // terminado (liquidando). Antes eran 3 h 30 min para todos y un partido de
    // fútbol (Pachuca vs Cruz Azul Sub-21) seguía «Vivo» hora y media después.
    // v503 — en una copa (eliminatoria) puede haber prórroga y penales: ~3 h, no 2
    const copa = ps[0].deporte === 'Fútbol' && (ps[0].solo_analisis || /copa|cup|pokal|coupe|ta[cç]a|trophy|troph[ée]e/i.test(String(ps[0].liga || '')));
    if (ini && ini <= new Date()) return Date.now() - ini > duracion(ps[0].deporte) * (copa ? 1.45 : 1) ? 'terminado' : 'vivo';
    return 'proximo';
  }
  function relojFila(ps) {
    const v = vivoDe(ps), f = faseDe(ps);
    if (f === 'vivo') { const rv = relojVivo(v, ps[0]); return '<span class="rl vivo"><i class="punto"></i>' + esc(rv.t) + (rv.sub ? '<small class="rl-comp">' + esc(rv.sub) + '</small>' : '') + '</span>'; }
    if (f === 'terminado') return '<span class="rl">Final' + (v && v.pen ? '<small class="rl-comp">pen ' + v.pen.g[0] + '-' + v.pen.g[1] + '</small>' : v && v.est === 'STATUS_FINAL_AET' ? '<small class="rl-comp">prórroga</small>' : '') + '</span>';
    const d = aFecha(ps[0].inicio);
    return '<span class="rl">' + (d ? F_HORA.format(d) : '') + '</span>';
  }
  function resumenPicks(ps) {
    // v463 — con el resultado al pitazo (no sólo el del servidor) y dicho en la tarjeta: «Verde» / «Roja»
    const es = ps.map((x) => estadoVisto(x)), v = es.filter((e) => e === 'verde').length, r = es.filter((e) => e === 'roja').length;
    if (ps.length === 1 && (v || r)) return v ? '<span class="ok res">✅ Verde</span>' : '<span class="ko res">❌ Roja</span>';
    if (v || r) return (v ? '<span class="ok">✅' + (v > 1 ? v : '') + '</span>' : '') + (r ? '<span class="ko">❌' + (r > 1 ? r : '') + '</span>' : '');
    return '';
  }
  // v391 — si un partido trae un dato raro, se salta (antes rompía TODA la lista y los toques ya no hacían nada)
  const seguro = (fn) => (x) => { try { return fn(x); } catch (e) { console.warn('[sharpicks] partido saltado', e); return ''; } };
  function filaPartido(ps) {
    const p = ps[0], nv = nivel(p), [L, V] = lados(p), v = vivoDe(ps);
    const k = clavePartido(p), abierto = estado.abiertos.has(k);
    const marc = v && v.fase !== 'pre' ? v.g : (p.marcador ? String(p.marcador).split('-').map((x) => x.trim()) : null);
    const ap = p.solo_analisis ? '<span class="sin-pick-txt">Sin pick</span>' : window.SPX ? SPX.apuesta(p) : esc(p.apuesta);
    // v440 — en «Mis picks» se desliza a la izquierda para quitar el pick seguido
    const mio = estado.vista === 'mios' && window.SPX && SPX.yo.user, abiertoRoce = mio && estado.deslizado === k;
    return '<div class="partido-fila ' + nv.c + (abierto ? ' abierto' : '') + (mio ? ' deslizable' : '') + (abiertoRoce ? ' desliza' : '') + '" data-k="' + esc(k) + '">' +
      (mio ? '<button class="quitar-fila" data-dejar="' + esc(ps.map((x) => x.id).join(',')) + '" aria-label="Quitar de Mis picks">🗑️ Quitar</button>' : '') +
      '<button class="pf" data-abrir="' + esc(k) + '" aria-expanded="' + abierto + '"' + (abiertoRoce ? ' style="transform:translateX(-92px)"' : '') + '>' +
      relojFila(ps) +
      '<span class="pf-eqs">' + (estado.porHora ? '<span class="pf-lig">' + esc(ligaDe(p)) + '</span>' : '') +
      '<span class="pf-eq">' + escudo(p.logo_h, L, p.deporte) + '<b>' + esc(L) + '</b>' + (marc ? '<em>' + esc(marc[0]) + '</em>' : '') + '</span>' +
      '<span class="pf-eq">' + escudo(p.logo_a, V, p.deporte) + '<b>' + esc(V) + '</b>' + (marc ? '<em>' + esc(marc[1]) + '</em>' : '') + '</span></span>' +
      '<span class="pf-pick"><span class="pf-niv">' + nv.i + '</span><span class="pf-ap">' + ap + '</span>' +
      '<span class="pf-cu">' + (p.cuota ? Number(p.cuota).toFixed(2) : '') + '</span>' +
      (ps.length > 1 ? '<span class="pf-mas">+' + (ps.length - 1) + '</span>' : '') + resumenPicks(ps) + '</span>' +
      '</button>' + (abierto ? '<div class="pf-detalle">' + tarjeta(ps) +
        // v468 — «hace falta algo para cerrar la tarjeta sin subir hasta arriba»: va pegado abajo mientras se lee
        '<div class="pf-cerrar"><button data-abrir="' + esc(k) + '" data-cerrar-pf="1">' + ico('chevron-down', 'arriba') + ' Cerrar</button></div></div>' : '') + '</div>';
  }
  // v422 — «✨ PARA TI». Cada pick que aún no empieza (hoy y mañana) se puntúa
  // con lo que el usuario eligió (deportes y ligas) y con sus tendencias (lo que
  // sigue y desbloquea: deporte, liga, nivel y la cuota que suele jugar); entre
  // parecidos gana el más probable. Sin intereses ni señales, no sale nada.
  function paraTi() {
    if (!window.SPX || !SPX.yo.user || !SPX.intereses) return [];
    const it = SPX.intereses(), g = it.gustos || { deporte: {}, liga: {}, nivel: {}, cuotas: [], n: 0 };
    if (!it.deportes.size && !it.ligas.size && !g.n) return [];
    const parte = (m, k) => { const tot = Object.values(m).reduce((s, x) => s + x, 0); return tot ? (m[k] || 0) / tot : 0; };
    const cs = g.cuotas.slice().sort((a, b) => a - b), med = cs.length ? cs[Math.floor(cs.length / 2)] : null;
    const ahora = new Date(), dias = [diaPestana(0), diaPestana(1)];
    const puntos = (p) => {
      let s = 0;
      if (p.liga && it.ligas.has(p.liga)) s += 3;
      if (it.deportes.has(p.deporte)) s += 2;
      s += 2 * parte(g.liga, p.liga) + 1.5 * parte(g.deporte, p.deporte) + parte(g.nivel, nivel(p).n);
      if (med && p.cuota) s += Math.max(0, 1 - Math.abs(Math.log(Number(p.cuota) / med)) * 3);
      return s + Number(p.prob || 0);
    };
    const cand = estado.picks.filter((p) => p.estado === 'pendiente' && dias.includes(diaDe(p)) && (aFecha(p.inicio) || 0) > ahora);
    const mejor = new Map();
    cand.forEach((p) => { const k = clavePartido(p), s = puntos(p); if (!mejor.has(k) || mejor.get(k).s < s) mejor.set(k, { s, p }); });
    const umbral = 2 + 0.8;                       // que encaje en algo más que la probabilidad
    // v483 — el usuario: «que tengan las fechas… debe priorizar los de hoy»: hoy primero, luego mañana
    return [...mejor.values()].filter((x) => x.s >= umbral)
      .sort((a, b) => (dias.indexOf(diaDe(a.p)) - dias.indexOf(diaDe(b.p))) || (b.s - a.s)).slice(0, 8).map((x) => [x.p]);
  }
  // y sus ligas van primero en la lista
  const ligaDe = (p) => (p.deporte === 'Tenis' ? '🎾 ' : '') + (p.liga || p.deporte || 'Otros');
  // v468 — las ligas de la A a la Z (el usuario); las que eligió en sus intereses, arriba
  const alfabetico = (mapa) => new Map([...mapa.entries()].sort((a, b) =>
    a[0].replace(/^🎾 /, '').localeCompare(b[0].replace(/^🎾 /, ''), 'es', { sensitivity: 'base' })));
  // v470 — el usuario: «de la A a la Z, y una estrellita para marcar la liga como favorita y que salga
  // al inicio». Antes subían solas las ligas de sus intereses y parecía que no estaba en orden.
  function ordenPreferido(mapa) {
    const fav = (l) => estado.ligasFav.has(l) ? 1 : 0;
    return new Map([...mapa.entries()].map((e, i) => [e, i]).sort((a, b) => (fav(b[0][0]) - fav(a[0][0])) || (a[1] - b[1])).map((x) => x[0]));
  }
  // v483 — el día del partido en las tarjetas de Destacados y «Para ti»: Hoy, Mañana, Ayer o «jue 30 oct»
  function diaCorto(p) {
    const d = diaDe(p), dif = { [diaPestana(0)]: 'Hoy', [diaPestana(1)]: 'Mañana', [diaPestana(-1)]: 'Ayer' };
    if (dif[d]) return dif[d];
    const f = aFecha(p.inicio) || new Date(d + 'T12:00:00');
    return isNaN(f) ? '' : F_FECHA.format(f).replace(/[.,]/g, '');
  }
  function relojDia(ps) {
    const dia = diaCorto(ps[0]);
    return '<span class="dest-cuando' + (dia === 'Hoy' ? ' hoy' : '') + '">' + (dia ? '<small>' + esc(dia) + '</small>' : '') + relojFila(ps) + '</span>';
  }
  function destacado(ps, etiqueta) {
    const p = ps[0], [L, V] = lados(p), v = vivoDe(ps);
    // v501 — el usuario: «en Final, en los Destacados debería salir el resultado final y si fue verde o
    // roja». El marcador del vivo o, ya terminado, el que quedó guardado; y el resultado del pick.
    const gm = /^\s*(\d+)\s*-\s*(\d+)\s*$/.exec(String(p.marcador || ''));
    const marc = v && v.fase !== 'pre' ? v.g[0] + ' - ' + v.g[1] : gm ? gm[1] + ' - ' + gm[2] : '';
    const ev = estadoVisto(p, v);
    const res = ev === 'verde' ? '<span class="ok res">' + OK() + ' Verde</span>' : ev === 'roja' ? '<span class="ko res">' + MAL() + ' Roja</span>' : ev === 'nula' ? '<span class="res">Nula</span>' : '';
    const ia = iaSegura(p);                                                       // v531 — el morado (VIP)
    return '<button class="dest' + (res ? ' dest-fin' : '') + (ia ? ' ia-' + ia : '') + '" data-abrir="' + esc(clavePartido(p)) + '" data-ir="1">' +
      '<div class="fila">' + (etiqueta || '<span class="et nivel diamante">💎 Diamante</span>') + relojDia(ps) + '</div>' + selloIA(ia) +
      '<div class="dest-eqs">' + escudo(p.logo_h, L, p.deporte) + '<span>' + esc(marc || 'vs') + '</span>' + escudo(p.logo_a, V, p.deporte) + '</div>' +
      '<div class="dest-nom">' + esc(L) + ' – ' + esc(V) + '</div>' +
      '<div class="dest-ap">' + (window.SPX ? SPX.apuesta(p) : esc(p.apuesta)) + '</div>' +
      '<div class="dest-pie"><b>' + (p.cuota ? Number(p.cuota).toFixed(2) : '') + '</b>' + (res || '<span>probabilidad ' + pct(p.prob) + '</span>') + '</div></button>';
  }
  function tiraMarcador() {
    const hoy = diaPestana(0), l0 = estado.picks.filter((p) => diaDe(p) === hoy), l = l0.filter((p) => p.tipo !== 'error'),
      t = cuenta(l), e = cuenta(l.filter((p) => p.elige)), er = cuenta(l0.filter((p) => p.tipo === 'error'));
    return '<button class="tira" data-vista-ir="historial">Hoy <b>✅ ' + t.v + ' ❌ ' + t.r + '</b> ' + pct(t.pct) +
      ' · 💎 <b>' + e.v + '-' + e.r + '</b>' + (e.pct == null ? '' : ' ' + pct(e.pct)) +
      (er.v + er.r ? ' · 💰 <b>' + er.v + '-' + er.r + '</b>' : '') + ' <span>Ver historial ›</span></button>';
  }

  // v483 — sin acentos ni mayúsculas: «america», «América» y «AMÉRICA» encuentran «Club America»
  const normBusca = (t) => String(t || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/\s+/g, ' ').trim();
  const _MEMO_NORM = new WeakMap();
  const textoBusca = (p) => { let t = _MEMO_NORM.get(p); if (t === undefined) { t = normBusca([p.partido, p.home, p.away, p.liga, p.deporte].filter(Boolean).join(' ')); _MEMO_NORM.set(p, t); } return t; };
  // todos los picks y las tarjetas de «sólo análisis» de partidos sin pick, de todos los días cargados
  function paraBuscar(q) {
    const picks = estado.picks.filter((p) => textoBusca(p).includes(q));
    const ya = new Set(picks.map(clavePartido));
    return picks.concat((estado.analisis || []).filter((a) => textoBusca(a).includes(q) && !ya.has(clavePartido(a))));
  }
  // los resultados por día: hoy primero, luego los que vienen y al final los ya jugados (el más reciente arriba)
  function pintarBusqueda(grupos) {
    const hoy = diaPestana(0), porDia = new Map();
    grupos.forEach((g) => { const d = diaDe(g[0]); if (!porDia.has(d)) porDia.set(d, []); porDia.get(d).push(g); });
    const dias = [...porDia.keys()].sort((a, b) => ((a < hoy) - (b < hoy)) || (a < hoy ? b.localeCompare(a) : a.localeCompare(b)));
    const orden = { vivo: 0, proximo: 1, terminado: 2 };
    $('tarjetas').innerHTML = '<p class="tenue chico busca-nota">Buscando «' + esc(estado.busca.trim()) + '» en todos los días y deportes · ' +
      grupos.length + (grupos.length === 1 ? ' partido' : ' partidos') + '</p>' +
      dias.map((d) => { const gs = porDia.get(d).sort((a, b) => (orden[faseDe(a)] - orden[faseDe(b)]) || String(a[0].inicio).localeCompare(String(b[0].inicio)));
        return '<section class="liga-bloque por-hora"><div class="liga-cab busca-dia"><span class="liga-nom">' + esc(diaCorto(gs[0][0])) + '</span><small>' +
          gs.length + (gs.length === 1 ? ' partido' : ' partidos') + '</small></div>' + gs.map(seguro(filaPartido)).join('') + '</section>'; }).join('');
    $('aviso').textContent = grupos.length ? '' : 'No encontramos «' + estado.busca.trim() + '» entre los partidos de estos días (los que ya se jugaron y los que vienen). Prueba con otra parte del nombre (p. ej. «Pumas» o «Madrid»).';
  }
  // v418 — la lista de la pantalla: los picks y, en Picks y En vivo, las tarjetas de
  // «sólo análisis» de los partidos que no tienen ningún pick ese día
  function listaConAnalisis() {
    const base = listaBase();
    if (!['picks', 'vivo'].includes(estado.vista) || !(estado.analisis || []).length) return base;
    const ya = new Set(base.map(clavePartido));
    const dia = diaPestana(OFFS[estado.dia] || 0);
    const enVivo = (p) => faseDe([p]) === 'vivo';
    return base.concat(estado.analisis.filter((a) => !ya.has(clavePartido(a)) && (estado.vista === 'vivo' ? enVivo(a) && a.estado !== 'final' : diaDe(a) === dia)));
  }
  // v471 — «ARMA TU COMBINADA». El usuario: «que pueda armar una combinada con los diamantes, los oros o
  // las platas, juntas o separadas, de 2 a 20 patas; que la arme primero el modelo con las más
  // probables y luego la IA le dé un doble chequeo: cuál se mete, cuál se descarta y por cuál cambiarla».
  //   1. el modelo: de cada partido que aún no empieza (del día y los deportes elegidos) su pick más
  //      probable de los niveles elegidos; se toman los N más probables (un partido, una pata).
  //   2. la IA: la pata que ve «en contra» se descarta y entra la siguiente más probable; la que ve
  //      «a favor» lo dice. Sin análisis de la IA (o sin VIP) la pata queda «sin revisar».
  // La probabilidad de la combinada es el producto (partidos distintos): baja con cada pata y se dice.
  estado.arm = { niv: new Set(['Diamante', 'Platino']), n: 3, res: null };
  const normTxt = (t) => String(t || '').toLowerCase().replace(/[^a-z0-9áéíóúñü.]+/g, ' ').trim();
  // v531 — EL MORADO DE LA IA (sólo VIP). El usuario: «que se iluminen de morado los que la IA vea con más probabilidad
  // de cumplirse… que con la IA le demos mayor probabilidad a la predicción del modelo». Medido (1.979 picks, 17-30 oct;
  // D:/Claude/mediciones/ia_confianza_morado.py): la «confianza» de la IA (1-5 por partido) SÍ separa en 💎/🔷/🥇:
  //   confianza 5 → 91,1 % vs 81,9 % (mitades +12,6 / +7,1, p5 +5,1); confianza ≥ 4 → 85,6 % vs 78,6 % (p5 +2,5).
  // En 🥈 Plata no separa (80 % con o sin): ahí no se marca. Su «a favor» tampoco separa (lo dice casi siempre).
  // 2 = la IA le da mayor probabilidad (morado fuerte), 1 = a favor (morado claro), 0 = nada.
  function iaSegura(p) {
    if (!window.SPX || !SPX.esVip || !SPX.esVip() || !p || p.tipo === 'error') return 0;
    if (!['diamante', 'platino', 'oro'].includes(nivel(p).c)) return 0;
    const a = (SPX.yo.ia || {})[p.partido], c = a ? Number(a.confianza) : 0;
    return c >= 5 ? 2 : c >= 4 ? 1 : 0;
  }
  // lo que de verdad salió en cada tono (💎/🔷/🥇, 17-30 oct): con eso «la IA le da más probabilidad» al modelo, medido
  const IA_SALIO = { 2: 0.91, 1: 0.86 };
  const selloIA = (n) => (n ? '<span class="ia-sello s' + n + '">' + ico('sparkles') + (n === 2 ? ' IA: mayor probabilidad' : ' IA: a favor') +
    ' · salió ' + Math.round(100 * IA_SALIO[n]) + ' %</span>' : '');
  function veredictoIA(p) {
    const a = window.SPX && SPX.yo.ia ? SPX.yo.ia[p.partido] : null;
    if (!a || !(a.veredictos || []).length) return null;
    const txt = normTxt((SPX.yo.desbloqueados || {})[p.id] || p.apuesta);
    const v = a.veredictos.find((x) => normTxt(x.apuesta) === txt);
    return v ? (v.opinion === 'en_contra' ? 'contra' : 'favor') : null;
  }
  // v473 — el usuario: «sólo el VIP arma con todos los niveles; el gratis, sólo con Oro (es lo que
  // trae su plan)». Los demás niveles salen con candado y llevan a Planes.
  const armVip = () => !!(window.SPX && SPX.esVip && SPX.esVip());
  const armNiveles = () => (armVip() ? estado.arm.niv : new Set(['Oro']));
  function armarCombinada(pasaDep) {
    const ahora = Date.now() + 10 * 60e3, sel = armNiveles();
    const mejor = new Map();
    listaBase().filter((p) => pasaDep(p) && p.estado === 'pendiente' && p.tipo !== 'error' && !p.solo_analisis && Number(p.cuota) > 1 &&
      (aFecha(p.inicio) || 0) > ahora && sel.has(nivel(p).n)).forEach((p) => {
      const k = clavePartido(p), o = mejor.get(k);
      if (!o || Number(p.prob) > Number(o.prob)) mejor.set(k, p);
    });
    const cands = [...mejor.values()].sort((a, b) => Number(b.prob) - Number(a.prob));
    const patas = [], fuera = [];
    for (const p of cands) {
      if (patas.length >= estado.arm.n) break;
      const v = veredictoIA(p);
      if (v === 'contra') { fuera.push(p); continue; }
      if (estado.arm.soloIA && !iaSegura(p)) continue;                      // v531 — «sólo las que la IA ve seguras»
      patas.push({ p, v });
    }
    return { patas, fuera, disponibles: cands.length };
  }
  function pintarArmador(pasaDep) {
    const caja = $('armador'); if (!caja) return;
    const A = estado.arm, r = A.res;
    const NIV = [['Diamante', ico('gem', 'nv-diamante')], ['Platino', ico('award', 'nv-platino')], ['Oro', ico('medal', 'nv-oro')], ['Plata', ico('medal', 'nv-plata')]];
    const vipA = armVip(), sel = armNiveles();
    let h = '<div class="tit">' + ico('target') + ' Arma tu combinada</div>' +
      '<div class="arm-fila"><span class="arm-et">Niveles</span><div class="chips">' + NIV.map(([n, i]) => vipA || n === 'Oro'
        ? '<button class="chip' + (sel.has(n) ? ' activa' : '') + '" data-arm-niv="' + n + '">' + i + ' ' + n + '</button>'
        : '<button class="chip bloq" data-vista-ir="planes" data-foco="plan-vip">' + i + ' ' + n + ' ' + ico('lock') + '</button>').join('') + '</div></div>' +
      (vipA ? '' : '<p class="tenue chico">Con tu plan gratis armas con 🥇 Oro. Con VIP, con todos los niveles.</p>') +
      '<div class="arm-fila"><span class="arm-et">Patas</span><div class="arm-n"><button data-arm-n="-1" aria-label="Menos patas">−</button><b>' + A.n +
      '</b><button data-arm-n="1" aria-label="Más patas">+</button></div><button class="vip-btn arm-ir" data-arm-ir="1">Armar</button></div>';
    if (r) {
      if (!r.patas.length) h += '<p class="aviso">No hay picks de esos niveles por jugar este día. Prueba con otros niveles u otro día.</p>';
      else {
        const prob = r.patas.reduce((x, y) => x * Number(y.p.prob || 0), 1), cuota = r.patas.reduce((x, y) => x * Number(y.p.cuota || 1), 1);
        const vip = window.SPX && SPX.esVip && SPX.esVip();
        h += '<div class="arm-res">' + r.patas.map(({ p, v }) => {
          const [L, V] = lados(p), nv = nivel(p);
          const ia = iaSegura(p);              // v531 — sin morado no se pone nada («“más difícil” les quita credibilidad»)
          return '<div class="arm-pata' + (ia ? ' ia-' + ia : '') + '"><span class="arm-niv">' + nv.i + '</span><span class="arm-txt"><b>' + (window.SPX ? SPX.apuesta(p) : esc(p.apuesta)) + '</b><small>' +
            esc(L) + ' vs ' + esc(V) + ' · ' + esc(horaCdmx(aFecha(p.inicio))) + '</small></span><span class="arm-num"><b>' + Number(p.cuota).toFixed(2) + '</b><small>' + pct(p.prob) + '</small></span>' +
            (ia ? '<span class="arm-ia ia-' + ia + '">' + ico('sparkles') + (ia === 2 ? ' Mayor probabilidad' : ' A favor') + '</span>' : '') + '</div>';
        }).join('') +
          (r.fuera.length ? '<div class="arm-fuera">' + MAL() + ' La IA descartó: ' + r.fuera.map((p) => '<b>' + (window.SPX ? SPX.apuesta(p) : esc(p.apuesta)) + '</b> (' + esc(lados(p).join(' vs ')) + ')').join(', ') + ' · entró la siguiente más probable</div>' : '') +
          (r.patas.length < A.n ? '<p class="aviso">Sólo hay ' + r.patas.length + ' patas que cumplan (de partidos distintos y que aún no empiezan).</p>' : '') +
          // v531 — cuántas ve seguras la IA, y armarla sólo con ésas (VIP)
          (vip ? '<div class="arm-ia-res">' + ico('sparkles') + ' La IA ve <b>' + r.patas.filter((x) => iaSegura(x.p)).length + ' de ' + r.patas.length +
            '</b> patas seguras <button class="chip' + (A.soloIA ? ' activa' : '') + '" data-arm-soloia="1">' + (A.soloIA ? 'Todas las patas' : 'Sólo las seguras') + '</button></div>' : '') +
          '<div class="arm-pie"><span>Cuota <b>' + cuota.toFixed(2) + '</b> · se cumplen todas ~<b>' + Math.round(100 * prob) + ' %</b>' +
          (vip && r.patas.some((x) => iaSegura(x.p)) ? ' · con la IA ~<b>' + Math.round(100 * r.patas.reduce((a, x) => a * (IA_SALIO[iaSegura(x.p)] || Number(x.p.prob || 0)), 1)) + ' %</b>' : '') + '</span>' +
          (r.patas.length >= 2 ? '<button class="vip-btn" data-arm-boleto="' + esc(r.patas.map((x) => x.p.id).join(',')) + '">Pasar a mi combinada</button>' : '') + '</div>' +
          '<p class="tenue chico">Cada pata de más baja la probabilidad de la combinada: con 3 patas de 85 % queda en ~61 %.</p></div>';
      }
    }
    caja.innerHTML = h;
  }
  function listaBase() {
    if (estado.vista === 'mios') return window.SPX ? SPX.filtrarMios(estado.picks) : [];
    if (estado.vista === 'vivo') return estado.picks.filter((p) => faseDe([p]) === 'vivo');
    const dia = diaPestana(OFFS[estado.dia] || 0);
    return estado.picks.filter((p) => diaDe(p) === dia);
  }

  // v414 — «cuando ando analizando con la IA se cierra solita y el scroll se va
  // para abajo». Cada 30 s (marcadores en vivo), cada 3 min (picks) y al
  // renovarse la sesión la lista se vuelve a pintar: las tarjetas abiertas se
  // recordaban, pero NO las secciones de dentro (Análisis IA, forma y H2H), que
  // se cerraban; la página se encogía y el scroll brincaba. Ahora se anota qué
  // secciones estaban abiertas y dónde estaba el usuario, y se restaura.
  function memoriaVista() {
    const abiertas = new Set();
    document.querySelectorAll('[data-k] details[open]').forEach((d) => {
      const c = d.closest('[data-k]'), i = [...c.querySelectorAll('details')].indexOf(d);
      abiertas.add(c.dataset.k + '|' + d.className + '|' + i);
    });
    let ancla = null;
    // v461 — el usuario: «al abrir la app se baja sola». Hasta arriba no hay nada que
    // sostener: si se anclaba a la 1.ª tarjeta y luego aparecían Destacados o «Para ti»
    // encima, la página «la seguía» hacia abajo. Sólo se ancla si el usuario ya bajó.
    if (window.scrollY < 40) return { abiertas, ancla };
    for (const c of document.querySelectorAll('[data-k]')) {
      const r = c.getBoundingClientRect();
      if (r.bottom > 0 && r.height) { ancla = { k: c.dataset.k, top: r.top }; break; }
    }
    return { abiertas, ancla };
  }
  function restaurarVista(m) {
    if (!m) return;
    if (m.abiertas.size) document.querySelectorAll('[data-k]').forEach((c) => {
      [...c.querySelectorAll('details')].forEach((d, i) => { if (m.abiertas.has(c.dataset.k + '|' + d.className + '|' + i)) d.open = true; });
    });
    if (m.ancla) {
      const c = [...document.querySelectorAll('[data-k]')].find((x) => x.dataset.k === m.ancla.k);
      if (c) { const dy = c.getBoundingClientRect().top - m.ancla.top; if (Math.abs(dy) > 1) window.scrollBy(0, dy); }
    }
  }
  function pintar() {
    const m = memoriaVista();
    try { pintarLista(); } finally { try { restaurarVista(m); } catch (e) { /* nunca tumba la página */ } }
  }
  function pintarLista() {
    document.querySelectorAll('[data-vista]').forEach((s) => { s.hidden = !String(s.dataset.vista).split(' ').includes(estado.vista); });
    document.querySelectorAll('#nav button').forEach((b) => b.classList.toggle('activa', b.dataset.vistaIr === estado.vista));
    const hoy = diaPestana(0), ayer = diaPestana(-1);
    $('marcadores').innerHTML = cajaMarcador('Hoy', estado.picks.filter((p) => diaDe(p) === hoy)) +
      cajaMarcador('Ayer', estado.picks.filter((p) => diaDe(p) === ayer));
    $('tira').innerHTML = tiraMarcador();
    if (!['picks', 'vivo', 'mios', 'combinadas'].includes(estado.vista)) return;

    // v483 — EL BUSCADOR. El usuario: «no me sale nada… quiero poder buscar cualquier equipo… los
    // partidos de hoy, mañana o el que ya terminó». Antes buscaba sólo en el día de la pestaña, en el
    // deporte elegido (fútbol de inicio), con los demás filtros y con acentos («América» no hallaba
    // «Club America»). Ahora, con texto, busca en TODOS los días y deportes, sin filtros ni acentos.
    const q = normBusca(estado.busca);
    const buscando = !!q && ['picks', 'vivo'].includes(estado.vista);
    let lista = buscando ? paraBuscar(q) : listaConAnalisis();
    const deps = ['Todos'].concat([...new Set(lista.map((p) => p.deporte).filter(Boolean))].sort());
    // varios a la vez: un conjunto (vacío = todos); lo que ya no hay hoy se suelta
    // v461 — el usuario: «que la primera opción sea fútbol (o el deporte que escogieron al inicio);
    // en Todos tarda». Mientras el usuario no toque el filtro, se elige solo.
    if (!estado.depTocado && deps.length > 1) {
      const it = window.SPX && SPX.intereses ? SPX.intereses() : null;
      const pref = it && it.deportes ? [...it.deportes].find((d) => deps.includes(d)) : null;
      const ini = pref || (deps.includes('Fútbol') ? 'Fútbol' : null);
      if (ini) estado.deportes = new Set([ini]);
    }
    estado.deportes = new Set([...(estado.deportes || [])].filter((d) => deps.includes(d)));
    estado.niveles = estado.niveles || new Set();
    const ICO = new Proxy({}, { get: (_, d) => icoDep(d) });
    const act = (s, v) => (v === 'Todos' ? s.size === 0 : s.has(v));
    $('deportes').innerHTML = deps.map((d) => '<button class="chip' + (act(estado.deportes, d) ? ' activa' : '') + '" data-dep="' + esc(d) + '">' + (ICO[d] ? ICO[d] + ' ' : '') + esc(d) + '</button>').join('');
    $('niveles').innerHTML = ['Todos', 'Diamante', 'Platino', 'Oro', 'Plata', 'Cuota alta'].map((n) => '<button class="chip' + (act(estado.niveles, n) ? ' activa' : '') + '" data-niv="' + n + '">' + ({ Diamante: ico('gem', 'nv-diamante') + ' ', Platino: ico('award', 'nv-platino') + ' ', Oro: ico('medal', 'nv-oro') + ' ', Plata: ico('medal', 'nv-plata') + ' ', 'Cuota alta': ico('coins', 'nv-error') + ' ' }[n] || '') + n + '</button>').join('');
    const pasaDep = (p) => estado.deportes.size === 0 || estado.deportes.has(p.deporte);
    if (estado.deportes.size && !buscando) lista = lista.filter(pasaDep);
    if (estado.niveles.size && !buscando) lista = lista.filter((p) => estado.niveles.has(nivel(p).n));
    if (q && !buscando) lista = lista.filter((p) => normBusca(p.partido + ' ' + (p.liga || '')).includes(q));
    // v380 — «en lugar de escribir, un desplegable con todas las ligas»
    const nomLiga = (p) => p.liga || p.deporte || 'Otros';
    const cuentaLigas = new Map();
    agrupar(lista).forEach((g) => { const l = nomLiga(g[0]); cuentaLigas.set(l, (cuentaLigas.get(l) || 0) + 1); });
    if (estado.liga && !cuentaLigas.has(estado.liga)) estado.liga = '';
    $('liga').innerHTML = '<option value="">🏆 Todas las ligas (' + cuentaLigas.size + ')</option>' +
      [...cuentaLigas.entries()].sort((a, b) => a[0].localeCompare(b[0], 'es'))
        .map(([l, n]) => '<option value="' + esc(l) + '"' + (l === estado.liga ? ' selected' : '') + '>' + esc(l) + ' · ' + n + '</option>').join('');
    if (estado.liga && !buscando) lista = lista.filter((p) => nomLiga(p) === estado.liga);

    let grupos = agrupar(lista);
    const n = { todos: grupos.length, proximo: 0, vivo: 0, terminado: 0 };
    grupos.forEach((g) => { n[faseDe(g)]++; });
    $('fases').innerHTML = [['todos', 'Todos'], ['proximo', 'Próximos'], ['vivo', '🔴 Vivo'], ['terminado', 'Final']]
      .map(([k, t]) => '<button class="seg' + (estado.fase === k ? ' activa' : '') + '" data-fase="' + k + '">' + t + ' <small>' + n[k] + '</small></button>').join('');
    $('fases').hidden = estado.vista === 'vivo' || estado.vista === 'combinadas' || buscando;
    if (estado.fase !== 'todos' && estado.vista !== 'vivo' && !buscando) grupos = grupos.filter((g) => faseDe(g) === estado.fase);

    // 💎 Destacados: los Diamante que aún no terminan
    const dest = estado.vista === 'picks' && !buscando ? agrupar(listaBase().filter(pasaDep)).filter((g) => g[0].elige && (estado.fase === 'todos' ? faseDe(g) !== 'terminado' : faseDe(g) === estado.fase))
      .sort((a, b) => String(a[0].inicio).localeCompare(String(b[0].inicio))).slice(0, 12) : [];
    $('destacados').hidden = !dest.length;
    // v531 — al VIP, primero los que la IA ve más seguros (morado)
    const porIA = (xs, f) => xs.map((x, i) => [x, i]).sort((a, b) => (iaSegura(f(b[0])) - iaSegura(f(a[0]))) || (a[1] - b[1])).map((x) => x[0]);
    $('destacados-lista').innerHTML = porIA(dest, (g) => g[0]).map(seguro(destacado)).join('');
    // v422 — ✨ Para ti
    const pt = estado.vista === 'picks' && !buscando ? paraTi() : [];
    if ($('parati')) {
      $('parati').hidden = !pt.length;
      $('parati-lista').innerHTML = porIA(pt, (g) => g[0]).map(seguro((g) => { const n = nivel(g[0]); return destacado(g, '<span class="et nivel ' + n.c + '">' + n.i + ' ' + n.n + '</span>'); })).join('');
    }
    // 🔗 Combinadas del día elegido, del deporte elegido (las mixtas siempre)
    const diaC = diaPestana(OFFS[estado.dia] || 0);
    // v398 — tienen su pestaña; en Picks sólo una línea que lleva a ella
    const combs = (estado.combinadas || []).filter((c) => c.fecha === diaC &&
      (estado.deportes.size === 0 || c.alcance === 'Mixta' || c.alcance === 'IA' || estado.deportes.has(c.alcance)));
    if ($('comb-hist')) $('comb-hist').innerHTML = histCombinadas();
    const vivas = combs.filter((c) => faseCombinada(c) !== 'terminado').length;
    $('comb-tira').innerHTML = combs.length ? '<button class="tira comb-tira" data-vista-ir="combinadas"><em>🔗 <b>' + combs.length + '</b> ' +
      (combs.length === 1 ? 'combinada' : 'combinadas') + (vivas ? '' : ' (ya jugadas)') + '</em><span>Ver ›</span></button>' : '';
    if (estado.vista === 'combinadas') {
      try { pintarArmador(pasaDep); } catch (e) { console.warn('[sharpicks] armador', e); }
      const orden = { vivo: 0, proximo: 1, terminado: 2 };
      $('combinadas-lista').innerHTML = combs.length ? combs.sort((a, b) => orden[faseCombinada(a)] - orden[faseCombinada(b)] ||
        (a.alcance === 'Mixta') - (b.alcance === 'Mixta') || String(a.alcance).localeCompare(b.alcance) || (a.tipo === 'alta') - (b.tipo === 'alta'))
        .map(seguro(tarjetaCombinada)).join('')
        : estado.errorCombinadas
          ? '<p class="aviso">No se pudieron consultar las combinadas. No es posible confirmar que no haya; reintenta en un momento.</p>'
          : '<p class="aviso">No hay combinadas para este día con estos filtros. Se arman con las patas de mayor probabilidad: si no hay suficientes, preferimos no darte una floja.</p>';
      return;
    }
    estado.grupos = new Map(agrupar(buscando ? lista : listaConAnalisis()).map((g) => [clavePartido(g[0]), g]));
    if (buscando) { pintarBusqueda(grupos); return; }

    // por liga: en vivo primero, luego por hora; la liga con su partido más temprano
    const orden = { vivo: 0, proximo: 1, terminado: 2 };
    grupos.sort((a, b) => (orden[faseDe(a)] - orden[faseDe(b)]) || String(a[0].inicio).localeCompare(String(b[0].inicio)));
    // en «Todos», lo ya terminado va al final en UN bloque plegado (de noche
    // son la mayoría y obligaban a bajar mucho para ver lo que viene)
    const plegar = estado.fase === 'todos' && estado.vista === 'picks';
    const fin = plegar ? grupos.filter((g) => faseDe(g) === 'terminado') : [];
    if (plegar) grupos = grupos.filter((g) => faseDe(g) !== 'terminado');
    const porLiga = (gs0) => {
      const m = new Map();
      gs0.forEach((g) => { const l = ligaDe(g[0]); if (!m.has(l)) m.set(l, []); m.get(l).push(g); });
      return alfabetico(m);
    };
    const ligas = ordenPreferido(porLiga(grupos));
    let finHtml = '';
    if (fin.length) {
      const ps = fin.flat(), v = ps.filter((x) => x.estado === 'verde').length, r = ps.filter((x) => x.estado === 'roja').length;
      finHtml = '<button class="fin-cab" data-ver-fin>' + (estado.verFinales ? '▾' : '▸') + ' Terminados · ' + fin.length + ' partidos · <b>✅ ' + v + ' ❌ ' + r + '</b></button>' +
        (estado.verFinales ? '<div class="fin-lista">' + pintarLigas(porLiga(fin)) + '</div>' : '');
    }
    const tog = estado.vista === 'picks' || estado.vista === 'mios'
      ? '<div class="orden-tog"><button class="' + (estado.porHora ? '' : 'activa') + '" data-ord="liga">Por liga</button>' +
        '<button class="' + (estado.porHora ? 'activa' : '') + '" data-ord="hora">' + ico('clock') + ' Por hora</button></div>' : '';
    // v484 — el usuario: «cuando ordenas por hora, que los que estén sin pick estén en una pestaña y,
    // si le pica, se despliegue», como las ligas. Los partidos con pick quedan a la vista; los de sólo
    // análisis, en un bloque plegado al final (antes de los terminados).
    const sinPick = (g) => g.every((x) => x.solo_analisis);
    const gConPick = estado.porHora ? grupos.filter((g) => !sinPick(g)) : [], gSinPick = estado.porHora ? grupos.filter(sinPick) : [];
    const sinPickHtml = gSinPick.length ? '<button class="fin-cab sinpick-cab" data-ver-sinpick>' + (estado.verSinPick ? '▾' : '▸') + ' Sin pick · ' +
      gSinPick.length + (gSinPick.length === 1 ? ' partido' : ' partidos') + ' <small>(sólo análisis)</small></button>' +
      (estado.verSinPick ? '<section class="liga-bloque por-hora">' + gSinPick.map(seguro(filaPartido)).join('') + '</section>' : '') : '';
    $('tarjetas').innerHTML = (estado.vista === 'vivo' ? candidatosPulso(grupos) : '') + tog + (estado.porHora
      ? (gConPick.length ? '<section class="liga-bloque por-hora">' + gConPick.map(seguro(filaPartido)).join('') + '</section>' : '') + sinPickHtml
      : pintarLigas(ligas)) + finHtml;
    function pintarLigas(mapa) { return [...mapa.entries()].map(([l, gs]) => {
      const cerrada = !(estado.busca || '').trim() && !estado.ligasAbiertas.has(l);
      const dia = gs.filter((g) => g[0].elige).length;
      const fav = estado.ligasFav.has(l);
      return '<section class="liga-bloque"><button class="liga-cab" data-liga="' + esc(l) + '"><span class="liga-nom">' +
        '<span class="fav' + (fav ? ' si' : '') + '" data-fav="' + esc(l) + '" role="button" aria-label="' + (fav ? 'Quitar de favoritas' : 'Marcar como favorita') + '">' + ico('star') + '</span>' + esc(l) + '</span>' +
        '<small>' + (dia ? '💎 ' + dia + ' · ' : '') + gs.length + ' ' + (gs.length === 1 ? 'partido' : 'partidos') + ' ' + (cerrada ? '▸' : '▾') + '</small></button>' +
        (cerrada ? '' : gs.map(seguro(filaPartido)).join('')) + '</section>';
    }).join(''); }
    const enVivo = Object.values(estado.vivo).filter((v) => v.fase === 'in').length;
    $('aviso').textContent = grupos.length ? '' :
      estado.vista === 'mios' ? (window.SPX && SPX.yo.user ? 'Todavía no sigues ningún pick: abre un partido y pulsa «☆ Seguir».' : 'Entra con tu correo para guardar tus picks.')
        : estado.vista === 'vivo' ? 'Ahorita no hay partidos en vivo con picks.'
          : estado.errorPicks ? 'No se pudieron consultar los pronósticos. Reintenta en un momento.'
            : !estado.picks.length ? 'La fuente respondió, pero no devolvió pronósticos. Revisa el precálculo o la publicación de datos.'
              : 'Sin partidos con estos filtros.';
    if (estado.respaldoPicks) $('aviso').textContent = '⚠️ La base no respondió; mostramos el archivo de respaldo. Los datos podrían estar desactualizados.';
    const b = $('nav-vivo-n'); if (b) { b.textContent = enVivo || ''; b.hidden = !enVivo; }
    // v384 — «falta béisbol»: si hay partidos de un deporte y ninguno pasó, se dice
    const sp = (estado.meta && estado.meta.sin_pick) || {};
    const conPick = new Set(lista.map((p) => p.deporte));
    const avisos = Object.entries(sp).filter(([dep, n]) => n > 0 && !conPick.has(dep) && estado.vista === 'picks' && estado.dia === 'hoy'
      && (estado.deportes.size === 0 || estado.deportes.has(dep)));
    if (avisos.length) $('tarjetas').insertAdjacentHTML('beforeend', avisos.map(([dep, n]) =>
      '<div class="sin-pick">' + ({ MLB: '⚾', KBO: '⚾', NBA: '🏀', NFL: '🏈', NHL: '🏒', Tenis: '🎾' }[dep] || '•') + ' <b>' + esc(dep) + '</b>: ' + n +
      (n === 1 ? ' partido hoy' : ' partidos hoy') + ', pero ninguno llegó a nuestro mínimo de probabilidad. Preferimos no darte un pick flojo.</div>').join(''));
  }

  window.SP = { pulsoIA: () => { if (estado.vista === 'vivo') pintar(); refrescarFicha(); }, nivel, pintar, estado, estadoVisto: (p) => estadoVisto(p), realDe: (p) => realDe(p), ico, icoDep, pedirResumen: (p) => pedirResumen(p) };   // v452: «Mis combinadas» usa lo mismo

  // v440 — DESLIZAR PARA QUITAR (sólo en «Mis picks», con el dedo): la fila se
  // corre a la izquierda y deja ver «Quitar»; si el gesto es vertical, es scroll.
  let roce = null;
  const pfDe = (f) => f && f.querySelector(':scope > .pf');
  document.addEventListener('touchstart', (e) => {
    const f = e.target.closest('.partido-fila.deslizable');
    if (!f || e.target.closest('.pf-detalle, .quitar-fila')) return;
    const t = e.touches[0], base = f.classList.contains('desliza') ? -92 : 0;
    roce = { f, x: t.clientX, y: t.clientY, base, dx: base, horiz: null };
  }, { passive: true });
  document.addEventListener('touchmove', (e) => {
    if (!roce) return;
    const t = e.touches[0], dx = t.clientX - roce.x, dy = t.clientY - roce.y;
    if (roce.horiz === null && Math.abs(dx) + Math.abs(dy) > 8) roce.horiz = Math.abs(dx) > Math.abs(dy) * 1.2;
    if (!roce.horiz) return;
    roce.dx = Math.max(-130, Math.min(0, roce.base + dx));
    roce.f.classList.add('desliza');
    const pf = pfDe(roce.f), bq = roce.f.querySelector(':scope > .quitar-fila');
    if (pf) { pf.style.transition = 'none'; pf.style.transform = 'translateX(' + roce.dx + 'px)'; if (bq) bq.style.height = pf.offsetHeight + 'px'; }
  }, { passive: true });
  document.addEventListener('touchend', () => {
    if (!roce) return;
    const { f, dx, horiz } = roce; roce = null;
    if (!horiz) return;
    estado.sinClic = Date.now();
    const pf = pfDe(f); if (pf) pf.style.transition = '';
    document.querySelectorAll('.partido-fila.desliza').forEach((o) => { if (o !== f) { o.classList.remove('desliza'); const q = pfDe(o); if (q) q.style.transform = ''; } });
    if (dx < -50) { if (pf) pf.style.transform = 'translateX(-92px)'; f.classList.add('desliza'); estado.deslizado = f.dataset.k; }
    else { if (pf) pf.style.transform = ''; f.classList.remove('desliza'); if (estado.deslizado === f.dataset.k) estado.deslizado = null; }
  });

  document.addEventListener('click', (e) => {
    const t = e.target.closest('[data-vista-ir],[data-dia],[data-dep],[data-niv],[data-fase],[data-abrir],[data-liga],[data-ficha],[data-ver-fin],[data-ver-sinpick],[data-ord],[data-fav],[data-arm-niv],[data-arm-n],[data-arm-ir],[data-arm-boleto],[data-arm-soloia],[data-par-k]');
    if (!t) return;
    if (t.hasAttribute('data-ver-fin')) { estado.verFinales = !estado.verFinales; pintar(); return; }
    if (t.hasAttribute('data-ver-sinpick')) { estado.verSinPick = !estado.verSinPick; pintar(); return; }
    if (t.dataset.vistaIr) {
      estado.vista = t.dataset.vistaIr; window.scrollTo({ top: 0 }); pintar();
      const foco = t.dataset.foco && document.getElementById(t.dataset.foco);   // v417 — directo al plan VIP
      if (foco) setTimeout(() => { foco.scrollIntoView({ behavior: 'smooth', block: 'start' }); foco.classList.add('resalta'); setTimeout(() => foco.classList.remove('resalta'), 2000); }, 80);
      return;
    }
    if (t.dataset.dia) { estado.dia = t.dataset.dia; document.querySelectorAll('#pestanas button').forEach((x) => x.classList.toggle('activa', x === t)); pintar(); return; }
    // tocar uno lo prende o lo apaga; «Todos» limpia
    const alterna = (s, v) => { if (v === 'Todos') s.clear(); else if (s.has(v)) s.delete(v); else s.add(v); };
    if (t.dataset.dep) { estado.depTocado = true; alterna(estado.deportes, t.dataset.dep); pintar(); return; }
    if (t.dataset.niv) { alterna(estado.niveles, t.dataset.niv); pintar(); return; }
    if (t.dataset.fase) { estado.fase = t.dataset.fase; pintar(); return; }
    if (t.dataset.ficha) { ficha(t.dataset.ficha); return; }
    if (t.dataset.parK) { estado.parley[t.dataset.parK] = Number(t.dataset.parN) || 3; pintar(); return; }
    if (t.dataset.armNiv) { const n = t.dataset.armNiv; if (!armVip() && n !== 'Oro') return; estado.arm.niv.has(n) ? estado.arm.niv.delete(n) : estado.arm.niv.add(n); estado.arm.res = null; pintar(); return; }
    if (t.dataset.armN) { estado.arm.n = Math.max(2, Math.min(20, estado.arm.n + Number(t.dataset.armN))); estado.arm.res = null; pintar(); return; }
    if (t.dataset.armSoloia) {                                       // v531 — sólo las patas que la IA ve seguras (VIP)
      estado.arm.soloIA = !estado.arm.soloIA;
      const pasaDep = (p) => estado.deportes.size === 0 || estado.deportes.has(p.deporte);
      estado.arm.res = armarCombinada(pasaDep); pintar(); return;
    }
    if (t.dataset.armIr) {
      const pasaDep = (p) => estado.deportes.size === 0 || estado.deportes.has(p.deporte);
      estado.arm.res = armarCombinada(pasaDep); pintar(); return;
    }
    if (t.dataset.armBoleto) {
      if (!(window.SPX && SPX.yo.user)) { if (window.SPX && SPX.avisoApp) SPX.avisoApp('Entra con tu correo para guardar tus combinadas.', 'aviso', 'Hace falta entrar'); return; }
      SPX.ponerBoleto(t.dataset.armBoleto.split(','));
      if (SPX.avisoApp) SPX.avisoApp('Ya está en «Tu combinada»: revísala y guárdala.', 'ok', 'Combinada lista');
      return;
    }
    if (t.dataset.fav) {
      const l = t.dataset.fav;
      estado.ligasFav.has(l) ? estado.ligasFav.delete(l) : estado.ligasFav.add(l);
      try { localStorage.setItem('sp_ligas_fav', JSON.stringify([...estado.ligasFav])); } catch (er) { /* sin almacenamiento */ }
      pintar(); return;
    }
    if (t.dataset.ord) { estado.porHora = t.dataset.ord === 'hora'; try { localStorage.setItem('sp_orden', t.dataset.ord); } catch (er) { /* sin almacenamiento */ } pintar(); return; }
    if (t.dataset.liga) {
      const l = t.dataset.liga;
      if (estado.ligasAbiertas.has(l)) {
        estado.ligasAbiertas.delete(l);
        // v468 — al cerrar la liga se cierran TODAS sus tarjetas (antes algunas seguían abiertas)
        (estado.grupos ? [...estado.grupos.entries()] : []).forEach(([k, g]) => { if (ligaDe(g[0]) === l) estado.abiertos.delete(k); });
      } else estado.ligasAbiertas.add(l);
      pintar(); return;
    }
    if (t.dataset.abrir) {
      const k = t.dataset.abrir;
      if (Date.now() - (estado.sinClic || 0) < 450) return;                 // v440: fue un deslizar, no un toque
      if (estado.deslizado) { const f = estado.deslizado; estado.deslizado = null; if (f === k || !t.dataset.ir) { pintar(); return; } }
      if (t.dataset.ir) {
        estado.abiertos.add(k); estado.fase = 'todos'; estado.niveles = new Set();
        const g = estado.grupos && estado.grupos.get(k), p0 = g && g[0];
        if (p0) {
          estado.ligasAbiertas.add((p0.deporte === 'Tenis' ? '🎾 ' : '') + (p0.liga || p0.deporte || 'Otros'));
          if (estado.deportes && estado.deportes.size && !estado.deportes.has(p0.deporte)) estado.deportes.add(p0.deporte);
        }
      }
      else {
        if (estado.abiertos.has(k)) estado.abiertos.delete(k); else estado.abiertos.add(k);
        const fila = t.closest('.partido-fila'), g = estado.grupos && estado.grupos.get(k);
        if (fila && g) {
          try {
            fila.outerHTML = filaPartido(g); setTimeout(vivo365, 50);
            // v468 — cerrada desde abajo: la fila vuelve a la vista (si no, se queda uno a media lista)
            if (t.dataset.cerrarPf) { const f2 = document.querySelector('.partido-fila[data-k="' + CSS.escape(k) + '"]'); if (f2 && f2.getBoundingClientRect().top < 70) f2.scrollIntoView({ block: 'start' }); }
            return;
          } catch (e) { /* abajo, repinta todo */ }
        }
      }
      pintar();
      const el = [...document.querySelectorAll('.pf')].find((x) => x.dataset.abrir === k);
      if (el && t.dataset.ir) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
  // v483 — se repinta cuando el usuario deja de escribir (250 ms), no con cada letra
  let _tBusca = null;
  $('busca').addEventListener('input', (e) => { clearTimeout(_tBusca); const v = e.target.value; $('busca-x').hidden = !v; _tBusca = setTimeout(() => { estado.busca = v; window.scrollTo({ top: 0 }); pintar(); }, 250); });
  // v484 — la equis blanca: borra todo de un toque y la lista vuelve al día de la pestaña
  $('busca-x').addEventListener('click', () => { clearTimeout(_tBusca); $('busca').value = ''; $('busca-x').hidden = true; estado.busca = ''; pintar(); $('busca').focus(); });
  $('liga').addEventListener('change', (e) => { estado.liga = e.target.value; pintar(); });
  $('ficha').addEventListener('click', (e) => { if (e.target.id === 'ficha' || e.target.closest('[data-cerrar]')) { $('ficha').hidden = true; fichaId = null; } });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') { $('ficha').hidden = true; fichaId = null; } });
  setInterval(() => { $('reloj').textContent = F_HORA.format(new Date()) + ' CDMX'; }, 1000);
  cargar();
  setInterval(cargar, 3 * 60 * 1000);   // picks nuevos y verdes/rojas oficiales
  setInterval(vivo, 20 * 1000);         // marcador y estadísticas (v436: cada 20 s)
  // v518 — el usuario: «cuando te sales un rato y vuelves, tarda en actualizarse el resultado y el
  // minuto». En segundo plano no se pide nada (v465) y el iPhone congela los relojes: al volver se
  // esperaba al siguiente turno (hasta 20 s, o más). Ahora se pide en cuanto la app vuelve a verse.
  let _ocultaDesde = 0;
  const alVolver = () => {
    const fuera = _ocultaDesde ? Date.now() - _ocultaDesde : 0;
    _ocultaDesde = 0;
    vivo(); vivo365(); vivoFs();
    if (fuera > 3 * 60 * 1000) cargar();                 // y los picks, si fue más de un rato
  };
  document.addEventListener('visibilitychange', () => { if (document.hidden) _ocultaDesde = Date.now(); else alVolver(); });
  window.addEventListener('pageshow', (e) => { if (e.persisted) alVolver(); });
  setInterval(vivoFs, 45 * 1000);       // v424 — y lo que ESPN no cubre
  setInterval(vivo365, 20 * 1000);      // v429 — la alineación y los tiros de las canchas a la vista
  setInterval(minutos365, 60 * 1000);   // v493 — el minuto de lo que sólo da Flashscore («1.ª parte»)
  setTimeout(minutos365, 6000);
  setInterval(() => { if (Object.keys(estado.m365).length && !document.hidden) pintar(); }, 60 * 1000);   // v493: el minuto corre
  setTimeout(vivoFs, 4000);

  // v454 — «INSTÁLALA COMO APP», sin tiendas ni licencias: en Android con el botón
  // del navegador; en el iPhone se explica «Compartir → Agregar a inicio». Sale a los
  // 20 s, nunca si ya está instalada, y si la cierras no vuelve en 14 días.
  (function instalarApp() {
    const yaApp = window.matchMedia('(display-mode: standalone)').matches || navigator.standalone;
    const ios = /iphone|ipad|ipod/i.test(navigator.userAgent) && !/crios|fxios/i.test(navigator.userAgent);
    let aviso = null, pedido = null;
    let cerrado = 0; try { cerrado = Number(localStorage.getItem('sharpicks-instalar-no') || 0); } catch (e) { /* sin almacenamiento */ }
    if (yaApp || Date.now() - cerrado < 14 * 864e5) return;
    window.addEventListener('beforeinstallprompt', (e) => { e.preventDefault(); pedido = e; });
    const cerrar = () => { if (aviso) aviso.remove(); aviso = null; try { localStorage.setItem('sharpicks-instalar-no', String(Date.now())); } catch (e) { /* nada */ } };
    setTimeout(() => {
      if (!ios && !pedido) return;          // el navegador no la deja instalar (o ya está)
      aviso = document.createElement('div');
      aviso.className = 'instalar';
      aviso.innerHTML = '<img src="marca/icon-192.png" alt="" width="40" height="40"><div class="ins-txt"><b>Instala SharPicks</b><small>' +
        (ios ? 'Toca ' + ico('share') + ' Compartir y luego «Agregar a inicio»' : 'Ábrela como app, a pantalla completa') + '</small></div>' +
        (ios ? '' : '<button class="ins-si">Instalar</button>') + '<button class="ins-no" aria-label="Cerrar">' + ico('x') + '</button>';
      document.body.appendChild(aviso);
      aviso.querySelector('.ins-no').addEventListener('click', cerrar);
      const si = aviso.querySelector('.ins-si');
      if (si) si.addEventListener('click', async () => { pedido.prompt(); await pedido.userChoice.catch(() => null); cerrar(); });
    }, 20000);
  })();
})();
