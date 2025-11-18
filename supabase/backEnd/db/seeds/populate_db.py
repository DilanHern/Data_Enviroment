# Nota: instalar dependencias antes de ejecutar:
#   pip install faker requests python-dotenv

import os
import random
from decimal import Decimal
from datetime import datetime
import sys
from typing import List, Dict, Any

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


def insert_products(session, base_url, headers, fake, n) -> List[str]:
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

    rows = []
    for _ in range(n):
        sku = fake.unique.lexify(text="SKU??????").upper()
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
    resp = session.get(
        f"{base_url}/rest/v1/orden_detalle",
        headers={**headers, "Prefer": "return=representation"},
        params={"select": "orden_id,cantidad,precio_unit"},
    )
    if not resp.ok:
        print("Error leyendo orden_detalle para actualizar totales:", resp.status_code, resp.text, file=sys.stderr)
        sys.exit(1)

    detalles: List[Dict[str, Any]] = resp.json()
    totals: Dict[str, float] = {}
    for d in detalles:
        oid = d["orden_id"]
        cantidad = d["cantidad"]
        precio = float(d["precio_unit"])
        subtotal = cantidad * precio
        totals[oid] = totals.get(oid, 0.0) + subtotal

    for orden_id, total in totals.items():
        resp = session.patch(
            f"{base_url}/rest/v1/orden",
            headers=headers,
            params={"orden_id": f"eq.{orden_id}"},
            json={"total": round(total, 2)},
        )
        if not resp.ok:
            print(f"Error actualizando total para orden_id={orden_id}:", resp.status_code, resp.text, file=sys.stderr)
            sys.exit(1)


def main():
    rows = int(os.environ.get("ROWS", "420"))

    base_url, headers = get_supabase_client()
    fake = Faker("es_ES")
    Faker.seed(0)
    random.seed(0)

    session = requests.Session()

    print(f"Insertando {rows} clientes via REST...")
    client_ids = insert_clients(session, base_url, headers, fake, rows)

    print(f"Insertando {rows} productos via REST...")
    product_ids = insert_products(session, base_url, headers, fake, rows)

    print(f"Insertando {rows} órdenes via REST...")
    order_ids = insert_orders(session, base_url, headers, fake, rows, client_ids)

    print(f"Insertando {len(order_ids)} detalles de orden via REST...")
    insert_order_details(session, base_url, headers, order_ids, product_ids, fake)

    print("Actualizando totales de órdenes via REST...")
    update_order_totals(session, base_url, headers)

    print("Inserción completada (vía Supabase REST API).")


if __name__ == "__main__":
    main()
