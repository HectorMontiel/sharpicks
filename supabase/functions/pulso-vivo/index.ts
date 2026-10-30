// v521 — EL PULSO EN VIVO EN LA NUBE (antes v520 corría en el runner del PC; el usuario: «el vigilante debe correr
// en la nube, no quiero tener mi compu encendida todo el tiempo»). pg_cron la llama cada 2 minutos (v521_pulso_nube.sql).
// En cada llamada, UNA vuelta:
//   1. los partidos de fútbol de hoy del sitio publicado (picks y sólo análisis) que van en el 2.º tiempo (ESPN),
//      con el Pulso calculado con el MISMO modelo y la MISMA cuenta que la página (web/pulso.js, pulso_historial.py);
//   2. aviso al canal VIP de Telegram de lo mejor si da 75 %+ (una vez por partido y mercado, telegram_enviados);
//   3. «IA + modelo»: Gemini elige SÓLO entre los mercados del Pulso (medible), una vez por partido y marcador
//      (pulso_ia), y se liquida al pitido.
// Las claves de Telegram y Gemini viven cifradas en Vault (las copia de GitHub el workflow «Claves a Supabase»).
// {"seco": true} calcula y devuelve sin escribir ni mandar; {"simular": {...}} prueba la cuenta con un partido dado.

const SITIO = 'https://sharpicksapp.com/';
const ESPN = 'https://site.api.espn.com/apis/site/v2/sports/';
// v522 — UMBRAL: 70 % (lo pidió el usuario; medido: 70-80 % salió 72-76 %) y que aún pague (justa ≥ 1,15). Es el aviso, la señal que se mide y lo que ve la IA
const AVISO_MIN = 0.70, SENAL_MIN = 0.70, CANDIDATO_MIN = 0.70, JUSTA_MIN = 1.15;
const TOPE: Record<string, number> = { gol: 0.85, gol2: 0.5, gol_l: 0.75, gol_v: 0.65 };
const TOPE_SF: Record<string, number> = { gol: 0.8, gol2: 0.45, gol_l: 0.7 };
const HASTA: Record<string, number> = { gol: 80, gol2: 80, gol_l: 80, gol_v: 80, cor1: 85, cor2: 85, cor3: 85 };
const DESDE: Record<string, number> = { gol: 55, gol2: 55, gol_l: 55, gol_v: 55, cor1: 46, cor2: 46, cor3: 46 };
const MERCADOS = ['gol', 'gol_l', 'gol_v', 'gol2', 'cor1', 'cor2', 'cor3'];
const NOMBRE: Record<string, string> = { gol: 'Cae otro gol', gol2: 'Caen 2 goles más', gol_l: 'Marca %L', gol_v: 'Marca %V',
  cor1: '1 córner más', cor2: '2 córners más', cor3: '3 córners más' };
const MODELOS_IA = ['gemini-flash-latest', 'gemini-flash-lite-latest'];
// v521 — ESPN y el sitio rechazan (403) lo que no dice ser un navegador: sin esto la función «no veía» el 2.º tiempo
const NAV = { 'User-Agent': 'Mozilla/5.0', Accept: 'application/json' };   // ni «Deno/…» ni «compatible; …bot»: ESPN da 403
const INSTRUCCION = 'Eres el analista en vivo de SharPicks. Te doy un partido de fútbol en el 2.º tiempo: minuto, marcador, ' +
  'estadísticas del momento y los mercados del Pulso con la probabilidad que da nuestro modelo (medido con miles de ' +
  'partidos) y lo que salió en el historial en ese tramo. Elige UNO de esos mercados: el que mejor combine probabilidad ' +
  'alta y lo que dicen las estadísticas del partido (quién ataca, tiros a puerta, córners, expulsados). No inventes ' +
  'mercados ni probabilidades. Todos los mercados que te doy todavía pagan algo; si dudas, el de probabilidad más alta. Escribe el motivo en español sencillo, MUY breve: 8 a 12 palabras, sin cifras ni emojis.';

type Dic = Record<string, any>;
let M: Dic | null = null, mDesde = 0;

// ---------- la misma cuenta que la página ----------
function interp(x: number, xs: number[], ys: number[]) {
  if (!xs.length) return x;
  if (x <= xs[0]) return ys[0];
  if (x >= xs[xs.length - 1]) return ys[ys.length - 1];
  let i = 1; while (xs[i] < x) i++;
  const t = (x - xs[i - 1]) / ((xs[i] - xs[i - 1]) || 1);
  return ys[i - 1] + t * (ys[i] - ys[i - 1]);
}
const claveModelo = (k: string, f: Dic) => (f.lh == null && TOPE_SF[k] && M!.modelos[k + '_sf'] ? k + '_sf' : k);
function prob(k: string, f: Dic): number | null {
  const kk = claveModelo(k, f), m = M!.modelos[kk];
  if (!m || f.t > (HASTA[k] || 90) || f.t < (DESDE[k] || 46)) return null;
  let z = m.inter;
  for (let i = 0; i < m.cols.length; i++) { const v = f[m.cols[i]]; if (v == null || isNaN(v)) return null; z += m.coef[i] * v; }
  return Math.min(interp(1 / (1 + Math.exp(-z)), m.iso_x, m.iso_y), (kk !== k ? TOPE_SF[k] : TOPE[k]) || 0.97);
}
function tramo(k: string, p: number) {
  const m = M!.modelos[k]; if (!m) return null;
  const t = m.tabla.find((x: Dic) => p >= x.desde && p <= x.hasta);
  return t && t.n >= 100 ? t : null;
}
function rasgos(ctx: Dic, t: number, gh: number, ga: number, c: number | null): Dic {
  const G = M!.G, K = M!.K, rem = 94 - t;
  const enc = (m: any, n: any) => ((Number(m) || G) * (Number(n) || 0) + G * K) / ((Number(n) || 0) + K);
  const f: Dic = { t, tot: gh + ga, dif: Math.abs(gh - ga), emp: gh === ga ? 1 : 0, sig: gh - ga, lrem: Math.log(Math.max(rem / 94, 0.01)) };
  const sl = (ctx || {}).sl, sv = (ctx || {}).sv;
  if (sl && sv) {
    const lh = (enc(sl.gf, sl.n) + enc(sv.gc, sv.n)) / 2 * rem / 94, la = (enc(sv.gf, sv.n) + enc(sl.gc, sl.n)) / 2 * rem / 94;
    f.lh = Math.log(Math.max(lh, 0.03)); f.la = Math.log(Math.max(la, 0.03)); f.ltot = Math.log(Math.max(lh + la, 0.05));
  }
  if (c != null) { f.c = c; f.ritmo = c / t * rem; }
  return f;
}
function mercados(f: Dic) {
  const out: Dic[] = [];
  for (const k of MERCADOS) {
    const p = prob(k, f); if (p == null || (k === 'gol2' && p < 0.15)) continue;
    out.push({ k, p, tramo: tramo(claveModelo(k, f), p) });
  }
  return out;
}
function mejor(ms: Dic[]) {
  const c = ms.filter((m) => m.tramo && 1 / m.p >= JUSTA_MIN && m.p >= 0.6);
  return c.length ? c.reduce((a, b) => (b.p > a.p ? b : a)) : null;
}
const lados = (p: Dic) => { const s = String(p.partido || ''), i = s.indexOf(' vs '); return i < 0 ? [s, ''] : [s.slice(0, i), s.slice(i + 4)]; };
const nombre = (k: string, p: Dic) => { const [L, V] = lados(p); return NOMBRE[k].replace('%L', L).replace('%V', V); };
// como web/fechas.js: «2026-10-29 23:00:00» es UTC; «2026-10-29T23:00:00+00:00» ya trae su zona (v522: antes daba fecha inválida)
const aFecha = (s: any) => {
  const t = String(s || '').trim().replace(' ', 'T'), zona = /[zZ]|[+-]\d{2}(?::?\d{2})?$/.test(t.slice(10));
  const d = new Date(t + (zona ? '' : 'Z'));
  return isNaN(d.getTime()) ? null : d;
};
// el día en CDMX (UTC−6, sin horario de verano desde 2022), como `diaDe` de la página
const dia = (p: Dic) => { const d = aFecha(p.inicio); return d ? new Date(d.getTime() - 6 * 3600e3).toISOString().slice(0, 10) : String(p.fecha || ''); };
// la misma clave que `clavePartido` de la página y que pulso_desbloqueos
const clavePartido = (p: Dic) => [p.deporte || '', lados(p).map((x) => x.toLowerCase().trim()).sort().join(' / '), dia(p)].join('|');

// ---------- ESPN ----------
function estadoVivo(d: Dic, girado: boolean) {
  const comp = (((d.header || {}).competitions) || [{}])[0], st = comp.status || {}, tp = st.type || {};
  const cs = comp.competitors || [];
  const h = cs.find((c: Dic) => c.homeAway === 'home') || {}, a = cs.find((c: Dic) => c.homeAway === 'away') || {};
  const idH = String((h.team || {}).id);
  let stats: Dic = {};
  for (const t of ((d.boxscore || {}).teams || [])) {
    const lado = String((t.team || {}).id) === idH ? 0 : 1;
    for (const s of t.statistics || []) { (stats[s.name] = stats[s.name] || [null, null])[lado] = s.displayValue; }
  }
  let g = [Number(h.score || 0), Number(a.score || 0)];
  if (girado) { g = [g[1], g[0]]; stats = Object.fromEntries(Object.entries(stats).map(([k, v]) => [k, [(v as any)[1], (v as any)[0]]])); }
  const m = String(st.displayClock || '').match(/(\d+)/);
  const num = (x: any) => (x != null && /^[\d.]+%?$/.test(String(x)) ? parseFloat(String(x)) : null);
  const cor = (stats.wonCorners || [null, null]).map(num);
  return { fase: tp.state, periodo: Number(st.period || 0), t: m ? Number(m[1]) : null, g, fin: !!tp.completed,
    c: cor[0] != null && cor[1] != null ? cor[0] + cor[1] : null, stats };
}
function liquidar(rec: Dic, gFin: number[], cFin: number | null): boolean | null {
  const [gh, ga] = String(rec.marcador).split('-').map(Number), k = rec.mercado;
  if (k.startsWith('cor')) return cFin == null || rec.corners == null ? null : cFin - rec.corners >= Number(k[3]);
  const r: Dic = { gol: gFin[0] + gFin[1] > gh + ga, gol2: gFin[0] + gFin[1] - gh - ga >= 2, gol_l: gFin[0] > gh, gol_v: gFin[1] > ga };
  return k in r ? r[k] : null;
}

// ---------- Supabase, Vault, Telegram y Gemini ----------
const SB = (Deno.env.get('SUPABASE_URL') || '').replace(/\/$/, '') + '/rest/v1/';
const KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') || '';
const H = { apikey: KEY, Authorization: 'Bearer ' + KEY, 'Content-Type': 'application/json' };
async function sbGet(tabla: string, q: string) { const r = await fetch(SB + tabla + '?' + q, { headers: H }); return r.ok ? r.json() : null; }
async function sbPost(tabla: string, filas: unknown) {
  return fetch(SB + tabla, { method: 'POST', headers: { ...H, Prefer: 'resolution=ignore-duplicates,return=minimal' }, body: JSON.stringify(filas) });
}
let SECRETOS: Dic | null = null, sDesde = 0;
async function secretos() {
  if (SECRETOS && SECRETOS.pulso_cron && Date.now() - sDesde < 600e3) return SECRETOS;   // se releen cada 10 min
  sDesde = Date.now();
  const r = await fetch(SB + 'rpc/leer_secretos_pulso', { method: 'POST', headers: H, body: '{}' });
  SECRETOS = Object.fromEntries(((r.ok ? await r.json() : []) as Dic[]).map((x) => [x.nombre, x.valor]));
  return SECRETOS;
}
const esc = (s: any) => String(s == null ? '' : s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' } as Dic)[c]);
// v526 — el usuario: «breves pero impactantes, más emojis, más vendedores». VIP: la jugada tal cual. Gratis: que el
// Pulso detectó algo, sin decir qué, para desbloquearlo con monedas o hacerse VIP.
const DEP_EMO: Dic = { 'Fútbol': '⚽' };
function textoAviso(p: Dic, e: Dic, m: Dic, rec: Dic | null) {
  const [L, V] = lados(p), t = m.tramo, ia = rec && rec.mercado && rec.mercado !== m.k ? rec : null;
  return [`⚡ <b>PULSO EN VIVO</b> · ${e.t}' 🔥`,
    `${DEP_EMO[p.deporte] || '⚽'} ${esc(L)} <b>${e.g[0]}-${e.g[1]}</b> ${esc(V)}`,
    `🎯 <b>${esc(nombre(m.k, p))}</b> · ${Math.round(100 * m.p)} %`,
    `📊 Salió ${Math.round(100 * t.fue)} % en el historial`]
    .concat(ia ? [`🤖 IA + modelo: <b>${esc(nombre(ia.mercado, p))}</b>`] : rec && rec.motivo ? [`🤖 <i>${esc(rec.motivo)}</i>`] : [])
    .concat(['👉 sharpicksapp.com']).join('\n');
}
function textoGancho(p: Dic, e: Dic, m: Dic) {
  const [L, V] = lados(p), piso = Math.floor(m.p * 10) * 10;
  return [`⚡ <b>EL PULSO DETECTÓ ALGO</b> 🔥`,
    `${DEP_EMO[p.deporte] || '⚽'} ${esc(L)} <b>${e.g[0]}-${e.g[1]}</b> ${esc(V)} · ${e.t}'`,
    `🎯 Una jugada con <b>${piso} %+</b> de probabilidad AHORA`,
    `🔓 Desbloquéala con 🪙 monedas 👉 sharpicksapp.com`,
    `💎 En el VIP te llega directo`].join('\n');
}
async function enviar(texto: string, canal: 'vip' | 'gratis' = 'vip') {
  const s = await secretos(), chat = canal === 'vip' ? s.TELEGRAM_CHAT_VIP : s.TELEGRAM_CHAT_GRATIS;
  if (!s.TELEGRAM_BOT_TOKEN || !chat) return false;
  const r = await fetch(`https://api.telegram.org/bot${s.TELEGRAM_BOT_TOKEN}/sendMessage`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chat_id: chat, text: texto, parse_mode: 'HTML', disable_web_page_preview: true }) });
  return r.ok;
}
async function preguntarIA(p: Dic, e: Dic, ms: Dic[]) {
  const s = await secretos();
  if (!s.GEMINI_API_KEY || !ms.length) return null;
  const claves = ms.map((m) => m.k);
  const datos = { partido: p.partido, liga: p.liga, minuto: e.t, marcador: `${e.g[0]}-${e.g[1]}`,
    estadisticas: Object.fromEntries(Object.entries(e.stats).filter(([n]) => ['totalShots', 'shotsOnTarget', 'wonCorners', 'possessionPct', 'redCards', 'saves', 'foulsCommitted'].includes(n))),
    mercados: ms.map((m) => ({ mercado: m.k, nombre: nombre(m.k, p), prob_modelo: Math.round(1000 * m.p) / 1000, salio_historial: m.tramo ? m.tramo.fue : null })) };
  const cuerpo = { systemInstruction: { parts: [{ text: INSTRUCCION }] }, contents: [{ role: 'user', parts: [{ text: JSON.stringify(datos) }] }],
    generationConfig: { temperature: 0.2, responseMimeType: 'application/json',
      responseSchema: { type: 'OBJECT', properties: { mercado: { type: 'STRING', enum: claves }, motivo: { type: 'STRING' } }, required: ['mercado', 'motivo'] } } };
  for (const modelo of MODELOS_IA) {
    try {
      const r = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${modelo}:generateContent?key=${s.GEMINI_API_KEY}`,
        { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(cuerpo), signal: AbortSignal.timeout(40000) });
      if (!r.ok) continue;
      const d = JSON.parse((await r.json()).candidates[0].content.parts[0].text);
      if (claves.includes(d.mercado)) return { mercado: d.mercado, motivo: String(d.motivo || '').slice(0, 200), modelo_ia: modelo };
    } catch (_) { /* siguiente modelo */ }
  }
  return null;
}

// ---------- v527 — avisos personales (quien sigue el partido o prendió «Pulso en vivo») ----------
let DESTINOS: Dic[] | null = null, dDesde = 0;
async function destinos() {
  if (DESTINOS && Date.now() - dDesde < 120e3) return DESTINOS;
  const r = await fetch(SB + 'rpc/alertas_destinos', { method: 'POST', headers: H, body: '{}' });
  DESTINOS = r.ok ? await r.json() : []; dDesde = Date.now();
  return DESTINOS!;
}
async function avisosPersonales(p: Dic, e: Dic, clave: string, nuevas: Dic[]) {
  const ds = (await destinos()).filter((d) => (d.tipo === 'partido' && d.valor === clave) || (d.tipo === 'pulso' && (p.deporte || 'Fútbol') === d.valor));
  if (!ds.length) return 0;
  const porUsuario = new Map<string, Dic>();
  for (const d of ds) porUsuario.set(d.usuario, d);
  const ids = [...porUsuario.keys()];
  const abiertos = new Set(((await sbGet('pulso_desbloqueos', `select=usuario&partido=eq.${encodeURIComponent(clave)}&usuario=in.(${ids.join(',')})`)) || []).map((x: Dic) => x.usuario));
  const ya = new Set(((await sbGet('telegram_enviados', `select=pick&canal=eq.dm&tipo=eq.pulso&pick=like.${encodeURIComponent('dm|*|' + clave + '|*')}&limit=5000`)) || []).map((x: Dic) => x.pick));
  const s = await secretos(), [L, V] = lados(p);
  let n = 0;
  for (const [uid, d] of porUsuario) {
    const xs = nuevas.filter((x) => !ya.has(`dm|${uid}|${clave}|${x.mercado}|${x.marcador}`));
    if (!xs.length) continue;
    const lleno = d.vip || abiertos.has(uid);
    const cab = `🔔 <b>Tu alerta</b> · ⚡ Pulso · ${e.t}'\n⚽ ${esc(L)} <b>${e.g[0]}-${e.g[1]}</b> ${esc(V)}`;
    const cuerpo = lleno
      ? xs.map((x) => `🎯 <b>${esc(nombre(x.mercado, p))}</b> · ${Math.round(100 * x.prob)} %`).join('\n')
      : `🎯 El Pulso detectó ${xs.length === 1 ? 'una jugada' : xs.length + ' jugadas'} de <b>${Math.floor(Math.max(...xs.map((x) => x.prob)) * 10) * 10} %+</b>\n🔓 Desbloquéala con 🪙 monedas o hazte 💎 VIP`;
    const r = await fetch(`https://api.telegram.org/bot${s.TELEGRAM_BOT_TOKEN}/sendMessage`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: d.chat, text: cab + '\n' + cuerpo + '\n👉 sharpicksapp.com', parse_mode: 'HTML', disable_web_page_preview: true }) });
    if (!r.ok) continue;
    await sbPost('telegram_enviados', xs.map((x) => ({ pick: `dm|${uid}|${clave}|${x.mercado}|${x.marcador}`, canal: 'dm', tipo: 'pulso',
      texto: nombre(x.mercado, p), partido: p.partido, inicio: String(p.inicio) })));
    n++;
  }
  return n;
}

// ---------- una vuelta ----------
async function partidos() {
  const out: Dic[] = [], vistos = new Set<string>();
  for (const [f, k] of [['datos/hoy.json', 'picks'], ['datos/analisis.json', 'analisis']]) {
    try {
      const d = await (await fetch(SITIO + f + '?t=' + Date.now(), { headers: NAV })).json();
      for (const p of d[k] || []) {
        if (p.deporte !== 'Fútbol' || !String(p.espn || '').includes(':')) continue;
        // v529 — UN partido, UNA vez: el mismo partido llega en los picks y en el análisis con nombres distintos
        // («Atlético Nacional vs Independiente Santa Fe» / «Atl. Nacional vs Santa Fe») y se avisaba dos veces.
        // Se une por el id de ESPN (el mismo evento); manda el de los picks (va primero).
        const c = 'espn:' + String(p.espn).split(':')[1]; if (vistos.has(c)) continue;
        vistos.add(c); out.push(p);
      }
    } catch (_) { /* sin ese archivo, esta vuelta sigue con el otro */ }
  }
  return out;
}
const enJuego = (p: Dic, ahora: number) => { const d = aFecha(p.inicio); return !!d && ahora >= d.getTime() - 5 * 60e3 && ahora <= d.getTime() + 165 * 60e3; };

async function vuelta(seco: boolean) {
  const ahora = Date.now(), desde = new Date(ahora - 30 * 3600e3).toISOString().slice(0, 10);
  const lista = (await partidos()).filter((p) => enJuego(p, ahora));
  const res: Dic = { en_juego: lista.length, segundo_tiempo: 0, avisos: 0, ia: 0, liquidadas: 0, lecturas: [] as Dic[], sin_espn: [] as unknown[], sin_ia: 0 };
  if (!lista.length) return res;
  const env = await sbGet('telegram_enviados', 'select=pick,canal,enviado&tipo=eq.pulso&enviado=gte.' + new Date(ahora - 2 * 864e5).toISOString() + '&limit=5000');
  const avisados = new Set<string>((env || []).map((x: Dic) => x.pick));
  let ultimoGancho = Math.max(0, ...(env || []).filter((x: Dic) => x.canal === 'gratis').map((x: Dic) => new Date(x.enviado).getTime()));
  const recs = new Map<string, Dic>();
  for (const x of (await sbGet('pulso_ia', 'select=*&fecha=gte.' + desde + '&limit=2000')) || []) recs.set(x.clave + '#' + x.marcador, x);
  const senales = new Map<string, Dic>();
  for (const x of (await sbGet('pulso_senales', 'select=*&fecha=gte.' + desde + '&limit=5000')) || []) senales.set([x.clave, x.mercado, x.marcador].join('#'), x);
  // v522 — calificar: ✅ en cuanto se cumple (goles y córners sólo suben), ❌ sólo al pitido
  const calificar = async (tabla: string, x: Dic, e: Dic) => {
    if (x.acierto != null) return;
    const ok = liquidar(x, e.g, e.c);
    if (ok == null || (!ok && !e.fin)) return;
    const cambio: Dic = { acierto: ok };
    if (tabla === 'pulso_senales' && ok) cambio.cumplida_min = e.fin ? null : e.t;
    x.acierto = ok;
    if (seco) return;
    const filtro = tabla === 'pulso_senales'
      ? `clave=eq.${encodeURIComponent(x.clave)}&mercado=eq.${x.mercado}&marcador=eq.${encodeURIComponent(x.marcador)}`
      : `clave=eq.${encodeURIComponent(x.clave)}&marcador=eq.${encodeURIComponent(x.marcador)}`;
    await fetch(SB + tabla + '?' + filtro, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify(cambio) });
    res.liquidadas++;
  };
  const estados = await Promise.all(lista.map(async (p) => {
    const [ruta, ev] = String(p.espn).split(':');
    try {
      const r = await fetch(ESPN + ruta + '/summary?event=' + ev, { headers: NAV, signal: AbortSignal.timeout(15000) });
      if (!r.ok) { res.sin_espn.push(r.status); return null; }
      return estadoVivo(await r.json(), !!p.girado);
    } catch (err) { res.sin_espn.push(String(err).slice(0, 60)); return null; }
  }));
  for (let i = 0; i < lista.length; i++) {
    const p = lista[i], e = estados[i]; if (!e) continue;
    const clave = clavePartido(p);
    if (e.fin || e.fase === 'in') {                                // lo apuntado de este partido: ¿ya se cumplió?
      for (const x of senales.values()) if (x.clave === clave) await calificar('pulso_senales', x, e);
      for (const x of recs.values()) if (x.clave === clave) await calificar('pulso_ia', x, e);
    }
    if (e.fin || e.fase !== 'in' || e.periodo !== 2 || e.t == null) continue;
    res.segundo_tiempo++;
    const ms = mercados(rasgos(p.ctx || {}, e.t, e.g[0], e.g[1], e.c)), m = mejor(ms);
    res.lecturas.push({ partido: p.partido, minuto: e.t, marcador: `${e.g[0]}-${e.g[1]}`, mejor: m && { k: m.k, p: Math.round(1000 * m.p) / 1000 } });
    const marc = `${e.g[0]}-${e.g[1]}`;
    // v522 — LA SEÑAL: la primera vez que un mercado cruza el 70 % y aún paga, con su minuto y sus córners
    const nuevas: Dic[] = [];
    for (const x of ms) {
      const k = [clave, x.k, marc].join('#');
      if (!x.tramo || x.p < SENAL_MIN || 1 / x.p < JUSTA_MIN || senales.has(k)) continue;
      // v524 — UNA ABIERTA POR MERCADO: si la de ese mercado sigue sin cumplirse, es la misma apuesta (el usuario vio
      // «3 córners más» al 48' y otra vez al 53' tras un gol; los córners no dependen del marcador). Otra, sólo al cumplirse.
      if ([...senales.values()].some((y) => y.clave === clave && y.mercado === x.k && y.acierto == null)) continue;
      const fila = { clave, partido: p.partido, fecha: dia(p), liga: p.liga || null, mercado: x.k, marcador: marc, minuto: e.t,
        corners: e.c, prob: Math.round(1000 * x.p) / 1000, ia: false };
      if (!seco) await sbPost('pulso_senales', fila);
      senales.set(k, fila); res.senales = (res.senales || 0) + 1; nuevas.push(fila);
    }
    if (nuevas.length && !seco) res.dm = (res.dm || 0) + await avisosPersonales(p, e, clave, nuevas);
    if (!m || m.p < CANDIDATO_MIN) continue;
    let rec = recs.get(clave + '#' + marc) || null;
    // v524 — cumplida la recomendación, la IA da otra con las probabilidades de ahora (la cumplida queda en sus señales)
    const cumplida = !!rec && (rec.acierto != null || liquidar(rec, e.g, e.c) === true);
    if (!rec || cumplida) {                                        // la IA: una por partido y marcador, y otra al cumplirse
      // sólo lo que aún paga (como «Mejor ahora»): un «1 córner más» al 96 % paga 1,04 y no sirve de recomendación
      const opciones = ms.filter((x) => x.tramo && x.p >= SENAL_MIN && 1 / x.p >= JUSTA_MIN), r = await preguntarIA(p, e, opciones);
      if (r) {
        const el = opciones.find((x) => x.k === r.mercado)!;
        rec = { ...r, clave, partido: p.partido, fecha: dia(p), marcador: marc, minuto: e.t, prob: Math.round(1000 * el.p) / 1000, corners: e.c };
        if (!seco) {
          await fetch(SB + 'pulso_ia', { method: 'POST', headers: { ...H, Prefer: 'resolution=merge-duplicates,return=minimal' },
            body: JSON.stringify({ ...rec, acierto: null }) });
          // y su señal queda marcada como la elegida por la IA (para medirla aparte)
          await fetch(SB + `pulso_senales?clave=eq.${encodeURIComponent(clave)}&mercado=eq.${r.mercado}&marcador=eq.${encodeURIComponent(marc)}`,
            { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ ia: true }) });
        }
        const sx = senales.get([clave, r.mercado, marc].join('#')); if (sx) sx.ia = true;
        recs.set(clave + '#' + marc, rec); res.ia++;
      } else res.sin_ia++;
    }
    // v526 — el gratis: el gancho (sin decir la jugada), uno por partido y a lo mucho uno cada 20 minutos
    const gancho = `pulso-gratis|${clave}`;
    if (m.p >= AVISO_MIN && !avisados.has(gancho) && ahora - ultimoGancho > 20 * 60e3) {
      if (seco) res.ganchos = (res.ganchos || 0) + 1;
      else if (await enviar(textoGancho(p, e, m), 'gratis')) {
        await sbPost('telegram_enviados', [{ pick: gancho, canal: 'gratis', tipo: 'pulso', texto: 'gancho del Pulso', partido: p.partido, inicio: String(p.inicio) }]);
        avisados.add(gancho); ultimoGancho = ahora; res.ganchos = (res.ganchos || 0) + 1;
      }
    }
    const pick = `pulso|${clave}|${m.k}`;
    if (m.p >= AVISO_MIN && !avisados.has(pick)) {                 // el aviso, una vez por partido y mercado
      if (seco) { res.avisos++; continue; }
      if (await enviar(textoAviso(p, e, m, rec))) {
        await sbPost('telegram_enviados', [{ pick, canal: 'vip', tipo: 'pulso', texto: nombre(m.k, p), partido: p.partido, inicio: String(p.inicio) }]);
        avisados.add(pick); res.avisos++;
      }
    }
  }
  return res;
}

Deno.serve(async (req) => {
  const s = await secretos();
  if (!s.pulso_cron || req.headers.get('x-pulso-clave') !== s.pulso_cron) return new Response('no', { status: 401 });
  try {
    if (!M || Date.now() - mDesde > 3600e3) { M = await (await fetch(SITIO + 'pulso_modelo.json?t=' + Date.now(), { headers: NAV })).json(); mDesde = Date.now(); }
    const body = await req.json().catch(() => ({}));
    if (body.simular) {                                            // la cuenta con un partido dado (verificación)
      const x = body.simular, e = estadoVivo(x.espn, !!x.girado);
      const f = rasgos(x.ctx || {}, e.t!, e.g[0], e.g[1], e.c);
      return Response.json({ estado: { t: e.t, g: e.g, c: e.c, periodo: e.periodo }, mercados: mercados(f), mejor: mejor(mercados(f)),
        clave: clavePartido(x.partido), liquidar: x.rec ? liquidar(x.rec, x.gfin, x.cfin) : null });
    }
    return Response.json(await vuelta(!!body.seco));
  } catch (err) {
    return Response.json({ error: String(err) }, { status: 500 });
  }
});
