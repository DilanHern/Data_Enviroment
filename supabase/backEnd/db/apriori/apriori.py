
import os
import sys
import requests
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from dotenv import load_dotenv
from insertapriori import guardarReglas

MIN_SUPPORT = 0.1    # soporte mínimo (40%)
MIN_CONFIDENCE = 0.3  # confianza mínima (60%)


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
    # map producto_id -> dict with nombre and sku for richer display
    prod_map = {
        str(p.get("producto_id")): {
            "nombre": (p.get("nombre") or ""),
            "sku": (p.get("sku") or "")
        }
        for p in productos
    }

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

        # Para evitar que pandas trunque los nombres de producto o las listas,
        # temporalmente ajustamos las opciones de display para imprimir toda la columna.
        pd_opts = {
            'display.max_colwidth': pd.get_option('display.max_colwidth'),
            'display.width': pd.get_option('display.width'),
            'display.max_rows': pd.get_option('display.max_rows'),
            'display.max_columns': pd.get_option('display.max_columns')
        }
        try:
            # None hace que pandas no trunque el contenido de la columna
            pd.set_option('display.max_colwidth', None)
            pd.set_option('display.width', 160)
            pd.set_option('display.max_rows', 200)
            pd.set_option('display.max_columns', 50)

            # ordenar por nombre de consecuente para lectura y quitar índice en la impresión
            display_df = grouped[out_cols].sort_values(by=['consecuente_name'])
            print(display_df.to_string(index=False))
        finally:
            # restaurar opciones originales
            pd.set_option('display.max_colwidth', pd_opts['display.max_colwidth'])
            pd.set_option('display.width', pd_opts['display.width'])
            pd.set_option('display.max_rows', pd_opts['display.max_rows'])
            pd.set_option('display.max_columns', pd_opts['display.max_columns'])

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
    # helper to format product display as "SKU - Nombre" when sku present
    def fmt_prod(id_or_entry):
        # Accept either an id or an already-resolved dict
        if isinstance(id_or_entry, dict):
            entry = id_or_entry
        else:
            entry = prod_map.get(str(id_or_entry))
        if not entry:
            return str(id_or_entry)
        sku = entry.get('sku') or ''
        nombre = entry.get('nombre') or ''
        return f"{sku} - {nombre}" if sku else nombre

    # Mostrar df con nombres (y SKUs) en lugar de IDs para lectura, mantener ids internamente
    df_display = df.copy()
    df_display["item"] = df_display["item"].map(lambda i: fmt_prod(i))
    print(df_display.head())

    print("\n=== Transformación a formato one-hot ===")
    basket = transformar_a_one_hot(df)
    # Para visualizar, mostramos una versión con nombres en las columnas
    try:
        basket_display = basket.copy()
        # renombrar columnas por nombre (SKU - Nombre cuando exista sku)
        rename_map = {col: fmt_prod(col) for col in basket.columns}
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
            lambda s: ', '.join(sorted([fmt_prod(x) for x in s]))
        )
        rules_display['consequents_names'] = rules_display['consequents'].apply(
            lambda s: ', '.join(sorted([fmt_prod(x) for x in s]))
        )

        # Deduplicate rules by exact sets of antecedents and consequents.
        # Keep the rule with highest confidence (then support, then lift) when duplicates occur.
        # Keep the last-calculated rule for each exact (antecedents, consequents) pair.
        # Iterating through `rules` in order, we simply overwrite any previous entry
        # so the final stored value corresponds to the latest computed rule.
        unique_rules = {}
        for r in rules.itertuples(index=False):
            ants = frozenset(getattr(r, 'antecedents'))
            cons = frozenset(getattr(r, 'consequents'))
            key = (ants, cons)
            # Overwrite so the last encountered rule wins (per user request)
            unique_rules[key] = {
                'antecedents': ants,
                'consequents': cons,
                'support': getattr(r, 'support'),
                'confidence': getattr(r, 'confidence'),
                'lift': getattr(r, 'lift')
            }

        # Now expand each unique rule into atomic rows (one antecedent -> one consequent)
        expanded = []
        rule_idx = 0
        for (ants, cons), info in unique_rules.items():
            rule_idx += 1
            rule_group = f'R{rule_idx}'
            pair_index = 0
            for a in sorted(ants):
                for c in sorted(cons):
                    pair_index += 1
                    expanded.append({
                        'rule_group': rule_group,
                        'rule_id': f'{rule_group}_{pair_index}',
                        'antecedent_id': str(a),
                        'antecedent_name': fmt_prod(a),
                        'consequent_id': str(c),
                        'consequent_name': fmt_prod(c),
                        'support': info['support'],
                        'confidence': info['confidence'],
                        'lift': info['lift'],
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
            # Imprimir reglas en un formato compacto y legible por itemset
            # Formato solicitado: itemset: reglas: {{antecedente: sku, nombre},{consecuente: sku, nombre}}
            try:
                for rg, grp in df_expanded.groupby('rule_group'):
                    # obtener antecedentes únicos (id + nombre tal como fue formateado)
                    ants_df = grp[['antecedent_id', 'antecedent_name']].drop_duplicates()
                    # obtener consecuentes únicos (nota: la columna de id se llama 'consequent_id')
                    cons_df = grp[['consequent_id', 'consecuente_name']].drop_duplicates()

                    ants_strs = []
                    for _, r in ants_df.iterrows():
                        pid = r['antecedent_id']
                        entry = prod_map.get(str(pid), {})
                        sku = entry.get('sku') or ''
                        nombre = entry.get('nombre') or r.get('antecedent_name') or str(pid)
                        ants_strs.append(f"{{antecedente: sku='{sku}', nombre='{nombre}'}}")

                    cons_strs = []
                    for _, r in cons_df.iterrows():
                        pid = r['consequent_id']
                        entry = prod_map.get(str(pid), {})
                        sku = entry.get('sku') or ''
                        nombre = entry.get('nombre') or r.get('consecuente_name') or str(pid)
                        cons_strs.append(f"{{consecuente: sku='{sku}', nombre='{nombre}'}}")

                    all_parts = ants_strs + cons_strs
                    print(f"itemset: {rg} reglas: {{" + ", ".join(all_parts) + "}}")
            except Exception as e:
                print(f"Error formateando reglas para impresión: {e}")

            # llamar a la función que agrupa por consecuente y muestra el resumen
            resumen_por_consecuente(df_expanded)
        guardarReglas(df_expanded.to_dict(orient='records'))
    else:
        print("No se encontraron reglas con los parámetros especificados.")

if __name__ == "__main__":
    main()
