#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reparte un cálculo entre los núcleos del servidor. Sin `SERVIDOR_PROCESOS`, todo sigue en serie.

Sólo para funciones que no dependan de lo ya calculado en el proceso y no escriban archivos: cada
proceso empieza limpio. Se usa `spawn` porque los hilos de las librerías de modelos no aguantan un `fork`.
"""
import logging
import multiprocessing as mp
import os
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from concurrent.futures.process import BrokenProcessPool

logger = logging.getLogger(__name__)
HILOS_DE_LIBRERIAS = ('LOKY_MAX_CPU_COUNT', 'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS')


def procesos() -> int:
    return max(int(os.environ.get('SERVIDOR_PROCESOS') or 1), 1)


def un_hilo_por_proceso(n: int = 1) -> None:
    """Cada proceso con un solo hilo (o `n`), para no pedirle más núcleos de los que hay."""
    for var in HILOS_DE_LIBRERIAS:
        os.environ[var] = str(n)


def hilos(funcion, elementos, n: int = 4) -> list:
    """Lo mismo para lo que sólo espera a la red. No se pasa de `n` a la vez para no saturar la fuente."""
    elementos = list(elementos)
    if procesos() <= 1 or len(elementos) < 2:
        return [funcion(x) for x in elementos]
    with ThreadPoolExecutor(n) as pool:
        return list(pool.map(funcion, elementos))


def mapa(funcion, elementos, hilos_por_proceso: int = 1) -> list:
    """`funcion` sobre cada elemento, con el resultado en el mismo orden."""
    elementos = list(elementos)
    n = procesos()
    if n <= 1 or len(elementos) < 2:
        return [funcion(x) for x in elementos]
    previo = {v: os.environ.get(v) for v in HILOS_DE_LIBRERIAS}
    un_hilo_por_proceso(hilos_por_proceso)
    try:
        with ProcessPoolExecutor(n, mp_context=mp.get_context('spawn')) as pool:
            return list(pool.map(funcion, elementos, chunksize=max(len(elementos) // (n * 4), 1)))
    except BrokenProcessPool as e:
        logger.warning('[reparto] murió un proceso (%s): se calcula en serie', e)
        return [funcion(x) for x in elementos]
    finally:
        for v, valor in previo.items():
            if valor is None:
                os.environ.pop(v, None)
            else:
                os.environ[v] = valor
