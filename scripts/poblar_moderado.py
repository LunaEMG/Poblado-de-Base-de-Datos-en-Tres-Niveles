import os
import time
import random
import psycopg2
from psycopg2 import extras
from faker import Faker
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

def run():
    print(f"\n--- EJECUTANDO NIVEL: MODERADO ---")
    conn = get_connection()
    cur = conn.cursor()
    total = 0
    start_time = time.time()

    try:
        print("  -> Llenando tabla: USUARIOS (2,000 registros en batch)...")
        data = [(fake.name(), fake.unique.email(), fake.sha256(), fake.country()) for _ in range(2000)]
        try:
            extras.execute_batch(cur, "INSERT INTO usuarios (nombre, email, password_hash, pais) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING", data, page_size=1000)
            total += 2000
            conn.commit()
        except psycopg2.Error: conn.rollback()

        print("  -> Llenando tabla: CATEGORÍAS (20 registros)...")
        cats_data = []
        for _ in range(20):
            cats_data.append((fake.unique.word().capitalize() + " " + str(random.randint(1,999)), fake.sentence()))
        
        try:
            extras.execute_batch(cur, "INSERT INTO categorias (nombre, descripcion) VALUES (%s, %s) ON CONFLICT DO NOTHING", cats_data)
            conn.commit()
            total += 20
        except psycopg2.Error: conn.rollback()

        print("  -> Llenando tabla: PRODUCTOS (5,000 registros en batch)...")
        cur.execute("SELECT categoria_id FROM categorias")
        cat_ids = [r[0] for r in cur.fetchall()]
        if not cat_ids: 
            cur.execute("INSERT INTO categorias (nombre) VALUES ('Default') RETURNING categoria_id")
            cat_ids = [cur.fetchone()[0]]
            conn.commit()

        data_prod = []
        for _ in range(5000):
            data_prod.append((
                random.choice(cat_ids), fake.bs(), round(random.uniform(5, 500), 2), 
                random.randint(10, 500), fake.unique.bothify(text='??-########')
            ))
        try:
            extras.execute_batch(cur, "INSERT INTO productos (categoria_id, nombre, precio, stock, sku) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING", data_prod, page_size=1000)
            total += 5000
            conn.commit()
        except psycopg2.Error: conn.rollback()

        print("  -> Llenando tabla: ÓRDENES, DETALLES y PAGOS (Generación SQL)...")
        try:
            cur.execute("""
                INSERT INTO ordenes (usuario_id, estado, fecha_orden)
                SELECT (SELECT usuario_id FROM usuarios ORDER BY RANDOM() LIMIT 1), 'ENTREGADO', NOW() - (RANDOM() * INTERVAL '100 days')
                FROM generate_series(1, 3000);
            """)
            cur.execute("""
                INSERT INTO detalle_ordenes (orden_id, producto_id, cantidad, precio_unitario)
                SELECT o.orden_id, p.producto_id, (RANDOM()*3+1)::INT, p.precio
                FROM ordenes o
                CROSS JOIN LATERAL (SELECT producto_id, precio FROM productos ORDER BY RANDOM() LIMIT 2) p
                WHERE o.total = 0;
            """)
            cur.execute("UPDATE ordenes SET total = (SELECT COALESCE(SUM(subtotal), 0) FROM detalle_ordenes WHERE orden_id = ordenes.orden_id)")
            cur.execute("INSERT INTO pagos (orden_id, metodo_pago, monto) SELECT orden_id, 'PAYPAL', total FROM ordenes WHERE total > 0 ON CONFLICT DO NOTHING")
            conn.commit()
            total += 3000
        except psycopg2.Error: conn.rollback()

        duration = time.time() - start_time
        db_size = get_db_size(conn)

        print("\n" + "="*40)
        print(f"RESULTADOS: MODERADO")
        print(f"Registros: {total:,}")
        print(f"Tiempo:    {duration:.4f} s")
        print(f"Velocidad: {total/duration if duration>0 else 0:,.2f} reg/s")
        print(f"Tamaño BD: {db_size:.2f} MB")
        print("="*40)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run()