<p align="center">
	<img src="https://img.shields.io/badge/status-academic%20project-green" alt="status" />
	<img src="https://img.shields.io/badge/domain-Data%20Engineering%20%26%20BI-blue" alt="domain" />
	<img src="https://img.shields.io/badge/stack-Python%2C%20SQL%2C%20Node.js%2C%20React-orange" alt="stack" />
</p>

# Data_Enviroment

Plataforma de analítica de ventas end‑to‑end que integra múltiples bases de datos transaccionales (Supabase/PostgreSQL, SQL Server, MySQL, MongoDB, Neo4j) con un Data Warehouse corporativo, procesos ETL en Python y modelos de Apriori para generar reglas de asociación consumidas por aplicaciones web y dashboards en Power BI.

El objetivo del proyecto es demostrar un flujo completo de ingeniería de datos y analítica avanzada, desde la captura transaccional hasta la explotación de datos por usuarios de negocio.

---

## 1. Arquitectura General

### Visión de alto nivel

La solución implementa una arquitectura de análisis de ventas multi‑fuente con los siguientes componentes principales:

- **Fuentes OLTP**
	- **Supabase/PostgreSQL**: base principal de ventas para el caso Apriori.
	- **SQL Server (`ventas_ms`)**: base de ventas transaccional clásica.
	- **MySQL (`sales_mysql`)**: base alternativa para escenarios de integración.
	- **MongoDB**: backend Node.js + colección de ventas.
	- **Neo4j**: grafo de ventas y relaciones cliente‑producto.

- **Data Warehouse (`DW_VENTAS`, SQL Server)**
	- Modelo dimensional en estrella con una tabla de hechos de ventas y dimensiones de Tiempo, Cliente, Producto y Canal.
	- Tabla de metas de ventas (`MetaVentas`) vinculada a `DimCliente` y `DimProducto`.

- **Procesos ETL / Integración** (Python)
	- ETLs específicos desde SQL Server, MySQL, MongoDB y Neo4j hacia el DW.
	- Job de tipo de cambio BCCR para enriquecer la dimensión Tiempo con tipo de cambio diario.

- **Capa de Ciencia de Datos**
	- Implementación de Apriori con `mlxtend` sobre datos transaccionales en Supabase.
	- Cálculo de reglas de asociación y persistencia en tablas especializadas en PostgreSQL.

- **Capa de Presentación (Frontends)**
	- **`supabase/frontend`**: React + Vite, conectado a Supabase, muestra clientes, productos, órdenes y recomendaciones basadas en reglas de asociación.
	- **`mongoDB/frontend`**: React + Vite (según `package.json`) para explorar datos traídos desde MongoDB.
	- **`neo4j/client`**: React + Vite para consumir el backend Neo4j.

- **APIs / Backends**
	- **Supabase**: expone REST/SQL sobre PostgreSQL (gestionado por Supabase).
	- **`mongoDB/backend`**: Node.js/Express, API REST para clientes, productos, órdenes (ver `src/routes/*Route.js`).
	- **`neo4j/server`**: Node.js/Express, API para consultar el grafo de ventas.

- **Dashboards BI**
	- Power BI sobre el DW `DW_VENTAS` para análisis de ventas, cumplimiento de metas y recomendaciones.

La interacción se resume así:

1. Sistemas OLTP generan y almacenan transacciones de ventas.
2. Procesos ETL extraen, transforman y cargan datos hacia el DW (`DW_VENTAS`).
3. Scripts de Apriori leen ventas de Supabase, calculan reglas y las guardan en tablas propias.
4. Frontends consultan Supabase y/o APIs para mostrar datos operativos y recomendaciones.
5. Power BI se conecta al DW para análisis histórico y métricas de negocio.

---

## 2. Bases de Datos Transaccionales (OLTP)

### 2.1 Supabase / PostgreSQL

Script principal: `supabase/backEnd/db/migrations/creationScript.sql`.

**Tablas núcleo:**

- `cliente`  
	- `cliente_id` (UUID, PK, `uuid_generate_v4()`), `nombre`, `email` (UNIQUE), `genero` (`M`/`F`), `pais`, `fecha_registro`.
- `producto`  
	- `producto_id` (UUID, PK), `sku` (UNIQUE, opcional), `nombre`, `categoria`.
- `orden`  
	- `orden_id` (UUID, PK), FK a `cliente`, `fecha` (`TIMESTAMPTZ`), `canal` (`WEB`/`APP`/`PARTNER`), `moneda` (`USD`/`CRC`), `total`.
- `orden_detalle`  
	- `orden_detalle_id` (UUID, PK), FKs a `orden` y `producto`, `cantidad`, `precio_unit`.

**Integridad y performance:**

- Foreign keys entre `orden` → `cliente` y `orden_detalle` → (`orden`, `producto`).
- Índices para consultas analíticas y Apriori:
	- `CREATE INDEX ix_orden_fecha ON orden(fecha);`
	- `CREATE INDEX ix_detalle_producto ON orden_detalle(producto_id);`

**Tablas Apriori en PostgreSQL:**

- `itemset` (itemsets frecuentes)
	- `itemset_id` (UUID, PK), `soporte` (NUMERIC), `tamano` (INT).
- `itemset_item` (detalle de productos por itemset)
	- PK compuesta (`itemset_id`, `producto_id`).
- `association_rule` (regla de asociación)
	- `rule_id` (UUID, PK), FK a `itemset`, `soporte`, `confianza`, `lift`, `active` (soft delete), `deleted_at`.
- `rule_antecedente` / `rule_consecuente`
	- Relaciones N‑a‑N entre reglas y productos para antecedente y consecuente.

### 2.2 SQL Server – `ventas_ms`

Scripts y utilidades en `sql server/`:

- `ScriptCreación.sql`: define tablas transaccionales `Cliente`, `Producto`, `Orden`, `OrdenDetalle` (no mostrado aquí pero análogo al modelo Supabase).
- `populate_db.py`: genera datos sintéticos (Faker) y puebla ~420 registros por tabla.

**Uso típico:**

- Integridad referencial con FKs entre cliente, producto, orden y detalle.
- Constraints de negocio (p.ej. cantidades negativas no permitidas, emails únicos, etc.).

### 2.3 MySQL – `sales_mysql`

Contenido en `mysql/`:

- `ScriptCreaciónMySQL.sql`: define tablas equivalentes a `Cliente`, `Producto`, `Orden`, `OrdenDetalle`.
- `populate_mysql.py`: inserta datos de prueba en MySQL.

### 2.4 MongoDB

Backend en `mongoDB/backend` (Node.js/Express) y frontend en `mongoDB/frontend`.

- Modelos en `mongoDB/backend/src/models/*.js` para `cliente`, `producto` y `orden`.
- Rutas REST en `mongoDB/backend/src/routes/*Route.js`.
- ETL Python `mongoDB/backend/data/etl.py` para extraer información de MongoDB y enviar al DW.

### 2.5 Neo4j

Carpeta `neo4j/`:

- `llenado.cypher`: crea nodos de clientes, productos, órdenes y relaciones (por ejemplo `COMPRO`, `PERTENECE_A`), con constraints únicos sobre SKUs, IDs y correos.
- BD principal: `ventas`.

Esta base orientada a grafos se usa para análisis relacional avanzado y como fuente adicional hacia el DW.

---

## 3. Data Warehouse (DW_VENTAS)

Script: `dw/ScriptCreaciónDW.sql`.

### 3.1 Modelo Dimensional (Esquema en Estrella)

- **Dimensiones:**
	- `DimTiempo` (`IdTiempo` INT IDENTITY, `Anio`, `Mes`, `Dia`, `Fecha`, `Semana`, `DiaSemana`, `TipoCambio`).
	- `DimCliente` (`IdCliente` INT IDENTITY, `Nombre`, `Email`, `Genero`, `Pais`, `FechaCreacion`).
	- `DimProducto` (`IdProducto` INT IDENTITY, `SKU`, `Nombre`, `Categoria`).
	- `DimCanal` (`IdCanal` INT IDENTITY, `Nombre`).

- **Tabla de Hechos:**
	- `FactVentas` (`IdFactVentas` INT IDENTITY PK) con FKs a `DimTiempo`, `DimProducto`, `DimCliente`, `DimCanal`.
	- Métricas: `TotalVentas`, `Cantidad`, `Precio`.

- **Metas:**
	- `MetaVentas` con FKs a `DimProducto` y `DimCliente` y columnas `Anio`, `Mes`, `MetaUSD`.

- **Equivalencias de SKUs:**
	- `Equivalencias` para mapear `SKU`, `CodigoMongo`, `CodigoAlt` entre orígenes heterogéneos.

### 3.2 Claves Sustitutas y Tiempo

- Todas las dimensiones usan claves sustitutas `INT IDENTITY` para desacoplar el DW de los IDs de origen.
- `DimTiempo` almacena un registro por fecha y contiene `TipoCambio` diario.
- Job `dw/job/bccr_exchange_rate.py` llena `DimTiempo.TipoCambio` consultando el BCCR para ~3 años de historia.

### 3.3 Llenado de Metas de Ventas

Script: `dw/LlenadoMetaVentas.sql`.

- Calcula metas mensuales por combinación `IdProducto`–`IdCliente`–`Año`–`Mes`.
- Fórmula base: meta ≈ 80% del promedio histórico de ventas reales de esa combinación, con un factor de variabilidad 0.9‑1.1.
- Se limita a los primeros 50 productos y 50 clientes para mantener el volumen manejable.

### 3.4 Razonamiento de Diseño

- Modelo en estrella para optimizar consultas analíticas (scans sobre `FactVentas` + joins a dimensiones denormalizadas).
- Desnormalización controlada en dimensiones (p.ej. `Pais`, `Categoria`) para simplificar reporting.
- Tabla `Equivalencias` permite integrar SKUs de MongoDB, SQL Server, MySQL y Supabase.

---

## 4. Proceso ETL / ELT

### 4.1 Extract

- **Supabase/PostgreSQL**
	- APIs REST de Supabase (`/rest/v1/orden`, `/rest/v1/orden_detalle`, `/rest/v1/producto`) usando `requests`.
	- Autenticación con `SUPABASE_SERVICE_ROLE_KEY` y control de paginación (`limit`, `offset`).

- **SQL Server** (`sql server/ETL_SQLSERVER_TO_DW.py`)
	- Conexión vía `pyodbc` usando parámetros de `env.txt`.
	- Lector de tablas `Cliente`, `Producto`, `Orden`, `OrdenDetalle` en `ventas_ms`.

- **MySQL** (`mysql/ETL_MYSQL_TO_DW.py`)
	- Conexión via `mysql-connector` o similar (definido en `requirements_mysql.txt`).

- **MongoDB** (`mongoDB/backend/data/etl.py`)
	- Lectura desde colecciones Mongo; normalización de documentos a registros tabulares.

- **Neo4j** (`neo4j/ETL_NEO4J.py`)
	- Conexión mediante `neo4j` driver.
	- Consultas Cypher para obtener patrones cliente‑producto‑orden.

### 4.2 Transform

Las transformaciones siguen estos principios:

- Limpieza y tipado:
	- Conversión de fechas a tipos `DATE`/`DATETIME` estándar.
	- Normalización de monedas (uso posterior de tipo de cambio BCCR).
- Validaciones:
	- Filtrado de filas con cantidades negativas o nulas.
	- Verificación de claves obligatorias (cliente, producto, fecha).
- Enriquecimiento:
	- Incorporación de `TipoCambio` desde `DimTiempo`.
	- Cálculo de `TotalVentas` = `Cantidad * Precio` cuando aplica.
- Integración de SKUs:
	- Uso de la tabla `Equivalencias` para mapear códigos entre sistemas.

Las transformaciones se implementan principalmente en Python utilizando `pandas` y SQL nativo cuando corresponde.

### 4.3 Load

- Carga en `DW_VENTAS` mediante inserciones batch hacia:
	- `DimCliente`, `DimProducto`, `DimCanal`, `DimTiempo`.
	- `FactVentas` y `MetaVentas`.
- Consideraciones de performance:
	- Uso de inserts por lotes (batch) en lugar de inserts fila por fila.
	- Índices creados después de la carga masiva cuando aplica.
- Manejo de duplicados:
	- Deduplicación basada en llaves de negocio (cliente+email, producto+sku, fecha+orden).
	- Uso de `Equivalencias` para asegurar mapeos 1‑a‑1 entre códigos.

### 4.4 Job de Tipo de Cambio (BCCR)

Script: `dw/job/bccr_exchange_rate.py`.

- Descarga tipos de cambio diarios para los últimos 3 años desde BCCR.
- Inserta o actualiza el campo `TipoCambio` en `DimTiempo`.
- Ofrece comandos para scheduling y limpieza de job:

```powershell
# Instalar dependencias (ejemplo genérico)
python -m venv .venv
.\.venv\Scripts\activate
pip install requests pyodbc python-dotenv

# Poblar tipos de cambio
python bccr_exchange_rate.py populate

# Programar job diario (ej. 05:00)
python bccr_exchange_rate.py scheduler 05:00

# Eliminar job
python bccr_exchange_rate.py remove-scheduler
```

---

## 5. Ciencia de Datos: Apriori y Reglas de Asociación

Scripts clave en `supabase/backEnd/db/apriori`:

- `apriori.py`: pipeline principal.
- `insertapriori.py`: persistencia en tablas Apriori de Supabase.
- `generarevision.py`: generación de reporte legible de reglas (`reglas_revision.txt`).

### 5.1 Dataset de Ventas

- Origen: tablas `orden` y `orden_detalle` de Supabase/PostgreSQL.
- Cada transacción se modela como un conjunto de productos por `orden_id`.

### 5.2 Preparación de Datos

1. Extracción via REST de `orden`, `orden_detalle` y `producto`.
2. Construcción de una tabla con columnas `transaction_id` y `item` (`producto_id`).
3. Transformación a formato **one‑hot encoding**: matriz transacción × producto con valores booleanos.

### 5.3 Cálculo de Métricas

Se utilizan las funciones de `mlxtend.frequent_patterns`:

- **Soporte ($support$)**
	- $support(X) = \frac{\text{transacciones que contienen X}}{\text{transacciones totales}}$
- **Confianza ($confidence$)**
	- $confidence(X \Rightarrow Y) = \frac{support(X \cup Y)}{support(X)}$.
- **Lift**
	- $lift(X \Rightarrow Y) = \frac{confidence(X \Rightarrow Y)}{support(Y)}$.

Parámetros configurados en `apriori.py`:

- `MIN_SUPPORT = 0.015` (1.5% de las transacciones).  
- `MIN_CONFIDENCE = 0.3`.

### 5.4 Algoritmo y Optimizaciones

- Uso del algoritmo **Apriori** de `mlxtend` sobre la matriz one‑hot.
- Post-procesamiento para:
	- Agregar columna `length` (tamaño del itemset) para priorizar itemsets más largos.
	- Mapear IDs de producto a nombres y SKUs para reportes legibles.
	- Deduplicar reglas por par exacto (antecedentes, consecuentes), quedándose con la regla de mejor calidad.
	- Expandir cada regla en pares atómicos antecedente → consecuente para facilitar el consumo en frontend.

### 5.5 Persistencia de Reglas

- Las reglas se guardan en las tablas `itemset`, `itemset_item`, `association_rule`, `rule_antecedente`, `rule_consecuente` en Supabase.
- `association_rule.active` permite soft delete; las reglas inactivas se excluyen de las recomendaciones.

### 5.6 Casos de Uso de Negocio

- **Recomendaciones de productos**: "Clientes que compraron X también compraron Y".
- **Cross‑selling y up‑selling** en el frontend (sugerencias en la vista de orden o detalle de producto).
- **Optimización de surtido**: análisis de combinaciones de productos frecuentemente adquiridos.

---

## 6. Dashboards en Power BI

Sobre el DW `DW_VENTAS` se propone un modelo conectado vía SQL Server connector con las siguientes vistas:

- **Métricas principales:**
	- Ventas totales (`TotalVentas`) por día, mes, año.
	- Cantidad de unidades vendidas (`Cantidad`).
	- Cumplimiento de metas vs `MetaVentas.MetaUSD`.

- **KPIs sugeridos:**
	- % Cumplimiento de Meta por cliente, producto y canal.
	- Ticket promedio.
	- Mix de productos por segmento.

- **Visualizaciones típicas:**
	- Series de tiempo por `DimTiempo`.
	- Segmentaciones por `DimCliente.Pais`, `DimProducto.Categoria`, `DimCanal.Nombre`.
	- Tableros comparativos meta vs real (semáforos por color).

**Uso del archivo PBIX (no incluido en el repo):**

1. Abrir Power BI Desktop.
2. Conectar a SQL Server → base `DW_VENTAS`.
3. Importar tablas `FactVentas`, `DimTiempo`, `DimCliente`, `DimProducto`, `DimCanal`, `MetaVentas`.
4. Crear relaciones según las FKs ya definidas en el DW.
5. Publicar el reporte o compartir el archivo `.pbix` dentro de la organización.

---

## 7. Páginas Web e Interfaces

### 7.1 Supabase Frontend (`supabase/frontend`)

- **Stack:** React + Vite, `@supabase/supabase-js`.
- **Funcionalidad principal:**
	- Listado y detalle de **clientes**, **productos** y **órdenes**.
	- Módulo de **recomendaciones**, consumiendo reglas en `association_rule` filtradas por `active = true`.
- **Flujo de usuario:**
	1. El usuario accede a la home (`App.jsx`) y elige vista (Clientes, Productos, Órdenes).
	2. Consulta datos directamente en Supabase usando el servicio `src/services/api.js`.
	3. En vista de producto/orden puede ver productos recomendados basados en reglas Apriori.

### 7.2 MongoDB Frontend (`mongoDB/frontend`)

- React + Vite, consume el backend `mongoDB/backend`.
- Permite navegar por colecciones de clientes, productos y órdenes.

### 7.3 Neo4j Client (`neo4j/client`)

- React + Vite, consume el backend `neo4j/server`.
- Expone consultas sobre el grafo de ventas (por ejemplo, productos relacionados a un cliente).

> Nota: Las UIs están diseñadas como herramientas de demostración para presentar la integración de datos más que para uso productivo final.

---

## 8. Casos de Uso y Beneficios

**Problema de negocio:**

Empresas de retail o e‑commerce necesitan consolidar datos de ventas dispersos en múltiples sistemas y extraer insights accionables (recomendaciones, análisis de metas, comportamiento de clientes).

**Usuarios objetivo:**

- Analistas de negocio y BI.
- Equipos de data engineering.
- Product managers y marketing.

**Beneficios aportados:**

- Vista unificada de ventas multi‑canal en un DW centralizado.
- Motor de recomendaciones basado en reglas de asociación.
- Infraestructura reutilizable para integrar nuevas fuentes de datos.
- Base sólida para desarrollar dashboards de performance comercial.

**Justificación de la arquitectura:**

- Separación clara entre OLTP y OLAP mediante un DW dimensional.
- Uso de tecnologías estándar de la industria (SQL Server, PostgreSQL, Python, React, Power BI).
- Capacidad de escalar a nuevos orígenes (MongoDB, Neo4j) gracias a la tabla de equivalencias y procesos ETL modulares.

---

## 9. Guía de Instalación y Ejecución

### 9.1 Requisitos Generales

- **Sistema operativo:** Windows 10/11 (probado) o equivalente.
- **Python:** 3.10+ recomendado.
- **Node.js:** v18+.
- **SQL Server local** con capacidad para crear `DW_VENTAS` y `ventas_ms`.
- **MySQL** (opcional) para `sales_mysql`.
- **MongoDB** (opcional) y **Neo4j Desktop** (opcional).

Se recomienda trabajar dentro de un entorno virtual Python en la raíz:

```powershell
cd Data_Enviroment
python -m venv .venv
.\.venv\Scripts\activate
```

### 9.2 Data Warehouse y Job de Tipo de Cambio

1. Crear DW en SQL Server ejecutando `dw/ScriptCreaciónDW.sql`.
2. Opcional: llenar metas de ventas ejecutando `dw/LlenadoMetaVentas.sql`.
3. Configurar `.env` para el job BCCR (ver `dw/job/env.txt` como referencia).
4. Instalar dependencias y ejecutar `dw/job/bccr_exchange_rate.py` según la sección de ETL.

### 9.3 SQL Server – Base `ventas_ms`

```powershell
cd "sql server"
python -m pip install -r .\requirements.txt
python .\populate_db.py --server localhost --database ventas_ms --trusted

# Ejecutar ETL hacia DW
python .\ETL_SQLSERVER_TO_DW.py
```

### 9.4 MySQL – Base `sales_mysql`

```powershell
cd mysql
python -m pip install -r .\requirements_mysql.txt
python .\populate_mysql.py --host localhost --port 3306 --database sales_mysql --user root --password "1234"

# Ejecutar ETL hacia DW
python .\ETL_MYSQL_TO_DW.py
```

### 9.5 MongoDB

```powershell
# Backend
cd mongoDB\backend
npm install
npm start

# ETL
cd data
pip install -r .\requirements_etl.txt
python .\etl.py

# Frontend
cd ..\..\frontend
npm install
npm run dev
```

### 9.6 Neo4j

1. Crear base `ventas` en Neo4j.
2. Ejecutar `llenado.cypher` sobre la base `ventas`.
3. Configurar `.env` en `neo4j/server` y raíz del proyecto Neo4j.

```powershell
cd neo4j
pip install -r .\requirements.txt
python .\ETL_NEO4J.py

cd server
npm install
npm run dev

cd ..\client
npm install
npm run dev
```

### 9.7 Supabase – Backend Apriori y Frontend

**Backend Apriori:**

```powershell
cd supabase\backEnd\db\apriori
python .\apriori.py
python .\generarevision.py
```

Requiere `supabase/backEnd/.env.local` con:

```env
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
SUPABASE_ANON_KEY=...
MSSQL_SERVER=...
MSSQL_DW_DB=DW_VENTAS
MSSQL_USER=...
MSSQL_PASSWORD=...
MSSQL_DRIVER=ODBC Driver 17 for SQL Server
```

**Frontend Supabase:**

```powershell
cd supabase\frontend
npm install
npm run dev
```

Requiere `supabase/frontend/.env.local` con:

```env
VITE_SUPABASE_URL=...
VITE_SUPABASE_ANON_KEY=...
```

### 9.8 Power BI

1. Confirmar que `DW_VENTAS` está poblada.
2. Abrir Power BI Desktop → Obtener datos → SQL Server.
3. Conectarse a la instancia de SQL Server y seleccionar la BD `DW_VENTAS`.
4. Cargar tablas dimensionales y de hechos y construir el modelo.

---

## 10. Tecnologías Utilizadas

### Lenguajes

- Python (ETL, Apriori, utilidades).
- SQL (PostgreSQL, T‑SQL, MySQL).
- JavaScript / TypeScript (Node.js, React, Vite).

### Frameworks y Librerías

- **Backend:** Node.js, Express, Supabase (PostgREST), Neo4j driver.
- **Frontend:** React, Vite, `@supabase/supabase-js`.
- **Data Engineering / Science:** `pandas`, `mlxtend`, `requests`, `python-dotenv`, `pyodbc`.

### Bases de Datos

- PostgreSQL (Supabase).
- SQL Server (`ventas_ms`, `DW_VENTAS`).
- MySQL (`sales_mysql`).
- MongoDB.
- Neo4j.

### BI y Herramientas

- Power BI Desktop.
- Neo4j Desktop.
- Supabase Dashboard.

---

Este repositorio está diseñado para reflejar el trabajo de un equipo de ingeniería de datos profesional: separación clara de capas, documentación de ETLs, modelo dimensional explícito y una integración end‑to‑end lista para demo técnica o revisión académica.
