-- v584 — al borrar una cuenta, la compra queda sin identificar en vez de desaparecer: hace falta para la contabilidad.
alter table public.compras alter column usuario drop not null;
alter table public.compras drop constraint if exists compras_usuario_fkey;
alter table public.compras add constraint compras_usuario_fkey foreign key (usuario) references auth.users (id) on delete set null;
