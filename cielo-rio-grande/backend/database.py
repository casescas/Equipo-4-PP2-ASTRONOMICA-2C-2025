import sqlite3
import os
from datetime import datetime, timedelta

# Nombre del archivo de nuestra base de datos
DB_FILE = "registros-octas.db"

def inicializar_db():
    """
    Crea la base de datos y las tablas necesarias si no existen.
    Esta función se debe llamar una vez cuando la aplicación FastAPI arranca.
    """
    
    # Comprobamos si la DB ya existe para no recrearla
    db_existe = os.path.exists(DB_FILE)
    
    # Conectamos a la base de datos (la crea si no existe)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    if not db_existe:
        print(f"INFO: Creando nueva base de datos en {DB_FILE}...")
        
        # --- 1. Crear la tabla de REGISTRO HISTÓRICO ---
        # Guardará una fila por cada predicción (filtrada por 1 hora)
        cursor.execute("""
        CREATE TABLE registro_historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_hora_prediccion DATETIME NOT NULL,
            octas_predichas INTEGER,
            confianza REAL,
            categoria TEXT,
            descripcion TEXT,
            url_imagen TEXT
        )
        """)
        
        # --- 2. Crear la tabla PIVOTE ---
        # Esta tabla tendrá *una sola fila* que se actualizará constantemente.
        # Nos dice cuál fue la última vez que guardamos un registro.
        cursor.execute("""
        CREATE TABLE control_registro (
            id INTEGER PRIMARY KEY DEFAULT 1,
            ultima_fecha_procesada DATETIME
        )
        """)
        
        # Insertamos la fila inicial en el pivote (vacía)
        # Usamos una fecha muy antigua para forzar el primer registro
        fecha_inicial = datetime(2025, 1, 1).isoformat()
        cursor.execute("INSERT INTO control_registro (ultima_fecha_procesada) VALUES (?)", (fecha_inicial,))
        
        print("✅ Tablas 'registro_historico' y 'pivote' creadas.")
        
    else:
        print(f"INFO: Base de datos {DB_FILE} ya existe. No se crearán tablas.")

    # Guardamos los cambios y cerramos la conexión
    conn.commit()
    conn.close()


def intentar_registrar_prediccion(datos_prediccion: dict, hora_prediccion: datetime):
    """
    Comprueba el pivote y, si ha pasado más de 1 hora,
    registra la nueva predicción en la DB.

    Retorna True si registró, False si no lo hizo (omitido).
    """
    
    # Es importante agregar check_same_thread=False para que FastAPI
    # (que funciona con hilos) pueda usar la DB de SQLite sin problemas.
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = conn.cursor()
        
        # --- 1. Obtener la última fecha del pivote ---
        cursor.execute("SELECT ultima_fecha_procesada FROM control_registro WHERE id = 1")
        resultado = cursor.fetchone()
        
        if not resultado:
            # Esto no debería pasar si inicializar_db() se ejecutó
            print("ERROR: No se encontró la fila pivote. Abortando registro.")
            return False

        # Convertir el string de la DB a un objeto datetime
        ultima_fecha = datetime.fromisoformat(resultado[0])
        
        # --- 2. Comprobar la lógica de 1 hora (usamos 60 minutos) ---
        if (hora_prediccion - ultima_fecha) <= timedelta(minutes=60):
            # No ha pasado suficiente tiempo
            print(f"INFO: Registro omitido. Último registro: {ultima_fecha.strftime('%H:%M')}. Actual: {hora_prediccion.strftime('%H:%M')}.")
            return False
            
        # --- 3. Sí ha pasado 1 hora, ¡a registrar! ---
        print("INFO: Han pasado más de 60 min. Registrando nueva predicción...")
        
        # Insertar en el histórico
        cursor.execute("""
            INSERT INTO registro_historico (
                fecha_hora_prediccion, octas_predichas, confianza, 
                categoria, descripcion, url_imagen
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            hora_prediccion,
            datos_prediccion['octas_predichas'],
            datos_prediccion['confianza'],
            datos_prediccion['categoria'],
            datos_prediccion['descripcion'],
            datos_prediccion['imagen'] # Las claves coinciden con el JSON de main.py
        ))
        
        # Actualizar el pivote con la hora actual
        cursor.execute("""
            UPDATE control_registro SET ultima_fecha_procesada = ? WHERE id = 1
        """, (hora_prediccion.isoformat(),))
        
        conn.commit()
        print(f"✅ Predicción de las {hora_prediccion.strftime('%H:%M')} registrada exitosamente.")
        return True
        
    except Exception as e:
        print(f"ERROR: Fallo al registrar en la base de datos: {e}")
        if conn:
            conn.rollback() # Revertir cambios si algo falla
        return False
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":

    # Esto permite ejecutar el archivo directamente con "python database.py"
    # para crear la base de datos por primera vez antes de lanzar el servidor.
    print("Ejecutando inicializador de base de datos...")
    inicializar_db()
    print("Proceso de inicialización completado.")