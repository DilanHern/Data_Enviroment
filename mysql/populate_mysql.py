import argparse
import random
from decimal import Decimal
from math import floor
from datetime import datetime

import mysql.connector
from faker import Faker


def chunked(iterable, size):
    for i in range(0, len(iterable), size):
        yield iterable[i:i+size]


def format_money(amount, use_thousands=False):
    # amount is Decimal or float
    amt = float(amount)
    if use_thousands and abs(amt) >= 1000:
        # include comma as thousands separator, dot for decimal
        return f"{amt:,.2f}"
    else:
        return f"{amt:.2f}"


def maybe_format_price(amount):
    # Return price string with 80% dot decimal, 20% comma decimal
    s = f"{amount:.2f}"
    if random.random() < 0.2:
        # replace dot with comma
        s = s.replace('.', ',')
    return s


def insert_clients(cursor, fake, n):
    rows = []
    genders = ['M', 'F', 'X']
    for _ in range(n):
        nombre = fake.name()
        correo = fake.unique.email()
        genero = random.choice(genders)
        pais = fake.country()
        created_at = fake.date_between(start_date='-3y', end_date='today').strftime('%Y-%m-%d')
        rows.append((nombre, correo, genero, pais, created_at))

    sql = "INSERT INTO Cliente (nombre, correo, genero, pais, created_at) VALUES (%s, %s, %s, %s, %s)"
    for part in chunked(rows, 200):
        cursor.executemany(sql, part)


def insert_products(cursor, fake, n):
    categories = ['Electrónica', 'Ropa', 'Hogar', 'Juguetes', 'Belleza', 'Deportes', 'Alimentos', 'Accesorios']
    rows = []
    for _ in range(n):
        codigo = fake.unique.bothify(text='ALT-????-####').upper()
        nombre = fake.sentence(nb_words=3).rstrip('.')
        categoria = random.choice(categories)
        rows.append((codigo, nombre, categoria))

    sql = "INSERT INTO Producto (codigo_alt, nombre, categoria) VALUES (%s, %s, %s)"
    for part in chunked(rows, 200):
        cursor.executemany(sql, part)


def insert_orders(cursor, fake, n, client_ids):
    canales = ['WEB', 'TIENDA', 'APP']
    rows = []
    for _ in range(n):
        cliente_id = random.choice(client_ids)
        fecha = fake.date_time_between(start_date='-2y', end_date='now').strftime('%Y-%m-%d %H:%M:%S')
        canal = random.choice(canales)
        moneda = random.choice(['USD', 'CRC'])
        total = '0.00'  # placeholder, we'll update after inserting detalles
        rows.append((cliente_id, fecha, canal, moneda, total))

    sql = "INSERT INTO Orden (cliente_id, fecha, canal, moneda, total) VALUES (%s, %s, %s, %s, %s)"
    for part in chunked(rows, 200):
        cursor.executemany(sql, part)


def insert_order_details(cursor, order_ids, product_ids, fake):
    # Create exactly one detail per order to guarantee each order has at least one detail
    rows = []
    for orden_id in order_ids:
        producto_id = random.choice(product_ids)
        cantidad = random.randint(1, 10)  # never zero
        precio = round(random.uniform(5, 500), 2)
        descuento_pct = None
        if random.random() < 0.3:
            descuento_pct = round(random.uniform(1, 30), 2)
        # precio_unit stored as string, sometimes with comma decimal
        precio_str = maybe_format_price(precio)
        rows.append((orden_id, producto_id, cantidad, precio_str))

    sql = "INSERT INTO OrdenDetalle (orden_id, producto_id, cantidad, precio_unit) VALUES (%s, %s, %s, %s)"
    for part in chunked(rows, 200):
        cursor.executemany(sql, part)


def update_order_totals(cursor):
    # Compute totals by joining details and summing numeric values.
    # We must parse precio_unit strings that may contain comma as decimal or thousands separator.
    # MySQL: use REPLACE to normalize commas used as thousand separators, and replace comma decimal to dot when needed.
    # A pragmatic approach: replace ',' with '' then restore decimal if necessary is complex; instead we compute per-row in Python.
    cursor.execute("SELECT id FROM Orden")
    order_ids = [r[0] for r in cursor.fetchall()]

    get_details_sql = "SELECT cantidad, precio_unit FROM OrdenDetalle WHERE orden_id = %s"
    update_sql = "UPDATE Orden SET total = %s WHERE id = %s"
    for oid in order_ids:
        cursor.execute(get_details_sql, (oid,))
        details = cursor.fetchall()
        total = Decimal('0.00')
        for cantidad, precio_unit in details:
            # precio_unit may be like '1,200.50' or '1200,50' or '1200.50'
            pu_str = str(precio_unit)
            # If both '.' and ',' present, assume comma thousands and dot decimal -> remove commas
            if ',' in pu_str and '.' in pu_str:
                normalized = pu_str.replace(',', '')
            elif ',' in pu_str and '.' not in pu_str:
                # comma used as decimal -> replace with dot
                normalized = pu_str.replace(',', '.')
            else:
                normalized = pu_str
            try:
                pu = Decimal(normalized)
            except Exception:
                # fallback
                pu = Decimal('0.00')
            total += pu * Decimal(cantidad)
        # ensure total not zero; if zero set to minimal 1.00
        if total <= 0:
            total = Decimal('1.00')
        # format sometimes with thousands separator
        use_thousands = random.random() < 0.25
        total_str = format_money(total, use_thousands=use_thousands)
        cursor.execute(update_sql, (total_str, oid))


def main():
    parser = argparse.ArgumentParser(description='Populate MySQL sales_mysql DB with fake data (420 rows per table by default)')
    parser.add_argument('--host', default='localhost', help='MySQL host')
    parser.add_argument('--port', type=int, default=3306, help='MySQL port')
    parser.add_argument('--database', default='sales_mysql', help='Database name')
    parser.add_argument('--user', default='root', help='DB username')
    parser.add_argument('--password', default='', help='DB password')
    parser.add_argument('--rows', type=int, default=420, help='Rows per table (default 420)')

    args = parser.parse_args()

    fake = Faker('es_ES')
    Faker.seed(1)
    random.seed(1)

    conn = mysql.connector.connect(host=args.host, port=args.port, user=args.user, password=args.password, database=args.database)
    cursor = conn.cursor()

    rows = args.rows

    # Insert clients
    cursor.execute("SELECT IFNULL(MAX(id),0) FROM Cliente")
    base_client = cursor.fetchone()[0]
    print(f'Insertando {rows} clientes...')
    insert_clients(cursor, fake, rows)
    conn.commit()
    cursor.execute("SELECT id FROM Cliente WHERE id > %s ORDER BY id", (base_client,))
    client_ids = [r[0] for r in cursor.fetchall()]

    # Insert products
    cursor.execute("SELECT IFNULL(MAX(id),0) FROM Producto")
    base_prod = cursor.fetchone()[0]
    print(f'Insertando {rows} productos...')
    insert_products(cursor, fake, rows)
    conn.commit()
    cursor.execute("SELECT id FROM Producto WHERE id > %s ORDER BY id", (base_prod,))
    product_ids = [r[0] for r in cursor.fetchall()]

    # Insert orders
    cursor.execute("SELECT IFNULL(MAX(id),0) FROM Orden")
    base_order = cursor.fetchone()[0]
    print(f'Insertando {rows} órdenes...')
    insert_orders(cursor, fake, rows, client_ids)
    conn.commit()
    cursor.execute("SELECT id FROM Orden WHERE id > %s ORDER BY id", (base_order,))
    order_ids = [r[0] for r in cursor.fetchall()]

    # Insert exactly one OrdenDetalle per newly created order
    print(f'Insertando {len(order_ids)} detalles (uno por orden insertada)...')
    insert_order_details(cursor, order_ids, product_ids, fake)
    conn.commit()

    # Compute and update totals (as strings)
    print('Actualizando totales de órdenes...')
    update_order_totals(cursor)
    conn.commit()

    cursor.close()
    conn.close()

    print('Inserción MySQL completada. Verifica con SELECT COUNT(*) en cada tabla.')


if __name__ == '__main__':
    main()
