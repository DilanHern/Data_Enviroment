"""
Script para exportar datos de Supabase a archivos CSV para Power BI
"""
import os
import csv
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Cargar variables de entorno
load_dotenv('../../env.txt')

# Configuración de Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Faltan credenciales de Supabase en el archivo env.txt")
    print("   Configura SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY (o SUPABASE_ANON_KEY)")
    exit(1)

# Crear cliente de Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Carpeta de salida para los CSV
OUTPUT_DIR = 'csv_exports'

# Crear carpeta si no existe
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def export_table_to_csv(table_name, filename=None):
    """
    Exporta una tabla de Supabase a un archivo CSV
    
    Args:
        table_name: Nombre de la tabla en Supabase
        filename: Nombre del archivo (opcional, por defecto usa el nombre de la tabla)
    """
    if filename is None:
        filename = f"{table_name}.csv"
    
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    try:
        # Obtener todos los datos de la tabla
        response = supabase.table(table_name).select("*").execute()
        data = response.data
        
        if not data:
            return
        
        # Escribir CSV
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(data)
        
        print(f"✓ {table_name}: {len(data)} registros")
        
    except Exception as e:
        print(f"✗ {table_name}: {str(e)}")

def export_custom_query(query_name, query_func, filename):
    """
    Exporta el resultado de una consulta personalizada a CSV
    
    Args:
        query_name: Nombre descriptivo de la consulta
        query_func: Función que ejecuta la consulta y retorna los datos
        filename: Nombre del archivo CSV
    """
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    try:
        data = query_func()
        
        if not data:
            return
        
        # Escribir CSV
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(data)
        
        print(f"✓ {query_name}: {len(data)} registros")
        
    except Exception as e:
        print(f"✗ {query_name}: {str(e)}")

def main():
    """Función principal que exporta todas las tablas"""
    
    print("Exportando datos a CSV...")
    print()
    
    # Tablas principales del sistema de ventas
    export_table_to_csv('cliente')
    export_table_to_csv('producto')
    export_table_to_csv('orden')
    export_table_to_csv('orden_detalle')
    
    # Tablas de Apriori (reglas de asociación)
    export_table_to_csv('itemset')
    export_table_to_csv('itemset_item')
    export_table_to_csv('association_rule')
    export_table_to_csv('rule_antecedente')
    export_table_to_csv('rule_consecuente')
    
    # Vistas/Consultas personalizadas útiles para Power BI
    
    # Vista de órdenes con información del cliente
    def query_ordenes_completas():
        response = supabase.rpc('get_ordenes_completas').execute()
        if hasattr(response, 'data'):
            return response.data
        # Si no existe la función RPC, hacer la consulta manual
        ordenes = supabase.table('orden').select(
            '*, cliente:cliente_id(nombre, email, genero, pais)'
        ).execute()
        
        # Aplanar los datos
        result = []
        for orden in ordenes.data:
            cliente = orden.pop('cliente', {})
            flat_orden = {**orden}
            if cliente:
                flat_orden['cliente_nombre'] = cliente.get('nombre')
                flat_orden['cliente_email'] = cliente.get('email')
                flat_orden['cliente_genero'] = cliente.get('genero')
                flat_orden['cliente_pais'] = cliente.get('pais')
            result.append(flat_orden)
        return result
    
    export_custom_query(
        'Órdenes con datos del cliente',
        query_ordenes_completas,
        'vista_ordenes_completas.csv'
    )
    
    # Vista de detalle de órdenes con producto
    def query_detalle_completo():
        detalles = supabase.table('orden_detalle').select(
            '*, orden:orden_id(fecha, canal, moneda, total, cliente_id), producto:producto_id(sku, nombre, categoria)'
        ).execute()
        
        # Aplanar los datos
        result = []
        for detalle in detalles.data:
            orden = detalle.pop('orden', {})
            producto = detalle.pop('producto', {})
            flat_detalle = {**detalle}
            if orden:
                flat_detalle['orden_fecha'] = orden.get('fecha')
                flat_detalle['orden_canal'] = orden.get('canal')
                flat_detalle['orden_moneda'] = orden.get('moneda')
                flat_detalle['orden_total'] = orden.get('total')
                flat_detalle['orden_cliente_id'] = orden.get('cliente_id')
            if producto:
                flat_detalle['producto_sku'] = producto.get('sku')
                flat_detalle['producto_nombre'] = producto.get('nombre')
                flat_detalle['producto_categoria'] = producto.get('categoria')
            
            # Calcular subtotal
            flat_detalle['subtotal'] = float(detalle['cantidad']) * float(detalle['precio_unit'])
            
            result.append(flat_detalle)
        return result
    
    export_custom_query(
        'Detalle de órdenes completo',
        query_detalle_completo,
        'vista_detalle_completo.csv'
    )
    
    # Vista de reglas de asociación con nombres de productos
    def query_reglas_legibles():
        try:
            # Obtener reglas activas
            reglas = supabase.table('association_rule').select(
                '*, itemset:itemset_id(soporte, tamano)'
            ).eq('active', True).execute()
            
            result = []
            for regla in reglas.data:
                # Obtener antecedentes
                antecedentes = supabase.table('rule_antecedente').select(
                    'producto:producto_id(nombre)'
                ).eq('rule_id', regla['rule_id']).execute()
                
                # Obtener consecuentes
                consecuentes = supabase.table('rule_consecuente').select(
                    'producto:producto_id(nombre)'
                ).eq('rule_id', regla['rule_id']).execute()
                
                itemset = regla.pop('itemset', {})
                
                flat_regla = {
                    'rule_id': regla['rule_id'],
                    'soporte': regla['soporte'],
                    'confianza': regla['confianza'],
                    'lift': regla['lift'],
                    'itemset_soporte': itemset.get('soporte') if itemset else None,
                    'itemset_tamano': itemset.get('tamano') if itemset else None,
                    'antecedentes': ', '.join([a['producto']['nombre'] for a in antecedentes.data if a.get('producto')]),
                    'consecuentes': ', '.join([c['producto']['nombre'] for c in consecuentes.data if c.get('producto')])
                }
                result.append(flat_regla)
            
            return result
        except Exception as e:
            return []
    
    export_custom_query(
        'Reglas de asociación',
        query_reglas_legibles,
        'vista_reglas_asociacion.csv'
    )
    
    print()
    print(f"✅ Exportación completada: {os.path.abspath(OUTPUT_DIR)}")

if __name__ == "__main__":
    main()
