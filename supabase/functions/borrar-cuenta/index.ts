// v584 — BORRAR MI CUENTA. El usuario la borra solo desde Mi cuenta (derecho de cancelación, LFPDPPP).
// Orden importante: primero se cancela lo que cobra; si eso falla NO se borra nada, porque quedaría cobrando sin cuenta.
// Lo de pago queda sin identificar (compras.usuario → null); Stripe y Mercado Pago guardan sus propios registros.
import { createClient } from 'npm:@supabase/supabase-js@2.45.4';

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
};
const json = (d: unknown, s = 200) => new Response(JSON.stringify(d), { status: s, headers: { ...CORS, 'Content-Type': 'application/json' } });

async function cancelarCobro(id: string): Promise<boolean> {
  if (id.startsWith('stripe:')) {
    const SK = Deno.env.get('STRIPE_SECRET_KEY');
    if (!SK) return false;
    const r = await fetch('https://api.stripe.com/v1/subscriptions/' + id.slice(7), { method: 'DELETE', headers: { Authorization: 'Bearer ' + SK } });
    return r.ok || r.status === 404;          // 404: ya no existe, no hay nada que cobre
  }
  const MP = Deno.env.get('MP_ACCESS_TOKEN');
  if (!MP) return false;
  const r = await fetch('https://api.mercadopago.com/preapproval/' + id, {
    method: 'PUT', headers: { Authorization: 'Bearer ' + MP, 'Content-Type': 'application/json' }, body: JSON.stringify({ status: 'cancelled' }) });
  return r.ok || r.status === 404;
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: CORS });
  try {
    const URL_ = Deno.env.get('SUPABASE_URL')!;
    const yo = createClient(URL_, Deno.env.get('SUPABASE_ANON_KEY')!, {
      global: { headers: { Authorization: req.headers.get('Authorization') ?? '' } }, auth: { persistSession: false } });
    const { data: { user } } = await yo.auth.getUser();
    if (!user) return json({ error: 'Inicia sesión.' }, 401);
    const { confirmar } = await req.json().catch(() => ({}));
    if (confirmar !== true) return json({ error: 'Falta confirmar.' }, 400);

    const admin = createClient(URL_, Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!, { auth: { persistSession: false } });
    const { data: pf } = await admin.from('perfiles').select('usuario,admin').eq('id', user.id).maybeSingle();
    if (pf?.admin) return json({ error: 'Una cuenta de administrador no se borra desde aquí.' }, 403);

    const { data: subs } = await admin.from('suscripciones').select('id').eq('usuario', user.id).in('estado', ['authorized', 'pending', 'cancela_al_final']);
    for (const s of subs || []) {
      if (!(await cancelarCobro(String(s.id)))) return json({ error: 'No se pudo cancelar tu renovación, así que no se borró nada. Intenta de nuevo en un momento.' }, 502);
    }

    // el grupo VIP: al borrar la fila de Telegram ya nadie lo sacaría al vencer
    const { data: tg } = await admin.from('telegram_usuarios').select('chat').eq('usuario', user.id).maybeSingle();
    if (tg?.chat) {
      const { data: sec } = await admin.rpc('leer_secretos_pulso');
      const s: Record<string, string> = {};
      for (const x of (sec || []) as { nombre: string; valor: string }[]) s[x.nombre] = x.valor;
      if (s.TELEGRAM_BOT_TOKEN && s.TELEGRAM_CHAT_VIP) {
        const tgApi = (m: string) => fetch(`https://api.telegram.org/bot${s.TELEGRAM_BOT_TOKEN}/${m}`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ chat_id: s.TELEGRAM_CHAT_VIP, user_id: tg.chat, only_if_banned: true }) }).catch(() => null);
        await tgApi('banChatMember');
        await tgApi('unbanChatMember');
      }
    }

    // lo que no cuelga de auth.users
    const nombres = [pf?.usuario, user.email].filter(Boolean).map((x) => String(x).toLowerCase());
    await admin.from('comentarios').delete().eq('usuario', user.id);
    await admin.from('codigos_intentos').delete().eq('usuario', user.id);
    if (nombres.length) await admin.from('intentos_entrar').delete().in('usuario', nombres);

    const { error } = await admin.auth.admin.deleteUser(user.id);
    if (error) return json({ error: 'No se pudo borrar tu cuenta. Intenta de nuevo o escríbenos a sharpicks.bet@gmail.com.' }, 500);
    return json({ ok: true });
  } catch (_e) {
    return json({ error: 'No se pudo borrar tu cuenta. Intenta de nuevo o escríbenos a sharpicks.bet@gmail.com.' }, 500);
  }
});
