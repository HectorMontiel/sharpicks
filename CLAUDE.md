# SharPicks — reglas del proyecto

- Responder SIEMPRE en español sencillo, con el menor texto posible.
- Antes de implementar: revisar `.claude/memoria.md` y el índice de memoria (MEMORY.md). No repetir un
  análisis o una medición que ya esté anotada; si una nota contradice lo que se va a hacer, avisar primero.
- Medir antes de enseñar: dos mitades y p5 > 0. Lo que no gana, no se publica.
- CERO fallos para publicar. La suite de SIEMPRE es la dirigida: `bash /d/Claude/herramientas/suite_dirigida.sh`
  (elige sola los tests que importan o leen lo cambiado, a dos saltos; corre el render de Streamlit y el
  catálogo sólo si el cambio los alcanza; workflows y JSON: los tests que los leen por su nombre; ~5 min).
  La completa (`suite.sh`, 40-70 min) sólo: los domingos, tras cambiar requirements o las herramientas, o si
  la dirigida no elige nada para un cambio de código.
  Mientras corre cualquiera, un hook bloquea editar código (no saltarlo).
- Skills del proyecto: `/medir` (protocolo de medición), `/publicar` (suite → producción verificada), `/handoff`.
- Antes de cada commit: `git checkout HEAD --` de los artefactos (activacion_v212.json,
  goleadores_cache.json, nombres_sin_mapear.json, pick_ledger_totales.csv, pronosticos_emitidos.json,
  radar_capturas.csv, radar_errores.json); luego `git pull --rebase` y push.
- SQL nuevo siempre en una migración NUEVA (`supabase/`).
- En bash: `rm -f "${D:?}"/*`, nunca `$D` sin `:?`. Textos en español: Write o .py puente, no heredoc.
- Guardar en memoria cada decisión técnica importante con su fecha (y actualizar `.claude/memoria.md`).
