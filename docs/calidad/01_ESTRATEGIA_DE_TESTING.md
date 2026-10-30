# Estrategia de testing de SharPicks

- **Estado:** IMPLEMENTADA para el contrato público v1; estrategia de regresión integral pendiente.
- **Fecha:** 2026-10-30.

## Capas

1. **Unitario:** validación de DTOs, timestamps/zonas, tipos, rangos numéricos, allowlists, serialización determinista y hashes.
2. **Contrato:** fixtures sintéticos v1 consumidos por orquestador/core; rechazo de versiones futuras, campos desconocidos y manifiestos alterados.
3. **Integración aislada:** proveedor, base de datos, archivos, exportación y Telegram con mocks/servicios de staging; las pruebas nunca envían mensajes reales.
4. **Caracterización/regresión:** golden fixtures que comparan probabilidades, rankings, selección, métricas y formato de salida antes/después de extraer core.
5. **Instalación limpia:** paquete, imports, runtime de modelos y comandos seguros en entorno nuevo.
6. **Operación:** idempotencia, timeouts, reintentos, datos incompletos, concurrency, backup/restore y rollback.

## Evidencia actual

- `python -m unittest discover -s tests -p "test_*.py" -v`: descubre y ejecuta los módulos de prueba locales (52 pruebas aprobadas en el corte 2026-10-30, Python 3.12). `tests/` no es un paquete Python; no invocar sus archivos como `tests.<módulo>`.
- `python -m unittest test_exportador_web_v402 -v`: 6 pruebas adicionales locales, incluyendo que los logs de fallos de publicación no expongan el cuerpo HTTP. Se ejecutaron además los scripts heredados v383, v389, v390, v394-v396, v400, v510 y el test JS v402; aprobados con `PYTHONIOENCODING=utf-8`. v400 informó que PIL no está instalado para el subcaso opcional de ticket. Estas pruebas no envían mensajes ni conectan con Supabase.
- `python -m py_compile sharpicks_contracts/__init__.py sharpicks_contracts/v1.py sharpicks_contracts/web_v1.py tests/test_sharpicks_contracts.py tests/test_public_web_contract.py exportar_web.py`: aprobado.
- La suite del contrato se añadió al workflow `validate_sharpicks.yml`; `instalar`, `tests` y `validar` aprobaron en el tree SHA `c162c7587cb960149459d41ede09097990250046`.
- Los tres checks del PR antes de cambios nuevos estaban aprobados en el SHA base; no acreditan el código posterior.

## Criterio de aprobación

Un test local con fixture demuestra sólo esa lógica. Un mock no demuestra que el proveedor responda. CI verifica su runner/SHA. Staging es necesario para Supabase, pagos, modelos privados y restore. Producción se etiqueta como validada sólo con ejecución real y evidencia identificable.
