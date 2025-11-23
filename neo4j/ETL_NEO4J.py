import os
import json
from neo4j import GraphDatabase
import pyodbc
from datetime import datetime, date
from dotenv import load_dotenv

# Cargar .env (si existe)
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "")
DB_NAME = os.getenv("NEO4J_DATABASE", "ventas")  # base de datos a extraer
#configuracion log
LOG_PATH = os.getenv("LOG_PATH", "etl_ventas.log")
LOG_FECHA_DEFAULT = datetime(1970, 1, 1).isoformat() + "Z"

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

def crearlogetlventas(fecha):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(str(fecha) + "\n")

def extract_nodes(session, fecha=None, out_path="nodes.jsonl", batch_size=1000):
    if fecha is None:
        try:
            fecha = consultarlogetlventas()
        except Exception:
            # Fallback to epoch-like default if the log can't be read
            fecha = LOG_FECHA_DEFAULT

    # Cypher: only return nodes that have a fecha and where datetime(n.fecha) > datetime($fecha)
    query = (
        "MATCH (n) WHERE n.fecha IS NOT NULL AND datetime(n.fecha) > datetime($fecha) "
        "RETURN elementId(n) AS elementId, labels(n) AS labels, properties(n) AS props"
    )

    with open(out_path, "w", encoding="utf-8") as f:
        for record in session.run(query, fecha=fecha):
            obj = {"elementId": record["elementId"], "labels": record["labels"], "props": record["props"]}
            f.write(json.dumps(obj, default=str, ensure_ascii=False) + "\n")

def extract_rels(session, nodes_path="nodes.jsonl", out_path="relationships.jsonl"):
    # Load node elementIds
    try:
        nodes = read_jsonl(nodes_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Nodes file not found: {nodes_path}")

    ids = [n["elementId"] for n in nodes if "elementId" in n]

    if not ids:
        # No nodes extracted; create empty output and return
        with open(out_path, "w", encoding="utf-8") as f:
            return

    # Query relationships where both endpoints are in the extracted node set
    query = (
        "MATCH (a)-[r]->(b)"
        " WHERE elementId(a) IN $ids AND elementId(b) IN $ids"
        " RETURN elementId(a) AS from, elementId(b) AS to, elementId(r) AS rel, type(r) AS type, properties(r) AS props"
    )

    with open(out_path, "w", encoding="utf-8") as f:
        for record in session.run(query, ids=ids):
            obj = {
                "from": record["from"],
                "to": record["to"],
                "rel": record["rel"],
                "type": record["type"],
                "props": record["props"]
            }
            f.write(json.dumps(obj, default=str, ensure_ascii=False) + "\n")


def read_jsonl(path):
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def get_max_fecha_from_nodes(nodes_path="nodes.jsonl"):
    try:
        nodes = read_jsonl(nodes_path)
    except FileNotFoundError:
        return None

    max_dt = None
    for n in nodes:
        props = n.get("props", {}) or {}
        raw = props.get("fecha")
        if raw is None:
            continue
        s = str(raw)
        # Normalize common variants
        if s.endswith("Z"):
            s_norm = s[:-1]
        else:
            s_norm = s
        s_norm = s_norm.replace(" ", "T")

        try:
            dt = datetime.fromisoformat(s_norm)
        except Exception:
            # Try without microseconds
            try:
                dt = datetime.strptime(s_norm.split(".")[0], "%Y-%m-%dT%H:%M:%S")
            except Exception:
                continue

        if max_dt is None or dt > max_dt:
            max_dt = dt

    if max_dt:
        return max_dt.isoformat()
    return None

def connect_sqlserver():
    SQL_SERVER = os.getenv("SQL_SERVER", "localhost")
    SQL_DRIVER = os.getenv("SQL_DRIVER", "ODBC Driver 17 for SQL Server")
    SQL_DB = os.getenv("SQL_DB", "DW_VENTAS")

    conn_str = (
        f"DRIVER={{{SQL_DRIVER}}};"
        f"SERVER={SQL_SERVER};"
        f"Trusted_Connection=yes;"
        f"DATABASE={SQL_DB};"
    )
    conn = pyodbc.connect(conn_str)
    return conn

'''def create_dw_tables(conn):
    ddl_statements = [
        """
CREATE TABLE IF NOT EXISTS DimTiempo (
    IdTiempo INT IDENTITY(1,1) PRIMARY KEY,
    Anio INT NOT NULL,
    Mes INT NOT NULL,
    Dia INT NOT NULL,
    Fecha DATE NOT NULL,
    Semana INT,
    DiaSemana VARCHAR(15),
    TipoCambio DECIMAL(10,2)
);
""",
        """
CREATE TABLE IF NOT EXISTS DimCliente (
    IdCliente INT IDENTITY(1,1) PRIMARY KEY,
    Nombre VARCHAR(100) NOT NULL,
    Email VARCHAR(150),
    Genero VARCHAR(15),
    Pais VARCHAR(100),
    FechaCreacion DATE
);
""",
        """
CREATE TABLE IF NOT EXISTS DimProducto (
    IdProducto INT IDENTITY(1,1) PRIMARY KEY,
    SKU VARCHAR(50) NOT NULL,
    Nombre VARCHAR(100) NOT NULL,
    Categoria VARCHAR(100)
);
""",
        """
CREATE TABLE IF NOT EXISTS FactVentas (
    IdFactVentas INT IDENTITY(1,1) PRIMARY KEY,
    IdTiempo INT NOT NULL,
    IdProducto INT NOT NULL,
    IdCliente INT NOT NULL,
    TotalVentas DECIMAL(18,2),
    Cantidad INT,
    Precio DECIMAL(18,2),
    CONSTRAINT FK_FactVentas_Tiempo FOREIGN KEY (IdTiempo) REFERENCES DimTiempo(IdTiempo),
    CONSTRAINT FK_FactVentas_Producto FOREIGN KEY (IdProducto) REFERENCES DimProducto(IdProducto),
    CONSTRAINT FK_FactVentas_Cliente FOREIGN KEY (IdCliente) REFERENCES DimCliente(IdCliente)
);
""",
        """
CREATE TABLE IF NOT EXISTS MetaVentas (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    IdProducto INT NOT NULL,
    IdCliente INT NOT NULL,
    Anio INT NOT NULL,
    Mes INT NOT NULL,
    MetaUSD DECIMAL(18,2)
);
""",
        """
CREATE TABLE IF NOT EXISTS Equivalencias (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    SKU VARCHAR(30) NULL,
    CodigoMongo VARCHAR(30) NULL,
    CodigoAlt VARCHAR(30) NULL
);
"""
    ]
    cur = conn.cursor()
    for ddl in ddl_statements:
        try:
            cur.execute(ddl)
        except Exception:
            # Some drivers/databases don't support IF NOT EXISTS with CREATE TABLE
            # Try executing without the IF NOT EXISTS
            stmt = ddl.replace("CREATE TABLE IF NOT EXISTS", "CREATE TABLE")
            try:
                cur.execute(stmt)
            except Exception:
                # If it still fails (table exists), ignore
                pass
    conn.commit()
'''

def transform_and_load(nodes_path="nodes.jsonl", rels_path="relationships.jsonl"):
    nodes = read_jsonl(nodes_path)
    rels = read_jsonl(rels_path)

    nodes_map = {n["elementId"]: n for n in nodes}

    productos = [n for n in nodes if "Producto" in n.get("labels", [])]
    clientes = [n for n in nodes if "Cliente" in n.get("labels", [])]
    ordenes = [n for n in nodes if "Orden" in n.get("labels", [])]

    # Conectar a SQL Server y crear las tablas DW si es necesario
    conn = None
    try:
        conn = connect_sqlserver()
    except Exception as e:
        print(f"Error conectando a SQL Server: {e}")
        return

    try:
        cur = conn.cursor()

        def _get_prop(props, *keys):
            for k in keys:
                v = props.get(k)
                if v is not None:
                    return v
            return None

        def _safe_str(v, maxlen=None):
            if v is None:
                return None
            s = str(v).strip()
            if maxlen:
                return s[:maxlen]
            return s

        # Procesar productos: insertar en Equivalencias y DimProducto si no existen
        for p in productos:
            props = p.get("props", {}) or {}

            # Extraer identificadores comunes con flexibilidad en nombres de campo
            sku = _get_prop(props, "sku", "SKU", "codigo", "codigo_sku", "sku_producto")
            codigo_mongo = _get_prop(props, "codigo_mongo", "codigoMongo", "_id", "id")
            codigo_alt = _get_prop(props, "codigo_alt", "codigoAlt", "codigo_alterno", "codigoAlterno")

            nombre = _get_prop(props, "nombre", "Nombre", "name")
            categoria = _get_prop(props, "categoria", "Categoria")

            # Normalizar a cadenas y recortar a longitudes razonables (usa _safe_str arriba)

            sku_s = _safe_str(sku, 50)
            codigo_mongo_s = _safe_str(codigo_mongo, 30)
            codigo_alt_s = _safe_str(codigo_alt, 30)
            nombre_s = _safe_str(nombre, 100) or (sku_s or "")
            categoria_s = _safe_str(categoria, 100)

            # Si no hay ningún identificador, saltar
            if not (sku_s or codigo_mongo_s or codigo_alt_s):
                print(f"Saltando producto sin identificadores: {props}")
                continue

            # Verificar existencia en Equivalencias comparando SKU, CodigoMongo o CodigoAlt
            try:
                query_check = (
                    "SELECT Id FROM Equivalencias WHERE (SKU IS NOT NULL AND SKU = ?) "
                    "OR (CodigoMongo IS NOT NULL AND CodigoMongo = ?) "
                    "OR (CodigoAlt IS NOT NULL AND CodigoAlt = ?);"
                )
                cur.execute(query_check, (sku_s, codigo_mongo_s, codigo_alt_s))
                exists = cur.fetchone()
            except Exception as e:
                print(f"Error al consultar Equivalencias: {e}")
                exists = None

            if exists:
                # Ya existe una equivalencia -> no insertar
                print(f"Equivalencia encontrada, omitiendo producto SKU={sku_s} codigo_mongo={codigo_mongo_s} codigo_alt={codigo_alt_s}")
                continue

            # Insertar en Equivalencias
            try:
                cur.execute("INSERT INTO Equivalencias (SKU, CodigoMongo, CodigoAlt) VALUES (?, ?, ?)", (sku_s, codigo_mongo_s, codigo_alt_s))
                conn.commit()
                # Intentar obtener SCOPE_IDENTITY(); si no está disponible, buscar la fila insertada
                eq_id = None
                try:
                    cur.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
                    row = cur.fetchone()
                    if row and row[0] is not None:
                        eq_id = int(row[0])
                except Exception:
                    # Fallback: buscar la fila por los valores insertados (última coincidente)
                    try:
                        cur.execute(
                            "SELECT TOP 1 Id FROM Equivalencias WHERE (SKU = ? OR (SKU IS NULL AND ? IS NULL)) AND (CodigoMongo = ? OR (CodigoMongo IS NULL AND ? IS NULL)) AND (CodigoAlt = ? OR (CodigoAlt IS NULL AND ? IS NULL)) ORDER BY Id DESC",
                            (sku_s, sku_s, codigo_mongo_s, codigo_mongo_s, codigo_alt_s, codigo_alt_s)
                        )
                        row2 = cur.fetchone()
                        if row2 and row2[0] is not None:
                            eq_id = int(row2[0])
                    except Exception:
                        eq_id = None
            except Exception as e:
                conn.rollback()
                print(f"Error insertando en Equivalencias: {e}")
                continue

            # Insertar en DimProducto
            try:
                cur.execute("INSERT INTO DimProducto (SKU, Nombre, Categoria) VALUES (?, ?, ?)", (sku_s, nombre_s, categoria_s))
                conn.commit()
                prod_id = None
                try:
                    cur.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
                    rowp = cur.fetchone()
                    if rowp and rowp[0] is not None:
                        prod_id = int(rowp[0])
                except Exception:
                    try:
                        cur.execute(
                            "SELECT TOP 1 IdProducto FROM DimProducto WHERE (SKU = ? OR (SKU IS NULL AND ? IS NULL)) AND (Nombre = ? OR (Nombre IS NULL AND ? IS NULL)) AND (Categoria = ? OR (Categoria IS NULL AND ? IS NULL)) ORDER BY IdProducto DESC",
                            (sku_s, sku_s, nombre_s, nombre_s, categoria_s, categoria_s)
                        )
                        rowp2 = cur.fetchone()
                        if rowp2 and rowp2[0] is not None:
                            prod_id = int(rowp2[0])
                    except Exception:
                        prod_id = None
            except Exception as e:
                conn.rollback()
                print(f"Error insertando en DimProducto: {e}")
                # Opcional: eliminar la equivalencia recién insertada para mantener integridad
                try:
                    if 'eq_id' in locals() and eq_id:
                        cur.execute("DELETE FROM Equivalencias WHERE Id = ?", (eq_id,))
                        conn.commit()
                except Exception:
                    pass
                continue

            # Confirmar los cambios para este producto
            try:
                conn.commit()
            except Exception:
                conn.rollback()
                print(f"No se pudo confirmar transacción para producto SKU={sku_s}")

            print(f"Insertado producto IdProducto={prod_id} y EquivalenciaId={eq_id} para SKU={sku_s}")

        # Procesar clientes: insertar en DimCliente
        for c in clientes:
            props = c.get("props", {}) or {}

            nombre = _get_prop(props, "nombre", "Nombre", "name")
            email = _get_prop(props, "email", "Email", "correo", "correo_electronico")
            genero_raw = _get_prop(props, "genero", "sexo", "gender")
            pais = _get_prop(props, "pais", "Pais", "country")
            fecha_creacion_raw = _get_prop(props, "fechaCreacion", "fecha_creacion", "created_at", "fecha")

            nombre_s = _safe_str(nombre, 100) or ""
            email_s = _safe_str(email, 150)
            pais_s = _safe_str(pais, 100)

            # Estandarizar genero: M|Masculino -> M ; F|Femenino -> F ; X|Otro|Null -> X
            def _norm_genero(val):
                if val is None:
                    return "X"
                s = str(val).strip().lower()
                if s == "m" or s.startswith("masc") or s in ("masculino", "male", "hombre"):
                    return "M"
                if s == "f" or s.startswith("fem") or s in ("femenino", "female", "mujer"):
                    return "F"
                if s == "x" or s in ("otro", "other", "unknown") or s == "null" or s == "none" or s == "":
                    return "X"
                # Default: if single letter like 'm' or 'f' already handled; otherwise map unknowns to 'X'
                return "X"

            genero_s = _norm_genero(genero_raw)

            # Parsear fecha a DATE (YYYY-MM-DD)
            fecha_s = None
            if fecha_creacion_raw is not None:
                try:
                    s = str(fecha_creacion_raw)
                    if s.endswith("Z"):
                        s = s[:-1]
                    s = s.replace(" ", "T")
                    dt = None
                    try:
                        dt = datetime.fromisoformat(s)
                    except Exception:
                        try:
                            dt = datetime.strptime(s.split(".")[0], "%Y-%m-%dT%H:%M:%S")
                        except Exception:
                            try:
                                dt = datetime.strptime(s, "%Y-%m-%d")
                            except Exception:
                                dt = None
                    if dt:
                        fecha_s = dt.date()
                except Exception:
                    fecha_s = None

            # Verificar existencia por Email (si está disponible) para evitar duplicados
            if email_s:
                try:
                    cur.execute("SELECT IdCliente FROM DimCliente WHERE Email = ?", (email_s,))
                    exists = cur.fetchone()
                    if exists:
                        try:
                            existing_id = int(exists[0]) if exists[0] is not None else None
                        except Exception:
                            existing_id = None
                        print(f"Cliente con email '{email_s}' ya existe IdCliente={existing_id}; omitiendo inserción.")
                        continue
                except Exception as e:
                    # Si falla la verificación por algún motivo, loggear y continuar intentando insertar
                    print(f"Error comprobando existencia de cliente por email '{email_s}': {e}")

            # Insertar en DimCliente
            try:
                cur.execute(
                    "INSERT INTO DimCliente (Nombre, Email, Genero, Pais, FechaCreacion) VALUES (?, ?, ?, ?, ?)",
                    (nombre_s, email_s, genero_s, pais_s, fecha_s)
                )
                conn.commit()
                cliente_id = None
                try:
                    cur.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
                    rowc = cur.fetchone()
                    if rowc and rowc[0] is not None:
                        cliente_id = int(rowc[0])
                except Exception:
                    try:
                        cur.execute(
                            "SELECT TOP 1 IdCliente FROM DimCliente WHERE Nombre = ? AND (Email = ? OR (? IS NULL AND Email IS NULL)) ORDER BY IdCliente DESC",
                            (nombre_s, email_s, email_s)
                        )
                        rowc2 = cur.fetchone()
                        if rowc2 and rowc2[0] is not None:
                            cliente_id = int(rowc2[0])
                    except Exception:
                        cliente_id = None
                print(f"Insertado cliente IdCliente={cliente_id} Nombre='{nombre_s}' Genero={genero_s} País='{pais_s}' FechaCreacion={fecha_s}")
            except Exception as e:
                conn.rollback()
                print(f"Error insertando cliente Nombre={nombre_s}: {e}")

        # Procesar órdenes: agrupar por Fecha(día) + Cliente + Producto + Canal
        agrupados = {}

        def _parse_date_to_date(raw):
            if raw is None:
                return None
            s = str(raw)
            if s.endswith("Z"):
                s = s[:-1]
            s = s.replace(" ", "T")
            try:
                dt = datetime.fromisoformat(s)
                return dt.date()
            except Exception:
                try:
                    dt = datetime.strptime(s.split(".")[0], "%Y-%m-%dT%H:%M:%S")
                    return dt.date()
                except Exception:
                    try:
                        dt = datetime.strptime(s, "%Y-%m-%d")
                        return dt.date()
                    except Exception:
                        return None

        # Index rels by order elementId to speed lookup
        rels_by_order = {}
        for r in rels:
            fr = r.get("from")
            to = r.get("to")
            rels_by_order.setdefault(fr, []).append(r)
            rels_by_order.setdefault(to, []).append(r)

        for o in ordenes:
            o_props = o.get("props", {}) or {}
            order_id = o.get("elementId")

            fecha_raw = _get_prop(o_props, "fecha", "Fecha", "created_at", "date")
            fecha_date = _parse_date_to_date(fecha_raw)
            if fecha_date is None:
                # No podemos asignar tiempo; saltar esta orden
                print(f"Orden sin fecha válida, omitiendo: {o_props}")
                continue

            moneda = _get_prop(o_props, "moneda", "currency", "moneda_orden") or ""
            moneda_s = _safe_str(moneda, 10).upper() if moneda else ""

            canal = _get_prop(o_props, "canal", "channel", "origen")
            canal_s = _safe_str(canal, 100) or "(sin canal)"

            # Buscar cliente asociado por relaciones, si existe
            cliente_email = None
            for r in rels_by_order.get(order_id, []):
                # identificar el otro extremo
                other_id = None
                if r.get("from") == order_id:
                    other_id = r.get("to")
                elif r.get("to") == order_id:
                    other_id = r.get("from")
                if not other_id:
                    continue
                other = nodes_map.get(other_id)
                if not other:
                    continue
                if "Cliente" in other.get("labels", []):
                    cprops = other.get("props", {}) or {}
                    cliente_email = _get_prop(cprops, "email", "Email", "correo", "correo_electronico")
                    if cliente_email:
                        break

            if not cliente_email:
                cliente_email = _get_prop(o_props, "email", "cliente_email", "cliente_correo")

            cliente_email_s = _safe_str(cliente_email, 150)

            # Obtener TipoCambio y IdTiempo para la fecha (si no existe, asumimos 1.0 y creamos registro)
            tipo_cambio = 1.0
            id_tiempo = None
            try:
                cur.execute("SELECT IdTiempo, TipoCambio FROM DimTiempo WHERE Fecha = ?", (fecha_date,))
                rowt = cur.fetchone()
                if rowt:
                    id_tiempo = int(rowt[0]) if rowt[0] is not None else None
                    try:
                        tipo_cambio = float(rowt[1]) if rowt[1] is not None else 1.0
                    except Exception:
                        tipo_cambio = 1.0
                else:
                    # Insertar fila mínima en DimTiempo con TipoCambio=1.0
                    anio = fecha_date.year
                    mes = fecha_date.month
                    dia = fecha_date.day
                    semana = None
                    dia_sem = None
                    try:
                        cur.execute(
                            "INSERT INTO DimTiempo (Anio, Mes, Dia, Fecha, Semana, DiaSemana, TipoCambio) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (anio, mes, dia, fecha_date, semana, dia_sem, 1.0)
                        )
                        conn.commit()
                        try:
                            cur.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
                            rowid = cur.fetchone()
                            if rowid and rowid[0] is not None:
                                id_tiempo = int(rowid[0])
                        except Exception:
                            cur.execute("SELECT TOP 1 IdTiempo FROM DimTiempo WHERE Fecha = ? ORDER BY IdTiempo DESC", (fecha_date,))
                            r2 = cur.fetchone()
                            if r2 and r2[0] is not None:
                                id_tiempo = int(r2[0])
                    except Exception:
                        conn.rollback()
                        id_tiempo = None
                        tipo_cambio = 1.0
            except Exception as e:
                print(f"Error consultando/creando DimTiempo para fecha {fecha_date}: {e}")

            # Recorrer relaciones que conectan esta orden con productos
            for r in rels_by_order.get(order_id, []):
                # Determinar nodo producto en la relación
                prod_node = None
                if r.get("from") == order_id:
                    cand = nodes_map.get(r.get("to"))
                    if cand and "Producto" in cand.get("labels", []):
                        prod_node = cand
                if r.get("to") == order_id:
                    cand = nodes_map.get(r.get("from"))
                    if cand and "Producto" in cand.get("labels", []):
                        prod_node = cand
                if not prod_node:
                    continue

                item_props = r.get("props", {}) or {}

                cantidad_raw = _get_prop(item_props, "cantidad", "qty", "quantity", "cant", "units")
                precio_raw = _get_prop(item_props, "precio_unit", "price", "unit_price", "precio_unitario", "precio")

                # Si no hay precio en la relación, intentar obtener del nodo producto
                if precio_raw is None:
                    precio_raw = _get_prop(prod_node.get("props", {}) or {}, "precio", "price", "precio_unit")

                try:
                    cantidad = int(float(cantidad_raw)) if cantidad_raw is not None else 0
                except Exception:
                    try:
                        cantidad = int(cantidad_raw)
                    except Exception:
                        cantidad = 0

                try:
                    precio = float(precio_raw) if precio_raw is not None else 0.0
                except Exception:
                    precio = 0.0

                if cantidad <= 0 and precio == 0.0:
                    # nada útil en esta relación
                    continue

                # Aplicar conversión si la moneda es CRC
                converted_price = precio
                if moneda_s == "CRC" and tipo_cambio and tipo_cambio != 0:
                    converted_price = precio / tipo_cambio

                product_total = converted_price * cantidad

                # Obtener identificador de producto (SKU preferible)
                pprops = prod_node.get("props", {}) or {}
                sku = _get_prop(pprops, "sku", "SKU", "codigo", "codigo_sku") or _get_prop(pprops, "codigo_mongo", "codigoMongo", "_id") or _get_prop(pprops, "codigo_alt", "codigoAlt")
                sku_s = _safe_str(sku, 50)

                key = (fecha_date.isoformat(), sku_s or "(sin_sku)", cliente_email_s or "(sin_email)", canal_s)
                acc = agrupados.get(key)
                if not acc:
                    agrupados[key] = {"total": 0.0, "cantidad": 0, "precio_sum": 0.0, "precio_count": 0, "fecha": fecha_date, "id_tiempo": id_tiempo}
                    acc = agrupados[key]

                acc["total"] += product_total
                acc["cantidad"] += cantidad
                if converted_price is not None:
                    acc["precio_sum"] += converted_price
                    acc["precio_count"] += 1

        # Insertar agregados en FactVentas
        for key, vals in agrupados.items():
            fecha_iso, sku_val, cliente_email_val, canal_val = key
            fecha_date = vals.get("fecha")
            id_tiempo = vals.get("id_tiempo")
            total_ventas = round(vals.get("total", 0.0), 2)
            cantidad_total = int(vals.get("cantidad", 0))
            precio_prom = 0.0
            if vals.get("precio_count", 0) > 0:
                precio_prom = round(vals.get("precio_sum", 0.0) / vals.get("precio_count", 1), 2)

            # Resolver IdCliente
            id_cliente = None
            try:
                if cliente_email_val and cliente_email_val != "(sin_email)":
                    cur.execute("SELECT IdCliente FROM DimCliente WHERE Email = ?", (cliente_email_val,))
                    rcli = cur.fetchone()
                    if rcli and rcli[0] is not None:
                        id_cliente = int(rcli[0])
                if not id_cliente:
                    # crear cliente mínimo usando el email como nombre si es posible
                    nombre_min = cliente_email_val or "(sin_nombre)"
                    cur.execute("INSERT INTO DimCliente (Nombre, Email, Genero) VALUES (?, ?, ?)", (nombre_min, cliente_email_val if cliente_email_val != "(sin_email)" else None, "X"))
                    conn.commit()
                    try:
                        cur.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
                        rr = cur.fetchone()
                        if rr and rr[0] is not None:
                            id_cliente = int(rr[0])
                    except Exception:
                        cur.execute("SELECT TOP 1 IdCliente FROM DimCliente WHERE Email = ? ORDER BY IdCliente DESC", (cliente_email_val,))
                        rr2 = cur.fetchone()
                        if rr2 and rr2[0] is not None:
                            id_cliente = int(rr2[0])
            except Exception as e:
                conn.rollback()
                print(f"Error resolviendo/creando cliente para email {cliente_email_val}: {e}")
                continue

            # Resolver SKU real desde Equivalencias si fue guardado con codigo alterno
            sku_real = sku_val if sku_val and sku_val != "(sin_sku)" else None
            try:
                if sku_real:
                    cur.execute("SELECT SKU FROM Equivalencias WHERE (SKU = ? OR CodigoMongo = ? OR CodigoAlt = ?)", (sku_real, sku_real, sku_real))
                    re = cur.fetchone()
                    if re and re[0]:
                        sku_real = re[0]
            except Exception:
                pass

            # Resolver IdProducto
            id_producto = None
            try:
                if sku_real:
                    cur.execute("SELECT IdProducto FROM DimProducto WHERE SKU = ?", (sku_real,))
                    rp = cur.fetchone()
                    if rp and rp[0] is not None:
                        id_producto = int(rp[0])
                if not id_producto:
                    # crear producto mínimo
                    nombre_p = sku_real or "(sin_sku)"
                    try:
                        cur.execute("INSERT INTO DimProducto (SKU, Nombre) VALUES (?, ?)", (sku_real, nombre_p))
                        conn.commit()
                        try:
                            cur.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
                            rp2 = cur.fetchone()
                            if rp2 and rp2[0] is not None:
                                id_producto = int(rp2[0])
                        except Exception:
                            cur.execute("SELECT TOP 1 IdProducto FROM DimProducto WHERE SKU = ? ORDER BY IdProducto DESC", (sku_real,))
                            rpp = cur.fetchone()
                            if rpp and rpp[0] is not None:
                                id_producto = int(rpp[0])
                    except Exception:
                        conn.rollback()
                        id_producto = None
            except Exception as e:
                print(f"Error resolviendo/creando producto SKU={sku_real}: {e}")
                continue

            # Resolver/crear IdCanal
            id_canal = None
            try:
                cur.execute("SELECT IdCanal FROM DimCanal WHERE Nombre = ?", (canal_val,))
                rc = cur.fetchone()
                if rc and rc[0] is not None:
                    id_canal = int(rc[0])
                else:
                    cur.execute("INSERT INTO DimCanal (Nombre) VALUES (?)", (canal_val,))
                    conn.commit()
                    try:
                        cur.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
                        rcc = cur.fetchone()
                        if rcc and rcc[0] is not None:
                            id_canal = int(rcc[0])
                    except Exception:
                        cur.execute("SELECT TOP 1 IdCanal FROM DimCanal WHERE Nombre = ? ORDER BY IdCanal DESC", (canal_val,))
                        rcc2 = cur.fetchone()
                        if rcc2 and rcc2[0] is not None:
                            id_canal = int(rcc2[0])
            except Exception as e:
                conn.rollback()
                print(f"Error resolviendo/creando canal '{canal_val}': {e}")
                continue

            # Asegurar IdTiempo
            if not id_tiempo:
                try:
                    cur.execute("SELECT IdTiempo FROM DimTiempo WHERE Fecha = ?", (fecha_date,))
                    rtt = cur.fetchone()
                    if rtt and rtt[0] is not None:
                        id_tiempo = int(rtt[0])
                except Exception:
                    id_tiempo = None

            if not id_tiempo or not id_producto or not id_cliente or not id_canal:
                print(f"Faltan dimensiones para insertar FactVentas (IdTiempo={id_tiempo} IdProducto={id_producto} IdCliente={id_cliente} IdCanal={id_canal}), omitiendo fila para key={key}")
                continue

            # Insertar en FactVentas
            try:
                cur.execute(
                    "INSERT INTO FactVentas (IdTiempo, IdProducto, IdCliente, IdCanal, TotalVentas, Cantidad, Precio) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (id_tiempo, id_producto, id_cliente, id_canal, total_ventas, cantidad_total, precio_prom)
                )
                conn.commit()
                print(f"Insertada FactVentas Fecha={fecha_date} SKU={sku_real} IdProducto={id_producto} IdCliente={id_cliente} IdCanal={id_canal} Total={total_ventas} Cant={cantidad_total} Precio={precio_prom}")
            except Exception as e:
                conn.rollback()
                print(f"Error insertando FactVentas para key={key}: {e}")
    finally:
        if conn:
            conn.close()


def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    try:
        with driver.session(database=DB_NAME) as session:
            print(f"Extrayendo nodos desde DB '{DB_NAME}'...")
            # Use the last logged fecha as the lower bound for extraction
            ultima_fecha = consultarlogetlventas()

            print(f"Extrayendo nodos con fecha posterior a: {ultima_fecha}")
            extract_nodes(session, fecha=ultima_fecha, out_path="nodes.jsonl")
            print("Nodos exportados a nodes.jsonl")

            print("Extrayendo relaciones entre nodos extraídos...")
            extract_rels(session, nodes_path="nodes.jsonl", out_path="relationships.jsonl")
            print("Relaciones exportadas a relationships.jsonl")
            # Compute the most recent fecha among extracted nodes and write it to the log
            max_fecha = get_max_fecha_from_nodes(nodes_path="nodes.jsonl")
            if max_fecha:
                print(f"Actualizando log con la fecha máxima encontrada en nodos: {max_fecha}")
                crearlogetlventas(max_fecha)
            else:
                # Fallback: preserve previous last-run timestamp
                print("No se encontró fecha en los nodos extraídos; manteniendo la fecha de último log.")
    finally:
        driver.close()

    # Transformar y cargar los datos extraídos
    transform_and_load(nodes_path="nodes.jsonl", rels_path="relationships.jsonl")

if __name__ == "__main__":
    main()