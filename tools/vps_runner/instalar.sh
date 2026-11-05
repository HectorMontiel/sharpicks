#!/usr/bin/env bash
# Prepara un servidor Ubuntu 24.04 (x64) con runners propios de GitHub Actions para SharPicks (ADR-0002).
# Se corre UNA vez, como root, en el servidor:
#
#   RUNNER_REG_TOKEN=<token de registro> REPO=HectorMontiel/sharpicks N=4 bash instalar.sh
#
# El token de registro dura 1 hora y sólo sirve para registrar runners. Se saca con:
#   gh api -X POST repos/HectorMontiel/sharpicks/actions/runners/registration-token -q .token
# No se guarda en ningún archivo ni se imprime. Seguro de repetir: lo ya registrado se salta.
set -euo pipefail

: "${RUNNER_REG_TOKEN:?falta RUNNER_REG_TOKEN}"
REPO="${REPO:-HectorMontiel/sharpicks}"
N="${N:-4}"            # 1 se queda con el Relevo (dormido, no gasta) y 3 trabajan; medido: 98 % del tiempo corren ≤ 2
ETIQUETA="sharpicks-vps"
BASE=/opt/runners
USUARIO=runner

[ "$(id -u)" = 0 ] || { echo "corre esto como root" >&2; exit 1; }
[ "$(uname -m)" = x86_64 ] || { echo "sólo x64: setup-python no siempre tiene versiones ARM" >&2; exit 1; }

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git curl jq unzip build-essential libgomp1 libicu-dev ca-certificates ufw unattended-upgrades

# memoria de respaldo: el reentreno y el precálculo tienen picos
if [ ! -f /swapfile ]; then
  fallocate -l 8G /swapfile && chmod 600 /swapfile && mkswap /swapfile >/dev/null && swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# sólo SSH hacia adentro: los runners salen a GitHub, nadie entra a ellos
ufw allow OpenSSH >/dev/null && ufw --force enable >/dev/null

id "$USUARIO" >/dev/null 2>&1 || useradd -m -s /bin/bash "$USUARIO"
mkdir -p "$BASE" /opt/hostedtoolcache
chown -R "$USUARIO":"$USUARIO" "$BASE" /opt/hostedtoolcache

# la versión más nueva del runner, verificada con el SHA-256 que GitHub publica en sus notas de versión
REL=$(curl -fsSL https://api.github.com/repos/actions/runner/releases/latest)
VER=$(jq -r .tag_name <<<"$REL" | sed 's/^v//')
SHA=$(jq -r .body <<<"$REL" | sed -n 's/.*BEGIN SHA linux-x64 -->\([0-9a-f]\{64\}\)<!-- END SHA linux-x64.*/\1/p' | head -1)
[ -n "$SHA" ] || { echo "no se encontró el SHA-256 del runner" >&2; exit 1; }
TGZ="/tmp/actions-runner-$VER.tar.gz"
curl -fsSL -o "$TGZ" "https://github.com/actions/runner/releases/download/v$VER/actions-runner-linux-x64-$VER.tar.gz"
echo "$SHA  $TGZ" | sha256sum -c - >/dev/null

# antes de cada trabajo: quita lo que un trabajo anterior dejó en la carpeta del runner (v519: un checkout parcial
# dejado por otro flujo vació el repo del siguiente)
cat > "$BASE/antes_del_trabajo.sh" <<'EOF'
#!/usr/bin/env bash
if [ -d "${GITHUB_WORKSPACE:-}/.git" ]; then
  git -C "$GITHUB_WORKSPACE" config --unset-all core.sparseCheckout 2>/dev/null || true
  rm -f "$GITHUB_WORKSPACE/.git/info/sparse-checkout" "$GITHUB_WORKSPACE"/.git/index.lock 2>/dev/null || true
fi
# si el disco va a más de 85 %, se limpian espacios de trabajo viejos (más de 7 días sin usar)
USO=$(df --output=pcent / | tail -1 | tr -dc 0-9)
if [ "${USO:-0}" -gt 85 ]; then
  find /opt/runners/r*/_work -mindepth 2 -maxdepth 2 -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true
fi
exit 0
EOF
chmod +x "$BASE/antes_del_trabajo.sh"

for i in $(seq 1 "$N"); do
  D="$BASE/r$i"
  if [ -f "$D/.runner" ]; then echo "r$i ya estaba registrado"; continue; fi
  mkdir -p "$D" && tar xzf "$TGZ" -C "$D" && chown -R "$USUARIO":"$USUARIO" "$D"
  "$D/bin/installdependencies.sh" >/dev/null
  cat > "$D/.env" <<EOF
LANG=C.UTF-8
AGENT_TOOLSDIRECTORY=/opt/hostedtoolcache
RUNNER_TOOL_CACHE=/opt/hostedtoolcache
ACTIONS_RUNNER_HOOK_JOB_STARTED=$BASE/antes_del_trabajo.sh
EOF
  chown "$USUARIO":"$USUARIO" "$D/.env"
  su - "$USUARIO" -c "cd '$D' && ./config.sh --unattended --url 'https://github.com/$REPO' --token '$RUNNER_REG_TOKEN' --name '$(hostname)-r$i' --labels '$ETIQUETA' --work _work --replace" >/dev/null
  (cd "$D" && ./svc.sh install "$USUARIO" >/dev/null && ./svc.sh start >/dev/null)
  echo "r$i listo"
done
rm -f "$TGZ"
echo "Listo: $N runners con la etiqueta $ETIQUETA. Para usarlos: gh variable set RUNNER_PESADO --body $ETIQUETA --repo $REPO"
