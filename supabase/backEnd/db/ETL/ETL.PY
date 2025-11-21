import os
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from dotenv import load_dotenv
import requests
import sys
from decimal import Decimal
import platform
from collections import defaultdict
import re
import hashlib

def generate_sku_from_name_category(nombre: str, categoria: str, existing_skus: List[str]) -> str:
    base_raw = f"{(nombre or '').strip()}-{(categoria or '').strip()}"
    if not base_raw.strip(" -"):
        base_raw = "sin-sku"

    existing_upper = {s.upper() for s in (existing_skus or []) if s}

    h = int(hashlib.sha1(base_raw.encode("utf-8")).hexdigest(), 16)
    digits = h % 10000  # 0000-9999
    letter1 = chr(ord("A") + ((h >> 16) % 26))
    letter2 = chr(ord("A") + ((h >> 21) % 26))

    sku = f"PRD-{digits:04d}-{letter1}{letter2}"

    attempts = 0
    # primero iteramos cambiando la parte numérica para evitar colisiones
    while sku in existing_upper and attempts < 10000:
        digits = (digits + 1) % 10000
        sku = f"PRD-{digits:04d}-{letter1}{letter2}"
        attempts += 1

    # si todavía colisiona, iteramos sobre combinaciones de dos letras
    if sku in existing_upper:
        extra = 0
        max_extra = 26 * 26
        while sku in existing_upper and extra < max_extra:
            l1 = chr(ord("A") + (extra // 26))
            l2 = chr(ord("A") + (extra % 26))
            sku = f"PRD-{digits:04d}-{l1}{l2}"
            extra += 1

    return sku.upper()


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

def utc_a_hora_cr(fecha_str):
    fecha_utc = datetime.fromisoformat(fecha_str.replace("Z", "+00:00")).astimezone(timezone.utc)


    tz_cr = timezone(timedelta(hours=-6))
    fecha_cr = fecha_utc.astimezone(tz_cr)

    return fecha_cr.date().isoformat()

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
    rows: list[dict] = []
    try:
        query = text(f"SELECT * FROM {table}")
        with engine.connect() as conn:
            result = conn.execute(query)
            colums = result.keys()
            for row in result.fetchall():
                rows.append(dict(zip(colums, row)))
    except SQLAlchemyError as e:
        print(f"Error al consultar SQL: {e}", file=sys.stderr)
        raise
    return rows

def transformadoryloadsupaproductos(engine, supa, productostable, equivalencias):
    # normalizar SKUs existentes a MAYÚSCULAS y filtrar nulos
    product_skus = [fila["SKU"].upper() for fila in productostable if fila.get("SKU")]
    equiv_skus = [fila["SKU"].upper() for fila in equivalencias if fila.get("SKU")]
    global mapa_sku
    with engine.begin() as conn:
        for producto in supa:
            id = producto.get("producto_id")
            sku_raw = producto.get("sku")
            nombre = producto.get("nombre")
            categoria = producto.get("categoria")

            sku = sku_raw.upper() if sku_raw else None

            # si SKU faltante o vacío, se genera uno basado en nombre+categoria
            if not sku:
                sku = generate_sku_from_name_category(nombre, categoria, product_skus + equiv_skus)

            if sku in product_skus:
                if id:
                    mapa_sku[id] = sku
                continue
            if sku in equiv_skus:
                if id:
                    mapa_sku[id] = sku
                continue

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
            if id:
                mapa_sku[id] = sku

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


def ensure_canales_exist(engine, required_canales=None):
    if required_canales is None:
        required_canales = ["WEB", "APP", "PARTNER"]

    # Normalizar a mayúsculas
    required_upper = [c.upper() for c in required_canales]

    with engine.begin() as conn:
        # Obtener los canales existentes (nombre) en uppercase
        rows = conn.execute(text("SELECT Nombre FROM dbo.DimCanal")).fetchall()
        existing = {str(r[0]).upper() for r in rows if r and r[0] is not None}

        to_insert = [c for c in required_upper if c not in existing]
        if not to_insert:
            print(f"Canales ya presentes: {', '.join(required_upper)}")
            return

        for canal in to_insert:
            # Insertar canal mínimo; si la tabla tiene más columnas requeridas,
            # el insert puede necesitar adaptarse (por ahora solo Nombre).
            conn.execute(
                text("INSERT INTO dbo.DimCanal (Nombre) VALUES (:nombre)"),
                {"nombre": canal}
            )
        print(f"Se insertaron canales faltantes: {', '.join(to_insert)}")


ETL_DIR = os.path.dirname(__file__)
LOG_DIR = os.path.join(ETL_DIR, "logVentasETLFechasIngreso")
LOG_PATH = os.path.join(LOG_DIR, "logVentasIngreso.txt")
LOG_FECHA_DEFAULT = "1900-12-31T00:00:00"

def crearlogetlventas(fecha):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
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

    return rows

def diccionario_ordenes_por_cliente_fecha(ordenesfecha):
    # estructura: cliente -> fecha -> canal -> [orden_id]
    ordenes_cliente_fecha = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for o in ordenesfecha:
        cliente = o["cliente_id"]
        fecha = utc_a_hora_cr(o["fecha"])
        canal = (o.get("canal") or "WEB").upper()
        ordenes_cliente_fecha[cliente][fecha][canal].append(o["orden_id"])

    return ordenes_cliente_fecha

def agrupar_con_detalles(ordenes_cliente_fecha, ordenes_list, url, headers, sqltablafecha):
    # 1. Traer TODOS los detalles de supabase en una sola llamada grande
    detalles_tabla = traetablassupa(url, headers, "orden_detalle")

    # 2. Indexar por orden_id para buscar rápido
    index_detalles = defaultdict(list)
    for det in detalles_tabla:
        index_detalles[det["orden_id"]].append(det)

    # 3. Map de ordenes por id para obtener moneda de cada orden
    orden_map = {o["orden_id"]: o for o in (ordenes_list or [])}

    # 4. Map de fecha -> tipo de cambio (usar Decimal)
    fecha_tipo_map: dict = {}
    for row in (sqltablafecha or []):
        key = row.get("Fecha")
        # convertir a string YYYY-MM-DD si es date/datetime
        try:
            fecha_key = key.isoformat()
        except Exception:
            fecha_key = str(key)
        tipo = row.get("TipoCambio")
        try:
            fecha_tipo_map[fecha_key] = Decimal(str(tipo)) if tipo is not None else None
        except Exception:
            fecha_tipo_map[fecha_key] = None

    # 5. Diccionario final: cliente → fecha → canal → producto → métricas (en DÓLARES)
    resultado = defaultdict(
        lambda: defaultdict(
            lambda: defaultdict(
                lambda: defaultdict(
                    lambda: {"cantidad_total": 0, "monto_total": Decimal("0")}
                )
            )
        )
    )

    # 6. JUNTA EN CASO DE QUE HAYA UN CLIENTE CON MISMO PEDIDO DE PRODUCTO EN EL MISMO DIA VARIAS VECES
    for cliente, fechas in ordenes_cliente_fecha.items():
        for fecha, canales in fechas.items():
            # obtener tipo de cambio para la fecha (clave en formato ISO YYYY-MM-DD)
            tipo_cambio = fecha_tipo_map.get(fecha)
            for canal, ordenes in canales.items():
                for orden_id in ordenes:
                    detalles = index_detalles.get(orden_id, [])
                    orden = orden_map.get(orden_id, {})
                    moneda = (orden.get("moneda") or "USD").upper()

                    for det in detalles:
                        producto = det["producto_id"]
                        cantidad = det.get("cantidad", 0)
                        precio = det.get("precio_unit", 0)

                        # convertir a Decimal para cálculos
                        cantidad_dec = Decimal(str(cantidad))
                        precio_dec = Decimal(str(precio))
                        monto = cantidad_dec * precio_dec  # monto en la moneda de la orden

                        if moneda in ("CRC"):
                            if tipo_cambio and tipo_cambio != 0:
                                # monto en dólares = monto_en_colones / tipo_cambio (colones por dolar)
                                monto_dolares = monto / tipo_cambio
                            else:
                                # si no hay tipo de cambio disponible, emitir advertencia y asumir no conversión
                                print(f"Warning: TipoCambio no encontrado para fecha {fecha}, orden {orden_id}; se asume USD", file=sys.stderr)
                                monto_dolares = monto
                        else:
                            # ya está en dólares
                            monto_dolares = monto

                        # agregar a los acumulados (monto_total en DECIMAL USD)
                        resultado[cliente][fecha][canal][producto]["cantidad_total"] += cantidad_dec
                        resultado[cliente][fecha][canal][producto]["monto_total"] += monto_dolares

    return resultado

def findFechaId(sqltablafecha, fechaconsegundos):
    fecha_str = fechaconsegundos[:10]
    fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d").date()

    for row in sqltablafecha:
        if row["Fecha"] == fecha_obj:
            return row["IdTiempo"]

    print(f"NO SE ENCONTRO UNA FECHA ({fecha_str}) - ESTE ERROR ES POR LLENADO DE FECHAS NO POR EL SCRIPT")
    return None

mapa_emails: dict = {}
mapa_sku: dict = {}

def init_mapas(url: str | None = None, headers: dict | None = None):
    global mapa_emails, mapa_sku
    if not url or not headers:
        url, headers = get_supabase_client()
    mapa_emails = {c["cliente_id"]: c.get("email") for c in traetablassupa(url, headers, "cliente")}
    mapa_sku = {p["producto_id"]: (p.get("sku").upper() if p.get("sku") else None) for p in traetablassupa(url, headers, "producto")}

def findClienteId(sqltablacliente, clienteobj):
    email = mapa_emails.get(clienteobj)
    for row in sqltablacliente:
        if row["Email"] == email:
            return row["IdCliente"]

    print(f"NO SE ENCONTRO UN CLIENTE, ESTE ES ERROR DEL SCRIPT DE LLENADO DE CLIENTES ({email})")
    return None

def findProductoId(sqltablaproducto, productobj):
    sku = mapa_sku.get(productobj)
    for row in sqltablaproducto:
        if row["SKU"] == sku:
            return row["IdProducto"]

    print(f"NO SE ENCONTRO UN PRODUCTO, ESTE ES ERROR DEL SCRIPT DE LLENADO DE PRODUCTO ({sku})")
    return None


def findCanalId(sqltablacanal, canal_name):
    if not canal_name:
        return None
    canal_up = canal_name.upper()
    for row in (sqltablacanal or []):
        nombre = row.get("Nombre") or row.get("Canal") or None
        if nombre and str(nombre).upper() == canal_up:
            return row.get("IdCanal")

    print(f"NO SE ENCONTRO UN CANAL, revise DimCanal ({canal_up})")
    return None


def transformadoryloadsupaVENTAS(engine, url, headers, ordenesfecha, sqltablafecha, sqltablacliente, sqltablaproducto, sqltablacanal):
    ordenes_cliente_fecha = diccionario_ordenes_por_cliente_fecha(ordenesfecha)
    ordenes_cliente_fecha_producto_metricas = agrupar_con_detalles(ordenes_cliente_fecha, ordenesfecha, url, headers, sqltablafecha)
    with engine.begin() as conn:
        for cliente, fechas in ordenes_cliente_fecha_producto_metricas.items():
            idcliente = findClienteId(sqltablacliente, cliente)
            if idcliente is None:
                print("Clienteid no existe conforme a esa factura")
                continue
            for fecha, canales in fechas.items():
                idtiempo = findFechaId(sqltablafecha, fecha)
                if idtiempo is None:
                    continue
                for canal, productos in canales.items():
                    idcanal = findCanalId(sqltablacanal, canal)
                    if idcanal is None:
                        print(f"Saltando ventas para canal desconocido: {canal}")
                        continue
                    for producto, metricas in productos.items():
                        idproducto = findProductoId(sqltablaproducto, producto)
                        if idproducto is None:
                            print("Producto no encontrado, se salta")
                            continue
                        total = metricas["monto_total"]
                        cantidad = metricas["cantidad_total"]
                        precio_unitario = (total / cantidad) if cantidad != 0 else Decimal("0")

                        row = conn.execute(
                            text("""
                                SELECT IdFactVentas, TotalVentas, Cantidad
                                FROM dbo.FactVentas
                                WHERE IdTiempo = :IdTiempo AND IdProducto = :IdProducto AND IdCliente = :IdCliente AND IdCanal = :IdCanal
                            """),
                            {"IdTiempo": idtiempo, "IdProducto": idproducto, "IdCliente": idcliente, "IdCanal": idcanal}
                        ).fetchone()

                        if row:
                            # Si ya existe entonces actualiza los datos en la tabla fact ventas
                            idfact = row[0]

                            total_prev = Decimal(row[1])           # viene como Decimal
                            cantidad_prev = Decimal(row[2])

                            total = Decimal(str(total))            # convertir el "total" del ETL a Decimal
                            cantidad = Decimal(str(cantidad))      # convertir la cantidad a Decimal

                            nuevo_total = total_prev + total
                            nueva_cantidad = cantidad_prev + cantidad

                            nuevo_precio = (nuevo_total / nueva_cantidad if nueva_cantidad != 0 else Decimal("0"))

                            conn.execute(
                                text("""
                                    UPDATE dbo.FactVentas
                                    SET TotalVentas = :TotalVentas, Cantidad = :Cantidad, Precio = :Precio
                                    WHERE IdFactVentas = :IdFactVentas
                                """),
                                {"TotalVentas": nuevo_total, "Cantidad": nueva_cantidad, "Precio": nuevo_precio, "IdFactVentas": idfact}
                            )
                        else:
                            # Si no existe solo hace un insert
                            conn.execute(
                                text("""
                                    INSERT INTO dbo.FactVentas
                                    (IdTiempo, IdProducto, IdCliente, IdCanal, TotalVentas, Cantidad, Precio)
                                    VALUES (:IdTiempo, :IdProducto, :IdCliente, :IdCanal, :TotalVentas, :Cantidad, :Precio)
                                """),
                                {
                                    "IdTiempo": idtiempo,
                                    "IdProducto": idproducto,
                                    "IdCliente": idcliente,
                                    "IdCanal": idcanal,
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
    # Asegurar que los canales mínimos existan en DimCanal al inicio del ETL
    try:
        ensure_canales_exist(enginesql)
    except Exception as e:
        print(f"Warning: fallo al asegurar canales en DimCanal: {e}", file=sys.stderr)
    contenidosproductossql = traetablassql(enginesql, "dbo.DimProducto")
    contenidoequivalencias = traetablassql(enginesql, "dbo.Equivalencias")
    contenidoclientessql = traetablassql(enginesql, "dbo.DimCliente")
    factVentas = traetablassql(enginesql, "dbo.FactVentas")
    tablafecha = traetablassql(enginesql, "dbo.DimTiempo")
    contenidocanal = traetablassql(enginesql, "dbo.DimCanal")

    init_mapas(url, headers)

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
    try:
        transformadoryloadsupaVENTAS(enginesql, url, headers, ordenesdetalle, tablafecha, contenidoclientessql, contenidosproductossql, contenidocanal)
    except Exception as e:
        print(f"Error procesando ventas — log no actualizado: {e}", file=sys.stderr)
        raise
    else:
        #solo actualiza el log si todo el procesamiento termina sin errores
        crearlogetlventas(fecha_max)

    print("ETL COMPLETADO CON EXITO")


if __name__ == "__main__":
    run_etl()
