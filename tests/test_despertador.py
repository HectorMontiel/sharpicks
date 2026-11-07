"""ADR-0002: el despertador del servidor. Corre el script de verdad con un curl falso y el reloj fijo."""
import calendar
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(RAIZ, 'tools', 'vps_runner', 'despertador.sh')
CHAIN = {'precalculo_dia', 'relevo'}   # no se despiertan: los dispara la cadena de cuotas_mx
CADA_HORA = {'cuotas_mx', 'sitio_web'}
LUNES = (2026, 11, 9)
MARTES = (2026, 11, 10)

CURL_FALSO = r'''#!/usr/bin/env bash
metodo=GET; url=; cuerpo=
while [ $# -gt 0 ]; do
  case "$1" in
    -X) metodo=$2; shift 2 ;;
    -d) cuerpo=$2; shift 2 ;;
    -H|--max-time|--config) shift 2 ;;
    -*) shift ;;
    *) url=$1; shift ;;
  esac
done
[ -e "$FIX/caido" ] && exit 22
case "$url" in
  */actions/variables*) [ -e "$FIX/vars_caidas" ] && exit 22; cat "$FIX/vars.json" ;;
  */dispatches)
    [ -e "$FIX/post_caido" ] && exit 22
    f=${url%/dispatches}; echo "${f##*/} $cuerpo" >> "$FIX/lanzados.txt" ;;
  */runs*)
    f=${url%/runs*}; f=${f##*/}
    if [ -e "$FIX/$f" ]; then cat "$FIX/$f"; else echo '{"workflow_runs":[]}'; fi ;;
esac
'''


def seg(dia, h, m=0):
    return calendar.timegm(dia + (h, m, 0))


def iso(s):
    import time
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(s))


@unittest.skipUnless(shutil.which('bash') and shutil.which('jq'), 'hace falta bash y jq')
class Despertador(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, True)
        bin_ = os.path.join(self.d, 'bin')
        os.mkdir(bin_)
        curl = os.path.join(bin_, 'curl')
        with open(curl, 'w', newline='\n', encoding='utf-8') as fh:
            fh.write(CURL_FALSO)
        os.chmod(curl, os.stat(curl).st_mode | stat.S_IEXEC)
        self.bin = bin_
        self.vars('activo')

    def vars(self, valor):
        v = [{'name': 'RUNNER_PESADO', 'value': 'x'}]
        if valor:
            v.append({'name': 'DESPERTADOR', 'value': valor})
        self.fix('vars.json', {'variables': v})

    def fix(self, nombre, datos):
        with open(os.path.join(self.d, nombre), 'w', encoding='utf-8') as fh:
            json.dump(datos, fh)

    def corridas(self, wf, *lista):
        self.fix(wf + '.yml', {'workflow_runs': [{'created_at': iso(s), 'event': e} for s, e in lista]})

    def frescos(self, ahora):
        """Todo corrió hace un momento: no debería lanzarse nada."""
        for wf in ('cuotas_mx', 'sitio_web', 'vigia_limites', 'precalcular_rosters', 'retrain_leagues', 'radar_diario',
                   'telegram_dia_completo', 'respaldo_base', 'telegram_bot', 'recalibrar'):
            self.corridas(wf, (ahora - 60, 'workflow_dispatch'))

    def correr(self, ahora, *args):
        env = dict(os.environ, FIX=self.d, GH_TOKEN='x', DESPERTADOR_AHORA=str(ahora),
                   PATH=self.bin + os.pathsep + os.environ['PATH'])
        p = subprocess.run(['bash', SCRIPT.replace('\\', '/'), *args], env=env, capture_output=True, text=True,
                           encoding='utf-8', timeout=120)
        self.salida = p.stdout + p.stderr
        return p.returncode

    def lanzados(self):
        f = os.path.join(self.d, 'lanzados.txt')
        if not os.path.exists(f):
            return []
        with open(f, encoding='utf-8') as fh:
            return [l.strip() for l in fh]

    def nombres(self):
        return [l.split()[0] for l in self.lanzados()]

    def test_todo_al_dia_no_lanza_nada(self):
        a = seg(MARTES, 14)
        self.frescos(a)
        self.assertEqual(self.correr(a), 0, self.salida)
        self.assertEqual(self.lanzados(), [])

    def test_cuotas_viejas_se_lanzan_sin_forzar(self):
        a = seg(MARTES, 14)
        self.frescos(a)
        self.corridas('cuotas_mx', (a - 56 * 60, 'schedule'))
        self.correr(a)
        self.assertEqual(self.lanzados(), ['cuotas_mx.yml {"ref":"main","inputs":{"forzar":"false"}}'])

    def test_cuotas_recientes_no_se_lanzan(self):
        a = seg(MARTES, 14)
        self.frescos(a)
        self.corridas('cuotas_mx', (a - 54 * 60, 'schedule'))
        self.correr(a)
        self.assertEqual(self.lanzados(), [])

    def test_si_github_falla_no_lanza_nada(self):
        a = seg(MARTES, 11)   # el .ps1 aquí lanzaba todo, Telegram incluido
        open(os.path.join(self.d, 'caido'), 'w').close()
        self.assertNotEqual(self.correr(a), 0)
        self.assertEqual(self.lanzados(), [])

    def test_si_una_lectura_falla_ese_flujo_no_se_lanza(self):
        a = seg(MARTES, 11)
        self.frescos(a)
        self.fix('telegram_bot.yml', {'mensaje': 'error'})   # respuesta sin workflow_runs
        self.assertNotEqual(self.correr(a), 0)
        self.assertEqual(self.lanzados(), [])

    def test_si_falla_el_lanzamiento_se_avisa(self):
        a = seg(MARTES, 14)
        self.frescos(a)
        self.corridas('cuotas_mx', (a - 3600, 'schedule'))
        open(os.path.join(self.d, 'post_caido'), 'w').close()
        self.assertNotEqual(self.correr(a), 0)
        self.assertIn('FALLO al lanzar cuotas_mx', self.salida)

    def test_sin_el_interruptor_sólo_anota(self):
        a = seg(MARTES, 14)
        self.vars('')
        self.assertEqual(self.correr(a), 0, self.salida)
        self.assertEqual(self.lanzados(), [])
        self.assertIn('[seco] lanzaría cuotas_mx.yml', self.salida)

    def test_otro_valor_no_activa(self):
        a = seg(MARTES, 14)
        self.vars('si')
        self.correr(a)
        self.assertEqual(self.lanzados(), [])

    def test_seco_gana_al_interruptor(self):
        a = seg(MARTES, 14)
        self.assertEqual(self.correr(a, '--seco'), 0, self.salida)
        self.assertEqual(self.lanzados(), [])
        self.assertIn('[seco] lanzaría sitio_web.yml', self.salida)

    def test_sin_leer_el_interruptor_no_lanza(self):
        a = seg(MARTES, 14)
        open(os.path.join(self.d, 'vars_caidas'), 'w').close()
        self.assertNotEqual(self.correr(a), 0)
        self.assertEqual(self.lanzados(), [])

    def test_variables_con_respuesta_rara_no_lanza(self):
        a = seg(MARTES, 14)
        self.fix('vars.json', {'mensaje': 'Resource not accessible'})
        self.assertNotEqual(self.correr(a), 0)
        self.assertEqual(self.lanzados(), [])

    def test_telegram_en_su_ventana_se_lanza(self):
        a = seg(MARTES, 10, 30)
        self.frescos(a)
        self.corridas('telegram_bot', (seg(MARTES, 0) - 3600, 'workflow_dispatch'))
        self.correr(a)
        self.assertEqual(self.nombres(), ['telegram_bot.yml'])

    def test_telegram_fuera_de_su_ventana_no_sale(self):
        a = seg(MARTES, 13, 20)   # 10:19 + 181 min
        self.frescos(a)
        self.corridas('telegram_bot', (seg(MARTES, 0) - 3600, 'workflow_dispatch'))
        self.correr(a)
        self.assertEqual(self.lanzados(), [])

    def test_telegram_ya_mandado_no_se_repite(self):
        a = seg(MARTES, 10, 30)
        self.frescos(a)
        self.corridas('telegram_bot', (seg(MARTES, 10, 20), 'workflow_dispatch'))
        self.correr(a)
        self.assertEqual(self.lanzados(), [])

    def test_cron_saltado_de_telegram_no_cuenta_como_enviado(self):
        # con el interruptor activo el cron de Telegram se salta su trabajo: esa corrida no mandó nada
        a = seg(MARTES, 10, 30)
        self.frescos(a)
        self.corridas('telegram_bot', (seg(MARTES, 10, 20), 'schedule'),
                      (seg(MARTES, 0) - 3600, 'workflow_dispatch'))
        self.correr(a)
        self.assertEqual(self.nombres(), ['telegram_bot.yml'])

    def test_en_seco_el_cron_de_telegram_sí_cuenta(self):
        # sin el interruptor el cron sí manda: la bitácora no debe decir que faltó
        a = seg(MARTES, 10, 30)
        self.frescos(a)
        self.vars('')
        self.corridas('telegram_bot', (seg(MARTES, 10, 20), 'schedule'))
        self.correr(a)
        self.assertNotIn('telegram_bot', self.salida)

    def test_diario_atrasado_se_recupera_sin_ventana(self):
        a = seg(MARTES, 20)
        self.frescos(a)
        self.corridas('retrain_leagues', (seg(MARTES, 0) - 3600, 'schedule'))
        self.correr(a)
        self.assertEqual(self.nombres(), ['retrain_leagues.yml'])

    def test_diario_antes_de_su_hora_no_se_lanza(self):
        a = seg(MARTES, 5, 40)
        self.frescos(a)
        self.corridas('retrain_leagues', (seg(MARTES, 0) - 3600, 'schedule'))
        self.correr(a)
        self.assertEqual(self.lanzados(), [])

    def test_dos_horas_en_un_flujo_se_lanza_una_vez(self):
        a = seg(MARTES, 14)
        self.frescos(a)
        self.corridas('vigia_limites', (seg(MARTES, 0) - 3600, 'schedule'))
        self.correr(a)
        self.assertEqual(self.nombres(), ['vigia_limites.yml'])

    def test_recalibrar_sólo_el_lunes(self):
        a = seg(LUNES, 6)
        self.frescos(a)
        self.corridas('recalibrar', (seg(LUNES, 0) - 3600, 'schedule'))
        self.corridas('retrain_leagues', (a - 60, 'schedule'))
        self.correr(a)
        self.assertEqual(self.nombres(), ['recalibrar.yml'])
        os.remove(os.path.join(self.d, 'lanzados.txt'))
        a = seg(MARTES, 6)
        self.frescos(a)
        self.corridas('recalibrar', (seg(LUNES, 0), 'schedule'))
        self.correr(a)
        self.assertEqual(self.lanzados(), [])

    def test_exige_token(self):
        env = dict(os.environ, FIX=self.d, PATH=self.bin + os.pathsep + os.environ['PATH'])
        env.pop('GH_TOKEN', None)
        p = subprocess.run(['bash', SCRIPT.replace('\\', '/')], env=env, capture_output=True, text=True, encoding='utf-8')
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(self.lanzados(), [])


def leer(*p):
    with open(os.path.join(RAIZ, *p), encoding='utf-8', newline='') as fh:
        return fh.read()


class Tabla(unittest.TestCase):
    """Si alguien cambia un cron y no el despertador, aquí truena."""

    def crons(self):
        res = {}
        carpeta = os.path.join(RAIZ, '.github', 'workflows')
        for f in os.listdir(carpeta):
            if f.endswith('.yml'):
                res[f[:-4]] = re.findall(r"^\s*- cron:\s*'([^']+)'", leer('.github', 'workflows', f), re.M)
        return {k: v for k, v in res.items() if v}

    def tabla(self):
        s = leer('tools', 'vps_runner', 'despertador.sh')
        filas = re.search(r"<<'TABLA'\n(.*?)\nTABLA", s, re.S).group(1).splitlines()
        res = {}
        for l in filas:
            wf, h, m, _ = l.split()
            res.setdefault(wf[:-4], set()).add((int(m), int(h)))
        return res, s

    def test_cada_flujo_con_cron_está_cubierto(self):
        tabla, s = self.tabla()
        for wf in self.crons():
            self.assertTrue(wf in tabla or wf in CHAIN or wf in CADA_HORA or (wf == 'recalibrar' and 'recalibrar.yml' in s), wf)

    def test_la_tabla_coincide_con_el_cron(self):
        tabla, _ = self.tabla()
        crons = self.crons()
        for wf, horas in tabla.items():
            declarado = {(int(c.split()[0]), int(c.split()[1])) for c in crons[wf]}
            self.assertEqual(horas, declarado, wf)

    def test_recalibrar_coincide(self):
        _, s = self.tabla()
        c = self.crons()['recalibrar'][0].split()
        self.assertIn(f'revisa_diario recalibrar.yml {c[1]} {c[0]} 0', s)
        self.assertEqual(c[4], '1')

    def test_cuotas_no_se_lanza_con_forzar_por_omisión(self):
        # el input `forzar` vale true por omisión: sin mandarlo se saltaría la guarda de frescura cada hora
        _, s = self.tabla()
        self.assertIn('''revisa_cada_hora cuotas_mx.yml '{"ref":"main","inputs":{"forzar":"false"}}\'''', s)

    def test_telegram_se_salta_el_cron_con_el_interruptor(self):
        for wf in ('telegram_bot', 'telegram_dia_completo'):
            self.assertIn("if: ${{ github.event_name != 'schedule' || vars.DESPERTADOR != 'activo' }}",
                          leer('.github', 'workflows', wf + '.yml'), wf)

    def test_telegram_lleva_ventana_y_lo_demás_no(self):
        s = leer('tools', 'vps_runner', 'despertador.sh')
        filas = re.search(r"<<'TABLA'\n(.*?)\nTABLA", s, re.S).group(1).splitlines()
        for l in filas:
            wf, _, _, ventana = l.split()
            self.assertEqual(wf.startswith('telegram_'), int(ventana) > 0, wf)


class Instalador(unittest.TestCase):
    def test_saltos_de_línea_lf(self):
        # en Windows con autocrlf un CRLF rompería bash en el servidor; .gitattributes lo fija
        self.assertIn('tools/vps_runner/* text eol=lf', leer('.gitattributes'))
        for f in ('despertador.sh', 'instalar.sh'):
            self.assertNotIn('\r', leer('tools', 'vps_runner', f), f)

    def test_token_fuera_del_alcance_de_los_runners(self):
        s = leer('tools', 'vps_runner', 'instalar.sh')
        self.assertIn('User=despertador', s)
        self.assertIn('ConditionPathExists=/etc/sharpicks/despertador.env', s)
        self.assertIn('install -d -m 700 -o despertador', s)

    def test_token_no_va_en_los_argumentos(self):
        s = leer('tools', 'vps_runner', 'despertador.sh')
        self.assertIn('--config <(printf', s)
        self.assertNotRegex(s, r'-H [\'"]Authorization')

    def test_git_del_trabajo_no_crece_sin_tope(self):
        # actions/checkout apaga gc.auto: en un runner propio el .git del trabajo sólo crece
        self.assertIn('du -sm "$GITHUB_WORKSPACE/.git"', leer('tools', 'vps_runner', 'instalar.sh'))


if __name__ == '__main__':
    unittest.main()
