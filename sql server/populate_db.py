import argparse
import os
import random
import json
from decimal import Decimal
from datetime import datetime, timedelta

import pyodbc
from faker import Faker


def build_conn_str(server, database, username, password, trusted, driver):
    if trusted:
        return f"Driver={{{driver}}};Server={server};Database={database};Trusted_Connection=yes;"
    else:
        return f"Driver={{{driver}}};Server={server};Database={database};UID={username};PWD={password};"


def chunked(iterable, size):
    for i in range(0, len(iterable), size):
        yield iterable[i:i+size]


def insert_clients(cursor, fake, n):
    rows = []
    genders = ['Masculino', 'Femenino']
    for _ in range(n):
        nombre = fake.name()
        email = fake.unique.email()
        genero = random.choice(genders)
        pais = fake.country()
        fecha = fake.date_between(start_date='-3y', end_date='today')
        rows.append((nombre, email, genero, pais, fecha))

    sql = "INSERT INTO sales_ms.Cliente (Nombre, Email, Genero, Pais, FechaRegistro) VALUES (?, ?, ?, ?, ?)"
    # executemany in chunks to avoid very large operations
    for part in chunked(rows, 200):
        cursor.executemany(sql, part)


def insert_products(cursor, fake, n, json_path=None):
    """
    Inserta productos. Si json_path es proporcionado, primero inserta los SKUs del JSON,
    luego completa hasta n productos con datos generados por Faker.
    """
    categories = [
        'Electrónica', 'Ropa', 'Hogar', 'Juguetes', 'Belleza', 'Deportes', 'Alimentos', 'Accesorios'
    ]
    rows = []
    seen_skus = set()  # Para evitar duplicados
    
    # Si hay JSON, cargar SKUs de ahí primero
    json_count = 0
    duplicates_skipped = 0
    if json_path and os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                equivalencias = json.load(f)
            
            # Insertar productos del JSON (solo usar SKU)
            for item in equivalencias:
                sku = item['SKU']
                
                # Saltar duplicados
                if sku in seen_skus:
                    duplicates_skipped += 1
                    continue
                
                seen_skus.add(sku)
                nombre = item.get('nombre', fake.sentence(nb_words=3).rstrip('.'))
                categoria = item.get('categoria', random.choice(categories))
                # Mapear categorías en español si vienen en minúsculas
                categoria_map = {
                    'electronicos': 'Electrónica',
                    'bebidas': 'Alimentos',
                    'alimentos': 'Alimentos',
                    'higiene': 'Belleza',
                    'limpieza': 'Hogar'
                }
                categoria = categoria_map.get(categoria.lower(), categoria.capitalize())
                
                rows.append((sku, nombre, categoria))
                json_count += 1
            
            print(f'  → Cargados {json_count} productos desde {json_path}')
            if duplicates_skipped > 0:
                print(f'  ⚠️  Omitidos {duplicates_skipped} SKUs duplicados del JSON')
        except Exception as e:
            print(f'  ⚠️  Error cargando JSON: {e}. Generando todos los productos con Faker.')
    
    # Completar con Faker hasta alcanzar n productos
    remaining = n - json_count
    if remaining > 0:
        print(f'  → Generando {remaining} productos adicionales con Faker...')
        for _ in range(remaining):
            # Generar SKU único
            while True:
                sku = fake.unique.lexify(text='SKU??????').upper()
                if sku not in seen_skus:
                    seen_skus.add(sku)
                    break
            
            nombre = fake.sentence(nb_words=3).rstrip('.')
            categoria = random.choice(categories)
            rows.append((sku, nombre, categoria))

    sql = "INSERT INTO sales_ms.Producto (SKU, Nombre, Categoria) VALUES (?, ?, ?)"
    for part in chunked(rows, 200):
        cursor.executemany(sql, part)


def insert_orders(cursor, fake, n, client_ids):
    """Insert n orders, choosing ClienteId from the provided client_ids list.
    This avoids referencing old ClienteId ranges when the table already contained rows.
    """
    canales = ['WEB', 'TIENDA', 'APP']
    rows = []
    for _ in range(n):
        cliente_id = random.choice(client_ids)
        fecha = fake.date_time_between(start_date='-2y', end_date='now')
        canal = random.choice(canales)
        # Total inicialmente 0, we'll compute after inserting detalles
        total = Decimal('0.00')
        rows.append((cliente_id, fecha, canal, 'USD', total))

    sql = "INSERT INTO sales_ms.Orden (ClienteId, Fecha, Canal, Moneda, Total) VALUES (?, ?, ?, ?, ?)"
    for part in chunked(rows, 200):
        cursor.executemany(sql, part)


def insert_order_details(cursor, order_ids, product_ids, fake):
    """
    Inserta detalles de orden. Algunas órdenes tendrán múltiples productos.
    - 60% de órdenes: 1 producto
    - 25% de órdenes: 2-3 productos
    - 15% de órdenes: 4-7 productos
    """
    rows = []
    for orden_id in order_ids:
        # Determinar cuántos productos tendrá esta orden
        rand = random.random()
        if rand < 0.60:
            num_productos = 1
        elif rand < 0.85:
            num_productos = random.randint(2, 3)
        else:
            num_productos = random.randint(4, 7)
        
        # Insertar los productos (sin repetir en la misma orden)
        productos_usados = set()
        for _ in range(num_productos):
            # Seleccionar producto único para esta orden
            producto_id = random.choice(product_ids)
            while producto_id in productos_usados and len(productos_usados) < len(product_ids):
                producto_id = random.choice(product_ids)
            productos_usados.add(producto_id)
            
            cantidad = random.randint(1, 10)
            precio = round(random.uniform(5, 500), 2)
            # 30% chance of having a discount (1-30%)
            descuento = None
            if random.random() < 0.3:
                descuento = round(random.uniform(1, 30), 2)
            rows.append((orden_id, producto_id, cantidad, precio, descuento))

    sql = "INSERT INTO sales_ms.OrdenDetalle (OrdenId, ProductoId, Cantidad, PrecioUnit, DescuentoPct) VALUES (?, ?, ?, ?, ?)"
    for part in chunked(rows, 200):
        cursor.executemany(sql, part)


def update_order_totals(cursor):
    # Calculate totals per order and update
    agg_sql = (
        "SELECT OrdenId, SUM(Cantidad * PrecioUnit * (1 - ISNULL(DescuentoPct,0)/100.0)) AS Total "
        "FROM sales_ms.OrdenDetalle GROUP BY OrdenId"
    )
    cursor.execute(agg_sql)
    updates = cursor.fetchall()
    update_sql = "UPDATE sales_ms.Orden SET Total = ? WHERE OrdenId = ?"
    params = [(row.Total, row.OrdenId) for row in updates]
    for part in chunked(params, 200):
        cursor.executemany(update_sql, part)


def main():
    parser = argparse.ArgumentParser(description='Populate sales_ms DB with fake data')
    parser.add_argument('--server', default='localhost', help='SQL Server host')
    parser.add_argument('--database', default='ventas_ms', help='Database name')
    parser.add_argument('--username', help='DB username (if not using integrated auth)')
    parser.add_argument('--password', help='DB password')
    parser.add_argument('--trusted', action='store_true', help='Use Trusted Connection (Windows auth). If set, username/password are ignored')
    parser.add_argument('--driver', default='ODBC Driver 17 for SQL Server', help='ODBC Driver name')
    parser.add_argument('--clientes', type=int, default=600, help='Número de clientes (default 600)')
    parser.add_argument('--productos', type=int, default=420, help='Número de productos (default 420)')
    parser.add_argument('--ordenes', type=int, default=5000, help='Número de órdenes (default 5000)')
    parser.add_argument('--json-equivalencias', default='../equivalencias.json', help='Ruta al JSON de equivalencias (default: ../equivalencias.json)')

    args = parser.parse_args()

    fake = Faker('es_ES')
    Faker.seed(0)
    random.seed(0)

    conn_str = build_conn_str(args.server, args.database, args.username, args.password, args.trusted, args.driver)
    print('Conectando con:', conn_str)

    with pyodbc.connect(conn_str, autocommit=False) as conn:
        cursor = conn.cursor()

        # Insertar clientes (600 por defecto)
        print(f'Insertando {args.clientes} clientes...')
        cursor.execute("SELECT ISNULL(MAX(ClienteId), 0) FROM sales_ms.Cliente")
        base_client = cursor.fetchone()[0]
        insert_clients(cursor, fake, args.clientes)
        conn.commit()
        cursor.execute("SELECT ClienteId FROM sales_ms.Cliente WHERE ClienteId > ? ORDER BY ClienteId", base_client)
        client_ids = [r[0] for r in cursor.fetchall()]

        # Insertar productos (420 por defecto)
        print(f'Insertando {args.productos} productos...')
        cursor.execute("SELECT ISNULL(MAX(ProductoId), 0) FROM sales_ms.Producto")
        base_product = cursor.fetchone()[0]
        insert_products(cursor, fake, args.productos, args.json_equivalencias)
        conn.commit()
        cursor.execute("SELECT ProductoId FROM sales_ms.Producto WHERE ProductoId > ? ORDER BY ProductoId", base_product)
        product_ids = [r[0] for r in cursor.fetchall()]

        # Insertar órdenes (5000 por defecto)
        print(f'Insertando {args.ordenes} órdenes (Total inicial 0)...')
        cursor.execute("SELECT ISNULL(MAX(OrdenId), 0) FROM sales_ms.Orden")
        base_order = cursor.fetchone()[0]
        insert_orders(cursor, fake, args.ordenes, client_ids)
        conn.commit()
        cursor.execute("SELECT OrdenId FROM sales_ms.Orden WHERE OrdenId > ? ORDER BY OrdenId", base_order)
        order_ids = [r[0] for r in cursor.fetchall()]

        # Insertar detalles (múltiples productos por orden)
        print(f'Insertando detalles de orden para {len(order_ids)} órdenes...')
        print(f'  → 60% órdenes: 1 producto')
        print(f'  → 25% órdenes: 2-3 productos')
        print(f'  → 15% órdenes: 4-7 productos')
        insert_order_details(cursor, order_ids, product_ids, fake)
        conn.commit()

        print('Actualizando totales de órdenes...')
        update_order_totals(cursor)
        conn.commit()

    print('Inserción completada. Verifica con SELECT COUNT(*) en cada tabla.')


if __name__ == '__main__':
    main()
