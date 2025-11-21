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




def insert_orders(session, base_url, headers, fake, n, client_ids, product_ids, correlated_patterns=None, corr_prob=0.0) -> List[str]:
    canales = ["WEB", "APP", "PARTNER"]
    moneda = ["USD", "CRC"]

    # Pre-generar payloads y items por orden (items temporales, sin orden_id aún)
    orders_payload = []
    items_per_order = []
    max_items_per_order = 35
    available = len(product_ids)

    for _ in range(n):
        cliente_id = random.choice(client_ids)
        fecha = fake.date_time_between(start_date="-2y", end_date="now")
        canal = random.choice(canales)
        moneda_seleccionada = random.choice(moneda)

        # generar items para esta orden
        k = random.randint(1, min(max_items_per_order, available))
        productos_seleccionados = random.sample(product_ids, k)

        # Inyectar patrón correlacionado con cierta probabilidad
        # `correlated_patterns` es una lista de (antecedents_list, consequent)
        if correlated_patterns and random.random() < corr_prob:
            ants, cons = random.choice(correlated_patterns)
            # asegurar que todos los antecedentes y el consecuente estén en la orden
            ants = list(ants)
            # construir nueva selección que garantice la presencia de ants + cons
            remaining = [p for p in product_ids if p not in set(ants) and p != cons]
            random.shuffle(remaining)
            new_sel = list(ants) + [cons]
            # rellenar hasta k elementos si hace falta
            for p in remaining:
                if len(new_sel) >= k:
                    break
                new_sel.append(p)
            # si k es menor que len(new_sel) (poco probable), truncamos pero conservando la pattern
            productos_seleccionados = new_sel[:max(k, len(ants) + 1)]
        detalles = []
        total = 0.0
        for producto_id in productos_seleccionados:
            cantidad = random.randint(1, 15)
            precio = round(random.uniform(155, 1900), 2)
            subtotal = cantidad * precio
            total += subtotal
            detalles.append({
                "producto_id": producto_id,
                "cantidad": cantidad,
                "precio_unit": precio,
            })

        orders_payload.append({
            "cliente_id": cliente_id,
            "fecha": fecha.isoformat(),
            "canal": canal,
            "moneda": moneda_seleccionada,
            "total": round(total, 2),
        })
        items_per_order.append(detalles)

    # Insertar órdenes por chunks y recoger orden_ids
    order_ids: List[str] = []
    all_details_rows = []
    idx = 0
    for part_orders in chunked(orders_payload, 200):
        try:
            resp = session.post(f"{base_url}/rest/v1/orden", json=part_orders, headers=headers)
        except requests.exceptions.RequestException as e:
            print("Error de red insertando órdenes:", e, file=sys.stderr)
            sys.exit(1)

        if not resp.ok:
            print("Error insertando órdenes:", resp.status_code, resp.text, file=sys.stderr)
            sys.exit(1)

        created = resp.json()
        # crear mapping por posición: se asume que PostgREST devuelve filas en el mismo orden
        for j, row in enumerate(created):
            orden_id = row.get("orden_id")
            order_ids.append(orden_id)
            # items correspondientes para esta orden
            detalles = items_per_order[idx]
            for d in detalles:
                all_details_rows.append({
                    "orden_id": orden_id,
                    "producto_id": d["producto_id"],
                    "cantidad": d["cantidad"],
                    "precio_unit": d["precio_unit"],
                })
            idx += 1

    # Insertar todos los detalles en chunks
    for part in chunked(all_details_rows, 200):
        try:
            resp = session.post(f"{base_url}/rest/v1/orden_detalle", json=part, headers=headers)
        except requests.exceptions.RequestException as e:
            print("Error de red insertando detalles de orden:", e, file=sys.stderr)
            sys.exit(1)

        if not resp.ok:
            print("Error insertando detalles de orden:", resp.status_code, resp.text, file=sys.stderr)
            sys.exit(1)

    return order_ids


def insert_order_details(session, base_url, headers, order_ids, product_ids, fake):
    rows = []
    # Cada orden contendrá entre 1 y 20 productos distintos (si hay menos productos, tomar el máximo disponible)
    max_items_per_order = 35
    available = len(product_ids)
    for orden_id in order_ids:
        # número de ítems distintos para esta orden
        k = random.randint(1, min(max_items_per_order, available))
        # seleccionar productos únicos por orden
        productos_seleccionados = random.sample(product_ids, k)
        for producto_id in productos_seleccionados:
            cantidad = random.randint(1, 15)
            precio = round(random.uniform(155, 1900), 2)
            rows.append(
                {
                    "orden_id": orden_id,
                    "producto_id": producto_id,
                    "cantidad": cantidad,
                    "precio_unit": precio,
                }
            )

    # Insertar en lotes (chunked) para no saturar la API
    for part in chunked(rows, 200):
        resp = session.post(
            f"{base_url}/rest/v1/orden_detalle",  # tabla: public.orden_detalle
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

    # resumen compacto: cuántos detalles se recuperaron (muestra suprimida)
    print(f"Detalles recuperados: {len(detalles)} (muestra suprimida)")

    totals: Dict[str, float] = {}
    for d in detalles:
        oid = d.get("orden_id")
        try:
            cantidad = float(d.get("cantidad", 0))
        except Exception:
            cantidad = 0.0
        try:
            precio = float(d.get("precio_unit", 0))
        except Exception:
            precio = 0.0
        subtotal = cantidad * precio
        totals[oid] = totals.get(oid, 0.0) + subtotal

    order_items = list(totals.items())
    total_orders = len(order_items)
    print(f"Actualizando totales para {total_orders} órdenes...")

    success_count = 0
    for idx, (orden_id, total) in enumerate(order_items, start=1):
        payload = {"total": round(total, 2)}
        success = False
        last_resp = None
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

            last_resp = resp
            if resp.ok:
                success = True
                success_count += 1
                break
            else:
                # transient server errors -> retry
                print(f"Intento {attempt+1}: fallo actualizando orden {orden_id}: {resp.status_code} - {resp.text}", file=sys.stderr)

        if not success:
            print(f"No se pudo actualizar total para orden_id={orden_id} después de reintentos. Última respuesta: {getattr(last_resp, 'status_code', None)} {getattr(last_resp, 'text', '')}", file=sys.stderr)

        if idx % 100 == 0 or idx == total_orders:
            print(f"Progreso: {idx}/{total_orders} órdenes actualizadas (éxitos: {success_count})")

    print(f"Actualización de totales finalizada. Éxitos: {success_count}/{total_orders}")


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

    # ------------------------------
    # Configuración de patrones correlacionados
    # - CORRELATED_TRIPLETS: cuántos patrones correlacionados crear (por defecto 30)
    # - CORRELATION_PROB: probabilidad por orden de inyectar un patrón correlacionado (por defecto 0.25)
    # Para cambiar la probabilidad, establece variables de entorno antes de ejecutar, por ejemplo:
    #   $env:CORRELATED_TRIPLETS = '50'
    #   $env:CORRELATION_PROB = '0.3'
    # ------------------------------
    correlated_count = int(os.environ.get("CORRELATED_TRIPLETS", "30"))
    corr_prob = float(os.environ.get("CORRELATION_PROB", "0.25"))
    # Generaremos patrones con 2 o 3 antecedentes (p.ej. {a,b}->{c} o {a,b,c}->{d})
    correlated_patterns = []
    if len(product_ids) >= 4 and correlated_count > 0:
        for _ in range(correlated_count):
            # choose antecedent size: 2 or 3 (bias can be adjusted here)
            ant_size = random.choices([2, 3], weights=[0.6, 0.4])[0]
            ants = random.sample(product_ids, ant_size)
            # choose consequent distinct from antecedents
            remaining = [p for p in product_ids if p not in ants]
            if not remaining:
                continue
            cons = random.choice(remaining)
            correlated_patterns.append((ants, cons))
        print(f"Se generaron {len(correlated_patterns)} patrones correlacionados (prob={corr_prob}) para inyección en órdenes")
    else:
        correlated_patterns = None

    print(f"Insertando {rows} clientes via REST...")
    client_ids = insert_clients(session, base_url, headers, fake, rows)

    print(f"Insertando {rows} órdenes + detalles via REST...")
    # nota: pasar `correlated_patterns` y `corr_prob` para inyectar patrones correlacionados en las órdenes
    order_ids = insert_orders(session, base_url, headers, fake, rows, client_ids, product_ids, correlated_patterns, corr_prob)

    print("Actualizando totales de órdenes via REST...")
    update_order_totals(session, base_url, headers)

    print("Inserción completada (vía Supabase REST API).")


if __name__ == "__main__":
    main()