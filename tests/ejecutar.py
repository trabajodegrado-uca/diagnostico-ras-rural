"""Ejecuta las pruebas sin necesidad de pytest:  python3 -m tests.ejecutar"""
import inspect
import sys
import traceback

from tests import test_motor

pruebas = [(n, f) for n, f in inspect.getmembers(test_motor, inspect.isfunction) if n.startswith("test_")]
fallas = 0
for nombre, f in pruebas:
    try:
        f()
        print(f"OK     {nombre}")
    except Exception:
        fallas += 1
        print(f"FALLA  {nombre}")
        traceback.print_exc()
print(f"\n{len(pruebas) - fallas} de {len(pruebas)} pruebas superadas")
sys.exit(1 if fallas else 0)
