# use_best_backup.py
import os, sqlite3, glob, shutil, sys

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "registros-octas.db"))
BACKUP_PATTERN = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "bak_registros-octas_*.db"))

def integrity_ok(path: str) -> bool:
    try:
        con = sqlite3.connect(path)
        ok = con.execute("PRAGMA integrity_check;").fetchone()[0]
        con.close()
        return ok == "ok"
    except Exception:
        return False

def main():
    print("🔎 DB objetivo:", DB_PATH)
    candidates = sorted(glob.glob(BACKUP_PATTERN), reverse=True)  # más recientes primero
    if not candidates:
        print("❌ No se encontraron backups con patrón:", BACKUP_PATTERN)
        sys.exit(2)

    print(f"📚 {len(candidates)} backup(s) hallados. Probando integridad…")
    for bak in candidates:
        print("→ Probando:", bak)
        if integrity_ok(bak):
            print("✅ Backup válido:", bak)
            print("🧰 Restaurando como DB principal…")
            shutil.copy2(bak, DB_PATH)
            # limpiar WAL/SHM si quedaron del archivo anterior
            for ext in ("-wal", "-shm"):
                p = DB_PATH + ext
                if os.path.exists(p):
                    try: os.remove(p)
                    except: pass
            print("✔ Listo. Restaurado:", DB_PATH)
            sys.exit(0)
        else:
            print("⚠ Backup corrupto o no abrible.")

    print("❌ Ningún backup pasó integrity_check. No se pudo restaurar automáticamente.")
    sys.exit(3)

if __name__ == "__main__":
    main()
