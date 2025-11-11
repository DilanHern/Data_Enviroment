import argparse
import os
import random
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


def insert_products(cursor, fake, n):
    categories = [
        'Electrónica', 'Ropa', 'Hogar', 'Juguetes', 'Belleza', 'Deportes', 'Alimentos', 'Accesorios'
    ]
    rows = []
    for _ in range(n):
        sku = fake.unique.lexify(text='SKU??????').upper()
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
    """Ensure every order in order_ids gets at least one OrdenDetalle.
    Creates exactly one detail per order (so total details == len(order_ids)).
    product_ids is a list of valid ProductoId values to choose from.
    """
    rows = []
    for orden_id in order_ids:
        producto_id = random.choice(product_ids)
        cantidad = random.randint(1, 10)
        precio = round(random.uniform(5, 500), 2)
        # 30% chance of having a discount (1-30%) — never 100%
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
    parser = argparse.ArgumentParser(description='Populate sales_ms DB with fake data (420 rows per table by default)')
    parser.add_argument('--server', default='localhost', help='SQL Server host')
    parser.add_argument('--database', default='ventas_ms', help='Database name')
    parser.add_argument('--username', help='DB username (if not using integrated auth)')
    parser.add_argument('--password', help='DB password')
    parser.add_argument('--trusted', action='store_true', help='Use Trusted Connection (Windows auth). If set, username/password are ignored')
    parser.add_argument('--driver', default='ODBC Driver 17 for SQL Server', help='ODBC Driver name')
    parser.add_argument('--rows', type=int, default=420, help='Rows per table (default 420)')

    args = parser.parse_args()

    fake = Faker('es_ES')
    Faker.seed(0)
    random.seed(0)

    conn_str = build_conn_str(args.server, args.database, args.username, args.password, args.trusted, args.driver)
    print('Conectando con:', conn_str)

    with pyodbc.connect(conn_str, autocommit=False) as conn:
        cursor = conn.cursor()

        rows = args.rows
        print(f'Insertando {rows} clientes...')
        # get base id to identify newly inserted rows
        cursor.execute("SELECT ISNULL(MAX(ClienteId), 0) FROM sales_ms.Cliente")
        base_client = cursor.fetchone()[0]
        insert_clients(cursor, fake, rows)
        conn.commit()
        cursor.execute("SELECT ClienteId FROM sales_ms.Cliente WHERE ClienteId > ? ORDER BY ClienteId", base_client)
        client_ids = [r[0] for r in cursor.fetchall()]

        print(f'Insertando {rows} productos...')
        cursor.execute("SELECT ISNULL(MAX(ProductoId), 0) FROM sales_ms.Producto")
        base_product = cursor.fetchone()[0]
        insert_products(cursor, fake, rows)
        conn.commit()
        cursor.execute("SELECT ProductoId FROM sales_ms.Producto WHERE ProductoId > ? ORDER BY ProductoId", base_product)
        product_ids = [r[0] for r in cursor.fetchall()]

        print(f'Insertando {rows} órdenes (Total inicial 0)...')
        cursor.execute("SELECT ISNULL(MAX(OrdenId), 0) FROM sales_ms.Orden")
        base_order = cursor.fetchone()[0]
        insert_orders(cursor, fake, rows, client_ids)
        conn.commit()
        cursor.execute("SELECT OrdenId FROM sales_ms.Orden WHERE OrdenId > ? ORDER BY OrdenId", base_order)
        order_ids = [r[0] for r in cursor.fetchall()]

        # Ensure every order has at least one detail. We'll create exactly one detail per order
        # so the total OrdenDetalle rows == rows (420 by default).
        print(f'Insertando {len(order_ids)} detalles de orden (uno por orden insertada)...')
        insert_order_details(cursor, order_ids, product_ids, fake)
        conn.commit()

        print('Actualizando totales de órdenes...')
        update_order_totals(cursor)
        conn.commit()

    print('Inserción completada. Verifica con SELECT COUNT(*) en cada tabla.')


if __name__ == '__main__':
    main()
