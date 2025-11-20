import os
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from dotenv import load_dotenv
import requests
import sys

import platform
from collections import defaultdict


#Aca se carga el .env.local 
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
dotenv_path = os.path.join(BASE_DIR, ".env.local")
if os.path.isfile(dotenv_path):
    load_dotenv(dotenv_path)
else:
    load_dotenv()


# -----------------------------
# Conexión Supabase
# -----------------------------

def get_supabase_client() -> tuple[str, dict]:
    dbg_url = os.environ.get("SUPABASE_URL")
    dbg_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    # ...puedes comentar los prints si no quieres debug...
    print(f"DEBUG SUPABASE_URL={dbg_url}", file=sys.stderr)
    print(
        f"DEBUG SUPABASE_SERVICE_ROLE_KEY={'present' if dbg_key else 'missing'}",
        file=sys.stderr,
    )

    url = dbg_url
    service_key = dbg_key

    if not url or not service_key:
        print(
            "Faltan variables de entorno para Supabase.\n"
            "Revisa que en .env.local:\n"
            "  SUPABASE_URL\n"
            "  SUPABASE_SERVICE_ROLE_KEY\n"
            f"Ruta buscada para .env.local: {dotenv_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    url = url.rstrip("/")
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    return url, headers


# -----------------------------
# Configuración de conexiones SQL Server - DATA WAREHOUSE
# -----------------------------

def get_dw_engine():
    import urllib.parse

    server = os.environ.get("MSSQL_SERVER")
    db = os.environ.get("MSSQL_DW_DB")
    user = os.environ.get("MSSQL_USER")
    pwd = os.environ.get("MSSQL_PASSWORD")
    if platform.system() == "Windows":
        driver = "ODBC Driver 17 for SQL Server"
    else:
        driver = "ODBC Driver 18 for SQL Server"

    if not all([server, db, user, pwd]):
        raise RuntimeError("Faltan vars de entorno MSSQL_SERVER/MSSQL_DW_DB/MSSQL_USER/MSSQL_PASSWORD")

    # Nota: las llaves alrededor del nombre del driver son necesarias: DRIVER={ODBC Driver 17 for SQL Server}
    odbc_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={db};"
        f"UID={user};PWD={pwd};"
        "TrustServerCertificate=yes;"
    )
    odbc_url = urllib.parse.quote_plus(odbc_str)
    return create_engine(f"mssql+pyodbc:///?odbc_connect={odbc_url}")

def a_utc_iso(fecha_str):
    tz_cr = timezone(timedelta(hours=-6))

    # Parsear fecha local con zona horaria de Costa Rica
    fecha_local = datetime.fromisoformat(fecha_str).replace(tzinfo=tz_cr)

    # Convertir a UTC (Supabase)
    fecha_utc = fecha_local.astimezone(timezone.utc)

    return fecha_utc.isoformat()


def traetablassupa(url, headers, table):
    rows: list[dict] = []
    offset = 0
    batch_size = 1000  # cuántas filas trae por viaje
    try:
        while True:
            params = {
                "select": "*",
                "limit": batch_size,
                "offset": offset
            }
            resp = requests.get(
                f"{url}/rest/v1/{table}",
                headers=headers,
                params=params,
                timeout=30
            )
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            rows.extend(batch)
            offset += batch_size

    except Exception as e:
        print(f"Error al consultar Supabase: {e}", file=sys.stderr)
        raise
    return rows


def traetablassql(engine, table):
    limit = None
    rows: list[dict] = []
    try:
        query = text(f"SELECT * FROM {table}" + (f" LIMIT {limit}" if limit is not None else ""))
        with engine.connect() as conn:
            result = conn.execute(query)
            colums = result.keys()
            for row in result.fetchall():
                rows.append(dict(zip(colums, row))) # Zip junta la columna con el valor de la fila, si la columna es id y el valor 1 queda {'id':1}
    except SQLAlchemyError as e:
        print(f"Error al consultar SQL: {e}", file=sys.stderr)
        raise
    return rows

def transformadoryloadsupaproductos(engine, supa, productostable, equivalencias):
    product_skus = [fila["SKU"] for fila in productostable]
    equiv_skus = [fila["SKU"] for fila in equivalencias]
    with engine.begin() as conn:
        for producto in supa:
            id = producto["producto_id"]
            sku = producto["sku"]
            nombre = producto["nombre"]
            categoria = producto["categoria"]
            if sku in product_skus:
                continue #confiamos en que si ya se hizo un insert del producto ya existe su equivalencia
            if sku in equiv_skus:
                continue # continuo al sgt pues este ya se que existe entonces no hace falta insertarlo
            conn.execute(
                text("INSERT INTO dbo.DimProducto (SKU, Nombre, Categoria) VALUES (:sku, :nombre, :categoria)"),
                {"sku": sku, "nombre": nombre, "categoria": categoria}
            )
            conn.execute(
                text("INSERT INTO dbo.Equivalencias (SKU, CodigoMongo, CodigoAlt) VALUES (:sku, :mongo, :alt)"),
                {"sku": sku, "mongo": None, "alt": None}
            )
            product_skus.append(sku)
            equiv_skus.append(sku)

def transformadoryloadsupaclientes(engine, supa, clientestable):
    emailexistente = [fila["Email"] for fila in clientestable]
    with engine.begin() as conn:
        for cliente in supa:
            nombre = cliente["nombre"]
            email = cliente["email"]
            genero = cliente["genero"]
            pais = cliente["pais"]
            fecha = cliente["fecha_registro"]
            try:
                fecha_python = datetime.fromisoformat(fecha.replace("Z", "")).date()
            except:
                fecha_python = datetime.strptime(fecha, "%Y-%m-%d").date()
            if email in emailexistente:
                continue
            conn.execute(
                text("INSERT INTO dbo.DimCliente (Nombre, Email, Genero, Pais, FechaCreacion) VALUES (:Nombre, :Email, :Genero, :Pais, :FechaCreacion)"),
                {"Nombre": nombre, "Email": email, "Genero": genero, "Pais": pais, "FechaCreacion": fecha_python}
            )
            emailexistente.append(email)


BASE_DIR = os.path.dirname(__file__)
LOG_PATH = os.path.join(BASE_DIR, "logVentasETLFechasIngreso", "logVentasIngreso.txt")
LOG_FECHA_DEFAULT = "1900-12-31T00:00:00"

def crearlogetlventas(fecha):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(str(fecha) + "\n")


def consultarlogetlventas():
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            lineas = f.read().strip().splitlines()

        if not lineas:
            crearlogetlventas(LOG_FECHA_DEFAULT)
            return LOG_FECHA_DEFAULT

        ultima = lineas[-1].strip()

        try:
            dt = datetime.fromisoformat(ultima.replace("Z", ""))
            return dt.isoformat()
        except ValueError:
            crearlogetlventas(LOG_FECHA_DEFAULT)
            return LOG_FECHA_DEFAULT

    except FileNotFoundError:
        crearlogetlventas(LOG_FECHA_DEFAULT)
        return LOG_FECHA_DEFAULT

def traer_ordenes_por_fecha_supa(url, headers, fecha_min, fecha_max):
    rows = []
    offset = 0
    batch_size = 1000

    try:
        while True:
            params = [
                ("select", "*"),
                ("fecha", f"gte.{fecha_min}"),
                ("fecha", f"lte.{fecha_max}"),
                ("order", "fecha.asc"),
                ("limit", batch_size),
                ("offset", offset)
            ]

            resp = requests.get(
                f"{url}/rest/v1/orden",
                headers=headers,
                params=params,
                timeout=30
            )
            resp.raise_for_status()

            batch = resp.json()
            if not batch:
                break

            rows.extend(batch)
            offset += batch_size

    except Exception as e:
        print(f"Error al consultar Supabase: {e}", file=sys.stderr)
        raise

    crearlogetlventas(fecha_max)
    return rows

def diccionario_ordenes_por_cliente_fecha(ordenesfecha):
    ordenes_cliente_fecha = defaultdict(lambda: defaultdict(list))

    for o in ordenesfecha:
        cliente = o["cliente_id"]
        fecha = o["fecha"][:10]  
        ordenes_cliente_fecha[cliente][fecha].append(o["orden_id"])

    return ordenes_cliente_fecha

def agrupar_con_detalles(ordenes_cliente_fecha, url, headers):
    # 1. Traer TODOS los detalles de supabase en una sola llamada grande
    detalles_tabla = traetablassupa(url, headers, "orden_detalle")  

    # 2. Indexar por orden_id para buscar rápido
    index_detalles = defaultdict(list)
    for det in detalles_tabla:
        index_detalles[det["orden_id"]].append(det)

    # 3. Diccionario final: cliente → fecha → producto → métricas
    resultado = defaultdict(
        lambda: defaultdict(
            lambda: defaultdict(
                lambda: {"cantidad_total": 0, "monto_total": 0}
            )
        )
    )

    # 4. JUNTA EN CASO DE QUE HAYA UN CLIENTE CON MISMO PEDIDO DE PRODUCTO EN EL MISMO DIA VARIAS VECES
    for cliente, fechas in ordenes_cliente_fecha.items():
        for fecha, ordenes in fechas.items():
            for orden_id in ordenes:

                # Obtener detalles de ese orden
                detalles = index_detalles.get(orden_id, [])

                # Acumular por producto
                for det in detalles:
                    producto = det["producto_id"]
                    cantidad = det["cantidad"]
                    precio = det["precio_unit"]

                    resultado[cliente][fecha][producto]["cantidad_total"] += cantidad
                    resultado[cliente][fecha][producto]["monto_total"] += cantidad * precio

    return resultado

def findFechaId(sqltablafecha, fechaconsegundos):
    fecha_str = fechaconsegundos[:10]
    fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d").date()

    for row in sqltablafecha:
        if row["Fecha"] == fecha_obj:
            return row["IdTiempo"]

    print(f"NO SE ENCONTRO UNA FECHA ({fecha_str}) - ESTE ERROR ES POR LLENADO DE FECHAS NO POR EL SCRIPT")
    return None

def transformadoryloadsupaVENTAS(engine, url, headers, ordenesfecha, sqltablafecha):
    ordenes_cliente_fecha = diccionario_ordenes_por_cliente_fecha(ordenesfecha)
    ordenes_cliente_fecha_producto_metricas = agrupar_con_detalles(ordenes_cliente_fecha, url, headers)
    with engine.begin() as conn:
        for cliente, fechas in ordenes_cliente_fecha_producto_metricas.items():
            for fecha, productos in fechas.items():
                idtiempo = findFechaId(sqltablafecha, fecha)
                if idtiempo is None:
                    continue
                for producto, metricas in productos.items():

                    total = metricas["monto_total"]
                    cantidad = metricas["cantidad_total"]
                    precio_unitario = total / cantidad if cantidad != 0 else 0

                    conn.execute(
                        text("""
                            INSERT INTO dbo.FactVentas 
                            (IdTiempo, IdProducto, IdCliente, TotalVentas, Cantidad, Precio)
                            VALUES (:IdTiempo, :IdProducto, :IdCliente, :TotalVentas, :Cantidad, :Precio)
                        """),
                        {
                            "IdTiempo": idtiempo,
                            "IdProducto": producto,
                            "IdCliente": cliente,
                            "TotalVentas": total,
                            "Cantidad": cantidad,
                            "Precio": precio_unitario
                        }
                    )


def run_etl():
    ### AQUI VA EL PIPELINE (EXTRACT DE SUPA Y DESPUES LOAD A SQL UNA VEZ FUE TRANSFORMADO);
    url, headers = get_supabase_client()
    contenidosclientessupa = traetablassupa(url, headers, "cliente")
    contenidosordenessupa = traetablassupa(url, headers, "orden")
    contenidosdetallessupa = traetablassupa(url, headers, "orden_detalle")
    contenidosproductossupa = traetablassupa(url, headers, "producto")
    
    enginesql = get_dw_engine()
    contenidosproductossql = traetablassql(enginesql, "dbo.DimProducto")
    contenidoequivalencias = traetablassql(enginesql, "dbo.Equivalencias")
    contenidoclientessql = traetablassql(enginesql, "dbo.DimCliente")
    factVentas = traetablassql(enginesql, "dbo.FactVentas")
    tablafecha = traetablassql(enginesql, "dbo.DimTiempo")

    #crea productos y sus equivalencias o en su defecto revisa equivalencias en dw
    transformadoryloadsupaproductos(enginesql, contenidosproductossupa, contenidosproductossql ,contenidoequivalencias)

    #crea clientes en dw
    transformadoryloadsupaclientes(enginesql, contenidosclientessupa, contenidoclientessql)

    contenidosproductossql = traetablassql(enginesql, "dbo.DimProducto")
    contenidoclientessql = traetablassql(enginesql, "dbo.DimCliente")

    #Fecha despues del ultimo insertado en factventas (se sabe mediante el log)
    fecha_min = consultarlogetlventas()
    fecha_max_local = datetime.now().isoformat()
    fecha_max = a_utc_iso(fecha_max_local)    

    ordenesdetalle = traer_ordenes_por_fecha_supa(url,headers,fecha_min,fecha_max)
    #para crear las ventas hechas a un cliente de un producto en un dia
    transformadoryloadsupaVENTAS(enginesql, url, headers, ordenesdetalle, tablafecha)
    #print(contenidosproductossql)

    print("ETL COMPLETADO CON EXITO")


if __name__ == "__main__":
    run_etl()

