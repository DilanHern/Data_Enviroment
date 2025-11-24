import os
import sys
import requests
import pandas as pd
import requests
import sys
from mlxtend.frequent_patterns import apriori, association_rules
from dotenv import load_dotenv
from collections import defaultdict
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta


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

def insertaReglasSupabase(reglas, url, headers, itemset, itemset_item, association_rule, antecedentes, consecuentes):
    try:
        # Agrupar por rule_group (p.ej. R1)
        from collections import defaultdict

        grupos = defaultdict(list)
        for r in reglas:
            grupos[r.get('rule_group')].append(r)

        # Construir índices a partir de los datos existentes
        # Normalizar IDs a str para comparaciones seguras
        # itemset_items_map: itemset_id -> set(producto_id)
        itemset_items_map = defaultdict(set)
        for ii in itemset_item or []:
            iid = ii.get('itemset_id')
            pid = ii.get('producto_id')
            if iid is None or pid is None:
                continue
            itemset_items_map[str(iid)].add(str(pid))

        # association rules existentes por itemset (solo activas)
        assoc_by_itemset = defaultdict(list)
        for ar in association_rule or []:
            # Si la columna 'active' existe y es False, ignorar (soft-deleted)
            if 'active' in ar and not ar.get('active'):
                continue
            assoc_by_itemset[ar.get('itemset_id')].append(ar)

        # antecedentes_map: rule_id -> set(producto_id) (todos como str)
        antecedentes_map = defaultdict(set)
        for a in antecedentes or []:
            rid = a.get('rule_id')
            pid = a.get('producto_id')
            if rid is None or pid is None:
                continue
            antecedentes_map[str(rid)].add(str(pid))

        consecuentes_map = defaultdict(set)
        for c in consecuentes or []:
            rid = c.get('rule_id')
            pid = c.get('producto_id')
            if rid is None or pid is None:
                continue
            consecuentes_map[str(rid)].add(str(pid))

        session = requests.Session()
        # nos aseguramos de pedir representación al insertar
        hdrs = {**headers, 'Prefer': 'return=representation'}

        # --- Pre-clean: desactivar reglas existentes que NO aparecen en el nuevo conjunto ---
        try:
            # construir fingerprints de las reglas nuevas (antecedents, consequents)
            new_fps = set()
            for rows in grupos.values():
                ants = {r.get('antecedent_id') for r in rows if r.get('antecedent_id')}
                cons = {r.get('consequent_id') or r.get('consequent_id') for r in rows if r.get('consequent_id')}
                new_fps.add((frozenset(ants), frozenset(cons)))

            # Para cada regla activa existente, si su fingerprint NO está en new_fps -> desactivar
            for ar in (association_rule or []):
                # ignorar ya desactivadas
                if 'active' in ar and not ar.get('active'):
                    continue
                rid = ar.get('rule_id')
                existing_ants = antecedentes_map.get(rid, set())
                existing_cons = consecuentes_map.get(rid, set())
                fp = (frozenset(existing_ants), frozenset(existing_cons))
                if fp not in new_fps:
                    try:
                        patch_url = f"{url}/rest/v1/association_rule?rule_id=eq.{rid}"
                        # use timezone-aware UTC timestamp
                        ts_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
                        patch_payload = {
                            "active": False,
                            "deleted_at": ts_utc
                        }
                        resp = session.patch(patch_url, json=patch_payload, headers=hdrs, timeout=30)
                        resp.raise_for_status()
                        print(f"Regla existente {rid} no presente en nuevo run -> marcada inactive (soft-delete)")
                    except Exception as e:
                        print(f"Advertencia: no se pudo desactivar regla existente {rid}: {e}", file=sys.stderr)
        except Exception as e:
            # si falla la limpieza previa, no abortamos el proceso; lo notificamos
            print(f"Advertencia: fallo durante pre-clean de reglas existentes: {e}", file=sys.stderr)

        for group, rows in grupos.items():
            # Reconstruir conjuntos de antecedentes y consecuentes completos
            antecedents = {r.get('antecedent_id') for r in rows if r.get('antecedent_id')}
            consequents = {r.get('consequent_id') or r.get('consequent_id') for r in rows if r.get('consequent_id')}

            # Tomar métricas (soporte/confianza/lift) de la primera fila
            first = rows[0]
            soporte = first.get('support')
            confianza = first.get('confidence')
            lift = first.get('lift')

            # itemset = union de antecedentes U consecuentes
            union_items = set(antecedents) | set(consequents)

            # Buscar itemset existente con los mismos productos
            found_itemset_id = None
            for iid, prodset in itemset_items_map.items():
                if prodset == union_items:
                    found_itemset_id = iid
                    break

            # Si no existe, crear nuevo itemset y sus itemset_item
            if not found_itemset_id:
                payload = {"soporte": soporte if soporte is not None else 0, "tamano": len(union_items)}
                resp = session.post(f"{url}/rest/v1/itemset", json=[payload], headers=hdrs)
                resp.raise_for_status()
                created = resp.json()
                if not created:
                    raise RuntimeError("No se creó el itemset esperado")
                found_itemset_id = created[0].get('itemset_id')

                # Insertar itemset_item para cada producto
                items_payload = [{"itemset_id": found_itemset_id, "producto_id": pid} for pid in union_items]
                if items_payload:
                    resp = session.post(f"{url}/rest/v1/itemset_item", json=items_payload, headers=hdrs)
                    resp.raise_for_status()

                # actualizar mapa local
                itemset_items_map[found_itemset_id] = set(union_items)

            # Verificar si ya existe una association_rule activa para este itemset con mismos antecedents/consequents
            found_existing_rule = None
            for ar in assoc_by_itemset.get(found_itemset_id, []):
                rid = ar.get('rule_id')
                existing_ants = antecedentes_map.get(rid, set())
                existing_cons = consecuentes_map.get(rid, set())
                if existing_ants == set(antecedents) and existing_cons == set(consequents):
                    found_existing_rule = ar
                    break

            if found_existing_rule:
                # Si métricas iguales (tolerancia pequeña), saltar; sino, soft-delete la existente y crear nueva
                try:
                    existing_support = float(found_existing_rule.get('soporte') or 0)
                    existing_conf = float(found_existing_rule.get('confianza') or 0)
                    existing_lift = float(found_existing_rule.get('lift') or 0)
                except Exception:
                    existing_support = existing_conf = existing_lift = 0.0

                # valores nuevos
                new_support = float(soporte or 0)
                new_conf = float(confianza or 0)
                new_lift = float(lift or 0)

                eps = 1e-6
                if (abs(existing_support - new_support) < eps and
                        abs(existing_conf - new_conf) < eps and
                        abs(existing_lift - new_lift) < eps):
                    print(f"Regla idéntica activa encontrada para {group}, se omite inserción")
                    continue

                # soft-delete: marcar existing rule active = false
                rid = found_existing_rule.get('rule_id')
                try:
                    patch_url = f"{url}/rest/v1/association_rule?rule_id=eq.{rid}"
                    # use timezone-aware UTC timestamp
                    ts_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
                    patch_payload = {
                        "active": False,
                        "deleted_at": ts_utc
                    }
                    # usar service role headers (hdrs) to allow update
                    resp = session.patch(patch_url, json=patch_payload, headers=hdrs, timeout=30)
                    resp.raise_for_status()
                    print(f"Regla antigua {rid} desactivada (soft-delete) para insertar versión nueva")
                except Exception as e:
                    print(f"Advertencia: no se pudo desactivar regla antigua {rid}: {e}", file=sys.stderr)
                # proceed to insert new rule

            # Insertar nueva association_rule (si no hay regla activa idéntica ya lo evitamos arriba)
            ar_payload = [{
                "itemset_id": found_itemset_id,
                "soporte": soporte if soporte is not None else 0,
                "confianza": confianza if confianza is not None else 0,
                "lift": lift if lift is not None else 0,
                "active": True,
                "deleted_at": None
            }]
            resp = session.post(f"{url}/rest/v1/association_rule", json=ar_payload, headers=hdrs)
            resp.raise_for_status()
            ar_created = resp.json()
            if not ar_created:
                raise RuntimeError("No se creó association_rule")
            new_rule_id = ar_created[0].get('rule_id')

            # Insertar antecedentes y consecuentes (en bloques)
            ants_payload = [{"rule_id": new_rule_id, "producto_id": pid} for pid in antecedents]
            cons_payload = [{"rule_id": new_rule_id, "producto_id": pid} for pid in consequents]

            if ants_payload:
                resp = session.post(f"{url}/rest/v1/rule_antecedente", json=ants_payload, headers=hdrs)
                resp.raise_for_status()

            if cons_payload:
                resp = session.post(f"{url}/rest/v1/rule_consecuente", json=cons_payload, headers=hdrs)
                resp.raise_for_status()

            print(f"Insertada regla {group} -> rule_id {new_rule_id}")

    except Exception as e:
        print(f"Error al insertar reglas en Supabase: {e}", file=sys.stderr)
        raise


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

def guardarReglas(reglas):
    supabase_url, headers = get_supabase_client()

    try:
        itemset = traetablassupa(supabase_url, headers, "itemset")
        itemset_item = traetablassupa(supabase_url, headers, "itemset_item")
        association_rule = traetablassupa(supabase_url, headers, "association_rule")
        antecedentes = traetablassupa(supabase_url, headers, "rule_antecedente")
        consecuentes = traetablassupa(supabase_url, headers, "rule_consecuente")
        insertaReglasSupabase(reglas, supabase_url, headers, itemset, itemset_item, association_rule, antecedentes, consecuentes)
    except Exception as e:
        print(f"Error al recuperar datos: {e}", file=sys.stderr)