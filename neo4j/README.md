**Proyecto Neo4j — Instrucciones de ejecución**

Breve guía para preparar y ejecutar este repositorio. Incluye pasos para poblar la base de datos Neo4j (`ventas`), arrancar el servidor y cliente, e instalar/ejecutar el ETL en `ETL_NEO4J.py`.

**Requisitos**
- **Neo4j**: local (Desktop). Versión compatible: Neo4j 4.x o 5.x.
- **Node.js & npm**: para `server` y `client`.
- **Python 3.8+**: para el ETL.

**Estructura relevante**
- `llenado.cypher` — Script Cypher que crea nodos, relaciones y constraints (usa la base `ventas`).
- `server/` — Backend Node.js (API).
- `client/` — Frontend (Vite + React).
- `requirements.txt` — Dependencias Python para el ETL.
- `ETL_NEO4J.py` — Script ETL (Python).

**1) Preparar la base de datos Neo4j (base `ventas`)**

Se recomienda crear la base de datos llamada `ventas` antes de ejecutar el script `llenado.cypher`. Opciones:

- Usando Neo4j Browser o Cypher Editor (Neo4j Desktop):

  1. Abrir Neo4j Browser / Desktop.
  2. Si tu instancia usa múltiples bases de datos, crear la base `ventas` (si aplica):

  ```cypher
  CREATE DATABASE ventas;
  ```

  3. Seleccionar la base `ventas` (selector de base de datos en la UI) y ejecutar el contenido de `llenado.cypher`.

  - Si la base `ventas` no existe, crea primero con `CREATE DATABASE ventas;` en el `cypher-shell` o Browser.

Nota: `llenado.cypher` crea constraints únicos (por ejemplo para `sku`, `codigo_alt`, `codigo_mongo`, `id`, y `email`) y nodos/relaciones. Ejecutar con cuidado en una base sin datos previos.

**2) Instalar y arrancar el backend (API)**

Se debe de eliminar el .example del .env.example y configurar las credenciales con las adecuadas para su máquina

```powershell
cd server
npm install
# Arrancar (según package.json):
npm run dev
# El servidor expone variables, revisa `server/index.js` para puerto/host
```

Por defecto el frontend apunta a `http://localhost:3000/api` (ver `client/src/services/api.js`), comprueba que el servidor esté en ese puerto.

**3) Instalar y arrancar el frontend (cliente)**

```powershell
cd ..\client
npm install
npm run dev
```

Abre el navegador en la URL que indique Vite (por defecto `http://localhost:5173` o similar).

**4) ETL (Python)**

El ETL depende de las librerías listadas en `requirements.txt`. Antes de ejecutar el ETL, asegúrate de que la base `ventas` esté creada y poblada si así lo requiere tu flujo.

Se debe de eliminar el .example del .env.example y configurar las credenciales con las adecuadas para su máquina

Recomendado (PowerShell):

```powershell
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar el ETL
python ETL_NEO4J.py
```