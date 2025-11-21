
import os
import sys
import requests
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from dotenv import load_dotenv

MIN_SUPPORT = 0.016    # soporte mínimo (40%)
MIN_CONFIDENCE = 0.03  # confianza mínima (60%)


def cargar_datos_desde_bd(database_url: str | None = None) -> tuple[pd.DataFrame, dict]:
    """Cargar datos desde Supabase REST (usando las vars en .env.local).

    En lugar de conectarse por SQLAlchemy aquí, usamos la API REST de Supabase
    (como hace el ETL) para traer `orden` y `orden_detalle` y construir el
    DataFrame transaction-item.
    """
    # Prefer the project's `.env.local` next to `supabase/backEnd/.env.local`
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    dotenv_path = os.path.join(base_dir, ".env.local")
    if os.path.isfile(dotenv_path):
        load_dotenv(dotenv_path)
    else:
        # fallback to any .env in cwd or environment
        load_dotenv()

    def get_supabase_client() -> tuple[str, dict]:
        dbg_url = os.environ.get("SUPABASE_URL")
        dbg_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        # prints de debug (siguen el patrón del ETL)
        print(f"DEBUG SUPABASE_URL={dbg_url}", file=sys.stderr)
        print(f"DEBUG SUPABASE_SERVICE_ROLE_KEY={'present' if dbg_key else 'missing'}", file=sys.stderr)

        if not dbg_url or not dbg_key:
            raise RuntimeError(
                "Faltan variables de entorno para Supabase. Revisa SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY en .env.local"
            )

        url = dbg_url.rstrip("/")
        headers = {
            "apikey": dbg_key,
            "Authorization": f"Bearer {dbg_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        return url, headers

    def traetablassupa(url: str, headers: dict, table: str) -> list[dict]:
        rows: list[dict] = []
        offset = 0
        batch_size = 1000
        try:
            while True:
                params = {"select": "*", "limit": batch_size, "offset": offset}
                resp = requests.get(f"{url}/rest/v1/{table}", headers=headers, params=params, timeout=30)
                resp.raise_for_status()
                batch = resp.json()
                if not batch:
                    break
                rows.extend(batch)
                offset += batch_size
        except Exception as e:
            print(f"Error al consultar Supabase (tabla={table}): {e}", file=sys.stderr)
            raise
        return rows

    # obtener cliente REST
    url, headers = get_supabase_client()

    # traer ordenes y detalles y unir manualmente
    ordenes = traetablassupa(url, headers, "orden")
    detalles = traetablassupa(url, headers, "orden_detalle")
    # traer productos para el mapeo id -> nombre
    productos = traetablassupa(url, headers, "producto")
    prod_map = {str(p.get("producto_id")): (p.get("nombre") or "") for p in productos}

    # indexar detalles por orden_id para unir eficientemente
    detalles_por_orden = {}
    for d in detalles:
        key = d.get("orden_id")
        if key not in detalles_por_orden:
            detalles_por_orden[key] = []
        detalles_por_orden[key].append(d)

    filas = []
    for o in ordenes:
        orden_id = o.get("orden_id")
        if orden_id is None:
            continue
        for det in detalles_por_orden.get(orden_id, []):
            producto_id = det.get("producto_id")
            if producto_id is None:
                continue
            filas.append({"transaction_id": str(orden_id), "item": str(producto_id)})

    df = pd.DataFrame(filas)
    return df, prod_map

def transformar_a_one_hot(df):
    # Crear una tabla transacción x item
    basket = (
        df
        .groupby(['transaction_id', 'item'])['item']
        .count()
        .unstack()
        .fillna(0)
    )
    # Convertimos a 1/0
    #basket = basket.applymap(lambda x: 1 if x > 0 else 0)
    basket = basket.astype(bool)
    return basket


def resumen_por_consecuente(df_expanded: pd.DataFrame) -> pd.DataFrame:
    """Agrupa las reglas por consecuente y muestra un resumen que detecta
    cuando un mismo consecuente tiene múltiples antecedentes.

    Devuelve el DataFrame agrupado (vacío si ocurre algún error o no hay datos).
    """
    if df_expanded is None or df_expanded.empty:
        print("No hay reglas para agrupar por consecuente.")
        return pd.DataFrame()

    try:
        grouped = (
            df_expanded
            .groupby(['consequent_id', 'consecuente_name'])
            .agg({
                'antecedent_id': lambda ids: ', '.join(sorted(set(ids))),
                'antecedent_name': lambda names: ', '.join(sorted(set(names))),
                'rule_group': lambda r: ', '.join(sorted(set(r))),
                'support': 'mean',
                'confidence': 'mean',
                'lift': 'mean',
            })
            .reset_index()
        )

        # contar cuantos antecedentes únicos tiene cada consecuente
        grouped['antecedent_count'] = grouped['antecedent_name'].apply(
            lambda s: 0 if pd.isna(s) or s == '' else len(s.split(', '))
        )
        grouped['multiple_antecedents'] = grouped['antecedent_count'] > 1

        # ordenar para mostrar primero los consecuentes con múltiples antecedentes
        grouped = grouped.sort_values(['multiple_antecedents', 'antecedent_count'], ascending=[False, False])

        print('\n--- Resumen por consecuente (antecedentes agrupados) ---')
        # columnas para mostrar: consecuente, lista de antecedentes, cantidad, reglas asociadas, confianza y lift
        out_cols = ['consecuente_name', 'antecedent_name', 'antecedent_count', 'rule_group', 'confidence', 'lift', 'multiple_antecedents']
        out_cols = [c for c in out_cols if c in grouped.columns]
        print(grouped[out_cols])

        return grouped
    except Exception as e:
        print(f"Error al agrupar reglas por consecuente: {e}")
        return pd.DataFrame()

def main():
    print("=== Cargando datos desde la base de datos ===")
    try:
        df, prod_map = cargar_datos_desde_bd()
    except Exception as e:
        print(f"Error cargando datos desde BD: {e}")
        return
    # Mostrar df con nombres en lugar de IDs para lectura, pero mantener ids internamente
    df_display = df.copy()
    df_display["item"] = df_display["item"].map(lambda i: prod_map.get(str(i), i))
    print(df_display.head())

    print("\n=== Transformación a formato one-hot ===")
    basket = transformar_a_one_hot(df)
    # Para visualizar, mostramos una versión con nombres en las columnas
    try:
        basket_display = basket.copy()
        # renombrar columnas por nombre (mantener mapeo id->name)
        rename_map = {col: prod_map.get(str(col), col) for col in basket.columns}
        basket_display = basket_display.rename(columns=rename_map)
        print(basket_display)
    except Exception:
        # si algo falla en display, caemos al print por defecto
        print(basket)

    print("\n=== Fase 1: Conjuntos frecuentes (Apriori con mlxtend) ===")
    frequent_itemsets = apriori(
        basket,
        min_support=MIN_SUPPORT,
        use_colnames=True
    )
    # Agregar columna con el tamaño del itemset para ordenar un poco
    frequent_itemsets['length'] = frequent_itemsets['itemsets'].apply(len)
    # Crear una versión para mostrar con nombres en lugar de IDs
    try:
        frequent_itemsets_display = frequent_itemsets.copy()
        frequent_itemsets_display['itemsets_names'] = frequent_itemsets_display['itemsets'].apply(
            lambda s: ', '.join(sorted([prod_map.get(str(x), str(x)) for x in s]))
        )
        print(frequent_itemsets_display[['itemsets_names', 'support', 'length']])
    except Exception:
        print(frequent_itemsets)

    print("\n=== Fase 2: Reglas de asociación ===")
    if frequent_itemsets.empty:
        print("No hay conjuntos frecuentes con el soporte especificado; ajusta MIN_SUPPORT o revisa los datos.")
        return

    rules = association_rules(
        frequent_itemsets,
        metric="confidence",
        min_threshold=MIN_CONFIDENCE
    )

    # Seleccionamos solo algunas columnas para mostrar, mapeando IDs a nombres
    if not rules.empty:
        rules_display = rules.copy()
        rules_display['antecedents_names'] = rules_display['antecedents'].apply(
            lambda s: ', '.join(sorted([prod_map.get(str(x), str(x)) for x in s]))
        )
        rules_display['consequents_names'] = rules_display['consequents'].apply(
            lambda s: ', '.join(sorted([prod_map.get(str(x), str(x)) for x in s]))
        )

        # Expand each rule into atomic rows: one row per (antecedent, consequent)
        expanded = []
        for i, r in enumerate(rules_display.itertuples(index=False), start=1):
            antecedents = list(getattr(r, 'antecedents'))
            consequents = list(getattr(r, 'consequents'))
            support = getattr(r, 'support')
            confidence = getattr(r, 'confidence')
            lift = getattr(r, 'lift')

            for a in antecedents:
                for c in consequents:
                    expanded.append({
                        'rule_group': f'R{i}',
                        'antecedent_id': str(a),
                        'antecedent_name': prod_map.get(str(a), str(a)),
                        'consequent_id': str(c),
                        'consequent_name': prod_map.get(str(c), str(c)),
                        'support': support,
                        'confidence': confidence,
                        'lift': lift,
                    })

        df_expanded = pd.DataFrame(expanded)
        # añadir columna combinada para mostrar antecedente -> consecuente
        if not df_expanded.empty:
            df_expanded['pair'] = df_expanded['antecedent_name'].astype(str) + ' -> ' + df_expanded['consequent_name'].astype(str)
            # renombrar columna del consecuente a español para la salida solicitada
            df_expanded = df_expanded.rename(columns={'consequent_name': 'consecuente_name'})
        if df_expanded.empty:
            print("No se encontraron reglas que expandir.")
        else:
            # imprimir con columnas legibles en el formato solicitado
            cols = ['rule_group', 'antecedent_name', 'consecuente_name', 'support', 'confidence', 'lift']
            # asegurar que todas las columnas existan
            cols = [c for c in cols if c in df_expanded.columns]
            print(df_expanded[cols])
            # llamar a la función que agrupa por consecuente y muestra el resumen
            resumen_por_consecuente(df_expanded)
    else:
        print("No se encontraron reglas con los parámetros especificados.")

if __name__ == "__main__":
    main()
