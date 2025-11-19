import os
from typing import Dict, Any, List
from datetime import datetime

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from dotenv import load_dotenv
import requests
import sys
import pyodbc
import platform

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

def traetablassupa(url, headers, table):
    rows: list[dict] = []
    offset = 0
    try:
        params = {"select": "*", "offset": offset}
        resp = requests.get(f"{url}/rest/v1/{table}", headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        batch = resp.json()
        rows.extend(batch)
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

def transformadoryloadsupaVENTAS(engine, ordenes, ordenesdetalle, clientestable, sqltablafecha):
    print(sqltablafecha)

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
    tablafecha = traetablassql(enginesql, "dbo.DimTiempo")

    #crea productos y sus equivalencias o en su defecto revisa equivalencias en dw
    transformadoryloadsupaproductos(enginesql, contenidosproductossupa, contenidosproductossql ,contenidoequivalencias)

    #crea clientes en dw
    transformadoryloadsupaclientes(enginesql, contenidosclientessupa, contenidoclientessql)

    #para crear las ventas hechas a un cliente de un producto en un dia
    transformadoryloadsupaVENTAS(enginesql, contenidosordenessupa, contenidosdetallessupa, contenidosclientessupa, tablafecha)
    #print(contenidosproductossql)


if __name__ == "__main__":
    run_etl()

