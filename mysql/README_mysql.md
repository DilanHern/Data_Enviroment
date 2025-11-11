# Población de la base sales_mysql (MySQL) con Faker

Contenido
- `populate_mysql.py`: script Python que inserta (por defecto) 420 filas por tabla: `Cliente`, `Producto`, `Orden`, `OrdenDetalle`.
- `requirements_mysql.txt`: dependencias para ejecutar el script en MySQL.

Instalación (PowerShell):
```powershell
python -m pip install -r .\requirements_mysql.txt
```

Ejecución (ejemplo):
```powershell
python .\populate_mysql.py --host localhost --port 3306 --database sales_mysql --user root --password "1234"
```
