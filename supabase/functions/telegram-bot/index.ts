// v527 — EL BOT DE TELEGRAM CONTESTA (webhook): liga la cuenta de SharPicks de quien le escribe.
//   «/start CÓDIGO» (el botón «Conectar Telegram» de Mi cuenta abre t.me/<bot>?start=CÓDIGO) → guarda su chat;
//   «/stop» → deja de mandarle avisos. Telegram firma cada llamada con X-Telegram-Bot-Api-Secret-Token (Vault).
// {"configurar": true} con la clave del cron: registra este webhook en Telegram y guarda el nombre del bot en
// `ajustes.telegram_bot` (lo usa la página para el enlace).

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
      const w = await tg('setWebhook', { url: URL_FN, secret_token: s.telegram_webhook, allowed_updates: ['message'], drop_pending_updates: true });
      if (yo.result && yo.result.username) {
        await fetch(SB + 'ajustes', { method: 'POST', headers: { ...H, Prefer: 'resolution=merge-duplicates,return=minimal' },
          body: JSON.stringify({ clave: 'telegram_bot', valor: yo.result.username }) });
      }
      return Response.json({ bot: yo.result && yo.result.username, webhook: w.ok, descripcion: w.description });
    }
    // 2. lo que le escriben al bot (firmado por Telegram)
    if (!s.telegram_webhook || req.headers.get('x-telegram-bot-api-secret-token') !== s.telegram_webhook) return new Response('no', { status: 401 });
    const u = await req.json().catch(() => ({}));
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
