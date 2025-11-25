# Exportación de Datos de Supabase a CSV para Power BI

## Uso

```powershell
pip install -r requirements_csv.txt
python export_to_csv.py
```

Los archivos CSV se generarán en la carpeta `csv_exports`.

## Orden de Importación en Power BI

Importar los archivos en este orden para evitar errores de relaciones:

### 1. Tablas Dimensionales (importar primero)
1. `cliente.csv`
2. `producto.csv`

### 2. Tablas de Hechos
3. `orden.csv`
4. `orden_detalle.csv`

### 3. Tablas de Apriori
5. `itemset.csv`
6. `association_rule.csv`
7. `itemset_item.csv`
8. `rule_antecedente.csv`
9. `rule_consecuente.csv`
