# Nota: instalar dependencias antes de ejecutar:
#   pip install faker requests python-dotenv

import os
import random
import string
from decimal import Decimal
from datetime import datetime
import sys
from typing import List, Dict, Any
import json
from dotenv import load_dotenv
import requests
from faker import Faker


# Cargar .env.local manualmente (sube dos niveles: seeds -> db -> backEnd)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
dotenv_path = os.path.join(BASE_DIR, ".env.local")
if os.path.isfile(dotenv_path):
    load_dotenv(dotenv_path)
else:
    # fallback: intentar .env.local en cwd
    load_dotenv()


def chunked(iterable, size):
    for i in range(0, len(iterable), size):
        yield iterable[i:i+size]

def get_supabase_client():
    # Debug opcional: mostrar qué ve el script (enmascarando la key)
    dbg_url = os.environ.get("SUPABASE_URL")
    dbg_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    print(f"DEBUG SUPABASE_URL={dbg_url}", file=sys.stderr)
    print(f"DEBUG SUPABASE_SERVICE_ROLE_KEY={'present' if dbg_key else 'missing'}", file=sys.stderr)

    url = dbg_url
    service_key = dbg_key

    if not url or not service_key:
        print(
            "Faltan variables de entorno para Supabase.\n"
            "Revisa que en .env.local tengas (en la carpeta backEnd):\n"
            "  SUPABASE_URL=https://<project>.supabase.co\n"
            "  SUPABASE_SERVICE_ROLE_KEY=<service_role_key>\n"
            f"Ruta buscada para .env.local: {dotenv_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    url = url.rstrip("/")
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",  # para que devuelva filas insertadas
    }
    return url, headers


def insert_clients(session, base_url, headers, fake, n) -> List[str]:
    rows = []
    genders = ["M", "F"]  # según constraint en creationScript.sql

    for _ in range(n):
        nombre = fake.name()
        email = fake.unique.email()
        genero = random.choice(genders)
        pais = fake.country()
        fecha = fake.date_between(start_date="-3y", end_date="today")
        rows.append(
            {
                # columnas reales en public.cliente (creationScript.sql)
                "nombre": nombre,
                "email": email,
                "genero": genero,
                "pais": pais,
                "fecha_registro": fecha.isoformat(),
            }
        )

    client_ids: List[str] = []
    for part in chunked(rows, 200):
        resp = session.post(
            f"{base_url}/rest/v1/cliente",  # tabla: public.cliente
            json=part,
            headers=headers,
        )
        if not resp.ok:
            print("Error insertando clientes:", resp.status_code, resp.text, file=sys.stderr)
            sys.exit(1)
        data = resp.json()
        # PK real: cliente_id (UUID)
        client_ids.extend(row["cliente_id"] for row in data)

    return client_ids


def insert_products(session, base_url, headers, fake, n, common_rows=None) -> List[str]:
    # If `common_rows` (from DatosComunes.json) is provided, use those rows
    # (mapping tolerant to key name variations). Otherwise generate products.
    rows = []
    # If common rows provided, insert ALL of them first (they are additional)
    if common_rows:
        for r in common_rows:
            rows.append(
                {
                    "sku": r.get("SKU") or r.get("sku"),
                    "nombre": r.get("Nombre") or r.get("nombre"),
                    "categoria": r.get("Categoria") or r.get("categoria"),
                }
            )

    # Always generate `n` additional products (so total = len(common_rows) + n)
    if n > 0:
        categories = [
            "Electrónica",
            "Ropa",
            "Hogar",
            "Juguetes",
            "Belleza",
            "Deportes",
            "Alimentos",
            "Accesorios",
        ]

        product_types = [
            "Auriculares",
            "Teléfono",
            "Portátil",
            "Cámara",
            "Monitor",
            "Camiseta",
            "Pantalones",
            "Chaqueta",
            "Zapatillas",
            "Vestido",
            "Sofá",
            "Mesa",
            "Silla",
            "Lámpara",
            "Alfombra",
            "Muñeco",
            "Puzzle",
            "Juego de mesa",
            "Pelota",
            "Lego",
            "Crema",
            "Perfume",
            "Champú",
            "Maquillaje",
            "Loción",
            "Raqueta",
            "Bicicleta",
            "Pesas",
            "Balón",
            "Mochila deportiva",
            "Galletas",
            "Cereal",
            "Chocolate",
            "Snack",
            "Café",
            "Reloj",
            "Gafas",
            "Bolso",
            "Cinturón",
            "Cartera",
        ]

        adjectives = [
            "Premium",
            "Clásico",
            "Moderno",
            "Compacto",
            "Ergonómico",
            "Ligero",
            "De lujo",
            "Económico",
            "Profesional",
            "Portátil",
        ]

        for _ in range(n):
            sku = f"PRD-{random.randint(1000,9999)}-{''.join(random.choices(string.ascii_uppercase, k=2))}"
            tipo = random.choice(product_types)
            adjetivo = random.choice(adjectives)
            nombre = f"{tipo} {adjetivo}"
            categoria = random.choice(categories)
            rows.append(
                {
                    "sku": sku,
                    "nombre": nombre,
                    "categoria": categoria,
                }
            )

    product_ids: List[str] = []
    for part in chunked(rows, 200):
        resp = session.post(
            f"{base_url}/rest/v1/producto",  # tabla: public.producto
            json=part,
            headers=headers,
        )
        if not resp.ok:
            print("Error insertando productos:", resp.status_code, resp.text, file=sys.stderr)
            sys.exit(1)
        data = resp.json()
        product_ids.extend(row["producto_id"] for row in data)

    return product_ids


def load_common_products(paths):
    """
    Buscar y cargar `equivalencias.json` (o un JSON con formato similar)
    desde una lista de rutas candidatas.
    Devuelve lista de filas (cada fila es dict con claves como en JSON) o None.
    """
    for p in paths:
        if os.path.isfile(p):
            try:
                with open(p, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                # Soporte para dos formatos comunes:
                # - El formato antiguo `DatosComunes.json` con una clave "rows": { "rows": [ ... ] }
                # - El formato de `equivalencias.json` que es una lista top-level: [ {...}, ... ]
                if isinstance(data, dict) and "rows" in data:
                    return data.get("rows", []), p
                if isinstance(data, list):
                    return data, p
                # Otros formatos: intentar devolver una lista si tiene elementos candidatos
                # Buscar claves comunes por si acaso
                if isinstance(data, dict):
                    # intentar devolver cualquier valor que sea lista
                    for v in data.values():
                        if isinstance(v, list):
                            return v, p
                # Si no se reconoce el formato, fallará al siguiente candidato
            except Exception as e:
                print(f"Error leyendo {p}: {e}", file=sys.stderr)
    return None, None




def insert_orders(session, base_url, headers, fake, n, client_ids) -> List[str]:
    canales = ["WEB", "APP", "PARTNER"]  # según CHECK en creationScript.sql
    rows = []
    for _ in range(n):
        cliente_id = random.choice(client_ids)
        fecha = fake.date_time_between(start_date="-2y", end_date="now")
        canal = random.choice(canales)
        total = Decimal("0.00")
        rows.append(
            {
                "cliente_id": cliente_id,
                "fecha": fecha.isoformat(),
                "canal": canal,
                "moneda": "USD",
                "total": float(total),
            }
        )

    order_ids: List[str] = []
    for part in chunked(rows, 200):
        resp = session.post(
            f"{base_url}/rest/v1/orden",  # tabla: public.orden
            json=part,
            headers=headers,
        )
        if not resp.ok:
            print("Error insertando órdenes:", resp.status_code, resp.text, file=sys.stderr)
            sys.exit(1)
        data = resp.json()
        order_ids.extend(row["orden_id"] for row in data)

    return order_ids


def insert_order_details(session, base_url, headers, order_ids, product_ids, fake):
    rows = []
    for orden_id in order_ids:
        producto_id = random.choice(product_ids)
        cantidad = random.randint(1, 10)
        precio = round(random.uniform(5, 500), 2)
        rows.append(
            {
                "orden_id": orden_id,
                "producto_id": producto_id,
                "cantidad": cantidad,
                "precio_unit": precio,
            }
        )

    for part in chunked(rows, 200):
        resp = session.post(
            f"{base_url}/rest/v1/orden_detalle",  # tabla: public.ordendetalle
            json=part,
            headers=headers,
        )
        if not resp.ok:
            print("Error insertando detalles de orden:", resp.status_code, resp.text, file=sys.stderr)
            sys.exit(1)


def update_order_totals(session, base_url, headers):
    try:
        resp = session.get(
            f"{base_url}/rest/v1/orden_detalle",
            headers={**headers, "Prefer": "return=representation"},
            params={"select": "orden_id,cantidad,precio_unit"},
            timeout=30,
        )
    except requests.exceptions.RequestException as e:
        print("Error de red al leer orden_detalle:", e, file=sys.stderr)
        return

    if not resp.ok:
        print("Error leyendo orden_detalle para actualizar totales:", resp.status_code, resp.text, file=sys.stderr)
        return

    detalles: List[Dict[str, Any]] = resp.json()
    if not detalles:
        print("No hay detalles de orden para procesar.")
        return

    totals: Dict[str, float] = {}
    for d in detalles:
        oid = d.get("orden_id")
        cantidad = d.get("cantidad", 0)
        precio = float(d.get("precio_unit", 0))
        subtotal = cantidad * precio
        totals[oid] = totals.get(oid, 0.0) + subtotal


    order_items = list(totals.items())
    total_orders = len(order_items)
    print(f"Actualizando totales para {total_orders} órdenes...")

    for idx, (orden_id, total) in enumerate(order_items, start=1):
        payload = {"total": round(total, 2)}
        success = False
        for attempt in range(3):
            try:
                resp = session.patch(
                    f"{base_url}/rest/v1/orden",
                    headers=headers,
                    params={"orden_id": f"eq.{orden_id}"},
                    json=payload,
                    timeout=15,
                )
            except requests.exceptions.RequestException as e:
                print(f"Intento {attempt+1}: error de red actualizando orden {orden_id}: {e}", file=sys.stderr)
                continue

            if resp.ok:
                success = True
                break
            else:
                # transient server errors -> retry
                print(f"Intento {attempt+1}: fallo actualizando orden {orden_id}: {resp.status_code}", file=sys.stderr)

        if not success:
            print(f"No se pudo actualizar total para orden_id={orden_id} después de reintentos.", file=sys.stderr)

        if idx % 100 == 0 or idx == total_orders:
            print(f"Progreso: {idx}/{total_orders} órdenes actualizadas")


def main():
    rows = int(os.environ.get("ROWS", "420"))

    base_url, headers = get_supabase_client()
    fake = Faker("es_ES")
    Faker.seed(0)
    random.seed(0)

    session = requests.Session()

    candidates = [
        # posibles ubicaciones relativas para `equivalencias.json` desde `backEnd` (BASE_DIR)
        os.path.join(BASE_DIR, "..", "equivalencias.json"),
        os.path.join(BASE_DIR, "..", "..", "equivalencias.json"),
        os.path.join(BASE_DIR, "equivalencias.json"),
        os.path.join(os.getcwd(), "equivalencias.json"),
    ]
    common_rows, common_path = load_common_products(candidates)

    if common_rows:
        print(f"Insertando {len(common_rows)} productos comunes + {rows} generados productos totales via REST...")
    else:
        print(f"Insertando {rows} productos generados via REST...")

    product_ids = insert_products(session, base_url, headers, fake, rows, common_rows)

    print(f"Insertando {rows} clientes via REST...")
    client_ids = insert_clients(session, base_url, headers, fake, rows)

    print(f"Insertando {rows} órdenes via REST...")
    order_ids = insert_orders(session, base_url, headers, fake, rows, client_ids)

    print(f"Insertando {len(order_ids)} detalles de orden via REST...")
    insert_order_details(session, base_url, headers, order_ids, product_ids, fake)

    print("Actualizando totales de órdenes via REST...")
    update_order_totals(session, base_url, headers)

    print("Inserción completada (vía Supabase REST API).")


if __name__ == "__main__":
    main()