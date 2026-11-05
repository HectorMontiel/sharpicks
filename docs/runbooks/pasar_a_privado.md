# Runbook: pasar el repo a privado con runner propio (ADR-0002)

**Estado:** preparado, sin ejecutar. Requiere autorización del propietario.

1. **Fusionar el PR #1** a `main`. Sin la variable nada cambia de comportamiento.
2. **Contratar OVH VPS-4** (8 núcleos, 24 GB, 200 GB) con Ubuntu 24.04, de preferencia en EUA y sin permanencia larga hasta pasar la semana de prueba del paso 4. **Portar antes el despertador** (ver ADR-0002).
3. **Registrar los runners**, en tu PC y luego en el servidor:

   ```bash
   gh api -X POST repos/HectorMontiel/sharpicks/actions/runners/registration-token -q .token
   ```

   ```bash
   RUNNER_REG_TOKEN=<token> REPO=HectorMontiel/sharpicks N=4 bash instalar.sh
   ```

4. **Prueba con el repo aún público:** en un repo público, un runner propio puede ejecutar código de pull requests de terceros. Antes de este paso, exige aprobación para todos los colaboradores externos en Settings → Actions, o saca `pull_request` de los flujos con runner propio. Luego:

   ```bash
   gh variable set RUNNER_PESADO --body sharpicks-vps --repo HectorMontiel/sharpicks
   ```

   Deja correr una semana. Compara con `python tools/medir_actions.py --dias 7`.
5. **Cambiar a privado** en Settings → General → Danger Zone.
6. **Verificar:** una corrida correcta de `sitio_web`, `precalculo_dia`, `cuotas_mx`, `retrain_leagues` (modelos del Release), `telegram_bot` y `respaldo_base`; y que `sharpicksapp.com` siga actualizándose.
7. **Después:** rotar cualquier credencial que haya estado expuesta (`tools/secret_scan.py`).

**Reversa del paso 4:** `gh variable delete RUNNER_PESADO --repo HectorMontiel/sharpicks`
