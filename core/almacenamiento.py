"""
Almacenamiento local en SQLite.

Cada proyecto guarda su Ficha 1 y su Ficha 3 como JSON, y tiene registros
hijos de fuentes y viviendas. Guardar las respuestas como JSON permite
modificar el catálogo de variables (config/variables.py) sin migrar la base.
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path

RUTA_BD = Path(__file__).resolve().parent.parent / "datos" / "diagnostico.db"

ESQUEMA = """
CREATE TABLE IF NOT EXISTS proyectos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT NOT NULL,
    creado      TEXT NOT NULL,
    actualizado TEXT NOT NULL,
    ficha1      TEXT NOT NULL DEFAULT '{}',
    ficha3      TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS registros (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    proyecto_id INTEGER NOT NULL REFERENCES proyectos(id) ON DELETE CASCADE,
    tipo        TEXT NOT NULL CHECK (tipo IN ('fuente', 'vivienda')),
    creado      TEXT NOT NULL,
    datos       TEXT NOT NULL
);
"""


def _ahora():
    return datetime.now().isoformat(timespec="seconds")


def conectar(ruta=None):
    ruta = Path(ruta or RUTA_BD)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(ruta, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(ESQUEMA)
    return con


# ---------------- Proyectos ----------------
def crear_proyecto(con, nombre):
    t = _ahora()
    cur = con.execute(
        "INSERT INTO proyectos (nombre, creado, actualizado, ficha1) VALUES (?, ?, ?, ?)",
        (nombre, t, t, json.dumps({"nombre_proyecto": nombre}, ensure_ascii=False)),
    )
    con.commit()
    return cur.lastrowid


def listar_proyectos(con):
    return [dict(r) for r in con.execute("SELECT id, nombre, actualizado FROM proyectos ORDER BY actualizado DESC")]


def obtener_proyecto(con, proyecto_id):
    r = con.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,)).fetchone()
    if r is None:
        return None
    p = dict(r)
    p["ficha1"] = json.loads(p["ficha1"])
    p["ficha3"] = json.loads(p["ficha3"])
    return p


def guardar_ficha(con, proyecto_id, ficha, datos):
    """ficha: 'ficha1' o 'ficha3'. Hace merge con lo ya guardado."""
    if ficha not in ("ficha1", "ficha3"):
        raise ValueError("Ficha no válida")
    actual = obtener_proyecto(con, proyecto_id)[ficha]
    actual.update(datos)
    nombre = actual.get("nombre_proyecto") if ficha == "ficha1" else None
    con.execute(f"UPDATE proyectos SET {ficha} = ?, actualizado = ? WHERE id = ?",
                (json.dumps(actual, ensure_ascii=False), _ahora(), proyecto_id))
    if nombre:
        con.execute("UPDATE proyectos SET nombre = ? WHERE id = ?", (nombre, proyecto_id))
    con.commit()


def eliminar_proyecto(con, proyecto_id):
    con.execute("DELETE FROM proyectos WHERE id = ?", (proyecto_id,))
    con.commit()


# ---------------- Fuentes y viviendas ----------------
def agregar_registro(con, proyecto_id, tipo, datos):
    cur = con.execute(
        "INSERT INTO registros (proyecto_id, tipo, creado, datos) VALUES (?, ?, ?, ?)",
        (proyecto_id, tipo, _ahora(), json.dumps(datos, ensure_ascii=False)),
    )
    con.execute("UPDATE proyectos SET actualizado = ? WHERE id = ?", (_ahora(), proyecto_id))
    con.commit()
    return cur.lastrowid


def actualizar_registro(con, registro_id, datos):
    con.execute("UPDATE registros SET datos = ? WHERE id = ?", (json.dumps(datos, ensure_ascii=False), registro_id))
    con.commit()


def listar_registros(con, proyecto_id, tipo):
    filas = con.execute(
        "SELECT id, creado, datos FROM registros WHERE proyecto_id = ? AND tipo = ? ORDER BY id",
        (proyecto_id, tipo),
    )
    return [{"id": r["id"], "creado": r["creado"], **json.loads(r["datos"])} for r in filas]


def eliminar_registro(con, registro_id):
    con.execute("DELETE FROM registros WHERE id = ?", (registro_id,))
    con.commit()
