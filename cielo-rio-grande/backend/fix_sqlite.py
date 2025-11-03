import os, sys, shutil, sqlite3, time

if len(sys.argv) < 2:
    print("Uso: python safe_fix_sqlite.py <ruta_db>")
    sys.exit(1)

SRC = os.path.abspath(sys.argv[1])                 # p.ej. .\data\registros-octas.db
DB_DIR = os.path.dirname(SRC)
DST = os.path.join(DB_DIR, "registros-octas_clean.db")
BAK = os.path.join(DB_DIR, f"bak_registros-octas_{int(time.time())}.db")

def exists(p): return p and os.path.exists(p)

if not exists(SRC):
    print("No encuentro la DB:", SRC); sys.exit(1)

print("📦 Backup:", BAK)
shutil.copy2(SRC, BAK)
for ext in ("-wal", "-shm"):
    f = SRC + ext
    if exists(f): shutil.copy2(f, BAK + ext)

print("🪄 Intento 1: backup() →", DST)
if exists(DST): os.remove(DST)
try:
    src = sqlite3.connect(f"file:{SRC}?mode=ro", uri=True)  # read-only (no toca el original)
    dst = sqlite3.connect(DST)
    try:
        src.backup(dst)  # copia consistente
        ok = dst.execute("PRAGMA integrity_check;").fetchone()[0]
        print("🔎 integrity_check(backup):", ok)
        if ok == "ok":
            print("✅ Reemplazo original por la copia limpia")
            os.replace(DST, SRC)
            for ext in ("-wal", "-shm"):
                f = SRC + ext
                if exists(f):
                    try: os.remove(f)
                    except: pass
            print("✔ Listo:", SRC)
            sys.exit(0)
        else:
            print("❌ La copia vía backup() no quedó OK; pruebo copia cruda…")
    finally:
        dst.close(); src.close()
except Exception as e:
    print("⚠ No se pudo usar backup():", e, " → copiado crudo…")

RAW = os.path.join(DB_DIR, "registros-octas_rawclone.db")
if exists(RAW): os.remove(RAW)
shutil.copy2(SRC, RAW)
try:
    con = sqlite3.connect(RAW)
    ok = con.execute("PRAGMA integrity_check;").fetchone()[0]
    con.close()
    print("🔎 integrity_check(raw clone):", ok)
    if ok == "ok":
        print("✅ Reemplazo original por la copia cruda")
        os.replace(RAW, SRC)
        for ext in ("-wal", "-shm"):
            f = SRC + ext
            if exists(f):
                try: os.remove(f)
                except: pass
        print("✔ Listo:", SRC)
        sys.exit(0)
    else:
        print("❌ La copia cruda tampoco está OK.")
except Exception as e:
    print("⚠ No pude abrir la copia cruda:", e)

print("➡ Siguiente paso: salvataje con iterdump (best-effort).")
sys.exit(2)