// v513 — PULSO SHARPICKS: la probabilidad EN VIVO, calibrada y medida, para cualquier marcador y minuto.
// Los modelos salen de pulso_modelo.json (D:/Claude/mediciones/pulso_exportar.py): 3.424 partidos de FotMob
// (goles) y 2.272 de ESPN (córners), medidos fuera de muestra en dos mitades por fecha; cada tramo enseña
// lo que de verdad salió. Medido también: el «ritmo» (xG, tiros de los últimos 15', momentum) NO mejora esta
// base, por eso no se usa. Gratis: «otro gol» y «2+ córners» en tramo; VIP o con monedas: todo, con % exacto,
// cuota justa y la probabilidad de tus picks en vivo.
(function () {
  'use strict';
  let M = null;
  fetch('pulso_modelo.json?v=1').then((r) => (r.ok ? r.json() : null)).then((j) => { M = j; }).catch(() => {});
  const TOPE = { gol: 0.85, gol2: 0.5, gol_l: 0.75, gol_v: 0.65 };   // arriba de esto lo medido no sostiene la cifra
  const NOMBRE = {
    gol: 'Cae otro gol', gol2: 'Caen 2 goles más', gol_l: 'Marca %L', gol_v: 'Marca %V',
    cor1: '1 córner más', cor2: '2 córners más', cor3: '3 córners más',
  };
  const GRATIS = { gol: 1, cor2: 1 };
  // hasta dónde se midió cada mercado: goles del descanso al 80', córners al 85' (más allá, el modelo inventa)
  const HASTA = { gol: 80, gol2: 80, gol_l: 80, gol_v: 80, cor1: 85, cor2: 85, cor3: 85 };

  function interp(x, xs, ys) {
    if (!xs.length) return x;
    if (x <= xs[0]) return ys[0];
    if (x >= xs[xs.length - 1]) return ys[ys.length - 1];
    let i = 1; while (xs[i] < x) i++;
    const t = (x - xs[i - 1]) / ((xs[i] - xs[i - 1]) || 1);
    return ys[i - 1] + t * (ys[i] - ys[i - 1]);
  }
  function prob(k, f) {
    const m = M && M.modelos[k]; if (!m || f.t > (HASTA[k] || 90)) return null;
    let z = m.inter;
    for (let i = 0; i < m.cols.length; i++) { const v = f[m.cols[i]]; if (v == null || isNaN(v)) return null; z += m.coef[i] * v; }
    const p = interp(1 / (1 + Math.exp(-z)), m.iso_x, m.iso_y);
    return Math.min(p, TOPE[k] || 0.97);
  }
  function tramo(k, p) {
    const m = M && M.modelos[k]; if (!m || p == null) return null;
    const t = m.tabla.find((x) => p >= x.desde && p <= x.hasta);
    return t && t.n >= 100 ? t : null;                            // con menos casos el «salió» no dice nada
  }
  const num = (s) => { const n = parseFloat(String(s == null ? '' : s).replace(',', '.')); return isNaN(n) ? null : n; };
  function minuto(v) {
    if (!v || v.fase !== 'in') return null;
    if (/HALF|Medio/i.test(v.est || '') || /Medio tiempo/i.test(v.detalle || '')) return 45.5;
    const m = String(v.reloj || '').match(/\d+/g);
    if (!m) return null;
    const t = Number(m[0]) + (m[1] ? Number(m[1]) / 100 : 0);
    return t >= 45 && t <= 92 ? t : null;                          // lo medido: del descanso al 90
  }

  // Lo que el modelo necesita, sólo con lo que la página tiene: minuto, marcador, córners y la media
  // de los últimos partidos de cada equipo (ctx.sl / ctx.sv), encogida igual que al medir.
  function rasgos(p, v, vs) {
    const t = minuto(v); if (t == null || !M) return null;
    const ctx = p.ctx || {}, sl = ctx.sl, sv = ctx.sv;
    const enc = (m, n) => ((Number(m) || M.G) * (Number(n) || 0) + M.G * M.K) / ((Number(n) || 0) + M.K);
    const rem = 94 - t, gh = v.g[0], ga = v.g[1];
    const f = { t, tot: gh + ga, dif: Math.abs(gh - ga), emp: gh === ga ? 1 : 0, sig: gh - ga };
    if (sl && sv) {
      const lh = (enc(sl.gf, sl.n) + enc(sv.gc, sv.n)) / 2 * rem / 94, la = (enc(sv.gf, sv.n) + enc(sl.gc, sl.n)) / 2 * rem / 94;
      f.lh = Math.log(Math.max(lh, 0.03)); f.la = Math.log(Math.max(la, 0.03)); f.ltot = Math.log(Math.max(lh + la, 0.05));
    }
    const c = ((vs && vs.stats) || {}).wonCorners;
    if (c && c.v && num(c.v[0]) != null && num(c.v[1]) != null) {
      f.c = num(c.v[0]) + num(c.v[1]); f.ritmo = f.c / t * rem;
    }
    return f;
  }

  function mercados(p, v, vs) {
    const f = rasgos(p, v, vs); if (!f) return [];
    const out = [];
    for (const k of ['gol', 'gol_l', 'gol_v', 'gol2', 'cor1', 'cor2', 'cor3']) {
      if (f.t > HASTA[k]) continue;
      const pr = prob(k, f); if (pr == null) continue;
      if (k === 'gol2' && pr < 0.15) continue;
      out.push({ k, p: pr, tramo: tramo(k, pr), justa: 1 / pr, gratis: !!GRATIS[k] });
    }
    return out;
  }

  // ¿Qué tan cerca está de verde un pick nuestro, ahora? Sólo para lo medido (goles y córners).
  function delPick(apuesta, p, v, vs) {
    const f = rasgos(p, v, vs); if (!f) return null;
    const a = String(apuesta || '');
    const no = (x) => (x == null ? null : 1 - x);                   // sin dato, sin cifra (1 - null daría 100 %)
    const [L, V] = p.partido.split(' vs ');
    let m = a.match(/^Goles: (Más|Menos) de ([\d.]+)$/);
    if (m) {
      const lim = Math.floor(Number(m[2])), falta = lim + 1 - f.tot;
      if (m[1] === 'Más') return falta <= 0 ? 1 : falta === 1 ? prob('gol', f) : falta === 2 ? prob('gol2', f) : null;
      const cabe = lim - f.tot; return cabe < 0 ? 0 : cabe === 0 ? no(prob('gol', f)) : cabe === 1 ? no(prob('gol2', f)) : null;
    }
    m = a.match(/^Goles (.+): (Más|Menos) de ([\d.]+)$/);
    if (m) {
      const k = m[1] === L ? 'gol_l' : m[1] === V ? 'gol_v' : null; if (!k) return null;
      const g = k === 'gol_l' ? v.g[0] : v.g[1], lim = Math.floor(Number(m[3]));
      if (m[2] === 'Más') { const falta = lim + 1 - g; return falta <= 0 ? 1 : falta === 1 ? prob(k, f) : null; }
      return g > lim ? 0 : g === lim ? no(prob(k, f)) : null;
    }
    m = a.match(/^Córners: (Más|Menos) de ([\d.]+)$/);
    if (m && f.c != null) {
      const lim = Math.floor(Number(m[2]));
      if (m[1] === 'Más') { const falta = lim + 1 - f.c; return falta <= 0 ? 1 : falta <= 3 ? prob('cor' + falta, f) : null; }
      const cabe = lim - f.c; return cabe < 0 ? 0 : cabe <= 2 ? no(prob('cor' + (cabe + 1), f)) : null;
    }
    return null;
  }

  window.PULSO = { listo: () => !!M, mercados, delPick, nombre: (k, L, V) => NOMBRE[k].replace('%L', L).replace('%V', V), modelo: () => M };
})();
