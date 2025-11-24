import os
import sys
import requests
from dotenv import load_dotenv
from typing import Dict, List


def get_supabase_headers():
    dbg_url = os.environ.get('SUPABASE_URL')
    dbg_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_ANON_KEY')
    # debug prints to stderr (same pattern as apriori.py)
    print(f"DEBUG SUPABASE_URL={dbg_url}", file=sys.stderr)
    print(f"DEBUG SUPABASE_SERVICE_ROLE_KEY={'present' if dbg_key else 'missing'}", file=sys.stderr)

    if not dbg_url or not dbg_key:
        raise RuntimeError('Faltan SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY/SUPABASE_ANON_KEY en el entorno')

    headers = {
        'apikey': dbg_key,
        'Authorization': f'Bearer {dbg_key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    return dbg_url.rstrip('/'), headers


def fetch_all(url: str, headers: Dict, table: str) -> List[Dict]:
    session = requests.Session()
    rows = []
    limit = 1000
    offset = 0
    while True:
        params = {'select': '*', 'limit': limit, 'offset': offset}
        resp = session.get(f"{url}/rest/v1/{table}", headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        rows.extend(batch)
        offset += limit
    return rows


def build_products_map(products_rows: List[Dict]):
    prodmap = {}
    for p in products_rows:
        pid = p.get('producto_id')
        sku = p.get('sku') if 'sku' in p else p.get('codigo') if 'codigo' in p else None
        name = p.get('nombre') or p.get('productname') or p.get('descripcion')
        prodmap[str(pid)] = {'sku': sku or str(pid), 'productname': name or ''}
    return prodmap


def main():
    out_path = os.path.join(os.path.dirname(__file__), 'reglas_revision.txt')
    # Load .env.local like apriori.py: prefer project-level .env.local two levels up
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    dotenv_path = os.path.join(base_dir, '.env.local')
    if os.path.isfile(dotenv_path):
        load_dotenv(dotenv_path)
    else:
        load_dotenv()

    url, headers = get_supabase_headers()

    # fetch all tables we need
    print('Recuperando tablas desde Supabase...', file=sys.stderr)
    products = fetch_all(url, headers, 'producto')
    assoc_rules = fetch_all(url, headers, 'association_rule')
    ants = fetch_all(url, headers, 'rule_antecedente')
    cons = fetch_all(url, headers, 'rule_consecuente')

    # Keep only active rules (soft-deleted rules have active=False)
    orig_count = len(assoc_rules)
    assoc_rules = [ar for ar in assoc_rules if ar.get('active') is True]
    print(f'Filtradas reglas: de {orig_count} totales a {len(assoc_rules)} activas', file=sys.stderr)

    prodmap = build_products_map(products)

    # group antecedents/cons by rule_id
    ants_by_rule = {}
    for a in ants:
        rid = str(a.get('rule_id'))
        pid = a.get('producto_id')
        ants_by_rule.setdefault(rid, []).append(pid)

    cons_by_rule = {}
    for c in cons:
        rid = str(c.get('rule_id'))
        pid = c.get('producto_id')
        cons_by_rule.setdefault(rid, []).append(pid)

    lines = []
    for ar in assoc_rules:
        rid = str(ar.get('rule_id'))
        antecedent_ids = ants_by_rule.get(rid, [])
        consequent_ids = cons_by_rule.get(rid, [])

        # build antecedent strings
        ant_parts = []
        for pid in antecedent_ids:
            p = prodmap.get(str(pid)) or {'sku': str(pid), 'productname': ''}
            ant_parts.append(f"{{sku: {p['sku']}, productname: {p['productname']}}}")

        # build consequent: if multiple, join with comma
        cons_parts = []
        for pid in consequent_ids:
            p = prodmap.get(str(pid)) or {'sku': str(pid), 'productname': ''}
            cons_parts.append(f"{{sku: {p['sku']}, productname: {p['productname']}}}")

        antecedentes_str = ', '.join(ant_parts) if ant_parts else '{}'
        consecuente_str = cons_parts[0] if cons_parts else '{}'

        # mark active state if present
        active_flag = ar.get('active')
        active_note = '' if active_flag is None else f" [active={active_flag}]"

        line = f"{{antecedentes: {antecedentes_str}}} -> {{consecuente: {consecuente_str}}}{active_note}"
        lines.append(line)

    # write to file
    with open(out_path, 'w', encoding='utf-8') as f:
        for l in lines:
            f.write(l + '\n')

    print(f'Escrito {len(lines)} reglas en {out_path}', file=sys.stderr)


if __name__ == '__main__':
    main()
