import os
import time
import random
import psycopg2
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
    print(f"\n--- EJECUTANDO NIVEL: LEVE ---")
    conn = get_connection()
    cur = conn.cursor()
    total = 0
    start_time = time.time()

    try:
        print("  -> Llenando tabla: USUARIOS (50 registros)...")
        for _ in range(50):
            try:
                cur.execute("INSERT INTO usuarios (nombre, email, password_hash, pais) VALUES (%s, %s, %s, %s)", 
                           (fake.name(), fake.unique.email(), fake.sha256(), fake.country()))
                total += 1
            except psycopg2.Error: conn.rollback()
        
        print("  -> Llenando tabla: CATEGORÍAS...")
        cats = ['Electrónica', 'Hogar', 'Ropa', 'Deportes', 'Juguetes', 'Libros', 'Salud', 'Muebles', 'Jardín', 'Mascotas']
        for cat in cats:
            try:
                cur.execute("INSERT INTO categorias (nombre, descripcion) VALUES (%s, %s) ON CONFLICT DO NOTHING", (cat, fake.sentence()))
                total += 1
            except psycopg2.Error: conn.rollback()
        conn.commit()

        print("  -> Llenando tabla: PRODUCTOS (100 registros)...")
        cur.execute("SELECT categoria_id FROM categorias")
        cat_ids = [r[0] for r in cur.fetchall()]
        products_cache = [] 
        
        if cat_ids:
            for _ in range(100):
                try:
                    price = round(random.uniform(10, 1000), 2)
                    cur.execute("INSERT INTO productos (categoria_id, nombre, precio, stock, sku) VALUES (%s, %s, %s, %s, %s) RETURNING producto_id, precio",
                               (random.choice(cat_ids), fake.word() + " " + fake.word(), price, random.randint(0,100), fake.unique.ean13()))
                    pid, p_price = cur.fetchone()
                    products_cache.append((pid, float(p_price)))
                    total += 1
                except psycopg2.Error: conn.rollback()
        conn.commit()

        print("  -> Llenando tablas: ÓRDENES, DETALLES y PAGOS...")
        cur.execute("SELECT usuario_id FROM usuarios")
        user_ids = [r[0] for r in cur.fetchall()]
        
        if user_ids and products_cache:
            for _ in range(50):
                try:
                    uid = random.choice(user_ids)
                    cur.execute("INSERT INTO ordenes (usuario_id, estado, total) VALUES (%s, %s, %s) RETURNING orden_id", (uid, 'PAGADO', 0))
                    oid = cur.fetchone()[0]
                    total += 1
                    
                    monto_orden = 0
                    for _ in range(random.randint(1, 3)):
                        pid, price = random.choice(products_cache)
                        qty = random.randint(1, 3)
                        subtotal = price * qty
                        cur.execute("INSERT INTO detalle_ordenes (orden_id, producto_id, cantidad, precio_unitario) VALUES (%s, %s, %s, %s)",
                                    (oid, pid, qty, price))
                        monto_orden += subtotal
                        total += 1
                    
                    cur.execute("UPDATE ordenes SET total = %s WHERE orden_id = %s", (monto_orden, oid))
                    cur.execute("INSERT INTO pagos (orden_id, metodo_pago, monto) VALUES (%s, 'TARJETA', %s)", (oid, monto_orden))
                    total += 1
                    conn.commit()
                except psycopg2.Error: conn.rollback()

        duration = time.time() - start_time
        db_size = get_db_size(conn)
        
        print("\n" + "="*40)
        print(f"RESULTADOS: LEVE")
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