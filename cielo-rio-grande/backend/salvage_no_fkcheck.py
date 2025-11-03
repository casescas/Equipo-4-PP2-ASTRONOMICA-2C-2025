# salvage_no_fkcheck.py
import os, sys, sqlite3, traceback

if len(sys.argv) < 3:
    print("Uso: python salvage_no_fkcheck.py <db_origen> <db_destino>")
    sys.exit(1)

SRC = os.path.abspath(sys.argv[1])
DST = os.path.abspath(sys.argv[2])

def exists(p): return p and os.path.exists(p)

if not exists(SRC):
    print("No encuentro la DB origen:", SRC); sys.exit(1)
if exists(DST):
    print("Destino ya existe, lo sobreescribo:", DST)
    os.remove(DST)

def connect_ro(path: str) -> sqlite3.Connection:
    # Abrir sólo lectura y evitar escribir nada en la corrupta
    uri = f"file:{os.path.abspath(path)}?mode=ro"
    return sqlite3.connect(uri, uri=True, isolation_level=None)

def copy_schema(src_con, dst_con):
    # foreign_keys OFF para evitar checkeos
    dst_con.execute("PRAGMA foreign_keys=OFF;")
    cur = src_con.execute("""
        SELECT type, name, sql
        FROM sqlite_master
        WHERE sql IS NOT NULL
        ORDER BY CASE type
                 WHEN 'table' THEN 0
                 WHEN 'index' THEN 1
                 WHEN 'trigger' THEN 2
                 WHEN 'view' THEN 3
                 ELSE 4 END, name
    """)
    for typ, name, stmt in cur.fetchall():
        try:
            # Saltamos objetos internos
            if name.startswith("sqlite_"): 
                continue
            dst_con.execute(stmt)
        except Exception as e:
            print(f"[WARN] No pude crear {typ} {name}: {e}")

def table_names(src_con):
    cur = src_con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    return [r[0] for r in cur.fetchall()]

def table_cols(src_con, table):
    cur = src_con.execute(f"PRAGMA table_info('{table}')")
    cols = [r[1] for r in cur.fetchall()]
    return cols

def rowid_bounds(src_con, table):
    try:
        lo = src_con.execute(f"SELECT MIN(ROWID) FROM '{table}'").fetchone()[0]
        hi = src_con.execute(f"SELECT MAX(ROWID) FROM '{table}'").fetchone()[0]
        return lo, hi
    except Exception:
        return None, None

def copy_table_full(src_con, dst_con, table, cols, batch=5000):
    collist = ", ".join([f'"{c}"' for c in cols])
    placeholders = ", ".join(["?"] * len(cols))
    q = f'SELECT {collist} FROM "{table}"'
    total = 0
    try:
        cur = src_con.execute(q)
        while True:
            rows = cur.fetchmany(batch)
            if not rows:
                break
            dst_con.executemany(
                f'INSERT OR IGNORE INTO "{table}" ({collist}) VALUES ({placeholders})',
                rows,
            )
            total += len(rows)
    except Exception as e:
        raise e
    return total

def copy_table_by_rowid(src_con, dst_con, table, cols, block=2000):
    collist = ", ".join([f'"{c}"' for c in cols])
    placeholders = ", ".join(["?"] * len(cols))
    lo, hi = rowid_bounds(src_con, table)
    if lo is None or hi is None:
        print(f"[WARN] {table}: sin ROWID válido.")
        return 0
    copied = 0
    start = lo
    while start <= hi:
        end = min(start + block - 1, hi)
        try:
            rows = src_con.execute(
                f'SELECT {collist} FROM "{table}" WHERE ROWID BETWEEN ? AND ?',
                (start, end),
            ).fetchall()
            if rows:
                dst_con.executemany(
                    f'INSERT OR IGNORE INTO "{table}" ({collist}) VALUES ({placeholders})',
                    rows,
                )
                copied += len(rows)
        except Exception as e:
            # Si un bloque falla, lo partimos a la mitad para salvar lo que se pueda
            if end > start:
                mid = (start + end) // 2
                # lado izquierdo
                try:
                    rows = src_con.execute(
                        f'SELECT {collist} FROM "{table}" WHERE ROWID BETWEEN ? AND ?',
                        (start, mid),
                    ).fetchall()
                    if rows:
                        dst_con.executemany(
                            f'INSERT OR IGNORE INTO "{table}" ({collist}) VALUES ({placeholders})',
                            rows,
                        )
                        copied += len(rows)
                except Exception:
                    pass
                # lado derecho
                try:
                    rows = src_con.execute(
                        f'SELECT {collist} FROM "{table}" WHERE ROWID BETWEEN ? AND ?',
                        (mid + 1, end),
                    ).fetchall()
                    if rows:
                        dst_con.executemany(
                            f'INSERT OR IGNORE INTO "{table}" ({collist}) VALUES ({placeholders})',
                            rows,
                        )
                        copied += len(rows)
                except Exception:
                    pass
            # reportar y seguir
            print(f"[WARN] {table}: bloque [{start},{end}] dañado, sigo… ({e})")
        start = end + 1
    return copied

def main():
    print("🔧 Origen:", SRC)
    print("📄 Destino:", DST)
    src = connect_ro(SRC)
    dst = sqlite3.connect(DST)
    try:
        dst.execute("PRAGMA journal_mode=WAL;")
        dst.execute("PRAGMA foreign_keys=OFF;")
        copy_schema(src, dst)

        for t in table_names(src):
            print(f"==> Tabla: {t}")
            cols = table_cols(src, t)
            if not cols:
                print(f"[WARN] {t}: sin columnas detectadas, salto.")
                continue
            copied = 0
            try:
                copied = copy_table_full(src, dst, t)
                print(f"[OK] {t}: copiado {copied} filas (full).")
            except Exception as e:
                print(f"[WARN] {t}: SELECT * falló ({e}), pruebo por ROWID…")
                copied = copy_table_by_rowid(src, dst, t)
                print(f"[OK] {t}: copiado {copied} filas (por ROWID).")

        # compactar y validar
        dst.execute("VACUUM;")
        ok = dst.execute("PRAGMA integrity_check;").fetchone()[0]
        print("🔎 integrity_check(destino):", ok)
    finally:
        dst.close(); src.close()

    if ok == "ok":
        print("✅ Recuperación lista:", DST)
        sys.exit(0)
    else:
        print("❌ El destino no quedó OK; revisar archivo recuperado:", DST)
        sys.exit(2)

if __name__ == "__main__":
    main()
