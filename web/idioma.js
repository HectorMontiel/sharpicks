// v582 — EL IDIOMA. El usuario: «que todos los textos sean dinámicos, español e inglés, para que la app pueda escalar; al abrir, una pantalla con banderas».
// La app se escribe en español y aquí, si eligieron inglés, TODO lo que se pinta se traduce antes de verse: textos, títulos, avisos, animaciones y lo que llega de
// los datos (apuestas, mercados). Así un texto nuevo no se escapa: `test_v582` falla si alguno no está en `idioma_en.js`. Quien usa español no carga nada de esto.
// Las fechas salen de `I18N.locale`. Lo que no es de la app (nombres de equipos y jugadores) se queda como está.
(function () {
  'use strict';
  const K_LANG = 'sp_idioma', K_FIJO = 'sp_idioma_fijo';
  const leer = (k) => { try { return localStorage.getItem(k); } catch (e) { return null; } };
  const escribir = (k, v) => { try { localStorage.setItem(k, v); } catch (e) { /* sin almacenamiento: dura esta visita */ } };
  const lang = leer(K_LANG) === 'en' ? 'en' : 'es';
  const I18N = window.I18N = { lang, locale: lang === 'en' ? 'en-US' : 'es-MX', t: (s) => s, traducir: () => {} };
  document.documentElement.lang = lang;
  if (lang === 'en') document.write('<script src="idioma_en.js"><\/script>');

  // ---- la pantalla para elegir
  const MX = '<svg viewBox="0 0 60 40" aria-hidden="true"><rect width="20" height="40" fill="#006847"/><rect x="20" width="20" height="40" fill="#fff"/><rect x="40" width="20" height="40" fill="#ce1126"/><circle cx="30" cy="20" r="5.5" fill="#8c6a2f"/><path d="M26 22q4 4 8 0" fill="none" stroke="#006847" stroke-width="1.4"/></svg>';
  const US = '<svg viewBox="0 0 60 40" aria-hidden="true"><rect width="60" height="40" fill="#fff"/>' +
    Array.from({ length: 7 }, (_, i) => '<rect y="' + (i * 40 / 6.5).toFixed(2) + '" width="60" height="' + (40 / 13).toFixed(2) + '" fill="#b22234"/>').join('') +
    '<rect width="26" height="21.5" fill="#3c3b6e"/>' + Array.from({ length: 12 }, (_, i) => '<circle cx="' + (4 + (i % 4) * 6) + '" cy="' + (4 + Math.floor(i / 4) * 6.5) + '" r="1.1" fill="#fff"/>').join('') + '</svg>';
  function elegir(nuevo, fijo) {
    escribir(K_LANG, nuevo);
    escribir(K_FIJO, fijo ? '1' : '0');
    if (nuevo !== lang) location.reload();
    else { const c = document.getElementById('idioma-pantalla'); if (c) c.remove(); }
  }
  function pantalla(obligada) {
    if (document.getElementById('idioma-pantalla')) return;
    const c = document.createElement('div');
    c.id = 'idioma-pantalla'; c.className = 'idioma-pantalla'; c.setAttribute('role', 'dialog'); c.setAttribute('aria-modal', 'true');
    c.setAttribute('translate', 'no');
    c.innerHTML = '<div class="idioma-caja"><img src="marca/logo-96.png" alt="" width="64" height="64"><h2>Elige tu idioma<small>Choose your language</small></h2>' +
      '<button class="idioma-op' + (lang === 'es' ? ' on' : '') + '" data-idioma="es">' + MX + '<span>Español</span></button>' +
      '<button class="idioma-op' + (lang === 'en' ? ' on' : '') + '" data-idioma="en">' + US + '<span>English</span></button>' +
      '<label class="idioma-fijo"><input type="checkbox" id="idioma-fijo" checked> <span>No volver a preguntar · Don\'t ask again</span></label>' +
      (obligada ? '' : '<button class="idioma-cerrar" data-idioma-cerrar>✕</button>') + '</div>';
    document.body.appendChild(c);
    c.addEventListener('click', (e) => {
      const b = e.target.closest('[data-idioma]');
      if (b) elegir(b.dataset.idioma, c.querySelector('#idioma-fijo').checked);
      else if (e.target.closest('[data-idioma-cerrar]')) c.remove();
    });
  }
  I18N.banderas = { es: MX, en: US };
  document.addEventListener('click', (e) => {
    const p = e.target.closest && e.target.closest('[data-idioma-poner]');
    if (p) elegir(p.dataset.idiomaPoner, true);
  });
  document.addEventListener('DOMContentLoaded', () => {
    // el botón del encabezado: la bandera del idioma de ahora, para cambiarlo sin entrar a la cuenta
    const der = document.querySelector('.top .derecha');
    if (der) {
      const b = document.createElement('button');
      b.className = 'idioma-btn'; b.setAttribute('aria-label', 'Idioma'); b.setAttribute('data-idioma-abrir', ''); b.innerHTML = lang === 'en' ? US : MX;
      b.addEventListener('click', () => pantalla(false));
      const ay = der.querySelector('.ayuda-btn');
      der.insertBefore(b, ay || der.firstChild);
    }
    if (leer(K_FIJO) !== '1') pantalla(true);
  });
  if (lang !== 'en') return;

  // ---- el traductor
  const LETRA = /[\p{L}\p{N}]/u;
  const num = /\d+(?:[.,]\d+)?/g;
  let DICT = new Map(), TROZOS = null, TROZO_RE = null;
  // lo que depende del texto: apuestas, marcador y frases con datos
  const MD = (x) => (/^m[áa]s/i.test(x) ? 'Over' : 'Under');
  const PATRONES = [
    [/^Gana (.+)$/, '$1 to win'],
    [/^(.+) o empate$/, '$1 or draw'],
    [/^Goles: (M[áa]s|Menos) de ([\d.]+)$/i, (m, a, n) => 'Goals: ' + MD(a) + ' ' + n],
    [/^Goles (.+): (M[áa]s|Menos) de ([\d.]+)$/i, (m, e, a, n) => e + ' goals: ' + MD(a) + ' ' + n],
    [/^Goles de (.+): (m[áa]s|menos) de ([\d.]+)$/i, (m, e, a, n) => e + ' goals: ' + MD(a) + ' ' + n],
    [/^C[óo]rners: (M[áa]s|Menos) de ([\d.]+)$/i, (m, a, n) => 'Corners: ' + MD(a) + ' ' + n],
    [/^C[óo]rners Local: (M[áa]s|Menos) de ([\d.]+)$/i, (m, a, n) => 'Home corners: ' + MD(a) + ' ' + n],
    [/^C[óo]rners Visita: (M[áa]s|Menos) de ([\d.]+)$/i, (m, a, n) => 'Away corners: ' + MD(a) + ' ' + n],
    [/^C[óo]rners (.+): (M[áa]s|Menos) de ([\d.]+)$/i, (m, e, a, n) => e + ' corners: ' + MD(a) + ' ' + n],
    [/^Tarjetas: (M[áa]s|Menos) de ([\d.]+)$/i, (m, a, n) => 'Cards: ' + MD(a) + ' ' + n],
    [/^Tarjetas del partido: (m[áa]s|menos) de ([\d.]+)$/i, (m, a, n) => 'Game cards: ' + MD(a) + ' ' + n],
    [/^Puntos: (M[áa]s|Menos) de ([\d.]+)$/i, (m, a, n) => 'Points: ' + MD(a) + ' ' + n],
    [/^Carreras: (M[áa]s|Menos) de ([\d.]+)$/i, (m, a, n) => 'Runs: ' + MD(a) + ' ' + n],
    [/^Sets: (M[áa]s|Menos) de ([\d.]+)$/i, (m, a, n) => 'Sets: ' + MD(a) + ' ' + n],
    [/^(M[áa]s|Menos) de ([\d.]+)$/i, (m, a, n) => MD(a) + ' ' + n],
    [/^(M[áa]s|Menos) de ([\d.]+) (goles|puntos|carreras|tarjetas|c[óo]rners)$/i, (m, a, n, u) => MD(a) + ' ' + n + ' ' + ({ goles: 'goals', puntos: 'points', carreras: 'runs', tarjetas: 'cards', 'córners': 'corners', corners: 'corners' }[u.toLowerCase()])],
    [/^Remates: (M[áa]s|Menos) de ([\d.]+)$/i, (m, a, n) => 'Shots: ' + MD(a) + ' ' + n],
    [/^Remates Local: (M[áa]s|Menos) de ([\d.]+)$/i, (m, a, n) => 'Home shots: ' + MD(a) + ' ' + n],
    [/^Remates Visita: (M[áa]s|Menos) de ([\d.]+)$/i, (m, a, n) => 'Away shots: ' + MD(a) + ' ' + n],
    [/^acierta de verdad (\d+) ?%(.*)$/, (m, a, r) => 'really hits ' + a + '%' + r.replace('medido', 'measured')],
    [/^Paga (\d+) ?% m[áa]s que el precio justo \(Pinnacle\) en (.+)$/, (m, a, c) => 'Pays ' + a + '% over the fair price (Pinnacle) at ' + c],
    [/^Ambos anotan: S[íi]$/i, 'Both teams to score: Yes'], [/^Ambos anotan: No$/i, 'Both teams to score: No'],
    [/^Handicap: (.+)$/, 'Handicap: $1'],
    [/^(Goles|Puntos|Carreras|Juegos|Tiros|C[óo]rners) de (.+)$/, (m, q, e) => e + ' ' + ({ goles: 'goals', puntos: 'points', carreras: 'runs', juegos: 'games', tiros: 'shots', 'córners': 'corners', corners: 'corners' }[q.toLowerCase()])],
    [/^Marca (.+)$/, '$1 scores'],
    // marcador de NFL y periodos
    [/^(\d)\.º y gol$/, (m, a) => ordinal(a) + ' & Goal'],
    [/^(\d)\.º y (\d+)(.*)$/, (m, a, b, r) => ordinal(a) + ' & ' + b + r],
    [/^(\d)\.º C(.*)$/, (m, a, r) => 'Q' + a + r],
    [/^C(\d)$/, 'Q$1'], [/^C(\d) (.+)$/, 'Q$1 $2'], [/^P(\d) (.+)$/, 'P$1 $2'], [/^TE(\d*)$/, 'OT$1'],
    [/^(\d)\.º PER$/, (m, a) => ordinal(a) + ' PER'],
    [/^(\d)\.º tiempo$/, (m, a) => ordinal(a) + ' half'], [/^(\d)\.º set$/, (m, a) => ordinal(a) + ' set'], [/^(\d)\.er set$/, (m, a) => ordinal(a) + ' set'],
    [/^(\d)\.º(?: cuarto)?$/, (m, a) => ordinal(a)], [/^(\d)\.er$/, (m, a) => ordinal(a)], [/^(\d)\.º periodo$/, (m, a) => ordinal(a) + ' period'],
    [/^(\d)\.ª parte$/, (m, a) => ordinal(a) + ' half'],
    [/^hoy (.+)$/i, 'today $1'], [/^mañana (.+)$/i, 'tomorrow $1'], [/^ayer (.+)$/i, 'yesterday $1'],
    [/^Hoy ([\d:]+)/, 'Today $1'],
    [/^Sale(.*)$/, 'Out$1'],
    [/^Resaltados (.+) y (.+)\. Fuente: (.+)$/, 'Highlights $1 & $2. Source: $3'],
    [/^de \+(\d+)$/, 'of +$1'],
    [/^Sali[óo] (\d+) ?% en (.+)$/, (m, a, b) => 'Happened ' + a + '% in ' + b],
    [/^quedan (\d+)/, '$1 left'],
  ];
  function ordinal(a) { const n = Number(a); return n + (n === 1 ? 'st' : n === 2 ? 'nd' : n === 3 ? 'rd' : 'th'); }
  // las palabras sueltas que sí se traducen dentro de una frase; las demás sólo si son el texto completo (nunca «Plata» dentro de «Mar del Plata»)
  const SUELTAS = new Set(['goles', 'córners', 'tarjetas', 'puntos', 'carreras', 'partidos', 'cuota', 'combinada', 'combinadas', 'monedas', 'patas', 'picks', 'días', 'hoy', 'ayer', 'mañana', 'gol', 'tiros', 'empate', 'gratis', 'hasta', 'desde', 'antes', 'después', 'últimos', 'últimas', 'partido', 'probabilidad']);
  const SUELTAS_EN = { partido: 'game', hasta: 'until', desde: 'from', antes: 'before', 'después': 'after', 'últimos': 'last', 'últimas': 'last', probabilidad: 'probability', goles: 'goals', puntos: 'points', carreras: 'runs', gol: 'goal', hoy: 'today', ayer: 'yesterday', 'mañana': 'tomorrow', empate: 'draw', gratis: 'free', tiros: 'shots', 'días': 'days', partidos: 'games', patas: 'legs', cuota: 'odds', combinada: 'parlay', combinadas: 'parlays', monedas: 'coins', 'córners': 'corners', tarjetas: 'cards' };
  const esc = (x) => x.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  function preparar() {
    const fuente = window.I18N_EN || {};
    DICT = new Map();
    const llaves = [];
    for (const k of Object.keys(fuente)) {
      DICT.set(k, fuente[k]);
      if (!/#/.test(k) && k.length >= 4 && /\s/.test(k)) llaves.push(k);
    }
    for (const k of Object.keys(SUELTAS_EN)) if (!DICT.has(k)) DICT.set(k, SUELTAS_EN[k]);
    llaves.sort((a, b) => b.length - a.length);
    TROZOS = new Map(llaves.map((k) => [k.toLowerCase(), fuente[k]]));
    SUELTAS.forEach((w) => TROZOS.set(w, SUELTAS_EN[w] || fuente[w] || w));
    const alts = llaves.concat([...SUELTAS]).map(esc).join('|');
    TROZO_RE = new RegExp('(?<![\\p{L}\\p{N}])(?:' + alts + ')(?![\\p{L}\\p{N}])', 'giu');
  }
  const ajustaCaso = (orig, en) => {
    if (!en) return en;
    if (orig[0] === orig[0].toUpperCase() && orig[0] !== orig[0].toLowerCase()) return en[0].toUpperCase() + en.slice(1);
    if (/^(VIP|AI|Telegram|Stripe|Mercado|SharPicks|PA1|Q\d|P\d)\b/.test(en)) return en;
    return en[0].toLowerCase() + en.slice(1);
  };
  const MEMO = new Map();
  function nucleo(core) {
    if (DICT.has(core)) return DICT.get(core);
    // con números: «3 goles más» → «# goles más»
    if (/\d/.test(core)) {
      const nums = core.match(num), pl = core.replace(num, '#');
      if (DICT.has(pl)) { let i = 0; return DICT.get(pl).replace(/#/g, () => nums[i++]); }
    }
    for (const [re, en] of PATRONES) if (re.test(core)) return core.replace(re, en);
    const m = DICT.get(core.charAt(0).toUpperCase() + core.slice(1));
    if (m) return ajustaCaso(core, m);
    return null;
  }
  // dentro de una frase, lo que lleva números
  const DENTRO = [
    [/(\d+) c[óo]rners? m[áa]s/g, (m, n) => n + (n === '1' ? ' more corner' : ' more corners')],
    [/(\d+) goles? m[áa]s/g, (m, n) => n + (n === '1' ? ' more goal' : ' more goals')],
    [/sali[óo] (\d+)( ?%)?/g, 'happened $1$2'],
    [/confianza/g, 'confidence'],
    [/G = gan[óo] · E = empat[óo] · P = perdi[óo]/, 'W = won · D = drew · L = lost'],
    [/G = gan[óo] · P = perdi[óo]/, 'W = won · L = lost'],
    [/Las de (\d+) patas del (\d+) al (\d+)/g, 'The $1-leg ones from $2 to $3'],
    [/(\d+) de (\d+)/g, '$1 of $2'],
    [/Pick (Diamante|Platino|Plata|Oro|Cuota alta)/g, (m, x) => ({ Diamante: 'Diamond', Platino: 'Platinum', Plata: 'Silver', Oro: 'Gold', 'Cuota alta': 'High odds' }[x]) + ' pick'],
    [/^Diamante(?=:| )/, 'Diamond'], [/^Platino(?=:| )/, 'Platinum'], [/^Plata(?=:)/, 'Silver'], [/^Oro(?=:)/, 'Gold'], [/^Cuota alta(?=:)/, 'High odds'],
    [/Diamante$/, 'Diamond'], [/Platino$/, 'Platinum'],
  ];
  // lo que no está completo en el diccionario: «a · b» parte por parte y, si no, cada pedazo que se reconoce
  function armar(core) {
    const en = nucleo(core);
    if (en != null) return en;
    if (core.includes(' · ') && !/ = /.test(core)) return core.split(' · ').map(armar).join(' · ');
    let r = core;
    for (const [re, a] of DENTRO) r = r.replace(re, a);
    return r.replace(TROZO_RE, (m) => ajustaCaso(m, TROZOS.get(m.toLowerCase()) || m)).replace(/[¿¡]/g, '');
  }
  function traduceFrase(s) {
    if (!/[\p{L}]/u.test(s)) return s;
    let i = 0, j = s.length;
    const chars = Array.from(s);
    i = 0; j = chars.length;
    while (i < j && !LETRA.test(chars[i])) i++;
    while (j > i && !LETRA.test(chars[j - 1])) j--;
    const pre = chars.slice(0, i).join('').replace(/[¿¡]/g, ''), core = chars.slice(i, j).join(''), suf = chars.slice(j).join('');
    const en = armar(core);
    if (en === core && !/[«»¿¡]/.test(s)) return s;
    return (pre + en + suf).replace(/«/g, '“').replace(/»/g, '”');
  }
  function t(s) {
    if (!s) return s;
    if (!TROZO_RE) preparar();
    let r = MEMO.get(s);
    if (r === undefined) {
      if (MEMO.size > 20000) MEMO.clear();
      r = traduceFrase(s);
      MEMO.set(s, r);
      MEMO.set(r, r);
    }
    return r;
  }
  I18N.t = t;
  const ATTRS = ['title', 'placeholder', 'aria-label', 'alt'];
  const SALTA = new Set(['SCRIPT', 'STYLE', 'TEXTAREA', 'CODE']);
  function nodoTexto(n) {
    const p = n.parentNode;
    if (!p || SALTA.has(p.nodeName) || !n.nodeValue || !/[\p{L}]/u.test(n.nodeValue) || (p.closest && p.closest('[translate="no"]'))) return;
    const r = t(n.nodeValue);
    if (r !== n.nodeValue) n.nodeValue = r;
  }
  function atributos(e) {
    for (const a of ATTRS) {
      if (!e.hasAttribute(a)) continue;
      const v = e.getAttribute(a), r = t(v);
      if (r !== v) e.setAttribute(a, r);
    }
  }
  function arbol(raiz) {
    if (raiz.nodeType === 3) { nodoTexto(raiz); return; }
    if (raiz.nodeType !== 1 && raiz.nodeType !== 11) return;
    if (raiz.nodeType === 1) { if (SALTA.has(raiz.nodeName)) return; atributos(raiz); }
    const w = document.createTreeWalker(raiz, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
    let n;
    while ((n = w.nextNode())) { if (n.nodeType === 3) nodoTexto(n); else if (n.attributes.length) atributos(n); }
  }
  I18N.traducir = arbol;
  new MutationObserver((lista) => {
    for (const m of lista) {
      if (m.type === 'characterData') nodoTexto(m.target);
      else if (m.type === 'attributes') atributos(m.target);
      else m.addedNodes.forEach(arbol);
    }
  }).observe(document.documentElement, { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ATTRS });
  // ventanas nativas
  ['alert', 'confirm'].forEach((f) => { const o = window[f]; window[f] = (x) => o.call(window, t(String(x))); });
  document.addEventListener('DOMContentLoaded', () => { document.title = t(document.title); arbol(document.body); });
})();
