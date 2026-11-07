#!/usr/bin/env bash
# El despertador de SharPicks, en el servidor (ADR-0002). Lo corre un temporizador de systemd cada 15 min.
# Viene de herramientas/despertador_sharpicks.ps1 (v516): el 29-oct, con el repo privado, GitHub no disparó
# ningún cron en 5 h. workflow_dispatch sí es fiable, así que aquí se despiertan los flujos:
#   · cuotas_mx (y con ella precálculo y relevo) y sitio_web, si llevan más de 55 min sin correr;
#   · los diarios y el semanal a la hora de su cron, una vez, si no han corrido ya.
#
# Un solo interruptor, la variable de GitHub DESPERTADOR:
#   · sin ella, sólo anota lo que haría y no lanza nada;
#   · con DESPERTADOR=activo lanza, y telegram_bot y telegram_dia_completo se saltan su cron (ver esos flujos):
#     un cron atrasado ya no puede mandar el mensaje por segunda vez.
#
# Diferencias con el .ps1:
#   · si no se puede leer GitHub, NO lanza. El .ps1 tomaba el error como «nunca corrió» y lanzaba todo, Telegram
#     incluido;
#   · añade vigia_limites, que nació después del .ps1.
#
# Necesita GH_TOKEN (token de grano fino sólo de este repo: Actions lectura/escritura, Variables lectura).
# Uso: despertador.sh [--seco]   --seco nunca lanza, aunque DESPERTADOR esté activo.
# DESPERTADOR_AHORA (segundos Unix) fija el reloj en las pruebas.
set -uo pipefail

REPO="${REPO:-HectorMontiel/sharpicks}"
AHORA="${DESPERTADOR_AHORA:-$(date -u +%s)}"
SECO=0
[ "${1:-}" = "--seco" ] && SECO=1
: "${GH_TOKEN:?falta GH_TOKEN}"

HOY=$(( AHORA - AHORA % 86400 ))
FALLOS=0
LANZADOS=" "
U=0

anota() { echo "$(date -u -d "@$AHORA" +%Y-%m-%dT%H:%MZ) $*"; }

# El token va por --config y no por -H: los argumentos de un proceso los ve cualquier usuario, incluido el de los runners.
api() {
  local metodo=$1 ruta=$2 cuerpo=${3:-}
  local args=(-fsS --max-time 30 -X "$metodo" -H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2022-11-28')
  [ -n "$cuerpo" ] && args+=(-d "$cuerpo")
  curl "${args[@]}" --config <(printf 'header = "Authorization: Bearer %s"\n' "$GH_TOKEN") \
    "https://api.github.com/repos/$REPO/$ruta"
}

# Deja en U la hora de la última corrida en main; 0 si nunca corrió. Devuelve 1 si no se pudo saber.
# Con «sin_cron» no cuenta las corridas de cron: con el despertador activo son las que se saltó Telegram.
ultima_corrida() {
  local wf=$1 sin_cron=${2:-} j fecha
  j=$(api GET "actions/workflows/$wf/runs?branch=main&per_page=10") || return 1
  fecha=$(jq -er --arg sc "$sin_cron" \
    'if (.workflow_runs | type) != "array" then error("respuesta rara") else
       (.workflow_runs | map(select($sc == "" or .event != "schedule")) | .[0].created_at) // "" end' <<<"$j" 2>/dev/null) || return 1
  if [ -z "$fecha" ]; then U=0; else U=$(date -u -d "$fecha" +%s) || return 1; fi
}

lanza() {
  local wf=$1 cuerpo=$2
  case "$LANZADOS" in *" $wf "*) return 0 ;; esac
  LANZADOS="$LANZADOS$wf "
  if [ "$SECO" = 1 ]; then anota "[seco] lanzaría $wf"; return 0; fi
  if api POST "actions/workflows/$wf/dispatches" "$cuerpo" >/dev/null; then
    anota "lanzado $wf"
  else
    anota "FALLO al lanzar $wf"; FALLOS=$(( FALLOS + 1 ))
  fi
}

revisa_cada_hora() {
  local wf=$1 cuerpo=$2 minutos=${3:-55}
  if ! ultima_corrida "$wf"; then anota "FALLO al leer $wf: no se lanza"; FALLOS=$(( FALLOS + 1 )); return; fi
  if [ $(( AHORA - U )) -gt $(( minutos * 60 )) ]; then lanza "$wf" "$cuerpo"; fi
}

# ventana (min): tope de atraso para lo que se ve afuera. Un envío de la mañana no sale a media tarde. 0 = sin tope.
revisa_diario() {
  local wf=$1 h=$2 m=$3 ventana=$4 hora=$(( HOY + $2 * 3600 + $3 * 60 )) sin_cron=""
  [ "$AHORA" -ge "$hora" ] || return 0
  if [ "$ventana" -gt 0 ]; then
    [ $(( AHORA - hora )) -le $(( ventana * 60 )) ] || return 0
    [ "$SECO" = 1 ] || sin_cron=si
  fi
  if ! ultima_corrida "$wf" "$sin_cron"; then anota "FALLO al leer $wf: no se lanza"; FALLOS=$(( FALLOS + 1 )); return; fi
  if [ "$U" -lt "$hora" ]; then lanza "$wf" '{"ref":"main"}'; fi
}

# El interruptor. Si no se puede leer, no se sabe si Telegram se salta su cron: no se lanza nada.
if ! VARS=$(api GET "actions/variables?per_page=30") \
  || ! ESTADO=$(jq -er 'if (.variables | type) != "array" then error("respuesta rara") else
       (.variables | map(select(.name == "DESPERTADOR")) | .[0].value) // "" end' <<<"$VARS" 2>/dev/null); then
  anota "FALLO al leer la variable DESPERTADOR: no se lanza nada"
  exit 1
fi
if [ "$ESTADO" != activo ] && [ "$SECO" = 0 ]; then
  anota "DESPERTADOR no está activo: sólo se anota"
  SECO=1
fi

# Sólo GitHub puede leer esas dos fuentes (v594). Cada 2 h: en privado, cada hora se pasaría de los 2,000 min gratis.
revisa_cada_hora foto_precios.yml '{"ref":"main"}' 115
revisa_cada_hora cuotas_mx.yml '{"ref":"main","inputs":{"forzar":"false"}}'
revisa_cada_hora sitio_web.yml '{"ref":"main"}'

# flujo  hora  minuto  ventana. Una prueba compara esta tabla con el cron de cada flujo.
while read -r wf h m ventana; do
  [ -n "$wf" ] && revisa_diario "$wf" "$h" "$m" "$ventana"
done <<'TABLA'
vigia_limites.yml 1 47 0
precalcular_rosters.yml 4 43 0
retrain_leagues.yml 5 47 0
radar_diario.yml 6 17 0
telegram_dia_completo.yml 6 41 180
respaldo_base.yml 9 15 0
telegram_bot.yml 10 19 180
vigia_limites.yml 13 17 0
TABLA

if [ "$(date -u -d "@$AHORA" +%u)" = 1 ]; then revisa_diario recalibrar.yml 5 29 0; fi

[ "$FALLOS" = 0 ]
