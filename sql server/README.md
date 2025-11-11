# Población de la base ventas_ms con Faker

Contenido:
- `populate_db.py`: script que inserta (por defecto) 420 filas en cada tabla: `Cliente`, `Producto`, `Orden`, `OrdenDetalle`.
- `requirements.txt`: dependencias Python.

Instalación

En PowerShell:

```powershell
python -m pip install -r .\requirements.txt
```

Ejecución (ejemplo, usando autenticación integrada de Windows):

```powershell
python .\populate_db.py --server localhost --database ventas_ms --trusted
```

Iniciar con autenticación SQL Server (usuario/contraseña):

```powershell
python .\populate_db.py --server tcp:MYHOST,1433 --database ventas_ms --username myuser --password mypass
```
