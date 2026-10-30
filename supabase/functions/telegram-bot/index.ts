// v527 — EL BOT DE TELEGRAM CONTESTA (webhook): liga la cuenta de SharPicks de quien le escribe.
//   «/start CÓDIGO» (el botón «Conectar Telegram» de Mi cuenta abre t.me/<bot>?start=CÓDIGO) → guarda su chat;
//   «/stop» → deja de mandarle avisos. Telegram firma cada llamada con X-Telegram-Bot-Api-Secret-Token (Vault).
// {"configurar": true} con la clave del cron: registra este webhook en Telegram y guarda el nombre del bot en
// `ajustes.telegram_bot` (lo usa la página para el enlace).
// v534 — EL GRUPO VIP CON LLAVE: su enlace pide permiso; el bot aprueba sólo si ese Telegram está ligado a una cuenta
// VIP vigente (telegram_quien) y si no, lo rechaza y le dice qué hacer. «configurar» crea ese enlace, apaga el viejo
// y lo guarda en `privados.telegram_vip` (el que da «Entrar al grupo VIP» en Mi cuenta).

type Dic = Record<string, any>;
const SB = (Deno.env.get('SUPABASE_URL') || '').replace(/\/$/, '') + '/rest/v1/';
const KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') || '';
const H = { apikey: KEY, Authorization: 'Bearer ' + KEY, 'Content-Type': 'application/json' };
const URL_FN = (Deno.env.get('SUPABASE_URL') || '').replace(/\/$/, '') + '/functions/v1/telegram-bot';

let S: Dic | null = null;
async function secretos() {
  if (S) return S;
  const r = await fetch(SB + 'rpc/leer_secretos_pulso', { method: 'POST', headers: H, body: '{}' });
  S = Object.fromEntries(((r.ok ? await r.json() : []) as Dic[]).map((x) => [x.nombre, x.valor]));
  return S!;
}
async function tg(metodo: string, cuerpo: Dic) {
  const s = await secretos();
  const r = await fetch(`https://api.telegram.org/bot${s.TELEGRAM_BOT_TOKEN}/${metodo}`, { method: 'POST',
    headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(cuerpo) });
  return r.json().catch(() => ({}));
}
const decir = (chat: number, texto: string) => tg('sendMessage', { chat_id: chat, text: texto, parse_mode: 'HTML', disable_web_page_preview: true });

Deno.serve(async (req) => {
  const s = await secretos();
  try {
    // 1. configurar el webhook (sólo con la clave del cron)
    if (req.headers.get('x-pulso-clave')) {
      if (req.headers.get('x-pulso-clave') !== s.pulso_cron) return new Response('no', { status: 401 });
      const yo = await tg('getMe', {});
      const w = await tg('setWebhook', { url: URL_FN, secret_token: s.telegram_webhook, allowed_updates: ['message', 'chat_join_request'], drop_pending_updates: true });
      if (yo.result && yo.result.username) {
        await fetch(SB + 'ajustes', { method: 'POST', headers: { ...H, Prefer: 'resolution=merge-duplicates,return=minimal' },
          body: JSON.stringify({ clave: 'telegram_bot', valor: yo.result.username }) });
      }
      // los permisos del bot en el grupo VIP (aprobar entradas y sacar gente) y el enlace con aprobación
      const permisos = yo.result ? await tg('getChatMember', { chat_id: s.TELEGRAM_CHAT_VIP, user_id: yo.result.id }) : {};
      let enlace: Dic = {};
      if ((await req.clone().json().catch(() => ({}))).enlace_vip) {
        const viejo = await (await fetch(SB + 'privados?select=valor&clave=eq.telegram_vip', { headers: H })).json().catch(() => []);
        enlace = await tg('createChatInviteLink', { chat_id: s.TELEGRAM_CHAT_VIP, name: 'SharPicks VIP (con aprobación)', creates_join_request: true });
        if (enlace.ok && enlace.result && enlace.result.invite_link) {
          await fetch(SB + 'privados?clave=eq.telegram_vip', { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' },
            body: JSON.stringify({ valor: enlace.result.invite_link }) });
          if (viejo[0] && viejo[0].valor && viejo[0].valor !== enlace.result.invite_link) {
            const r = await tg('revokeChatInviteLink', { chat_id: s.TELEGRAM_CHAT_VIP, invite_link: viejo[0].valor });
            enlace.viejo_apagado = !!r.ok; enlace.viejo_motivo = r.description;
          }
        }
      }
      // v538 — la descripción del canal gratis (sólo ése, sólo este texto fijo: la manda el administrador desde aquí)
      const cuerpoC = await req.clone().json().catch(() => ({}));
      let desc: Dic = {};
      if (cuerpoC.descripcion_gratis && s.TELEGRAM_CHAT_GRATIS) {
        desc = await tg('setChatDescription', { chat_id: s.TELEGRAM_CHAT_GRATIS, description: 'Picks medidos, no adivinados. En vivo en sharpicksapp.com · +18' });
      }
      const pr = permisos.result || {};
      return Response.json({ bot: yo.result && yo.result.username, webhook: w.ok, descripcion: w.description,
        vip: { estado: pr.status, aprobar: pr.can_invite_users, sacar: pr.can_restrict_members },
        enlace_creado: !!(enlace.ok && enlace.result), enlace_viejo_apagado: enlace.viejo_apagado, motivo: enlace.description || enlace.viejo_motivo,
        descripcion_gratis: desc.ok, descripcion_motivo: desc.description });
    }
    // 2. lo que le escriben al bot (firmado por Telegram)
    if (!s.telegram_webhook || req.headers.get('x-telegram-bot-api-secret-token') !== s.telegram_webhook) return new Response('no', { status: 401 });
    const u = await req.json().catch(() => ({}));
    // v534 — alguien pide entrar al grupo VIP: se revisa en la app si su Telegram es de una cuenta VIP vigente
    const jr = u.chat_join_request;
    if (jr && jr.chat && String(jr.chat.id) === String(s.TELEGRAM_CHAT_VIP)) {
      const quien = jr.from && jr.from.id;
      const q = await (await fetch(SB + 'rpc/telegram_quien', { method: 'POST', headers: H, body: JSON.stringify({ p_chat: quien }) })).json().catch(() => []);
      const fila = q[0];
      if (fila && fila.vip) {
        await tg('approveChatJoinRequest', { chat_id: jr.chat.id, user_id: quien });
        await fetch(SB + `telegram_usuarios?usuario=eq.${fila.usuario}`, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ en_vip: true }) });
        await decir(quien, '💎 <b>¡Bienvenido al VIP de SharPicks!</b> Ya estás dentro. Aquí llegan los picks VIP, los errores de cuota y el ⚡ Pulso completo.');
      } else if (fila) {
        // ligado pero sin VIP vigente: fuera, y a comprarlo en la app
        await tg('declineChatJoinRequest', { chat_id: jr.chat.id, user_id: quien });
        await decir(quien, '🔒 Tu cuenta de SharPicks no tiene VIP activo, por eso no pudimos dejarte entrar al grupo VIP.\n\n👉 Hazte VIP en sharpicksapp.com → Planes y vuelve a pedir entrar: te aprobamos al momento.');
      } else {
        // v536 — sin ligar: la solicitud se queda ESPERANDO; al ligar su Telegram, si es VIP, se aprueba sola
        await decir(quien, '👋 Para entrar al grupo VIP conecta tu Telegram con tu cuenta de SharPicks: sharpicksapp.com → <b>Mi cuenta</b> → <b>Conectar Telegram</b>.\n\n' +
          'Tu solicitud se queda esperando: en cuanto lo conectes, si tienes VIP te aprobamos solo. ¿Aún no eres VIP? Hazte VIP en Planes.');
      }
      return new Response('ok');
    }
    const m = u.message || {}, chat = m.chat && m.chat.id, texto = String(m.text || '').trim();
    if (!chat || !m.chat || m.chat.type !== 'private') return new Response('ok');
    const cod = (texto.match(/^\/start\s+([A-Za-z0-9]{6,20})$/) || [])[1];
    if (cod) {
      const f = await (await fetch(SB + `telegram_usuarios?select=usuario,codigo_hasta&codigo=eq.${encodeURIComponent(cod.toUpperCase())}`, { headers: H })).json();
      if (!f.length || new Date(f[0].codigo_hasta).getTime() < Date.now()) {
        await decir(chat, '⏳ Ese enlace ya venció. Vuelve a tocar <b>Conectar Telegram</b> en sharpicksapp.com → Mi cuenta.');
        return new Response('ok');
      }
      // un chat, una cuenta: si este chat estaba ligado a otra, se suelta
      await fetch(SB + `telegram_usuarios?chat=eq.${chat}`, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ chat: null, ligado: null }) });
      await fetch(SB + `telegram_usuarios?usuario=eq.${f[0].usuario}`, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' },
        body: JSON.stringify({ chat, codigo: null, codigo_hasta: null, ligado: new Date().toISOString() }) });
      // v536 — si pidió entrar al grupo VIP antes de ligarse y es VIP, se le aprueba ya (si no había solicitud, no pasa nada)
      const q = await (await fetch(SB + 'rpc/telegram_quien', { method: 'POST', headers: H, body: JSON.stringify({ p_chat: chat }) })).json().catch(() => []);
      if (q[0] && q[0].vip) {
        const ap = await tg('approveChatJoinRequest', { chat_id: s.TELEGRAM_CHAT_VIP, user_id: chat });
        if (ap.ok) {
          await fetch(SB + `telegram_usuarios?usuario=eq.${f[0].usuario}`, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ en_vip: true }) });
          await decir(chat, '💎 <b>¡Bienvenido al VIP de SharPicks!</b> Tu solicitud quedó aprobada: ya estás dentro del grupo VIP.');
        }
      }
      await decir(chat, '✅ <b>¡Listo! Tu cuenta de SharPicks quedó conectada</b> 🔔\n\n' +
        'Elige en la app qué quieres que te avisemos: tus deportes, el ⚡ Pulso en vivo o un partido en específico (la 🔔 en «Ver partido»).\n\n' +
        'Para dejar de recibir avisos escribe /stop');
      return new Response('ok');
    }
    if (/^\/stop\b/.test(texto)) {
      await fetch(SB + `telegram_usuarios?chat=eq.${chat}`, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ chat: null, ligado: null }) });
      await decir(chat, '🔕 Listo, ya no te mandaremos avisos. Para volver, toca <b>Conectar Telegram</b> en sharpicksapp.com → Mi cuenta.');
      return new Response('ok');
    }
    await decir(chat, '👋 ¡Hola! Soy el bot de <b>SharPicks</b>.\n\nPara recibir tus avisos (picks de tus deportes, el ⚡ Pulso en vivo o un partido en específico), ' +
      'entra a sharpicksapp.com → <b>Mi cuenta</b> → <b>Conectar Telegram</b>.');
    return new Response('ok');
  } catch (_) {
    return new Response('ok');                                 // a Telegram siempre «ok»: si no, reintenta sin fin
  }
});
