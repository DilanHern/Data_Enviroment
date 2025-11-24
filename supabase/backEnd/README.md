**Resumen**: Utilidades y scripts ETL para la instancia de Supabase. Contiene el pipeline Apriori y helpers usados para generar reglas de asociación y poblar datos.

**Ubicación**: `supabase/backEnd` y `supabase/backEnd/db`

**Cómo ejecutar**
- El código Apriori está en `supabase/backEnd/db/apriori/apriori.py`; los helpers `insertapriori.py` y `generarevision.py` se encuentran en la misma carpeta.
- Ejecútalo desde la carpeta del script:
  ```powershell
  cd supabase/backEnd/db/apriori
  python .\apriori.py
  # generar archivo legible con las reglas
  python .\generarevision.py
  ```

**Variables de entorno**
- Coloca la configuración en `supabase/backEnd/.env.local` (este repositorio lo usa por defecto). Variables necesarias:
  - `SUPABASE_URL` — URL del proyecto Supabase (ej.: `https://xyz.supabase.co`)
  - `SUPABASE_SERVICE_ROLE_KEY` — clave service role (necesaria para operaciones de escritura/patch)
  - `SUPABASE_ANON_KEY` — opcional; usado por utilidades que sólo necesitan lectura
  - `MSSQL_SERVER`, `MSSQL_DW_DB`, `MSSQL_USER`, `MSSQL_PASSWORD`, `MSSQL_DRIVER` — si usas ETLs con SQL Server

Ejemplo de `.env.local` (NO subir claves reales):
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...service-role-key...
SUPABASE_ANON_KEY=eyJ...anon-key...
MSSQL_SERVER=DESKTOP-XXXX
MSSQL_DW_DB=DW_VENTAS
MSSQL_USER=sa
MSSQL_PASSWORD=yourpassword
MSSQL_DRIVER=ODBC Driver 17 for SQL Server
```

**Notas**
- Los scripts cargan `.env.local` usando `python-dotenv`; `apriori.py` y `generarevision.py` prefieren el `.env.local` del proyecto ubicado dos niveles arriba.
- `generarevision.py` crea `reglas_revision.txt` y por defecto sólo incluye reglas activas.
- `insertapriori.py` utiliza la clave service role para escribir/soft-delete en Supabase. Mantén esa clave privada.

**Si hay errores**
- Verifica los valores en `.env.local` y los permisos de las claves de Supabase. Para operaciones de escritura usa la `SUPABASE_SERVICE_ROLE_KEY`.

**Siguientes pasos (opcional)**
- Puedo añadir salida en JSON para `generarevision.py` o tareas automáticas (CI) que ejecuten Apriori.
