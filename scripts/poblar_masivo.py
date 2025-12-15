import os
import time
import random
import psycopg2
from faker import Faker
from io import StringIO
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

if not DB_HOST:
    DB_HOST = "localhost"
    DB_NAME = "ecommerce_db"
    DB_USER = "postgres"
    DB_PASS = "postgres"
    
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='latin-1') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        k, v = line.strip().split('=', 1)
                        if k.strip() == 'DB_HOST': DB_HOST = v.strip()
                        if k.strip() == 'DB_NAME': DB_NAME = v.strip()
                        if k.strip() == 'DB_USER': DB_USER = v.strip()
                        if k.strip() == 'DB_PASS': DB_PASS = v.strip()
        except Exception: pass

fake = Faker('es_MX')

def get_connection():
    return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)

def get_db_size(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT pg_database_size(current_database()) / 1024.0 / 1024.0;")
        return cur.fetchone()[0]

def clean_str(s):
    if not isinstance(s, str): return s
    return s.replace('\t', ' ').replace('\n', ' ').replace('\\', '')

def run():
    print(f"\n--- EJECUTANDO NIVEL: MASIVO ---")
    conn = get_connection()
    cur = conn.cursor()
    total = 0
    start_time = time.time()

    print("  ⚠️  Limpiando tablas (TRUNCATE) para carga limpia...")
    try:
        cur.execute("TRUNCATE TABLE detalle_ordenes, pagos, ordenes, productos, categorias, usuarios RESTART IDENTITY CASCADE;")
        conn.commit()
    except psycopg2.Error: conn.rollback()

    print("  -> Llenando tabla: USUARIOS (100,000 registros con COPY)...")
    buffer = StringIO()
    for _ in range(100000):
        buffer.write(f"{clean_str(fake.name())}\t{fake.unique.email()}\thash\t{time.strftime('%Y-%m-%d')}\ttrue\t{clean_str(fake.country())}\n")
    buffer.seek(0)
    try:
        cur.copy_from(buffer, 'usuarios', columns=('nombre', 'email', 'password_hash', 'fecha_registro', 'es_activo', 'pais'))
        conn.commit()
        total += 100000
    except psycopg2.Error as e: 
        print(f"Error Usuarios: {e}")
        return

    print("  -> Llenando tabla: CATEGORÍAS (50 registros)...")
    buffer = StringIO()
    for i in range(50):
        nombre_cat = f"Categoria {i} - {fake.word()}"
        buffer.write(f"{nombre_cat}\t{fake.sentence()}\n")
    buffer.seek(0)
    try:
        cur.copy_from(buffer, 'categorias', columns=('nombre', 'descripcion'))
        conn.commit()
        total += 50
    except psycopg2.Error: conn.rollback()

    cur.execute("SELECT min(categoria_id), max(categoria_id) FROM categorias")
    min_cat, max_cat = cur.fetchone()
    if not min_cat: min_cat, max_cat = 1, 1

    print("  -> Llenando tabla: PRODUCTOS (100,000 registros con COPY)...")
    buffer = StringIO()
    for _ in range(100000):
        cat_id = random.randint(min_cat, max_cat)
        buffer.write(f"{cat_id}\tProd {fake.word()}\t{random.randint(10,100)}\t100\t{fake.unique.ean13()}\n")
    buffer.seek(0)
    try:
        cur.copy_from(buffer, 'productos', columns=('categoria_id', 'nombre', 'precio', 'stock', 'sku'))
        conn.commit()
        total += 100000
    except psycopg2.Error: conn.rollback()

    print("  -> Llenando tabla: ÓRDENES (1,000,000 registros con COPY)...")
    bloque = 200000
    for i in range(5): 
        buffer = StringIO()
        for _ in range(bloque):
            buffer.write(f"{random.randint(1,100000)}\t{time.strftime('%Y-%m-%d')}\tENTREGADO\t100\n")
        buffer.seek(0)
        try:
            cur.copy_from(buffer, 'ordenes', columns=('usuario_id', 'fecha_orden', 'estado', 'total'))
            conn.commit()
            total += bloque
            sys.stdout.write(f"\r     Bloque insertado. Total: {total}")
        except psycopg2.Error: conn.rollback()
    print("")

    print("  -> Llenando tabla: DETALLES DE ÓRDENES (500,000 registros con COPY)...")
    buffer = StringIO()
    for i in range(500000):
        buffer.write(f"{random.randint(1, 1000000)}\t{random.randint(1, 100000)}\t1\t50\n")
    buffer.seek(0)
    try:
        cur.copy_from(buffer, 'detalle_ordenes', columns=('orden_id', 'producto_id', 'cantidad', 'precio_unitario'))
        conn.commit()
    except psycopg2.Error: conn.rollback()

    print("  -> Llenando tabla: PAGOS (500,000 registros con COPY)...")
    buffer = StringIO()
    for i in range(1, 500001):
        buffer.write(f"{i}\tTARJETA\t100\n")
    buffer.seek(0)
    try:
        cur.copy_from(buffer, 'pagos', columns=('orden_id', 'metodo_pago', 'monto'))
        conn.commit()
    except psycopg2.Error: conn.rollback()

    duration = time.time() - start_time
    db_size = get_db_size(conn)

    print("\n" + "="*40)
    print(f"RESULTADOS: MASIVO")
    print(f"Registros: {total:,}")
    print(f"Tiempo:    {duration:.4f} s")
    print(f"Velocidad: {total/duration if duration>0 else 0:,.2f} reg/s")
    print(f"Tamaño BD: {db_size:.2f} MB")
    print("="*40)
    conn.close()

if __name__ == "__main__":
    run()