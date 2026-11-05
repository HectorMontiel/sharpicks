// v573 — LAS CANCHAS DE LOS DEMÁS DEPORTES. El usuario, con la de fútbol lista: «armemos las demás con la misma lógica y un buen
// diseño». Misma lógica que v570: la cancha sobrevive al repintado, cada cuadro se calcula con el tiempo real, todos con inercia y
// tope de velocidad, y el balón vuela de verdad. El usuario: «los pases pueden ser falsos, pero si hay alguien en primera, sí está en
// primera». Es animación sólo el movimiento entre jugadas. Es REAL: quién está en juego, los corredores en su base, la línea de golpeo,
// el lugar de tiros y batazos, quién hace cada jugada y todo lo que cuenta. La fuente:
//   NHL y NBA  ESPN `plays[].coordinate`.        NFL  ESPN `drives`: yarda, intento y distancia.
//   Béisbol    statsapi.mlb.com (también invierno): bateador, cuenta, corredores y lugar del batazo.
//   Tenis      nadie da posiciones: peloteo animado con el marcador real.
// La de fútbol vive en app.js y no se toca. Todas las medidas van en una escala de 105 de ancho, como la de fútbol.
(function () {
  'use strict';
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const entre = (a, x, b) => Math.max(a, Math.min(b, x));
  const azar = (a, b) => a + Math.random() * (b - a);
  const CALMA = !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);
  const MOTORES = {}, VIVAS = {};
  const ALTO = { NHL: 44.6, NBA: 55.9, NFL: 46.7, BEIS: 84, Tenis: 58 };
  const familia = (d) => (d === 'MLB' || d === 'KBO' || d === 'Béisbol' ? 'BEIS' : d);
  const TIENE = (d) => !!ALTO[familia(d)];
  const SIM = {
    NHL: { v: 17, vP: 14, vE: 32, vPase: 72, rig: 4.4, T: [0.3, 1], robo: 0.13, pase: 0.74, sep: 3.2, corto: 5, largo: 30, muyLargo: 55, seguir: 0.72, seguirG: 0.05 },
    NBA: { v: 13, vP: 10, vE: 28, vPase: 55, rig: 4, T: [0.4, 1.2], robo: 0, pase: 0.72, sep: 3, corto: 6, largo: 26, muyLargo: 42 },
  };

  // ---------------------------------------------------------------- color
  const rgb = (h) => [1, 3, 5].map((i) => parseInt(String(h).slice(i, i + 2), 16));
  function tono(h) {
    const [r, g, b] = rgb(h), mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn;
    if (!mx || d / mx < 0.25) return null;
    return (mx === r ? ((g - b) / d + 6) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4) * 60;
  }
  const verdoso = (h) => { const t = tono(h); return t != null && t > 80 && t < 170; };
  function colores(v, fam) {
    const c = (v && v.colores) || { l: '#38bdf8', r: '#f472b6' };
    if (fam !== 'NFL' && fam !== 'BEIS') return [c.l, c.r];
    const f = (x, o) => (verdoso(x) ? (/^#f{6}$/i.test(o) ? '#38bdf8' : '#ffffff') : x);      // un equipo verde se pierde en el pasto
    return [f(c.l, c.r), f(c.r, c.l)];
  }

  // ---------------------------------------------------------------- en español: ESPN y la MLB lo dan en inglés
  const ES_NHL = [[/Goal/, 'Gol'], [/Face Off/, 'Saque de centro'], [/Shot/, 'Tiro a puerta'], [/Missed/, 'Tiro fuera'], [/Blocked/, 'Tiro bloqueado'], [/Hit/, 'Golpe'], [/Giveaway/, 'Pierde el disco'],
    [/Takeaway/, 'Roba el disco'], [/Stoppage/, 'Se detiene el juego'], [/Period Start/, 'Empieza el periodo'], [/Period End/, 'Termina el periodo'], [/End of Game/, 'Fin del partido']];
  const ES_NBA = [[/Free Throw/, 'Tiro libre'], [/Rebound/, 'Rebote'], [/Turnover/, 'Pérdida'], [/Steal/, 'Robo'], [/Foul/, 'Falta'], [/Timeout/, 'Tiempo muerto'], [/Jumpball/, 'Salto entre dos'],
    [/Dunk/, 'Clavada'], [/Layup/, 'Bandeja'], [/Three Point|3PT/, 'Triple'], [/Shot|Jumper|Hook|Tip/, 'Tiro'], [/End Period|End of/, 'Fin del cuarto'], [/Substitution/, 'Cambio']];
  const ES_NFL = [[/Touchdown/, 'Touchdown'], [/Rush/, 'Carrera'], [/Pass Reception/, 'Pase completo'], [/Pass Incompletion/, 'Pase incompleto'], [/Sack/, 'Captura'], [/Interception/, 'Intercepción'], [/Fumble/, 'Balón suelto'],
    [/Punt/, 'Despeje'], [/Kickoff/, 'Patada inicial'], [/Field Goal Good/, 'Gol de campo'], [/Field Goal/, 'Gol de campo'], [/Extra Point/, 'Punto extra'], [/Penalty/, 'Castigo'], [/Timeout/, 'Tiempo muerto'], [/End of/, 'Fin del cuarto']];
  const ES_MLB = [[/Home Run/, 'Jonrón'], [/Single/, 'Sencillo'], [/Double Play/, 'Doble matanza'], [/Double/, 'Doble'], [/Triple/, 'Triple'], [/Strikeout/, 'Ponche'], [/Walk/, 'Base por bolas'], [/Hit By Pitch/, 'Golpeado'],
    [/Groundout|Forceout|Grounded/, 'Rola, out'], [/Flyout|Sac Fly/, 'Elevado, out'], [/Lineout/, 'Línea, out'], [/Pop Out/, 'Globo, out'], [/Field Error/, 'Error'], [/Sac Bunt|Bunt/, 'Toque'], [/Fielders Choice/, 'Selección']];
  const ES_SERIE = [[/Touchdown/i, 'Touchdown'], [/Missed FG/i, 'Gol de campo fallado'], [/Field Goal|^FG/i, 'Gol de campo'], [/Punt/i, 'Despeje'], [/Fumble/i, 'Balón suelto'], [/Interception/i, 'Intercepción'],
    [/Downs/i, 'Perdió el balón'], [/End of Game/i, 'Fin del partido'], [/End of Half|Half/i, 'Fin de la mitad'], [/Safety/i, 'Safety']];
  const traduce = (tabla, t) => { const x = tabla.find(([r]) => r.test(String(t || ''))); return x ? x[1] : null; };
  const ICONO = { NHL: '🏒', NBA: '🏀', NFL: '🏈', BEIS: '⚾' };
  // «P.Mahomes pass short left to T.Kelce for 8 yards»: [el que la juega, el que la recibe]
  const nombresNfl = (t) => { const m = String(t || '').match(/\b[A-Z][a-zA-Z]{0,2}\.[A-Z][a-zA-Z'-]+/g) || []; const i = /\bpass\b/i.test(String(t)) && m[1] ? m[1] : null; return [m[0] ? m[0].replace('.', '. ') : '', i ? i.replace('.', '. ') : '']; };
  function etiqueta(fam, q, nombres) {
    const tabla = { NHL: ES_NHL, NBA: ES_NBA, NFL: ES_NFL, BEIS: ES_MLB }[fam];
    let t = traduce(tabla, q.t) || (fam === 'NHL' ? 'Falta' : fam === 'NBA' ? 'Jugada' : fam === 'NFL' ? 'Jugada' : 'Jugada');
    if (fam === 'NBA' && /Shot|Layup|Dunk|Jumper|Hook|Tip|Free Throw/.test(q.t) && !/Rebound/.test(q.t)) t = (q.anota ? 'Encesta: ' : 'Falla: ') + t.toLowerCase();
    const quien = q.part && q.part.length && nombres ? nombres[q.part[0]] : '';
    const delTexto = fam === 'NFL' ? (nombresNfl(q.txt)[1] || nombresNfl(q.txt)[0] || '') : '';
    return ICONO[fam] + ' <b>' + esc(t) + '</b>' + (quien || delTexto ? ' · ' + esc(quien || delTexto) : '') + (q.clk ? ' · ' + esc(q.clk) : '');
  }
  const bajaEs = (x) => String(x || '').replace(/(\d)(st|nd|rd|th) & Goal/, '$1.º y gol').replace(/(\d)(st|nd|rd|th) & (\d+)/, '$1.º y $3');

  // ---------------------------------------------------------------- los datos de ESPN
  const reloj = (x) => { const m = String(x || '').match(/(\d+):(\d+)/); return m ? Number(m[1]) + Number(m[2]) / 60 : 0; };
  function plantilla(d, n1) {
    const out = [[], []];
    for (const t of (d.boxscore || {}).players || []) {
      const lado = String((t.team || {}).id) === String(n1) ? 0 : 1;
      for (const g of t.statistics || []) {
        for (const a of g.athletes || []) {
          if (!a.athlete || out[lado].some((x) => x.id === a.athlete.id)) continue;
          out[lado].push({ id: a.athlete.id, n: a.athlete.jersey || '', nombre: a.athlete.shortName || a.athlete.displayName || '', grupo: g.name || g.label || '',
            pos: (a.athlete.position || {}).abbreviation || '', titular: !!a.starter });
        }
      }
    }
    return out;
  }
  function jugadasPista(d, dep, n1) {
    const crudas = (d.plays || []).filter((p) => p && p.id != null);
    const cs = (((d.header || {}).competitions || [])[0] || {}).competitors || [];
    const casa = String((cs.find((c) => c.homeAway === 'home') || { team: {} }).team.id) === String(n1);
    const lado = (p) => (String((p.team || {}).id) === String(n1) ? 0 : 1);
    const voltear = {};
    if (dep === 'NHL') {                      // en hockey cambian de lado cada periodo: aquí el 1.º siempre ataca a la derecha
      const suma = {};
      crudas.forEach((p) => {
        const c = p.coordinate, tipo = (p.type || {}).text || '';
        if (!c || !/Shot|Goal|Missed/.test(tipo) || !p.team) return;
        const per = (p.period || {}).number || 0;
        suma[per] = (suma[per] || 0) + (lado(p) === 0 ? c.x : -c.x);
      });
      let previo = false;
      for (let i = 1; i <= 8; i++) { voltear[i] = suma[i] ? suma[i] < 0 : (i > 1 ? !previo : false); previo = voltear[i]; }
    }
    const lugar = (p) => {
      const c = p.coordinate;
      if (!c || Math.abs(c.x) > 1000 || Math.abs(c.y) > 1000) return null;
      if (dep === 'NHL') {
        const f = voltear[(p.period || {}).number || 1] ? -1 : 1;
        return [((f * c.x + 100) / 200) * 105, ((f * c.y + 42.5) / 85) * ALTO.NHL];
      }
      // NBA: x de 0 a 50 a lo ancho; y, pies desde la línea de fondo de la canasta que se ataca (la defensa rebota en la suya)
      const L = lado(p), tipo = (p.type || {}).text || '', propia = /Defensive Rebound/.test(tipo), ataca = propia ? 1 - L : L;
      const pies = entre(0, c.y, 90), a = ataca === 0 ? 94 - pies : pies;
      return [(a / 94) * 105, ((ataca === 0 ? c.x : 50 - c.x) / 50) * ALTO.NBA];
    };
    return crudas.map((p) => {
      const per = (p.period || {}).number || 1, largo = dep === 'NHL' ? 20 : 12, clk = reloj((p.clock || {}).displayValue);
      const u = lugar(p);
      return { id: String(p.id), t: (p.type || {}).text || '', txt: p.shortDescription || p.text || '', lado: p.team ? lado(p) : null, per, clk: (p.clock || {}).displayValue || '',
        min: (Math.min(per - 1, 4) * largo) + Math.max(0, largo - clk), x: u && u[0], y: u && u[1], anota: !!p.scoringPlay, val: Number(p.scoreValue || 0),
        dif: casa === false ? Number(p.awayScore || 0) - Number(p.homeScore || 0) : Number(p.homeScore || 0) - Number(p.awayScore || 0), part: (p.participants || []).map((z) => String((z.athlete || {}).id || '')) };
    });
  }
  function jugadasNfl(d, n1) {
    const dr = d.drives || {}, previas = dr.previous || [], todos = previas.concat(dr.current ? [dr.current] : []);
    const out = [], series = [];
    todos.forEach((s) => {
      const L = String((s.team || {}).id) === String(n1) ? 0 : 1;
      if (s.id !== (dr.current || {}).id) series.push({ lado: L, yds: Number(s.yards || 0), res: s.displayResult || s.result || '', anota: !!s.isScore });
      (s.plays || []).forEach((p) => {
        const fin = p.end || {}, ini = p.start || {};
        out.push({ id: String(p.id), t: (p.type || {}).text || '', txt: p.shortText || p.text || '', lado: L, anota: !!p.scoringPlay, per: (p.period || {}).number || 1, clk: (p.clock || {}).displayValue || '',
          ydI: ini.yardsToEndzone, ydF: fin.yardsToEndzone, down: fin.down, dist: fin.distance, baja: fin.shortDownDistanceText || fin.downDistanceText || '', pos: fin.possessionText || '',
          equipoFin: String((fin.team || {}).id || '') === String(n1) ? 0 : 1 });
      });
    });
    const lideres = [{}, {}];
    for (const t of d.leaders || []) {
      const L = String((t.team || {}).id) === String(n1) ? 0 : 1;
      for (const g of t.leaders || []) {
        const a = ((g.leaders || [])[0] || {}).athlete || {};
        const clave = /passing/i.test(g.name || '') ? 'QB' : /rushing/i.test(g.name || '') ? 'RB' : /receiving/i.test(g.name || '') ? 'WR' : null;
        if (clave) lideres[L][clave] = { nombre: a.shortName || a.displayName || '', n: a.jersey || '' };
      }
    }
    return { jugadas: out, series, lideres };
  }
  // NHL: ESPN dice quién está en el hielo ahora mismo
  function enHielo(d, n1) {
    const out = [[], []];
    for (const t of d.onIce || []) {
      const L = String(t.teamId) === String(n1) ? 0 : 1;
      out[L] = (t.entries || []).map((x) => String(x.athleteid || '')).filter(Boolean);
    }
    return out;
  }
  // NBA: no lo dice; se lee de la última jugada hacia atrás (quien sale en un cambio ya no cuenta) y se completa con los titulares
  function enCancha(js, pl) {
    const out = [[], []], fuera = [new Set(), new Set()];
    for (let i = js.length - 1; i >= 0 && (out[0].length < 5 || out[1].length < 5); i--) {
      const q = js[i]; if (q.lado == null) continue;
      const L = q.lado, a = q.part || [];
      if (/Substitution/.test(q.t)) {
        if (a[0] && out[L].length < 5 && !fuera[L].has(a[0]) && !out[L].includes(a[0])) out[L].push(a[0]);
        if (a[1] && !out[L].includes(a[1])) fuera[L].add(a[1]);
        continue;
      }
      a.forEach((id) => { if (id && out[L].length < 5 && !fuera[L].has(id) && !out[L].includes(id) && pl[L].some((x) => String(x.id) === id)) out[L].push(id); });
    }
    [0, 1].forEach((L) => pl[L].filter((a) => a.titular).concat(pl[L]).forEach((a) => { const id = String(a.id); if (out[L].length < 5 && !fuera[L].has(id) && !out[L].includes(id)) out[L].push(id); }));
    return out;
  }
  // lo que app.js guarda en el «en vivo» de cada partido (nos1 = el primero de NUESTRO «A vs B»)
  function leer(dep, d, n1) {
    try {
      if (dep === 'NHL' || dep === 'NBA') {
        const pl = plantilla(d, n1), nombres = {}, numeros = {};
        pl.flat().forEach((a) => { nombres[String(a.id)] = a.nombre; numeros[String(a.id)] = a.n; });
        const jugadas = jugadasPista(d, dep, n1);
        return { jugadas, plantilla: pl, nombres, numeros, enJuego: dep === 'NHL' ? enHielo(d, n1) : enCancha(jugadas, pl) };
      }
      if (dep === 'NFL') return jugadasNfl(d, n1);
    } catch (e) { /* una respuesta rara no tumba la página */ }
    return null;
  }

  // ---------------------------------------------------------------- béisbol: statsapi.mlb.com
  const API_MLB = 'https://statsapi.mlb.com/api/';
  const palabras = (x) => new Set(String(x || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().match(/[a-z0-9]+/g) || []);
  const SOBRA = new Set(['de', 'del', 'la', 'las', 'los', 'el']);
  function mismoEquipo(a, b) {
    const x = [...palabras(a)].filter((w) => !SOBRA.has(w)), y = [...palabras(b)].filter((w) => !SOBRA.has(w));
    if (!x.length || !y.length) return false;
    return x.every((w) => y.includes(w)) || y.every((w) => x.includes(w));
  }
  const BEIS = {}; let calMem = { t: 0, juegos: [] };
  async function calendario() {
    if (Date.now() - calMem.t < 10 * 60e3 && calMem.juegos.length) return calMem.juegos;
    const hoy = new Date(), f = (d) => d.toISOString().slice(0, 10), ayer = new Date(hoy - 864e5), man = new Date(+hoy + 864e5);
    const juegos = [];
    for (const s of [17, 1]) {
      try {
        const r = await fetch(API_MLB + 'v1/schedule?sportId=' + s + '&startDate=' + f(ayer) + '&endDate=' + f(man));
        if (r.ok) (await r.json()).dates.forEach((x) => x.games.forEach((g) => juegos.push({ pk: g.gamePk, h: g.teams.home.team.name, a: g.teams.away.team.name, ini: new Date(g.gameDate).getTime() })));
      } catch (e) { /* sin red: la cancha sigue con su animación */ }
    }
    calMem = { t: Date.now(), juegos };
    return juegos;
  }
  async function pedirBeisbol(k, p) {
    const b = BEIS[k] = BEIS[k] || { t: 0 };
    if (Date.now() - b.t < 20000 || b.pidiendo) return;
    b.pidiendo = true; b.t = Date.now();
    try {
      const [L, V] = String(p.partido || '').split(' vs ');
      const ini = new Date(String(p.inicio).replace(' ', 'T') + 'Z').getTime();
      if (b.pk == null) {
        const g = (await calendario()).find((x) => Math.abs(x.ini - ini) < 6 * 3600e3 && ((mismoEquipo(L, x.h) && mismoEquipo(V, x.a)) || (mismoEquipo(L, x.a) && mismoEquipo(V, x.h))));
        if (g) { b.pk = g.pk; b.girado = mismoEquipo(L, g.a); }
      }
      if (b.pk != null) {
        const r = await fetch(API_MLB + 'v1.1/game/' + b.pk + '/feed/live');
        if (r.ok) b.d = leerBeisbol(await r.json(), b.girado);
      }
    } catch (e) { /* sigue con lo que tenía */ }
    b.pidiendo = false;
  }
  function leerBeisbol(f, girado) {
    const ld = f.liveData || {}, ls = ld.linescore || {}, of = ls.offense || {}, de = ls.defense || {}, pl = (ld.plays || {}).allPlays || [];
    const corto = (x) => { const n = String((x || {}).fullName || ''); const s = n.split(' '); return s.length > 1 ? s[0][0] + '. ' + s.slice(1).join(' ') : n; };
    const jugadas = pl.filter((p) => (p.about || {}).isComplete).map((p) => {
      const ev = (p.playEvents || []).filter((e) => e.hitData && e.hitData.coordinates).pop(), hit = ev && ev.hitData.coordinates;
      return { id: String((p.about || {}).atBatIndex), t: (p.result || {}).event || '', txt: (p.result || {}).description || '', anota: !!(p.about || {}).isScoringPlay || Number((p.result || {}).rbi || 0) > 0,
        arriba: !!(p.about || {}).isTopInning, ent: (p.about || {}).inning, hx: hit && hit.coordX, hy: hit && hit.coordY, tray: ev && ev.hitData.trajectory };
    });
    // en el orden de NUESTRO «A vs B»: `home` y `away` de la fuente pueden venir al revés
    const fila = (e, l) => (e[l] || {});      // arriba de la entrada batea el visitante
    return { jugadas, entrada: ls.currentInning, arriba: !!ls.isTopInning, bolas: ls.balls || 0, strikes: ls.strikes || 0, outs: ls.outs || 0, bateador: corto(of.batter), lanzador: corto(de.pitcher),
      en1: !!of.first, en2: !!of.second, en3: !!of.third, ids: [(of.first || {}).id || null, (of.second || {}).id || null, (of.third || {}).id || null],
      nombres: { r1: corto(of.first), r2: corto(of.second), r3: corto(of.third),  c1b: corto(de.first), c2b: corto(de.second), c3b: corto(de.third), ss: corto(de.shortstop), lf: corto(de.left), cf: corto(de.center), rf: corto(de.right), ca: corto(de.catcher) },
      entradas: (ls.innings || []).map((e) => { const a = fila(e, 'away'), h = fila(e, 'home'); return girado ? [a.runs, h.runs] : [h.runs, a.runs]; }),
      tot: (() => { const t = ls.teams || {}, a = t.away || {}, h = t.home || {}; const x = [a.runs, a.hits, a.errors], y = [h.runs, h.hits, h.errors]; return girado ? [x, y] : [y, x]; })(),
      batea: girado ? (ls.isTopInning ? 0 : 1) : (ls.isTopInning ? 1 : 0), girado: !!girado };
  }

  // ---------------------------------------------------------------- los terrenos
  const FONDO = {
    NHL: () => '<defs><linearGradient id="p-hielo" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#16324f"/><stop offset="1" stop-color="#0b1f35"/></linearGradient>' +
      '<radialGradient id="p-hielo2" cx="50%" cy="50%" r="70%"><stop offset="0" stop-color="rgba(170,220,255,.2)"/><stop offset="1" stop-color="rgba(170,220,255,0)"/></radialGradient></defs>' +
      '<rect width="105" height="44.6" rx="10" fill="url(#p-hielo)"/><rect width="105" height="44.6" rx="10" fill="url(#p-hielo2)"/>' +
      '<g class="p-nhl"><rect class="borde" x=".5" y=".5" width="104" height="43.6" rx="9.6"/>' +
      '<line class="gol" x1="5.8" y1="2" x2="5.8" y2="42.6"/><line class="gol" x1="99.2" y1="2" x2="99.2" y2="42.6"/>' +
      '<line class="azul" x1="38.4" y1=".5" x2="38.4" y2="44.1"/><line class="azul" x1="66.6" y1=".5" x2="66.6" y2="44.1"/><line class="rojo" x1="52.5" y1=".5" x2="52.5" y2="44.1"/>' +
      '<circle class="azulc" cx="52.5" cy="22.3" r="7.9"/><circle class="pt azulp" cx="52.5" cy="22.3" r=".6"/>' +
      [[16.2, 11.3], [16.2, 33.3], [88.8, 11.3], [88.8, 33.3]].map(([x, y]) => '<circle class="rojoc" cx="' + x + '" cy="' + y + '" r="7.9"/><circle class="pt" cx="' + x + '" cy="' + y + '" r=".6"/>').join('') +
      [[42, 11.3], [42, 33.3], [63, 11.3], [63, 33.3]].map(([x, y]) => '<circle class="pt" cx="' + x + '" cy="' + y + '" r=".55"/>').join('') +
      '<path class="area" d="M5.8 18.6 h2 a3.7 3.7 0 0 1 0 7.4 h-2z"/><path class="area" d="M99.2 18.6 h-2 a3.7 3.7 0 0 0 0 7.4 h2z"/>' +
      '<rect class="red" x="3.6" y="20.6" width="2.2" height="3.4"/><rect class="red" x="99.2" y="20.6" width="2.2" height="3.4"/></g>',
    NBA: () => '<defs><linearGradient id="p-duela" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#7d5428"/><stop offset=".5" stop-color="#a6743a"/><stop offset="1" stop-color="#7d5428"/></linearGradient>' +
      '<pattern id="p-tablas" width="7" height="3.2" patternUnits="userSpaceOnUse"><rect width="7" height="3.2" fill="rgba(0,0,0,0)"/><path d="M0 0H7M0 1.6H3.5M3.5 3.2H7" stroke="rgba(40,20,0,.13)" stroke-width=".12"/></pattern></defs>' +
      '<rect width="105" height="55.9" rx="2.5" fill="url(#p-duela)"/><rect width="105" height="55.9" rx="2.5" fill="url(#p-tablas)"/>' +
      '<g class="p-nba"><rect class="pinta l" x=".6" y="19.4" width="21.3" height="17.1"/><rect class="pinta r" x="83.1" y="19.4" width="21.3" height="17.1"/>' +
      '<rect class="lin" x=".6" y=".6" width="103.8" height="54.7"/><line class="lin" x1="52.5" y1=".6" x2="52.5" y2="55.3"/><circle class="lin" cx="52.5" cy="27.95" r="6.7"/>' +
      '<rect class="lin" x=".6" y="19.4" width="21.3" height="17.1"/><rect class="lin" x="83.1" y="19.4" width="21.3" height="17.1"/>' +
      '<circle class="lin" cx="21.9" cy="27.95" r="6.7"/><circle class="lin" cx="83.1" cy="27.95" r="6.7"/>' +
      '<path class="lin" d="M.6 3.4H16 A26.6 26.6 0 0 1 16 52.5 H.6"/><path class="lin" d="M104.4 3.4H89 A26.6 26.6 0 0 0 89 52.5 H104.4"/>' +
      '<line class="tablero" x1="4.8" y1="24.5" x2="4.8" y2="31.4"/><line class="tablero" x1="100.2" y1="24.5" x2="100.2" y2="31.4"/>' +
      '<circle class="aro-c" cx="6.6" cy="27.95" r="1"/><circle class="aro-c" cx="98.4" cy="27.95" r="1"/></g>',
    NFL: (e) => '<defs><linearGradient id="p-pasto" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1c7a45"/><stop offset="1" stop-color="#11532e"/></linearGradient></defs>' +
      '<rect width="105" height="46.7" rx="2" fill="url(#p-pasto)"/>' +
      Array.from({ length: 10 }, (_, i) => (i % 2 ? '' : '<rect x="' + (8.75 + i * 8.75) + '" y="0" width="8.75" height="46.7" fill="rgba(255,255,255,.035)"/>')).join('') +
      '<rect x="0" y="0" width="8.75" height="46.7" rx="2" fill="' + e[0] + '" opacity=".78"/><rect x="96.25" y="0" width="8.75" height="46.7" rx="2" fill="' + e[1] + '" opacity=".78"/>' +
      '<g class="p-nfl">' + Array.from({ length: 21 }, (_, i) => { const x = 8.75 + i * 4.375; return '<line class="yd' + (i % 2 ? ' fina' : '') + '" x1="' + x + '" y1=".5" x2="' + x + '" y2="46.2"/>'; }).join('') +
      [10, 20, 30, 40, 50, 40, 30, 20, 10].map((n, i) => { const x = 17.5 + i * 8.75; return '<text class="num" x="' + x + '" y="7.2">' + n + '</text><text class="num" x="' + x + '" y="42">' + n + '</text>'; }).join('') +
      '<rect class="borde" x=".4" y=".4" width="104.2" height="45.9" rx="1.6"/></g>',
    BEIS: () => '<defs><radialGradient id="p-jardin" cx="50%" cy="96%" r="100%"><stop offset="0" stop-color="#208a4e"/><stop offset="1" stop-color="#11552f"/></radialGradient>' +
      '<linearGradient id="p-tierra" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#b57a44"/><stop offset="1" stop-color="#8f5c2f"/></linearGradient>' +
      '<clipPath id="p-fan"><path d="M52.5 78 L2 27 A71 71 0 0 1 103 27 Z"/></clipPath></defs>' +
      '<rect width="105" height="84" rx="3" fill="#0b1f18"/><path d="M52.5 78 L2 27 A71 71 0 0 1 103 27 Z" fill="url(#p-jardin)"/>' +
      '<path d="M52.5 78 L2 27 A71 71 0 0 1 103 27 Z" fill="none" stroke="#b57a44" stroke-width="2.4" opacity=".8"/>' +
      '<g clip-path="url(#p-fan)">' + Array.from({ length: 6 }, (_, i) => '<path d="M' + (8 + i * 16) + ' 8 L52.5 78" stroke="rgba(255,255,255,.035)" stroke-width="7"/>').join('') + '</g>' +
      '<path d="M52.5 80 L27 54.5 A36 36 0 0 1 78 54.5 Z" fill="url(#p-tierra)"/><path d="M52.5 69 L38 54.5 L52.5 40 L67 54.5 Z" fill="#1d7c46"/>' +
      '<g class="p-beis"><line x1="52.5" y1="78" x2="2" y2="27"/><line x1="52.5" y1="78" x2="103" y2="27"/><path d="M52.5 69 L38 54.5 L52.5 40 L67 54.5 Z"/></g>' +
      '<circle cx="52.5" cy="56" r="2.6" fill="#b57a44"/><rect x="51.4" y="55.6" width="2.2" height=".5" fill="#fff"/>' +
      '<circle cx="52.5" cy="72" r="5" fill="#a56e3a"/>' +
      [[67, 54.5], [52.5, 40], [38, 54.5]].map(([x, y], i) => '<rect class="base" data-base="' + (i + 1) + '" x="' + (x - 1.1) + '" y="' + (y - 1.1) + '" width="2.2" height="2.2" transform="rotate(45 ' + x + ' ' + y + ')" fill="#fff"/>').join('') +
      '<path d="M51.3 71.2h2.4v1.2l-1.2 1.2-1.2-1.2z" fill="#fff"/>',
    Tenis: () => '<defs><linearGradient id="p-dura" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2563a8"/><stop offset="1" stop-color="#1b4b85"/></linearGradient></defs>' +
      '<rect width="105" height="58" rx="3" fill="#166a57"/><rect x="11" y="6" width="83" height="46" fill="url(#p-dura)"/>' +
      '<g class="p-tenis"><rect x="11" y="6" width="83" height="46"/><line x1="11" y1="11.2" x2="94" y2="11.2"/><line x1="11" y1="46.8" x2="94" y2="46.8"/>' +
      '<line x1="29.5" y1="11.2" x2="29.5" y2="46.8"/><line x1="75.5" y1="11.2" x2="75.5" y2="46.8"/><line x1="29.5" y1="29" x2="75.5" y2="29"/>' +
      '<line x1="11" y1="29" x2="12.5" y2="29"/><line x1="92.5" y1="29" x2="94" y2="29"/><line class="red" x1="52.5" y1="4" x2="52.5" y2="54"/></g>',
  };

  // ---------------------------------------------------------------- los jugadores de cada deporte
  const fHockey = [['G', 4, 22.3], ['D', 26, 12], ['D', 26, 32.6], ['C', 46, 22.3], ['A', 54, 7], ['A', 54, 37.6]];
  const fBasket = [['PG', 18, 27.9], ['SG', 30, 10], ['SF', 30, 46], ['PF', 40, 17], ['C', 40, 39]];
  function equipos(dep, v, datos) {
    const lista = [];
    const pla = (datos && datos.plantilla) || [[], []];
    const pon = (lado, i, x, y, n, nombre, rol, id) => lista.push({ key: lado + '|' + i, lado, n: n || '', nombre: nombre || '', rol, x, y, id: id || '' });
    const enJ = (datos && datos.enJuego) || [[], []], por = (L, id) => pla[L].find((a) => String(a.id) === String(id));
    if (dep === 'NHL') {
      [0, 1].forEach((L) => {
        const g = pla[L].filter((a) => /goal/i.test(a.grupo) || a.pos === 'G'), de = pla[L].filter((a) => /defen/i.test(a.grupo) || a.pos === 'D'), fw = pla[L].filter((a) => /forward/i.test(a.grupo) || /^(C|LW|RW|F)$/.test(a.pos));
        // los que están en el hielo ahora; si ESPN no lo trae, los que más juegan
        const hielo = enJ[L].map((id) => por(L, id)).filter(Boolean), es = (r) => (a) => r.test(a.grupo) || r.test(a.pos);
        const hG = hielo.filter(es(/goal|^G$/i)), hD = hielo.filter(es(/defen|^D$/i)), hF = hielo.filter((a) => !hG.includes(a) && !hD.includes(a));
        const q = hielo.length >= 5 ? [hG[0] || g[0], hD[0] || hF[3], hD[1] || hF[4], hF[0], hF[1], hF[2]] : [g[0], de[0], de[1], fw[0], fw[1], fw[2]];
        fHockey.forEach(([rol, x, y], i) => pon(L, i, L === 0 ? x : 105 - x, y, q[i] && q[i].n, q[i] && q[i].nombre, rol, q[i] && q[i].id));
      });
    } else if (dep === 'NBA') {
      [0, 1].forEach((L) => {
        const cinco = enJ[L].map((id) => por(L, id)).filter(Boolean), tit = cinco.length >= 5 ? cinco : pla[L].filter((a) => a.titular).concat(pla[L].filter((a) => !a.titular));
        fBasket.forEach(([rol, x, y], i) => pon(L, i, L === 0 ? x : 105 - x, y, tit[i] && tit[i].n, tit[i] && tit[i].nombre, rol, tit[i] && tit[i].id));
      });
    } else if (dep === 'NFL') {
      const ld = (datos && datos.lideres) || [{}, {}];
      [0, 1].forEach((L) => {
        for (let i = 0; i < 11; i++) {
          const rol = ['QB', 'RB', 'WR', 'WR', 'TE', 'OL', 'OL', 'OL', 'OL', 'OL', 'WR'][i], q = i === 0 ? ld[L].QB : i === 1 ? ld[L].RB : i === 2 ? ld[L].WR : null;
          pon(L, i, L === 0 ? 40 : 65, 6 + i * 3.4, q && q.n, q && q.nombre, rol);
        }
      });
    } else if (familia(dep) === 'BEIS') {
      [['ca', 52.5, 75.5], ['p', 52.5, 56], ['c1b', 66, 50], ['c2b', 59, 42], ['ss', 45, 42], ['c3b', 39, 50], ['lf', 28, 22], ['cf', 52.5, 13], ['rf', 77, 22]].forEach(([rol, x, y], i) => pon(1, i, x, y, '', '', rol));
      ['bat', 'r1', 'r2', 'r3'].forEach((rol, i) => pon(0, 20 + i, rol === 'bat' ? 49.8 : -5, rol === 'bat' ? 72.5 : -5, '', '', rol));
    } else {
      const L = String((v && v.nombres && v.nombres[0]) || ''), V = String((v && v.nombres && v.nombres[1]) || '');
      pon(0, 0, 9, 29, '', L, 'J'); pon(1, 0, 96, 29, '', V, 'J');
    }
    return lista;
  }

  // ---------------------------------------------------------------- el HTML
  function barraPresion(q) {
    const fin = q.fin, xm = (m) => 100 * m / fin, W = 100 / fin;
    const tope = Math.max(1, ...q.val.map(Math.abs));
    return q.val.map((x, i) => { const h = 11 * Math.abs(x) / tope; return h < 0.2 ? '' : '<rect x="' + (xm(i) - W * 0.38).toFixed(2) + '" y="' + (x > 0 ? 12 - h : 12).toFixed(2) + '" width="' + Math.max(0.3, W * 0.76).toFixed(2) + '" height="' + h.toFixed(2) + '" fill="' + (x > 0 ? q.c[0] : q.c[1]) + '"/>'; }).join('') +
      q.cortes.map((m) => '<line x1="' + xm(m).toFixed(2) + '" y1="1" x2="' + xm(m).toFixed(2) + '" y2="23" class="eje medio"/>').join('') + '<line x1="0" y1="12" x2="100" y2="12" class="eje"/>';
  }
  function tira(dep, v, datos, c, L, V, k) {
    if (dep === 'NHL' || dep === 'NBA') {
      const js = (datos && datos.jugadas) || [];
      if (!js.length) return '';
      const per = dep === 'NHL' ? 20 : 12, fin = Math.max(per * (dep === 'NHL' ? 3 : 4), Math.ceil(js[js.length - 1].min)), val = new Array(fin + 1).fill(0);
      let marcas = '';
      if (dep === 'NHL') {
        const peso = (t) => (/Goal/.test(t) ? 5 : /Shot/.test(t) ? 3 : /Missed/.test(t) ? 1.6 : /Blocked/.test(t) ? 1.2 : /Takeaway/.test(t) ? 1 : /Hit/.test(t) ? 0.5 : 0);
        js.forEach((q) => { const m = Math.floor(q.min); if (q.lado != null && val[m] != null) val[m] += (q.lado === 0 ? 1 : -1) * peso(q.t); });
        for (let i = fin; i >= 0; i--) val[i] = val.slice(Math.max(0, i - 2), i + 1).reduce((a, b) => a + b, 0);
        marcas = js.filter((q) => /Goal/.test(q.t)).map((q) => '<span class="ola-gol ' + (q.lado === 0 ? 'arriba' : 'abajo') + '" style="left:' + Math.min(98, 100 * q.min / fin).toFixed(1) + '%">●</span>').join('');
      } else {
        const hasta = Math.floor(js[js.length - 1].min), por = {};
        js.forEach((q) => { por[Math.floor(q.min)] = q.dif; });
        let va = 0;
        for (let i = 0; i <= hasta && i <= fin; i++) { if (por[i] != null) va = por[i]; val[i] = va; }
      }
      const cortes = []; for (let m = per; m < fin; m += per) cortes.push(m);
      const et = dep === 'NHL' ? ['1.er', '2.º', '3.er'] : ['1.º', '2.º', '3.º', '4.º'];
      return '<div class="cancha-tit"><span>' + (dep === 'NHL' ? 'Presión' : 'Ventaja en el marcador') + '</span></div><div class="ola"><svg class="presion-svg" viewBox="0 0 100 24" preserveAspectRatio="none" aria-label="El partido minuto a minuto">' + barraPresion({ val, fin, c, cortes }) + '</svg>' + marcas + '</div>' +
        '<div class="ola-tiempos pista-t">' + et.map((t) => '<span>' + t + '</span>').join('') + '</div>';
    }
    if (dep === 'NFL') {
      const s = ((datos && datos.series) || []).slice(-8);
      if (!s.length) return '';
      return '<div class="cancha-tit"><span>Últimas series</span></div><div class="p-series">' + s.map((x) => '<div><i style="width:' + entre(4, (Math.abs(x.yds) / 80) * 100, 100).toFixed(0) + '%;background:' + c[x.lado] + '"></i><span>' + esc(x.lado === 0 ? L : V) + '</span><b>' + x.yds + ' yd · ' + esc(traduce(ES_SERIE, x.res) || x.res) + '</b></div>').join('') + '</div>';
    }
    if (familia(dep) === 'BEIS') {
      const b = (BEIS[k] || {}).d;
      if (!b || !b.entradas.length) return '';
      const n = Math.max(9, b.entradas.length), celda = (l, i) => { const e = b.entradas[i]; const x = e && e[l]; return '<td>' + (x == null ? '' : x) + '</td>'; };
      const fila = (l, nom) => '<tr><th>' + esc(nom) + '</th>' + Array.from({ length: n }, (_, i) => celda(l, i)).join('') + '<td class="t">' + (b.tot[l][0] == null ? '' : b.tot[l][0]) + '</td><td class="t">' + (b.tot[l][1] == null ? '' : b.tot[l][1]) + '</td><td class="t">' + (b.tot[l][2] == null ? '' : b.tot[l][2]) + '</td></tr>';
      return '<div class="p-linea"><table><tr><th></th>' + Array.from({ length: n }, (_, i) => '<th>' + (i + 1) + '</th>').join('') + '<th class="t">C</th><th class="t">H</th><th class="t">E</th></tr>' + fila(0, L) + fila(1, V) + '</table></div>';
    }
    return '';
  }
  const LEY = { NHL: '<span>× tiro</span><span>★ gol</span>', NBA: '<span>○ falló</span><span>● encestó</span>', NFL: '<span class="l-los">línea de golpeo</span><span class="l-fd">primer intento</span>', BEIS: '', Tenis: '' };
  function marcasDe(dep, datos, c, ahora) {
    const js = ((datos && datos.jugadas) || []).filter((q) => q.x != null);
    if (dep === 'NHL') {
      return js.filter((q) => /Goal/.test(q.t) || (/Shot|Missed/.test(q.t) && q.min >= ahora - 8)).map((q) => {
        const tr = 'translate(' + q.x.toFixed(2) + ' ' + q.y.toFixed(2) + ')';
        return /Goal/.test(q.t) ? '<g class="tiro gol" transform="' + tr + '"><path d="M0,-2 L.59,-.62 L1.9,-.62 L.85,.25 L1.25,1.62 L0,.82 L-1.25,1.62 L-.85,.25 L-1.9,-.62 L-.59,-.62Z" fill="' + c[q.lado] + '"/></g>'
          : '<g class="tiro" transform="' + tr + '"><path d="M-.9,-.9 L.9,.9 M-.9,.9 L.9,-.9" stroke="' + c[q.lado] + '"/></g>';
      }).join('');
    }
    if (dep === 'NBA') {
      return js.filter((q) => /Shot|Layup|Dunk|Jumper|Tip/.test(q.t) && !/Free Throw/.test(q.t) && q.min >= ahora - 5).map((q) => '<g class="tiro nba' + (q.anota ? ' gol' : '') + '" transform="translate(' + q.x.toFixed(2) + ' ' + q.y.toFixed(2) + ')"><circle r="1" fill="' + (q.anota ? c[q.lado] : 'none') + '" stroke="' + c[q.lado] + '"/></g>').join('');
    }
    return '';
  }
  // lo que app.js pinta en lugar de la cancha de fútbol
  function html(v, p, clave) {
    const dep = p.deporte, fam = familia(dep), k = clave || p.partido, alto = ALTO[fam];
    const datos = v && v.pista, c = colores(v, fam), [L, V] = (v && v.nombres && v.nombres[0] ? v.nombres : String(p.partido || '').split(' vs '));
    const pausa = !v || v.fase !== 'in' || /half|intermission|end of|fin de|descanso|entretiempo/i.test(String(v.est || '') + ' ' + String(v.detalle || ''));
    const ult = datos && datos.jugadas && datos.jugadas.length ? datos.jugadas[datos.jugadas.length - 1] : null;
    const m = MOTORES[k] = Object.assign(MOTORES[k] || { vistas: new Set(), dep, fam }, { pausa, datos, v, p });
    if (!m.ini && ult) { m.ini = true; (datos.jugadas || []).forEach((q) => m.vistas.add(q.id)); }
    const ahora = ult && ult.min != null ? ult.min : 0;
    const js = equipos(dep, v, datos);
    const firma = js.map((j) => j.key + (j.n || '')).join(',') + c.join('');
    const letrero = !v || v.fase === 'pre' ? '' : v.terminado || v.fase === 'post' ? 'FINAL' : pausa ? 'DESCANSO' : '';
    const altoL = alto / 2;
    let s = '<svg class="cancha-svg pista-svg" viewBox="0 0 105 ' + alto + '" role="img" aria-label="Cancha en vivo" data-pista="' + esc(k) + '" data-firma="' + esc(firma) + '">' + FONDO[fam](c) + '<g class="marcas">' + marcasDe(dep, datos, c, ahora) + '</g>';
    if (dep === 'NFL') s += '<line class="p-los" x1="-5" y1="0" x2="-5" y2="46.7"/><line class="p-fd" x1="-5" y1="0" x2="-5" y2="46.7"/>';
    js.forEach((j) => {
      s += '<g class="jug" data-key="' + esc(j.key) + '" data-lado="' + j.lado + '" data-rol="' + esc(j.rol) + '" data-id="' + esc(j.id) + '" data-bx="' + j.x.toFixed(2) + '" data-by="' + j.y.toFixed(2) + '" style="transform:translate(' + j.x.toFixed(2) + 'px,' + j.y.toFixed(2) + 'px)">' +
        '<circle class="aro" r="2.4" fill="' + c[j.lado] + '"/><circle class="pto" r="1.05" fill="' + c[j.lado] + '"/><text y=".75" class="num">' + esc(j.n) + '</text><text y="5" class="nom">' + esc(j.nombre) + '</text></g>';
    });
    const bola = fam === 'NHL' ? '<ellipse rx="1" ry=".75" class="disco"/><ellipse rx="1.9" ry="1.5" class="halo"/>'
      : fam === 'NBA' ? '<circle r="2" class="halo"/><circle r="1.2" class="bbola"/><path d="M-1.2 0H1.2M0 -1.2V1.2" class="bcost"/>'
        : fam === 'NFL' ? '<circle r="2" class="halo"/><ellipse rx="1.35" ry=".82" class="ovalo"/><path d="M-.5 0H.5" class="bcost blanco"/>'
          : fam === 'BEIS' ? '<circle r="1.5" class="halo"/><circle r=".75" class="bola"/>' : '<circle r="1.6" class="halo"/><circle r=".8" class="pelota"/>';
    s += '<line class="pase" x1="0" y1="0" x2="0" y2="0"/><g class="balon"><ellipse cx=".3" cy=".7" rx="1" ry=".42" class="sombra"/>' + bola + '</g>';
    s += '<g class="gol-aviso"><text x="52.5" y="' + (altoL + 3).toFixed(1) + '"></text></g>';
    if (letrero) s += '<g class="letrero"><rect x="32.5" y="' + (altoL - 7).toFixed(1) + '" width="40" height="14" rx="3"/><text x="52.5" y="' + (altoL + 2.2).toFixed(1) + '">' + letrero + '</text></g>';
    s += '</svg>';
    const setsTxt = fam === 'Tenis' && v && v.g && (v.g[0] || v.g[1]) ? ' · sets ' + v.g[0] + '-' + v.g[1] : '';
    const chip = ult && ICONO[fam] ? etiqueta(fam, ult, datos.nombres) : (fam === 'Tenis' ? '🎾 <b>' + esc((v && v.detalle) || 'En vivo') + '</b>' + setsTxt : (ICONO[fam] || '') + ' <b>En vivo</b>');
    const ley = LEY[fam] ? '<div class="cancha-ley" title="El movimiento es una animación; lo que anotan sale de lo que de verdad pasó.">' + LEY[fam] + '</div>' : '';
    return '<div class="cancha cancha-' + fam.toLowerCase() + '"><div class="cancha-ult"><span class="chip-ult">' + chip + '</span></div>' + s + ley + tira(dep, v, datos, c, L, V, k) + '</div>';
  }

  // ---------------------------------------------------------------- el motor
  function adoptar() {
    document.querySelectorAll('.pista-svg[data-pista]:not([data-vivo])').forEach((n) => {
      const lugar = n.dataset.pista + '|' + (n.closest('#ficha-cuerpo') ? 'f' : 'l'), o = VIVAS[lugar];
      if (o && !o.isConnected && o.dataset.firma === n.dataset.firma) {
        const a = o.querySelector('.marcas'), b = n.querySelector('.marcas');
        if (a && b) a.innerHTML = b.innerHTML;
        o.querySelectorAll('.letrero').forEach((x) => x.remove());
        const l = n.querySelector('.letrero'); if (l) o.appendChild(l);
        o._chip = null;
        n.replaceWith(o);
        return;
      }
      n.dataset.vivo = '1';
      n._els = {};
      n.querySelectorAll('.jug[data-key]').forEach((j) => { n._els[j.dataset.key] = j; });
      n._balon = n.querySelector('.balon'); n._pase = n.querySelector('.pase'); n._aviso = n.querySelector('.gol-aviso text');
      n._los = n.querySelector('.p-los'); n._fd = n.querySelector('.p-fd');
      VIVAS[lugar] = n;
    });
  }
  function preparar(svg, m) {
    if (m.js && m.firma === svg.dataset.firma) return;
    const antes = {}; (m.js || []).forEach((q) => { antes[q.key] = q; });
    m.js = [...svg.querySelectorAll('.jug[data-key]')].map((j) => {
      const key = j.dataset.key, a = antes[key], lado = Number(j.dataset.lado), x0 = Number(j.dataset.bx), y0 = Number(j.dataset.by);
      return { key, lado, id: j.dataset.id || '', rol: j.dataset.rol, dir: lado === 0 ? 1 : -1, x0, y0, cx: a ? a.cx : x0, cy: a ? a.cy : y0, vx: a ? a.vx : 0, vy: a ? a.vy : 0, tx: a ? a.tx : x0, ty: a ? a.ty : y0, rx: lado === 0 ? 1 : -1, ry: 0, fase: Math.random() * 6.283 };
    });
    m.firma = svg.dataset.firma;
    m.t = m.t || 0; m.prox = m.t; m.proxA = m.t; m.proxJ = m.t;
    m.port = m.js.find((q) => q.key === m.portador) || null;
    m.vuelo = null;
    if (m.bx == null) { m.bx = 52.5; m.by = ALTO[m.fam] / 2; }
    (FASES[m.fam] || {}).ini && FASES[m.fam].ini(m);
  }
  const campoDe = (m, l) => m.js.filter((q) => q.lado === l && q.rol !== 'G');
  const cerca = (lista, x, y) => lista.slice().sort((a, b) => Math.hypot(a.cx - x, a.cy - y) - Math.hypot(b.cx - x, b.cy - y));
  function anunciar(m, txt) { m.chipTxt = txt; m.chipN = (m.chipN || 0) + 1; m.chipT = m.t; }
  function aviso(m, txt, seg) { m.aviso = txt; m.avisoHasta = m.t + seg; }
  function lanzar(m, a, conLinea, destino, vel) {
    const x0 = m.bx, y0 = m.by, sp = vel || SIM[m.fam].vPase;
    const obj = destino || (a ? [a.cx, a.cy] : [m.bx, m.by]);
    const T = entre(0.2, Math.hypot(obj[0] - x0, obj[1] - y0) / sp, 1.5);
    const x1 = destino ? obj[0] : obj[0] + (a ? a.vx * T * 0.6 : 0), y1 = destino ? obj[1] : obj[1] + (a ? a.vy * T * 0.6 : 0);
    m.vuelo = { x0, y0, x1, y1, t0: m.t, T, a };
    if (a) { a.tx = x1; a.ty = y1; }
    m.port = null; m.portador = null;
    if (conLinea) { m.pase = [x0, y0, x1, y1]; m.paseN = (m.paseN || 0) + 1; }
  }
  // el del dibujo pasa a ser quien de verdad hizo la jugada (ESPN no siempre trae a todos en la lista)
  function nombrar(m, q, nombre, n) { (m.nombres = m.nombres || {})[q.key] = { nombre: nombre || '', n: n == null ? '' : n }; m.nombresN = (m.nombresN || 0) + 1; }
  function dar(m, q) { m.port = q; m.portador = q ? q.key : null; m.vuelo = null; if (q) m.bt = null; }

  // ------------- el flujo: NHL y NBA (como el fútbol)
  function posesionInicial(m) {
    const ult = m.datos && m.datos.jugadas && m.datos.jugadas[m.datos.jugadas.length - 1];
    return ult && ult.lado != null ? ult.lado : 0;
  }
  function decidirFlujo(m) {
    const port = m.port, s = SIM[m.fam];
    m.prox = m.t + azar(s.T[0], s.T[1]);
    const r = Math.random(), otro = port.lado === 0 ? 1 : 0;
    if (s.robo && r < s.robo) {
      const rival = cerca(campoDe(m, otro), port.cx, port.cy)[0];
      if (rival) { lanzar(m, rival, false); return; }
    }
    if (r < s.pase) {
      const mx = Math.random() < 0.15 ? s.muyLargo : s.largo;
      const cands = campoDe(m, port.lado).filter((q) => q !== port).map((q) => {
        const dd = Math.hypot(q.cx - port.cx, q.cy - port.cy), av = (q.cx - port.cx) * port.dir;
        return { q, w: dd < s.corto || dd > mx ? 0 : Math.max(0.2, (av + 12) / dd) * (m.carrera && m.carrera.key === q.key ? 2.5 : 1) };
      }).filter((c) => c.w > 0);
      const tot = cands.reduce((a, c) => a + c.w, 0);
      if (tot > 0) { let x = Math.random() * tot; const el = cands.find((c) => (x -= c.w) <= 0) || cands[0]; lanzar(m, el.q, true); return; }
    }
    const ang = (Math.random() - 0.5) * (m.fam === 'NBA' ? 3.4 : 1.4); port.rx = port.dir * Math.cos(ang); port.ry = Math.sin(ang);
  }
  function acomodarNhl(m) {
    const port = m.port || (m.vuelo && m.vuelo.a); if (!port) return;
    const bx = m.vuelo ? m.vuelo.x1 : m.bx, by = m.vuelo ? m.vuelo.y1 : m.by, s = SIM.NHL, A = ALTO.NHL;
    m.js.forEach((q) => {
      const g = q.rol === 'G';
      q.tx = g ? (q.lado === 0 ? 4.5 : 100.5) : q.x0 + (bx - 52.5) * s.seguir + q.dir * (q.lado === port.lado ? 4 : -3);
      q.ty = g ? entre(19, 22.3 + (by - 22.3) * s.seguirG * 3, 25.6) : q.y0 + (by - A / 2) * 0.32;
    });
    campoDe(m, port.lado).filter((q) => q !== port).sort((a, b) => Math.hypot(a.cx - bx, a.cy - by) - Math.hypot(b.cx - bx, b.cy - by)).slice(0, 2).forEach((q, i) => { q.tx = bx + q.dir * (i ? 4 : 11); q.ty = by + (by > A / 2 ? -1 : 1) * (i ? 8 : 13); });
    cerca(campoDe(m, port.lado === 0 ? 1 : 0), bx, by).slice(0, 2).forEach((q, i) => { q.tx = bx - port.dir * (i ? 8 : 2.6); q.ty = by + (i ? (by > A / 2 ? -6 : 6) : 1); });
    separar(m, port, s.sep);
  }
  const SPOTS = [[16, 28], [7, 8], [7, 48], [11, 18], [11, 38], [22, 12], [22, 44]];
  function acomodarNba(m) {
    const port = m.port || (m.vuelo && m.vuelo.a); if (!port) return;
    const L = port.lado, ataca = (x) => (L === 0 ? 105 - x : x), of = m.js.filter((q) => q.lado === L), de = m.js.filter((q) => q.lado !== L);
    m.girar = m.girar || 0;
    if (m.t > (m.proxGiro || 0)) { m.girar = (m.girar + 1) % SPOTS.length; m.proxGiro = m.t + azar(1.6, 3); }
    of.forEach((q, i) => { const sp = SPOTS[(i + m.girar + (i > 2 ? 2 : 0)) % SPOTS.length]; q.tx = ataca(sp[0]); q.ty = sp[1] + Math.sin(m.t * 0.7 + q.fase) * 1.6; });
    const aro = [ataca(6.6), 27.95];
    de.forEach((q, i) => {            // cada quien con su marca, entre él y la canasta
      const o = of[i] || of[0], ox = o === port ? port.cx : o.tx, oy = o === port ? port.cy : o.ty, d = Math.hypot(aro[0] - ox, aro[1] - oy) || 1;
      q.tx = ox + (aro[0] - ox) / d * 3; q.ty = oy + (aro[1] - oy) / d * 3;
    });
    separar(m, port, SIM.NBA.sep);
  }
  function separar(m, port, sep) {
    const l = m.js.filter((q) => q !== port);
    for (let i = 0; i < l.length; i++) for (let j = i + 1; j < l.length; j++) {
      const a = l[i], b = l[j], dx = a.tx - b.tx, dy = a.ty - b.ty, dd = Math.hypot(dx, dy);
      if (dd < sep && dd > 0.01) { const f = (sep - dd) / (2 * dd); a.tx += dx * f; a.ty += dy * f; b.tx -= dx * f; b.ty -= dy * f; }
    }
    if (m.vuelo && m.vuelo.a) { m.vuelo.a.tx = m.vuelo.x1; m.vuelo.a.ty = m.vuelo.y1; }
  }
  // una jugada real: `pasos` son [segundos, función] que se van cumpliendo
  function pasosDe(m, q) {
    const fam = m.fam, atk = q.lado, x = q.x, y = q.y, tiene = x != null, redX = atk === 0 ? (fam === 'NHL' ? 99.2 : 98.4) : (fam === 'NHL' ? 5.8 : 6.6), redY = fam === 'NHL' ? 22.3 : 27.95, t = q.t;
    const tirador = () => {
      if (atk == null) return null;
      const id = q.part && q.part[0], real = id && m.js.find((j) => j.id === id);
      if (real) return real;
      const j = cerca(m.js.filter((z) => z.lado === atk && z.rol !== 'G'), x == null ? m.bx : x, y == null ? m.by : y)[0];
      const d = m.datos || {};
      if (j && id && d.nombres && d.nombres[id]) { j.id = id; nombrar(m, j, d.nombres[id], (d.numeros || {})[id]); }
      return j;
    };
    const enLugar = (j) => { if (j && tiene) { j.tx = x; j.ty = y; } };
    const rebote = (lado, gx, gy) => { const r = cerca(m.js.filter((j) => j.lado === lado), gx, gy)[0]; if (r) lanzar(m, r, false); };
    const otro = atk === 0 ? 1 : 0;
    if (fam === 'NHL') {
      if (/Face Off/.test(t)) {
        const fx = tiene ? x : 52.5, fy = tiene ? y : 22.3;
        return [[0, () => { m.fijo = true; m.bt = [fx, fy]; dar(m, null); [0, 1].forEach((l) => { cerca(campoDe(m, l), fx, fy).forEach((j, i) => { const s = j.dir; j.tx = fx - s * (i === 0 ? 1.6 : 8); j.ty = fy + (i === 0 ? 0 : (i % 2 ? -1 : 1) * (4 + i * 2)); }); }); }],
          [2.2, () => { m.fijo = false; m.bt = null; const w = atk == null ? null : cerca(campoDe(m, atk), fx, fy)[0]; if (w) lanzar(m, cerca(campoDe(m, atk), fx - w.dir * 8, fy)[1] || w, false); }]];
      }
      if (/Goal/.test(t)) {
        const j = tirador();
        return [[0, () => { m.fijo = true; enLugar(j); dar(m, j); }], [0.9, () => { lanzar(m, null, true, [redX, redY + azar(-1, 1)], 95); aviso(m, '¡GOL!', 3.5); }], [3.6, () => { dar(m, null); m.bt = [52.5, 22.3]; }], [4.6, () => { m.fijo = false; m.bt = null; }]];
      }
      if (/^Shot|Missed|Blocked/.test(t)) {
        const j = tirador(), def = m.js.find((g) => g.lado === otro && g.rol === 'G');
        const dest = /Missed/.test(t) ? [redX, redY + (Math.random() < 0.5 ? -8 : 8)] : /Blocked/.test(t) && tiene ? [x + (atk === 0 ? 5 : -5), y] : [def ? def.cx : redX, redY + azar(-1.5, 1.5)];
        return [[0, () => { m.fijo = true; enLugar(j); dar(m, j); }], [0.9, () => { lanzar(m, null, true, dest, 90); }], [1.7, () => { m.fijo = false; rebote(otro, dest[0], dest[1]); }]];
      }
      if (/Hit/.test(t)) { const j = tirador(); return [[0, () => { enLugar(j); if (tiene) m.bt = [x, y]; }], [0.9, () => { m.bt = null; }]]; }
      if (/Giveaway|Takeaway/.test(t)) {
        const gana = /Takeaway/.test(t) ? atk : otro, j = gana == null ? null : cerca(campoDe(m, gana), x == null ? m.bx : x, y == null ? m.by : y)[0];
        return [[0, () => { if (j) { lanzar(m, j, false, tiene ? [x, y] : null); m.vuelo && (m.vuelo.a = j); } }]];
      }
      if (/Stoppage|Period/.test(t)) return [[0, () => { m.fijo = true; dar(m, null); m.bt = [m.bx, m.by]; }], [1.8, () => { m.fijo = false; m.bt = null; }]];
      return [[0, () => { m.fijo = true; dar(m, null); m.bt = [m.bx, m.by]; }], [2.2, () => { m.fijo = false; m.bt = null; }]];       // falta: se detiene
    }
    // NBA
    if (/Free Throw/.test(t)) {
      const fx = atk === 0 ? 83.1 : 21.9, encesta = q.anota;
      const j = tirador() || m.js.find((z) => z.lado === (atk == null ? 0 : atk));
      return [[0, () => { m.fijo = true; dar(m, j); if (j) { j.tx = fx; j.ty = 27.95; } m.js.filter((z) => z !== j).forEach((z, i) => { z.tx = (atk === 0 ? 88 : 17) + (i % 2 ? 4 : 0) * (atk === 0 ? 1 : -1); z.ty = i % 2 ? 19 : 37; if (i > 5) { z.tx = fx - (atk === 0 ? 8 : -8); z.ty = 14 + i * 4; } }); }],
        [1.2, () => { lanzar(m, null, true, [redX, encesta ? redY : redY + 2], 34); if (encesta) aviso(m, '+1', 1.1); }], [2.3, () => { m.fijo = false; rebote(otro, redX, redY); }]];
    }
    if (/Shot|Layup|Dunk|Jumper|Hook|Tip/.test(t)) {
      const j = tirador(), val = q.val || 2;
      return [[0, () => { m.fijo = true; enLugar(j); dar(m, j); }], [1, () => { lanzar(m, null, true, [redX, q.anota ? redY : redY + azar(-3, 3)], 42); if (q.anota) aviso(m, '+' + val, 1.3); }], [1.9, () => { m.fijo = false; if (q.anota) rebote(otro, redX, redY); }]];
    }
    if (/Rebound/.test(t)) {
      const j = tirador();
      return [[0, () => { if (j) { lanzar(m, j, false, tiene ? [x, y] : null); if (m.vuelo) m.vuelo.a = j; } }]];
    }
    if (/Turnover|Steal/.test(t)) {
      const gana = /Steal/.test(t) ? atk : otro, j = gana == null ? null : cerca(m.js.filter((z) => z.lado === gana), m.bx, m.by)[0];
      return [[0, () => { if (j) lanzar(m, j, false); }]];
    }
    if (/Timeout/.test(t)) return [[0, () => { m.fijo = true; dar(m, null); m.bt = [52.5, 27.95]; m.js.forEach((z, i) => { z.tx = z.lado === 0 ? 36 + (i % 3) * 3 : 69 - (i % 3) * 3; z.ty = 53 - (i % 3); }); }], [2.8, () => { m.fijo = false; m.bt = null; }]];
    return [[0, () => { m.fijo = true; dar(m, null); m.bt = [m.bx, m.by]; }], [1.4, () => { m.fijo = false; m.bt = null; }]];
  }
  function flujo(m) {
    const js = (m.datos && m.datos.jugadas) || [];
    if (!m.guion && m.t >= m.proxJ) {
      m.proxJ = m.t + 0.25;
      const pend = js.filter((q) => !m.vistas.has(q.id));
      if (pend.length > 8) pend.slice(0, -8).filter((q) => !q.anota).forEach((q) => m.vistas.add(q.id));
      const nueva = js.find((q) => !m.vistas.has(q.id));
      if (nueva) {
        m.vistas.add(nueva.id);
        anunciar(m, etiqueta(m.fam, nueva, m.datos.nombres));
        m.guion = pasosDe(m, nueva).map(([s, f]) => ({ en: m.t + s, f }));
      }
    }
    if (m.guion) {
      while (m.guion.length && m.t >= m.guion[0].en) m.guion.shift().f();
      if (!m.guion.length) m.guion = null;
    }
    if (m.fijo) return;
    if (!m.port && !m.vuelo) {
      const l = m.posesion != null ? m.posesion : posesionInicial(m);
      dar(m, cerca(campoDe(m, l), m.bx, m.by)[0] || null); m.prox = m.t + 0.4;
    }
    if (m.port && !m.guion && m.t >= m.prox) decidirFlujo(m);
    if (m.t >= m.proxA) {
      m.proxA = m.t + 0.35;
      (m.fam === 'NHL' ? acomodarNhl : acomodarNba)(m);
    }
  }

  // ------------- NFL: series con su línea real
  const yardaAx = (yte, lado) => (lado === 0 ? (110 - yte) : (10 + yte)) * 0.875;
  function nflLineaUp(m) {
    const L = m.of, dir = L === 0 ? 1 : -1, x = m.losX, cy = 23.35, A = ALTO.NFL;
    const of = m.js.filter((q) => q.lado === L), de = m.js.filter((q) => q.lado !== L);
    const lug = { QB: [-4.4, 0], RB: [-6.4, 2.6], OL: null, TE: [-0.7, 9] };
    let ol = 0, wr = 0;
    of.forEach((q) => {
      if (q.rol === 'OL') { q.tx = x - dir * 0.7; q.ty = cy + (ol++ - 2) * 2.6; }
      else if (q.rol === 'WR') { q.tx = x - dir * 0.7; q.ty = [5, A - 5, 11][wr++] || cy; }
      else { const l = lug[q.rol] || [0, 0]; q.tx = x + dir * l[0]; q.ty = cy + l[1]; }
    });
    de.forEach((q, i) => {
      if (i < 4) { q.tx = x + dir * 0.9; q.ty = cy + (i - 1.5) * 3.2; }
      else if (i < 7) { q.tx = x + dir * 4; q.ty = cy + (i - 5) * 6; }
      else { q.tx = x + dir * (i < 9 ? 7 : 12); q.ty = i < 9 ? [6, A - 6][i - 7] : cy + (i - 9.5) * 12; }
    });
    const qb = of.find((q) => q.rol === 'QB'); if (qb) dar(m, null);
    m.bt = [x, cy];
  }
  function nflSituacion(m) {
    const u = m.datos && m.datos.jugadas && m.datos.jugadas[m.datos.jugadas.length - 1];
    if (u && u.ydF != null) {
      m.of = u.equipoFin; m.losX = yardaAx(entre(0, u.ydF, 100), m.of);
      const d = m.of === 0 ? 1 : -1; m.fdX = u.dist ? entre(8.75, m.losX + d * Number(u.dist) * 0.875, 96.25) : null;
      if (u.baja) m.baja = bajaEs(u.baja) + (u.pos ? ' · ' + u.pos : '');
    } else if (m.losX == null) { m.of = 0; m.losX = 52.5; m.fdX = 61.25; }
  }
  function nflJugada(m, real) {
    const L = m.of, dir = L === 0 ? 1 : -1, of = m.js.filter((q) => q.lado === L), de = m.js.filter((q) => q.lado !== L);
    const qb = of.find((q) => q.rol === 'QB'), rb = of.find((q) => q.rol === 'RB'), wrs = of.filter((q) => q.rol === 'WR' || q.rol === 'TE');
    const pases = real ? /Pass|Sack|Interception/i.test(real.t) : Math.random() < 0.62;
    const rutas = () => wrs.forEach((w, i) => { w.tx = m.losX + dir * azar(8, 19); w.ty = entre(4, w.cy + (i % 2 ? 1 : -1) * azar(2, 12), 42.7); });
    const presion = () => de.forEach((d, i) => { if (i < 4 && qb) { d.tx = qb.cx + dir * 1.5; d.ty = qb.cy + (i - 1.5) * 2; } else { const w = wrs[i % wrs.length]; if (w) { d.tx = w.tx + dir * 1.5; d.ty = w.ty + azar(-1, 1); } } });
    const fin = real ? yardaAx(entre(0, real.ydF == null ? 50 : real.ydF, 100), real.lado) : null;
    if (real) {
      const [juega, recibe] = nombresNfl(real.txt);
      if (pases) { if (juega && qb) nombrar(m, qb, juega, ''); } else if (juega && rb) nombrar(m, rb, juega, '');
      if (recibe && wrs[0]) m.receptor = recibe;
    }
    const guion = [[0, () => { dar(m, qb); m.bt = null; }]];
    if (real && /Punt|Kickoff|Field Goal/i.test(real.t)) {
      const larga = /Field Goal/i.test(real.t);
      return [[0, () => { dar(m, null); m.bt = null; lanzar(m, null, true, larga ? [L === 0 ? 100 : 5, 23.35] : [fin == null ? m.losX + dir * 35 : fin, azar(10, 36)], 34); }], [2.4, () => { m.bt = null; }]];
    }
    if (pases) {
      guion.push([0.2, () => { if (qb) { qb.tx = m.losX - dir * 7.5; qb.ty = 23.35; } rutas(); presion(); }]);
      if (real && /Sack/i.test(real.t)) guion.push([1.9, () => { const c = de[0]; if (c && qb) { c.tx = qb.cx; c.ty = qb.cy; } }]);
      else {
        const w = wrs[Math.floor(Math.random() * wrs.length)];
        if (real && m.receptor && w) { nombrar(m, w, m.receptor, ''); m.receptor = null; }
        guion.push([1.8, () => { if (w) lanzar(m, w, true, null, 30); }]);
        if (!real || !/Incompletion/i.test(real.t)) guion.push([3, () => { if (w && m.port === w) { const meta = fin == null ? w.cx + dir * azar(2, 5) : fin; w.rx = dir; w.ry = 0; w.tx = meta; m.corre = meta; } }]);
      }
    } else {
      guion.push([0.2, () => { if (rb && qb) { rb.tx = qb.cx; rb.ty = qb.cy + 0.6; } }]);
      guion.push([0.7, () => { if (rb) { dar(m, rb); const meta = fin == null ? m.losX + dir * azar(1, 5) : fin; rb.rx = dir; rb.ry = 0; m.corre = meta; } de.slice(0, 7).forEach((d) => { d.tx = (m.corre || m.losX) + dir * 0.5; d.ty = 23.35 + azar(-5, 5); }); }]);
    }
    if (real && real.anota) guion.push([3.8, () => aviso(m, /Touchdown/i.test(real.t + real.txt) ? '¡TOUCHDOWN!' : '¡ANOTAN!', 3)]);
    return guion;
  }
  function nfl(m) {
    const js = (m.datos && m.datos.jugadas) || [];
    if (m.losX == null) { nflSituacion(m); m.estado = 'linea'; m.espera = m.t + 1; nflLineaUp(m); }
    if (m.guion) {
      while (m.guion.length && m.t >= m.guion[0].en) m.guion.shift().f();
      if (m.port && m.corre != null) {
        const q = m.port, d = q.dir;
        q.tx = m.corre; q.ty = q.cy;
        if ((m.corre - q.cx) * d <= 0.4) { m.corre = null; dar(m, null); m.bt = [q.cx, q.cy]; }
      }
      if (!m.guion.length && m.t >= m.finGuion) { m.guion = null; m.corre = null; m.estado = 'silbato'; m.espera = m.t + 0.9; dar(m, null); m.bt = [m.bx, m.by]; }
      return;
    }
    if (m.t < m.espera) return;
    if (m.estado === 'silbato') { nflSituacion(m); nflLineaUp(m); m.estado = 'linea'; m.espera = m.t + azar(2.2, 3.6); return; }
    const nueva = js.find((q) => !m.vistas.has(q.id));
    if (nueva) { m.vistas.add(nueva.id); anunciar(m, etiqueta('NFL', nueva)); m.finGuion = m.t + 4.6; m.guion = nflJugada(m, nueva).map(([s, f]) => ({ en: m.t + s, f })); return; }
    m.finGuion = m.t + 4.2; m.guion = nflJugada(m, null).map(([s, f]) => ({ en: m.t + s, f }));
  }

  // ------------- béisbol: lanzamiento a lanzamiento, batazos en su lugar real
  const BASES = [[67, 54.5], [52.5, 40], [38, 54.5]], LOMA = [52.5, 56], HOME = [52.5, 72];
  function golpeDe(q) {           // la API da 250x250 con el home cerca de (125,205)
    if (q.hx == null) return [azar(24, 80), azar(16, 46)];
    return [entre(3, 52.5 + (q.hx - 125) * 0.47, 102), entre(4, 72 + (q.hy - 205) * 0.47, 76)];
  }
  function beisRoles(m) {
    const b = (BEIS[m.clave] || {}).d;
    const por = (r) => m.js.find((q) => q.rol === r);
    const ids = b ? b.ids : [null, null, null], ant = m.idsB;
    ['r1', 'r2', 'r3'].forEach((r, i) => {
      const q = por(r), id = ids[i];
      if (!q) return;
      q.oculto = !id;
      if (!id) { q.cx = q.tx = -5; q.cy = q.ty = -5; q.vx = q.vy = 0; return; }
      const sitio = [BASES[i][0], BASES[i][1] - 0.2];
      // recién abierta la tarjeta ya está en su base; si cambió, corre desde la base donde estaba o desde home (si acaba de batear)
      if (!ant) { q.cx = sitio[0]; q.cy = sitio[1]; q.vx = q.vy = 0; }
      else if (ant[i] !== id) { const j = ant.indexOf(id), o = j >= 0 ? BASES[j] : HOME; q.cx = o[0]; q.cy = o[1]; q.vx = q.vy = 0; }
      q.tx = sitio[0]; q.ty = sitio[1];
    });
    if (b) m.idsB = ids;
    return b;
  }
  function beis(m) {
    const b = beisRoles(m);
    const pit = m.js.find((q) => q.rol === 'p'), ca = m.js.find((q) => q.rol === 'ca'), bat = m.js.find((q) => q.rol === 'bat');
    if (bat && !m.guion) { bat.tx = 49.8; bat.ty = 72.5; }
    if (m.guion) {
      while (m.guion.length && m.t >= m.guion[0].en) m.guion.shift().f();
      if (!m.guion.length) m.guion = null;
      return;
    }
    const js = (b && b.jugadas) || [];
    if (!m.iniB && b) { m.iniB = true; js.forEach((q) => m.vistas.add(q.id)); }
    const nueva = js.find((q) => !m.vistas.has(q.id));
    const al = (seg, f) => ({ en: m.t + seg, f });
    if (nueva) {
      m.vistas.add(nueva.id); anunciar(m, etiqueta('BEIS', nueva));
      const hit = nueva.hx != null, g = golpeDe(nueva), def = hit ? cerca(m.js.filter((q) => q.lado === 1 && q.rol !== 'ca' && q.rol !== 'p'), g[0], g[1])[0] : null;
      const hr = /Home Run/i.test(nueva.t);
      m.guion = [al(0, () => { dar(m, pit); m.bt = null; }), al(0.5, () => lanzar(m, null, true, HOME, 62))];
      if (hit) {
        m.guion.push(al(0.95, () => lanzar(m, null, true, hr ? [g[0], 3] : g, hr ? 50 : 42)), al(1, () => { if (def && !hr) { def.tx = g[0]; def.ty = g[1]; } if (bat && !hr) { bat.tx = BASES[0][0]; bat.ty = BASES[0][1]; } }));
        if (hr) m.guion.push(al(1.4, () => aviso(m, '¡JONRÓN!', 3)));
        m.guion.push(al(hr ? 3.4 : 2.6, () => { if (def && !hr) dar(m, def); }), al(hr ? 4.4 : 3.4, () => { dar(m, pit); }));
      } else m.guion.push(al(1.2, () => { dar(m, ca); }), al(2, () => { dar(m, pit); }));
      if (nueva.anota && !hr) m.guion.push(al(2.2, () => aviso(m, '¡CARRERA!', 1.8)));
      return;
    }
    if (m.t < m.prox) return;
    m.prox = m.t + azar(3.2, 5.2);
    const faul = Math.random() < 0.22;
    m.guion = [al(0, () => { dar(m, pit); m.bt = null; }), al(0.45, () => lanzar(m, null, true, [azar(51.5, 53.5), HOME[1] + 0.4], 62))];
    if (faul) m.guion.push(al(0.9, () => lanzar(m, null, false, [Math.random() < 0.5 ? azar(4, 24) : azar(81, 101), azar(38, 60)], 45)), al(2.1, () => { m.vuelo = null; }), al(2.2, () => { lanzar(m, pit, false, null, 26); }));
    else m.guion.push(al(1, () => dar(m, ca)), al(1.5, () => lanzar(m, pit, false, null, 26)));
    if (pit) pit.tx = LOMA[0];
  }

  // ------------- tenis: el peloteo
  const CANCHA_T = { x0: 11, x1: 94, y0: 6, y1: 52, red: 52.5 };
  function tenis(m) {
    if (m.pausa) return;
    const j = m.js;
    if (m.guion) {
      while (m.guion.length && m.t >= m.guion[0].en) m.guion.shift().f();
      if (!m.guion.length) m.guion = null;
      return;
    }
    if (m.t < m.prox) return;
    const saca = m.saca || 0, s = j[saca], r = j[1 - saca];
    if (!s || !r) return;
    const lado = (m.ladoSaque = (m.ladoSaque || 0) + 1) % 2 ? 1 : -1;
    const al = (seg, f) => ({ en: m.t + seg, f });
    const fondo = (q) => (q.lado === 0 ? CANCHA_T.x0 - 3 : CANCHA_T.x1 + 3);
    s.tx = fondo(s); s.ty = 29 + lado * 8; r.tx = fondo(r); r.ty = 29 - lado * 10;
    const golpes = 3 + Math.floor(Math.random() * 8);
    const serie = [al(1, () => { dar(m, s); m.bt = null; })];
    let t = 2, de = s;
    for (let i = 0; i < golpes; i++) {
      const aQ = de === s ? r : s, tt = t, dest = [aQ.lado === 0 ? azar(CANCHA_T.x0 + 2, 38) : azar(67, CANCHA_T.x1 - 2), azar(CANCHA_T.y0 + 7, CANCHA_T.y1 - 7)];
      serie.push(al(tt, () => {
        aQ.tx = dest[0] + (aQ.lado === 0 ? -2.5 : 2.5); aQ.ty = dest[1];
        lanzar(m, null, i === 0, dest, i === 0 ? 85 : 64);
        m.objetivo = aQ;
      }));
      serie.push(al(tt + 0.85, () => dar(m, aQ)));
      t += 1.05; de = aQ;
    }
    const ult = de;
    serie.push(al(t, () => { const fuera = [ult.lado === 0 ? 100 : 5, azar(10, 48)]; lanzar(m, null, false, fuera, 42); }));
    serie.push(al(t + 1.1, () => { m.saca = (saca + (Math.random() < 0.25 ? 1 : 0)) % 2; dar(m, null); m.bt = [52.5, 55]; }));
    m.prox = m.t + t + 1.8;
    m.guion = serie;
  }

  const FASES = { NHL: { paso: flujo }, NBA: { paso: flujo }, NFL: { paso: nfl }, BEIS: { paso: beis }, Tenis: { paso: tenis } };

  function integrar(m, dt) {
    const s = SIM[m.fam] || { v: 11, vP: 9, vE: 16, rig: 3.8 }, quieto = m.pausa, A = ALTO[m.fam], port = m.port, parado = quieto || m.fijo;
    const velEq = m.fam === 'BEIS' ? 15 : m.fam === 'NFL' ? 13 : m.fam === 'Tenis' ? 22 : s.v, velC = m.fam === 'NFL' ? 12 : m.fam === 'BEIS' ? 15 : m.fam === 'Tenis' ? 22 : s.vP;
    m.js.forEach((q) => {
      if (q.oculto) return;
      const conduce = q === port && !parado && (m.fam === 'NHL' || m.fam === 'NBA');
      if (conduce) { q.tx = entre(6, q.cx + q.rx * 5, 99); q.ty = entre(4, q.cy + q.ry * 5, A - 4); }
      let tx = q.tx, ty = q.ty;
      if (!parado && q !== port && m.fam !== 'NFL' && m.fam !== 'BEIS') { tx += Math.sin(m.t * 0.9 + q.fase) * 1; ty += Math.cos(m.t * 0.7 + q.fase * 1.7) * 1; }
      if (m.fam === 'BEIS' && q.lado === 1 && !parado) { tx += Math.sin(m.t * 0.6 + q.fase) * 0.45; ty += Math.cos(m.t * 0.5 + q.fase) * 0.45; }
      const w = conduce ? s.rig * 1.4 : s.rig;
      q.vx += (w * w * (tx - q.cx) - 2 * w * q.vx) * dt; q.vy += (w * w * (ty - q.cy) - 2 * w * q.vy) * dt;
      const sp = Math.hypot(q.vx, q.vy), tope = conduce ? velC : m.fijo ? (s.vE || velEq * 1.4) : velEq;
      if (sp > tope) { q.vx *= tope / sp; q.vy *= tope / sp; }
      q.cx += q.vx * dt; q.cy += q.vy * dt;
      const bd = q === port ? 3 : 1.2;
      q.cx = Math.max(bd - (m.fam === 'Tenis' ? 2 : 0), Math.min(105 - bd + (m.fam === 'Tenis' ? 2 : 0), q.cx)); q.cy = Math.max(bd, Math.min(A - bd, q.cy));
    });
    let bx, by;
    if (m.vuelo) {
      const v = m.vuelo, u = Math.min(1, (m.t - v.t0) / v.T), e = u * (1.5 - 0.5 * u);
      bx = v.x0 + (v.x1 - v.x0) * e; by = v.y0 + (v.y1 - v.y0) * e;
      if (u >= 1) {
        const a = v.a; m.vuelo = null;
        if (a) { dar(m, a); const ang = (Math.random() - 0.5) * 1.2; a.rx = a.dir * Math.cos(ang); a.ry = Math.sin(ang); m.posesion = a.lado; m.prox = m.t + azar(0.3, 0.9); } else { m.bt = [bx, by]; }
      }
    } else {
      let ox = m.bx, oy = m.by, rap = 3;
      if (m.bt) { ox = m.bt[0]; oy = m.bt[1]; rap = 5; }
      else if (m.port) {
        const p = m.port, h = Math.hypot(p.vx, p.vy), hx = h > 1 ? p.vx / h : p.dir, hy = h > 1 ? p.vy / h : 0;
        const pie = m.fam === 'NFL' || m.fam === 'BEIS' ? 1.1 : 1.9;
        ox = p.cx + hx * pie; oy = p.cy + hy * pie + 0.3; rap = 16;
      }
      const f = 1 - Math.exp(-dt * rap);
      let dx = (ox - m.bx) * f, dy = (oy - m.by) * f;
      const d = Math.hypot(dx, dy), tope = 110 * dt;              // aunque cambie de dueño de golpe, el balón no salta
      if (d > tope) { dx *= tope / d; dy *= tope / d; }
      bx = m.bx + dx; by = m.by + dy;
    }
    m.bx = entre(0.2, bx, 104.8); m.by = entre(0.2, by, A - 0.2);
  }
  function dibujar(svg, m) {
    m.js.forEach((q) => {
      const el = svg._els[q.key]; if (!el) return;
      if (q.oculto) { if (!el._oculto) { el._oculto = true; el.style.display = 'none'; } return; }
      if (el._oculto) { el._oculto = false; el.style.display = ''; }
      el.style.transform = 'translate(' + q.cx.toFixed(2) + 'px,' + q.cy.toFixed(2) + 'px)';
    });
    if (svg._port !== m.portador) {
      const a = svg._port && svg._els[svg._port], b = m.portador && svg._els[m.portador];
      if (a) a.classList.remove('portador');
      if (b) b.classList.add('portador');
      svg._port = m.portador;
    }
    if (svg._nombresN !== m.nombresN) {
      svg._nombresN = m.nombresN;
      Object.entries(m.nombres || {}).forEach(([k, x]) => {
        const el = svg._els[k]; if (!el) return;
        const a = el.querySelector('.nom'), b = el.querySelector('.num');
        if (a) a.textContent = x.nombre;
        if (b) b.textContent = x.n;
      });
    }
    if (svg._balon) svg._balon.style.transform = 'translate(' + m.bx.toFixed(2) + 'px,' + m.by.toFixed(2) + 'px)';
    const ln = svg._pase;
    if (ln && svg._paseN !== m.paseN) {
      svg._paseN = m.paseN;
      if (m.pase) { ['x1', 'y1', 'x2', 'y2'].forEach((a, i) => ln.setAttribute(a, m.pase[i].toFixed(1))); ln.classList.add('ve'); void ln.getBBox(); }
    }
    if (ln && !m.vuelo && ln.classList.contains('ve')) ln.classList.remove('ve');
    const hayAviso = m.aviso && m.t < m.avisoHasta;
    if (svg._av !== (hayAviso ? m.aviso : '')) {
      svg._av = hayAviso ? m.aviso : '';
      if (svg._aviso) svg._aviso.textContent = svg._av;
      svg.classList.toggle('golazo', !!hayAviso);
    }
    if (m.fam === 'NFL' && svg._los && m.losX != null && svg._xLos !== m.losX) {
      svg._xLos = m.losX;
      svg._los.setAttribute('x1', m.losX); svg._los.setAttribute('x2', m.losX);
      const f = m.fdX == null ? -5 : m.fdX; svg._fd.setAttribute('x1', f); svg._fd.setAttribute('x2', f);
    }
    if (m.fam === 'BEIS') beisTexto(svg, m);
    const clave = (m.chipN || 0) + '|' + (m.baja || '') + (m.beisChip || '');
    if (svg._chip !== clave) {
      svg._chip = clave;
      const et = svg.parentElement && svg.parentElement.querySelector('.chip-ult');
      if (et) {
        const fresco = m.chipTxt && m.t - m.chipT < 5;
        if (fresco) et.innerHTML = m.chipTxt;
        else if (m.fam === 'NFL' && m.baja) et.innerHTML = '🏈 <b>' + esc(m.baja) + '</b>';
        else if (m.fam === 'BEIS' && m.beisChip) et.innerHTML = m.beisChip;
        else if (m.chipTxt) et.innerHTML = m.chipTxt;
        if (fresco && m.t - m.chipT < 1.5) { et.classList.remove('nuevo'); void et.offsetWidth; et.classList.add('nuevo'); }
      }
    }
  }
  function beisTexto(svg, m) {
    const b = (BEIS[m.clave] || {}).d; if (!b) return;
    const chip = '⚾ <b>' + (b.arriba ? '▲' : '▼') + ' ' + (b.entrada || '') + '</b> · ' + esc(b.bateador || '') + ' · ' + b.bolas + '-' + b.strikes + ' · ' + b.outs + ' out' + (b.outs === 1 ? '' : 's');
    if (m.beisChip !== chip) { m.beisChip = chip; m.chipN = (m.chipN || 0); }
    if (svg._b !== chip) {
      svg._b = chip;
      const nom = (r, n) => { const q = m.js.find((z) => z.rol === r); const el = q && svg._els[q.key]; const t = el && el.querySelector('.nom'); if (t) t.textContent = n || ''; };
      nom('bat', b.bateador); nom('p', b.lanzador); ['ca', 'c1b', 'c2b', 'c3b', 'ss', 'lf', 'cf', 'rf', 'r1', 'r2', 'r3'].forEach((r) => nom(r, (b.nombres || {})[r]));
      // bateador, lanzador y corredores siempre con su nombre: es lo que de verdad se sabe
      ['bat', 'p', 'r1', 'r2', 'r3'].forEach((r) => { const q = m.js.find((z) => z.rol === r), el = q && svg._els[q.key]; if (el) el.classList.add('nombrado'); });
      svg.querySelectorAll('.base').forEach((el) => { el.classList.toggle('ocupada', !!b['en' + el.dataset.base]); });
      // el que batea va de su color; el fildeo, del otro
      const c = (m.v && m.v.colores) || null;
      if (c) {
        const cols = colores(m.v, 'BEIS'), def = cols[b.batea === 0 ? 1 : 0], ofe = cols[b.batea === 0 ? 0 : 1];
        m.js.forEach((q) => { const el = svg._els[q.key]; if (el) el.querySelectorAll('circle').forEach((x) => x.setAttribute('fill', q.lado === 1 ? def : ofe)); });
      }
    }
  }
  let tAnt = 0;
  function bucle(ts) {
    requestAnimationFrame(bucle);
    const dt = Math.min(0.1, Math.max(0, (ts - tAnt) / 1000)); tAnt = ts;
    if (document.hidden) return;
    adoptar();
    if (CALMA) return;
    const vistas = {};
    document.querySelectorAll('.pista-svg[data-vivo]').forEach((svg) => {
      const rc = svg.getBoundingClientRect();
      if (rc.bottom < 0 || rc.top > window.innerHeight || !rc.height) return;
      (vistas[svg.dataset.pista] = vistas[svg.dataset.pista] || []).push(svg);
    });
    Object.entries(vistas).forEach(([k, svgs]) => {
      const m = MOTORES[k]; if (!m) return;
      m.clave = k;
      preparar(svgs[0], m);
      if (!m.js.length) return;
      if (m.fam === 'BEIS' && m.p && m.v && m.v.fase === 'in') pedirBeisbol(k, m.p);
      if (dt > 0) {
        m.t += dt;
        if (m.pausa) { m.js.forEach((q) => { q.tx = q.x0; q.ty = q.y0; }); dar(m, null); m.bt = [52.5, ALTO[m.fam] / 2]; m.guion = null; m.fijo = false; } else FASES[m.fam].paso(m);
        if (!m.pausa && m.guion === undefined) m.guion = null;
        integrar(m, dt);
      }
      svgs.forEach((s) => dibujar(s, m));
    });
  }
  requestAnimationFrame(bucle);
  window.Pistas = { TIENE, html, leer, MOTORES, mismoEquipo };
})();
