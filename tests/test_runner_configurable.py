"""ADR-0002: el runner se elige con una variable, sin ella nada cambia, y nada depende de que el repo sea público."""
import glob
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
LIGEROS = {'claves_supabase', 'respaldo_base', 'smoke_sharpicks', 'test_instalacion_limpia', 'vigia_limites', 'web_rapido'}


def leer(*p):
    with open(os.path.join(RAIZ, *p), encoding='utf-8') as fh:
        return fh.read()


class RunnerConfigurable(unittest.TestCase):
    def test_pesados_usan_la_variable_con_github_por_omision(self):
        for f in glob.glob(os.path.join(RAIZ, '.github', 'workflows', '*.yml')):
            n = os.path.basename(f)[:-4]
            s = leer('.github', 'workflows', n + '.yml')
            if n in LIGEROS:
                self.assertNotIn('RUNNER_PESADO', s, n)
                continue
            lineas = [l for l in s.splitlines() if l.strip().startswith('runs-on:')]
            self.assertTrue(lineas, n)
            for l in lineas:
                self.assertIn("vars.RUNNER_PESADO || 'ubuntu-latest'", l, n)

    def test_vigilante_no_usa_raw_publico(self):
        s = leer('.github', 'workflows', 'vigia_limites.yml')
        self.assertNotIn('raw.githubusercontent', s)
        self.assertIn('GH_TOKEN: ${{ github.token }}', s)

    def test_instalador_verifica_runner_y_no_guarda_token(self):
        s = leer('tools', 'vps_runner', 'instalar.sh')
        self.assertIn('sha256sum -c', s)
        self.assertIn('${RUNNER_REG_TOKEN:?', s)
        self.assertNotIn('echo "$RUNNER_REG_TOKEN', s)
        self.assertIn('ACTIONS_RUNNER_HOOK_JOB_STARTED', s)

    def test_fuente_pasa_el_contrato_web(self):
        from sharpicks_contracts.web_v1 import public_pick
        self.assertEqual(public_pick({'id': 'x', 'fuente': 'casa'})['fuente'], 'casa')


class Yaml(unittest.TestCase):
    def test_todos_los_flujos_son_yaml_valido(self):
        try:
            import yaml
        except ImportError:
            self.skipTest('sin PyYAML')
        for f in glob.glob(os.path.join(RAIZ, '.github', 'workflows', '*.yml')):
            with open(f, encoding='utf-8') as fh:
                self.assertIn('jobs', yaml.safe_load(fh), f)


class MedirActions(unittest.TestCase):
    def test_resumen_y_simultaneos(self):
        sys.path.insert(0, os.path.join(RAIZ, 'tools'))
        import datetime as dt
        import medir_actions as m
        t0 = dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc)
        h = lambda x: t0 + dt.timedelta(hours=x)
        filas = [{'flujo': 'A', 'job': 'j', 'ini': h(0), 'fin': h(2), 'min': 120.0},
                 {'flujo': 'B', 'job': 'j', 'ini': h(1), 'fin': h(3), 'min': 120.0},
                 {'flujo': 'R', 'job': 'j', 'ini': h(0), 'fin': h(3), 'min': 180.0}]
        r = m.resumen(filas, 30, excluir=('R',))
        self.assertEqual(r['min_total'], 420)
        self.assertEqual(r['pico_simultaneos'], 2)
        self.assertEqual(r['usd_mes_alojado'], 0)   # 420 min × 0.006 = 2.52 < 12 incluidos
        self.assertEqual(r['tiempo_con_n']['2'], 33.3)


if __name__ == '__main__':
    unittest.main()
