# Runbook: pasar el repo a privado con runner propio (ADR-0002)

**Estado:** preparado, sin ejecutar. Requiere autorización del propietario.

1. **Fusionar el PR #1** a `main`. Sin la variable nada cambia de comportamiento.
2. **Contratar el servidor. Aún sin decidir.** Requisitos: Ubuntu 24.04 x64, de preferencia en EUA y sin permanencia larga hasta pasar la semana de prueba del paso 5. Candidato de referencia, no elegido: OVH VPS-3 (6 núcleos, 12 GB, 100 GB).
3. **Registrar los runners.** Copia al servidor `instalar.sh` y `despertador.sh` (`tools/vps_runner/`). Saca el token en tu PC y corre el instalador en el servidor, como root:

   ```bash
   gh api -X POST repos/HectorMontiel/sharpicks/actions/runners/registration-token -q .token
   ```

   ```bash
   RUNNER_REG_TOKEN=<token> REPO=HectorMontiel/sharpicks N=3 bash instalar.sh
   ```

4. **Dar el token al despertador.** En GitHub crea un token de grano fino sólo para este repo, con **Actions: lectura y escritura** y **Variables: lectura**. Anota cuándo vence: al vencer, el despertador falla. En el servidor, como root (el token no se escribe en la línea de comandos ni se manda por chat):

   ```bash
   read -rs TOKEN && umask 077 && printf 'GH_TOKEN=%s\n' "$TOKEN" > /etc/sharpicks/despertador.env && chown despertador: /etc/sharpicks/despertador.env && unset TOKEN
   ```

   Prueba, y mira lo que anota. Sin `DESPERTADOR=activo` no lanza nada:

   ```bash
   systemctl start sharpicks-despertador.service; journalctl -u sharpicks-despertador -n 30 --no-pager
   ```

5. **Prueba con el repo aún público:** en un repo público, un runner propio puede ejecutar código de pull requests de terceros. Antes de este paso, exige aprobación para todos los colaboradores externos en Settings → Actions, o saca `pull_request` de los flujos con runner propio. Luego:

   ```bash
   gh variable set RUNNER_PESADO --body sharpicks-vps --repo HectorMontiel/sharpicks
   ```

   Deja correr una semana. Compara con `python tools/medir_actions.py --dias 7`. El despertador sigue sólo anotando: revisa en su bitácora que lo que lanzaría tiene sentido.
6. **Cambiar a privado** en Settings → General → Danger Zone, y en seguida activa el despertador. Desde aquí Telegram sólo envía por él:

   ```bash
   gh variable set DESPERTADOR --body activo --repo HectorMontiel/sharpicks
   ```

7. **Verificar:** una corrida correcta de `sitio_web`, `precalculo_dia`, `cuotas_mx`, `retrain_leagues` (modelos del Release), `telegram_bot` y `respaldo_base`; que `sharpicksapp.com` siga actualizándose; y que Telegram haya mandado cada mensaje una sola vez.
8. **Después:** rotar cualquier credencial que haya estado expuesta (`tools/secret_scan.py`).

**Reversa del paso 5:** `gh variable delete RUNNER_PESADO --repo HectorMontiel/sharpicks`

**Reversa del despertador:** `gh variable delete DESPERTADOR --repo HectorMontiel/sharpicks`. Vuelve a sólo anotar y Telegram vuelve a usar su cron.

**Si el servidor se cae con el repo privado:** se detiene todo, porque los runners y el despertador viven ahí. Borra `RUNNER_PESADO` para volver a los runners de GitHub (de pago en privado, 2 CPU y 8 GB) y `DESPERTADOR` para volver al cron, que en privado puede no dispararse.
