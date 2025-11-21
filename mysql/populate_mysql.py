import argparse
import random
import json
from decimal import Decimal
from math import floor
from datetime import datetime
from pathlib import Path

import mysql.connector
from faker import Faker


# función para dividir una lista grande en pedacitos más pequeños
# sirve para no insertar todos los datos de golpe y no saturar la base de datos
def chunked(iterable, size):
    for i in range(0, len(iterable), size):
        yield iterable[i:i+size]


# función para convertir números en texto con formato de dinero (con dos decimales)
def format_money(amount, use_thousands=False):
    # Convertimos el número a float por si viene en otro formato
    amt = float(amount)
    if use_thousands and abs(amt) >= 1000:
        # Si el número es grande (1000 o más) y queremos, le ponemos coma para separar los miles
        return f"{amt:,.2f}"
    else:
        # Si no, solo lo convertimos a texto con dos decimales
        return f"{amt:.2f}"


# función para agregar "errores" a propósito en el formato de los precios
# el 80% de las veces usa punto (123.45), el 20% usa coma (123,45)
# esto fue por la parte del enunciado que dice "Fechas y montos como texto (requiere limpieza, reemplazo de comas/puntos)."
def maybe_format_price(amount):
    # convertimos el precio a texto con dos decimales usando punto
    s = f"{amount:.2f}"
    if random.random() < 0.2:
        # en el 20% de los casos, cambiamos el punto por coma para simular datos "sucios"
        s = s.replace('.', ',')
    return s


# función para crear clientes en la base de datos
# genera la cantidad de clientes que se le pida, con nombres, correos y países aleatorios
# los géneros pueden ser M (masculino), F (femenino) o X (otro)
# las fechas de creación están entre hace 3 años y hoy
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


# función para insertar productos en la base de datos desde el archivo equivalencias.json
# lee el archivo JSON y saca de ahí el código del producto, el nombre y la categoría
# además crea 100 productos adicionales inventados con Faker
def insert_products(cursor, fake, equivalencias_data):
    # insertamos productos usando el código que viene del archivo equivalencias.json
    rows = []
    for item in equivalencias_data:
        codigo = item['CodigoAlt']
        nombre = item['nombre']
        categoria = item['categoria'].capitalize()
        rows.append((codigo, nombre, categoria))
    
    # Ahora agregamos 100 productos más inventados con Faker, todos únicos
    categorias_faker = ['Electronicos', 'Bebidas', 'Alimentos', 'Higiene', 'Limpieza']
    
    for i in range(100):
        # Generamos códigos con formato ALT-XXNN donde XX son letras y NN son números
        codigo = fake.unique.bothify(text='ALT-??##').upper()
        # Cada producto tiene un nombre único generado con Faker
        nombre = fake.unique.word().capitalize() + ' ' + random.choice(['Premium', 'Deluxe', 'Pro', 'Plus', 'Max', 'Ultra', 'Mini', 'Mega', 'Super', 'Eco'])
        categoria = random.choice(categorias_faker)
        rows.append((codigo, nombre, categoria))

    sql = "INSERT INTO Producto (codigo_alt, nombre, categoria) VALUES (%s, %s, %s)"
    for part in chunked(rows, 200):
        cursor.executemany(sql, part)


# función para crear órdenes de compra en la base de datos
# genera la cantidad de órdenes que se le pida y las asigna a clientes al azar
# las fechas son entre hace 2 años y hoy, los canales pueden ser WEB, TIENDA o APP
# las monedas son USD (dólares) o CRC (colones), y el total empieza en 0 (se calcula después)
def insert_orders(cursor, fake, n, client_ids):
    canales = ['WEB', 'TIENDA', 'APP']
    rows = []
    for _ in range(n):
        cliente_id = random.choice(client_ids)
        fecha = fake.date_time_between(start_date='-2y', end_date='now').strftime('%Y-%m-%d %H:%M:%S')
        canal = random.choice(canales)
        moneda = random.choice(['USD', 'CRC'])
        total = '0.00'  # por ahora ponemos 0, después calculamos cuánto es el total de la orden
        rows.append((cliente_id, fecha, canal, moneda, total))

    sql = "INSERT INTO Orden (cliente_id, fecha, canal, moneda, total) VALUES (%s, %s, %s, %s, %s)"
    for part in chunked(rows, 200):
        cursor.executemany(sql, part)


# Función para agregar los productos que lleva cada orden
# Cada orden tiene entre 1 y 5 productos diferentes (lo más común es 2 o 3 productos)
# Cada producto tiene una cantidad al azar (entre 1 y 10 unidades) y un precio inventado
# El 30% de los productos tienen descuento (entre 1% y 30%)
def insert_order_details(cursor, order_ids, product_ids, fake):
    # Vamos a crear entre 1 y 5 productos por cada orden
    rows = []
    for orden_id in order_ids:
        # Decidimos cuántos productos va a tener esta orden (1 a 5, con mayor chance de tener 2 o 3)
        num_products = random.choices([1, 2, 3, 4, 5], weights=[20, 35, 25, 15, 5], k=1)[0]
        selected_products = random.sample(product_ids, min(num_products, len(product_ids)))
        
        for producto_id in selected_products:
            cantidad = random.randint(1, 10)  # Cuántas unidades se compran (mínimo 1, nunca 0)
            precio = round(random.uniform(5, 500), 2)
            descuento_pct = None
            if random.random() < 0.3:
                descuento_pct = round(random.uniform(1, 30), 2)
            # El precio lo guardamos como texto, y a veces usamos coma en vez de punto
            precio_str = maybe_format_price(precio)
            rows.append((orden_id, producto_id, cantidad, precio_str))

    sql = "INSERT INTO OrdenDetalle (orden_id, producto_id, cantidad, precio_unit) VALUES (%s, %s, %s, %s)"
    for part in chunked(rows, 200):
        cursor.executemany(sql, part)


# Función para calcular cuánto cuesta cada orden en total
# Lee todos los productos de cada orden y suma (cantidad × precio) de cada uno
# El problema es que los precios están guardados como texto y pueden tener formatos diferentes:
# - '1,200.50' significa mil doscientos con cincuenta centavos (coma separa miles)
# - '1200,50' significa mil doscientos con cincuenta centavos (coma es el decimal)
# - '1200.50' es el formato normal
# También el 25% de los totales se guardan con coma de miles para simular datos inconsistentes
def update_order_totals(cursor):
    # Calculamos los totales sumando todos los productos de cada orden
    # Como los precios están guardados como texto con formatos raros, hay que limpiarlos primero
    cursor.execute("SELECT id FROM Orden")
    order_ids = [r[0] for r in cursor.fetchall()]

    get_details_sql = "SELECT cantidad, precio_unit FROM OrdenDetalle WHERE orden_id = %s"
    update_sql = "UPDATE Orden SET total = %s WHERE id = %s"
    for oid in order_ids:
        cursor.execute(get_details_sql, (oid,))
        details = cursor.fetchall()
        total = Decimal('0.00')
        for cantidad, precio_unit in details:
            # El precio puede venir como '1,200.50' o '1200,50' o '1200.50'
            pu_str = str(precio_unit)
            # Si tiene punto Y coma, la coma es para separar miles, entonces la quitamos
            if ',' in pu_str and '.' in pu_str:
                normalized = pu_str.replace(',', '')
            elif ',' in pu_str and '.' not in pu_str:
                # Si solo tiene coma, entonces la coma representa el decimal, la cambiamos por punto
                normalized = pu_str.replace(',', '.')
            else:
                normalized = pu_str
            try:
                pu = Decimal(normalized)
            except Exception:
                # Si algo falla, usamos 0 para no romper el programa
                pu = Decimal('0.00')
            total += pu * Decimal(cantidad)
        # Si el total sale 0 o negativo, lo cambiamos a 1.00 para que tenga sentido
        if total <= 0:
            total = Decimal('1.00')
        # A veces guardamos el total con separador de miles, a veces no (para variar)
        use_thousands = random.random() < 0.25
        total_str = format_money(total, use_thousands=use_thousands)
        cursor.execute(update_sql, (total_str, oid))


# Función principal que hace todo el trabajo de llenar la base de datos
# Inserta 600 clientes inventados, 180 productos (sacados del archivo equivalencias.json)
# y 5000 órdenes de compra con sus productos
# Los datos tienen "errores" a propósito para simular información del mundo real
def main():
    parser = argparse.ArgumentParser(description='Populate MySQL sales_mysql DB with fake data')
    parser.add_argument('--host', default='localhost', help='MySQL host')
    parser.add_argument('--port', type=int, default=3306, help='MySQL port')
    parser.add_argument('--database', default='sales_mysql', help='Database name')
    parser.add_argument('--user', default='root', help='DB username')
    parser.add_argument('--password', default='', help='DB password')

    args = parser.parse_args()

    fake = Faker('es_ES')
    Faker.seed(1)
    random.seed(1)

    # Leemos el archivo equivalencias.json que tiene la lista de productos
    equivalencias_path = Path(__file__).parent.parent / 'equivalencias.json'
    with open(equivalencias_path, 'r', encoding='utf-8') as f:
        equivalencias_data = json.load(f)

    conn = mysql.connector.connect(host=args.host, port=args.port, user=args.user, password=args.password, database=args.database)
    cursor = conn.cursor()

    # Cantidades que vamos a insertar (números fijos)
    num_clients = 600
    num_orders = 5000

    # Paso 1: Insertar clientes
    cursor.execute("SELECT IFNULL(MAX(id),0) FROM Cliente")
    base_client = cursor.fetchone()[0]
    print(f'Insertando {num_clients} clientes...')
    insert_clients(cursor, fake, num_clients)
    conn.commit()
    cursor.execute("SELECT id FROM Cliente WHERE id > %s ORDER BY id", (base_client,))
    client_ids = [r[0] for r in cursor.fetchall()]

    # Paso 2: Insertar productos del archivo equivalencias.json
    cursor.execute("SELECT IFNULL(MAX(id),0) FROM Producto")
    base_prod = cursor.fetchone()[0]
    print(f'Insertando {len(equivalencias_data)} productos desde equivalencias.json...')
    insert_products(cursor, fake, equivalencias_data)
    conn.commit()
    cursor.execute("SELECT id FROM Producto WHERE id > %s ORDER BY id", (base_prod,))
    product_ids = [r[0] for r in cursor.fetchall()]

    # Paso 3: Insertar órdenes
    cursor.execute("SELECT IFNULL(MAX(id),0) FROM Orden")
    base_order = cursor.fetchone()[0]
    print(f'Insertando {num_orders} órdenes...')
    insert_orders(cursor, fake, num_orders, client_ids)
    conn.commit()
    cursor.execute("SELECT id FROM Orden WHERE id > %s ORDER BY id", (base_order,))
    order_ids = [r[0] for r in cursor.fetchall()]

    # Paso 4: Insertar los productos de cada orden (cada orden tiene de 1 a 5 productos)
    print(f'Insertando detalles para {len(order_ids)} órdenes (1-5 productos por orden)...')
    insert_order_details(cursor, order_ids, product_ids, fake)
    conn.commit()

    # Paso 5: Calcular cuánto cuesta cada orden en total
    print('Actualizando totales de órdenes...')
    update_order_totals(cursor)
    conn.commit()

    cursor.close()
    conn.close()

    print('Inserción MySQL completada. Verifica con SELECT COUNT(*) en cada tabla.')


if __name__ == '__main__':
    main()
