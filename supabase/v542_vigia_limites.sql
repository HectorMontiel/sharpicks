-- v542 — EL VIGILANTE DE LÍMITES. El usuario (30-oct): «no creo que necesitemos al lanzar cambiarnos al plan de paga, a
-- menos que tú me digas y estés monitoreando cuándo ya estemos en riesgo de colapso… si a los 1000 usuarios es el límite,
-- a los 800 me tienes que estar avisando». `vigia_limites.py` (cada día, en GitHub) mide el uso contra los límites del
-- plan gratis de Supabase y guarda aquí lo medido y los avisos ya mandados (uno por métrica, nivel y mes).

create table if not exists public.vigia_uso (
  fecha date not null,
  metrica text not null,
  valor numeric not null,
  limite numeric,
  detalle jsonb,
  primary key (fecha, metrica)
);
create table if not exists public.vigia_avisos (
  mes text not null,
  metrica text not null,
  nivel int not null,
  enviado timestamptz not null default now(),
  primary key (mes, metrica, nivel)
);
alter table public.vigia_uso enable row level security;
alter table public.vigia_avisos enable row level security;
revoke all on public.vigia_uso from public, anon, authenticated;
revoke all on public.vigia_avisos from public, anon, authenticated;
grant all on public.vigia_uso to service_role;
grant all on public.vigia_avisos to service_role;
