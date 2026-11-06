# SharPicks — reglas del proyecto

- Responder SIEMPRE en español sencillo, con el menor texto posible.
- Antes de implementar: revisar `.claude/memoria.md` y el índice de memoria (MEMORY.md). No repetir un
  análisis o una medición que ya esté anotada; si una nota contradice lo que se va a hacer, avisar primero.
- Medir antes de enseñar: dos mitades y p5 > 0. Lo que no gana, no se publica.
- CERO fallos en lo que se corre. REGLA DEL USUARIO: la suite no tarda salvo que haga falta. Decidir antes de correr:
  · Memoria, documentos, mediciones o SQL sin código: nada.
  · Textos, comentarios, diccionario, una prueba: sólo las pruebas de ese archivo.
  · Arreglo tras una falla: sólo las que fallaron y las que tocan lo corregido. Nunca repetir la suite entera.
  · Lógica nueva: `bash /d/Claude/herramientas/suite_dirigida.sh` UNA vez antes de publicar (~5 min).
  · Flujos de GitHub: las pruebas que los leen y validar el YAML; se comprueban corriéndolos.
  · Lo que decide picks o toca el render: dirigida, aunque incluya catálogo o render.
  · Completa (`suite.sh`, 40-70 min): domingos, o tras cambiar requirements o las herramientas de la suite.
  Si la dirigida va a tardar más de ~10 min sin que el cambio decida picks, parar y correr sólo lo relevante.
  Mientras corre cualquiera, un hook bloquea editar código (no saltarlo).
- Skills del proyecto: `/medir` (protocolo de medición), `/publicar` (suite → producción verificada), `/handoff`.
- Antes de cada commit: `git checkout HEAD --` de los artefactos (activacion_v212.json,
  goleadores_cache.json, nombres_sin_mapear.json, pick_ledger_totales.csv, pronosticos_emitidos.json,
  radar_capturas.csv, radar_errores.json); luego `git pull --rebase` y push.
- SQL nuevo siempre en una migración NUEVA (`supabase/`).
- En bash: `rm -f "${D:?}"/*`, nunca `$D` sin `:?`. Textos en español: Write o .py puente, no heredoc.
- Guardar en memoria cada decisión técnica importante con su fecha (y actualizar `.claude/memoria.md`).
