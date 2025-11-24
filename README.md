<p align="center">
	<img src="https://img.shields.io/badge/status-academic%20project-green" alt="status" />
	<img src="https://img.shields.io/badge/domain-Data%20Engineering%20%26%20BI-blue" alt="domain" />
	<img src="https://img.shields.io/badge/stack-Python%2C%20SQL%2C%20Node.js%2C%20React-orange" alt="stack" />
</p>

# Data_Enviroment

End‑to‑end sales analytics platform that integrates multiple transactional databases (Supabase/PostgreSQL, SQL Server, MySQL, MongoDB, Neo4j) with a corporate Data Warehouse, Python‑based ETL processes, and Apriori models to generate association rules consumed by web applications and Power BI dashboards.

The goal of this project is to demonstrate a complete data engineering and advanced analytics flow, from transactional capture to business user consumption.

---

## 1. Overall Architecture

### High‑Level View

The solution implements a multi‑source sales analytics architecture with the following main components:

- **OLTP Sources**
	- **Supabase/PostgreSQL**: main sales database used for the Apriori case.
	- **SQL Server (`ventas_ms`)**: traditional transactional sales database.
	- **MySQL (`sales_mysql`)**: alternative database for integration scenarios.
	- **MongoDB**: Node.js backend + sales collections.
	- **Neo4j**: graph database for customer–product relationships.

- **Data Warehouse (`DW_VENTAS`, SQL Server)**
	- Star schema with a sales fact table and Time, Customer, Product, and Channel dimensions.
	- Sales target table (`MetaVentas`) linked to `DimCliente` and `DimProducto`.

- **ETL / Integration Layer** (Python)
	- Dedicated ETLs from SQL Server, MySQL, MongoDB, and Neo4j into the DW.
	- BCCR (Central Bank) FX job enriching the Time dimension with daily exchange rate.

- **Data Science Layer**
	- Apriori implementation using `mlxtend` on transactional data in Supabase.
	- Association rule computation and persistence into dedicated PostgreSQL tables.

- **Presentation Layer (Frontends)**
	- **`supabase/frontend`**: React + Vite, connected to Supabase, displays customers, products, orders, and association‑rule‑based recommendations.
	- **`mongoDB/frontend`**: React + Vite (as per `package.json`) to explore data sourced from MongoDB.
	- **`neo4j/client`**: React + Vite consuming the Neo4j backend.

- **APIs / Backends**
	- **Supabase**: exposes REST/SQL on top of PostgreSQL (managed by Supabase).
	- **`mongoDB/backend`**: Node.js/Express REST API for customers, products, and orders (see `src/routes/*Route.js`).
	- **`neo4j/server`**: Node.js/Express API exposing the sales graph.

- **BI Dashboards**
	- Power BI connected to `DW_VENTAS` for sales analysis, target tracking, and recommendation insights.

**Interaction flow:**

1. OLTP systems generate and store sales transactions.
2. ETL processes extract, transform, and load data into the DW (`DW_VENTAS`).
3. Apriori scripts read sales from Supabase, compute rules, and persist them into dedicated tables.
4. Frontends query Supabase and/or APIs to display operational data and recommendations.
5. Power BI connects to the DW for historical analysis and business metrics.

---

## 2. Transactional Databases (OLTP)

### 2.1 Supabase / PostgreSQL

Main DDL script: `supabase/backEnd/db/migrations/creationScript.sql`.

**Core Tables:**

- `cliente`  
	- `cliente_id` (UUID, PK, `uuid_generate_v4()`), `nombre`, `email` (UNIQUE), `genero` (`M`/`F`), `pais`, `fecha_registro`.
- `producto`  
	- `producto_id` (UUID, PK), `sku` (UNIQUE, optional), `nombre`, `categoria`.
- `orden`  
	- `orden_id` (UUID, PK), FK to `cliente`, `fecha` (`TIMESTAMPTZ`), `canal` (`WEB`/`APP`/`PARTNER`), `moneda` (`USD`/`CRC`), `total`.
- `orden_detalle`  
	- `orden_detalle_id` (UUID, PK), FKs to `orden` and `producto`, `cantidad`, `precio_unit`.

**Integrity & Performance:**

- Foreign keys:
	- `orden.cliente_id → cliente.cliente_id`
	- `orden_detalle.orden_id → orden.orden_id`
	- `orden_detalle.producto_id → producto.producto_id`
- Indexes for analytics and Apriori:
	- `CREATE INDEX ix_orden_fecha ON orden(fecha);`
	- `CREATE INDEX ix_detalle_producto ON orden_detalle(producto_id);`

**Apriori Tables in PostgreSQL:**

- `itemset` (frequent itemsets)
	- `itemset_id` (UUID, PK), `soporte` (NUMERIC), `tamano` (INT).
- `itemset_item` (products per itemset)
	- Composite PK (`itemset_id`, `producto_id`).
- `association_rule` (association rules)
	- `rule_id` (UUID, PK), FK to `itemset`, `soporte`, `confianza`, `lift`, `active` (soft delete), `deleted_at`.
- `rule_antecedente` / `rule_consecuente`
	- Many‑to‑many relationships between rules and products for antecedent and consequent sides.

### 2.2 SQL Server – `ventas_ms`

Scripts and utilities under `sql server/`:

- `ScriptCreación.sql`: defines transactional tables `Cliente`, `Producto`, `Orden`, `OrdenDetalle` (conceptually aligned with the Supabase model).
- `populate_db.py`: generates synthetic data (Faker), ~420 records per table.

**Typical usage:**

- Referential integrity enforced via FKs between customer, product, order, and order detail.
- Business constraints (e.g., positive quantities only, unique emails).

### 2.3 MySQL – `sales_mysql`

Content under `mysql/`:

- `ScriptCreaciónMySQL.sql`: defines tables equivalent to `Cliente`, `Producto`, `Orden`, `OrdenDetalle`.
- `populate_mysql.py`: populates MySQL with test data.

### 2.4 MongoDB

Backend under `mongoDB/backend` (Node.js/Express) with frontend in `mongoDB/frontend`.

- Models in `mongoDB/backend/src/models/*.js` for `cliente`, `producto`, and `orden`.
- REST routes in `mongoDB/backend/src/routes/*Route.js`.
- Python ETL `mongoDB/backend/data/etl.py` to extract data from MongoDB and send it to the DW.

### 2.5 Neo4j

Folder `neo4j/`:

- `llenado.cypher`: creates customer, product, and order nodes and relationships (e.g. `COMPRO`, `PERTENECE_A`), with unique constraints on SKUs, IDs, and emails.
- Main database: `ventas`.

This graph‑oriented database is used for advanced relational analysis and as an additional source to the DW.

---

## 3. Data Warehouse (DW_VENTAS)

DDL script: `dw/ScriptCreaciónDW.sql`.

### 3.1 Dimensional Model (Star Schema)

- **Dimensions:**
	- `DimTiempo` (`IdTiempo` INT IDENTITY, `Anio`, `Mes`, `Dia`, `Fecha`, `Semana`, `DiaSemana`, `TipoCambio`).
	- `DimCliente` (`IdCliente` INT IDENTITY, `Nombre`, `Email`, `Genero`, `Pais`, `FechaCreacion`).
	- `DimProducto` (`IdProducto` INT IDENTITY, `SKU`, `Nombre`, `Categoria`).
	- `DimCanal` (`IdCanal` INT IDENTITY, `Nombre`).

- **Fact Table:**
	- `FactVentas` (`IdFactVentas` INT IDENTITY PK) with FKs to `DimTiempo`, `DimProducto`, `DimCliente`, `DimCanal`.
	- Measures: `TotalVentas`, `Cantidad`, `Precio`.

- **Targets:**
	- `MetaVentas` with FKs to `DimProducto` and `DimCliente` and columns `Anio`, `Mes`, `MetaUSD`.

- **SKU Equivalences:**
	- `Equivalencias` mapping `SKU`, `CodigoMongo`, `CodigoAlt` across heterogeneous sources.

### 3.2 Surrogate Keys and Time

- All dimensions use surrogate keys (`INT IDENTITY`) to decouple the DW from source IDs.
- `DimTiempo` stores one row per date and includes `TipoCambio` (FX) per day.
- Job `dw/job/bccr_exchange_rate.py` populates `DimTiempo.TipoCambio` using BCCR FX for ~3 years of history.

### 3.3 Sales Targets Population

Script: `dw/LlenadoMetaVentas.sql`.

- Computes monthly targets per `IdProducto`–`IdCliente`–`Year`–`Month`.
- Base formula: target ≈ 80% of historical average sales for that combination, with a variability factor of 0.9–1.1.
- Restricted to the first 50 products and 50 customers to keep volume manageable.

### 3.4 Design Rationale

- Star schema to optimize analytical queries (scans on `FactVentas` plus joins to denormalized dimensions).
- Controlled denormalization in dimensions (e.g., `Pais`, `Categoria`) to simplify reporting.
- `Equivalencias` enables integrating SKUs from MongoDB, SQL Server, MySQL, and Supabase.

---

## 4. ETL / ELT Process

### 4.1 Extract

- **Supabase/PostgreSQL**
	- Uses Supabase REST APIs (`/rest/v1/orden`, `/rest/v1/orden_detalle`, `/rest/v1/producto`) via `requests`.
	- Authenticated with `SUPABASE_SERVICE_ROLE_KEY` and paginated using `limit`/`offset`.

- **SQL Server** (`sql server/ETL_SQLSERVER_TO_DW.py`)
	- Connects via `pyodbc` using parameters from `env.txt`.
	- Reads `Cliente`, `Producto`, `Orden`, and `OrdenDetalle` from `ventas_ms`.

- **MySQL** (`mysql/ETL_MYSQL_TO_DW.py`)
	- Connects via `mysql-connector` (or equivalent, defined in `requirements_mysql.txt`).

- **MongoDB** (`mongoDB/backend/data/etl.py`)
	- Reads from Mongo collections and normalizes documents into tabular records.

- **Neo4j** (`neo4j/ETL_NEO4J.py`)
	- Uses the `neo4j` driver.
	- Executes Cypher queries to retrieve customer–product–order patterns.

### 4.2 Transform

Transformations follow these principles:

- Cleaning & typing:
	- Converting dates to standard `DATE`/`DATETIME` types.
	- Normalizing currencies (with FX from BCCR used later in the flow).
- Validation:
	- Filtering out rows with negative or null quantities.
	- Enforcing mandatory keys (customer, product, date).
- Enrichment:
	- Joining `DimTiempo` to attach `TipoCambio`.
	- Computing `TotalVentas = Cantidad * Precio` when appropriate.
- SKU integration:
	- Using `Equivalencias` to map codes across systems.

Most transformations are implemented in Python using `pandas`, combined with native SQL when it is more efficient.

### 4.3 Load

- Loading into `DW_VENTAS` using batch inserts into:
	- `DimCliente`, `DimProducto`, `DimCanal`, `DimTiempo`.
	- `FactVentas` and `MetaVentas`.
- Performance considerations:
	- Batch inserts instead of row‑by‑row inserts.
	- Indexes created or rebuilt after large bulk loads where appropriate.
- Duplicates handling:
	- De‑duplication based on business keys (customer+email, product+sku, date+order).
	- `Equivalencias` ensures 1‑to‑1 mappings between codes.

### 4.4 FX Job (BCCR)

Script: `dw/job/bccr_exchange_rate.py`.

- Downloads daily FX rates for the last 3 years from BCCR.
- Inserts or updates `TipoCambio` in `DimTiempo`.
- Provides commands for scheduling and removing the job:

```powershell
# Install dependencies (generic example)
python -m venv .venv
\.venv\Scripts\activate
pip install requests pyodbc python-dotenv

# Populate FX data
python bccr_exchange_rate.py populate

# Schedule daily job (e.g., 05:00)
python bccr_exchange_rate.py scheduler 05:00

# Remove job
python bccr_exchange_rate.py remove-scheduler
```

---

## 5. Data Science: Apriori and Association Rules

Key scripts under `supabase/backEnd/db/apriori`:

- `apriori.py`: main pipeline.
- `insertapriori.py`: persists results into Supabase Apriori tables.
- `generarevision.py`: generates a human‑readable report (`reglas_revision.txt`).

### 5.1 Sales Dataset

- Source: `orden` and `orden_detalle` tables in Supabase/PostgreSQL.
- Each transaction is modeled as a set of products per `orden_id`.

### 5.2 Data Preparation

1. Extract `orden`, `orden_detalle`, and `producto` via REST.
2. Build a table with `transaction_id` and `item` (`producto_id`).
3. Transform into **one‑hot encoding**: transaction × product matrix with boolean values.

### 5.3 Metrics

Using `mlxtend.frequent_patterns`:

<<<<<<< HEAD
- **Support ($support$)**
	- $support(X) = \frac{\text{# transactions containing } X}{\text{# total transactions}}$.
- **Confidence ($confidence$)**
=======
- **Soporte ($support$)**
	- $support(X) = \frac{\text{transacciones que contienen X}}{\text{transacciones totales}}$
- **Confianza ($confidence$)**
>>>>>>> 493f652826bb3d822495b952cef7073499cd6b0a
	- $confidence(X \Rightarrow Y) = \frac{support(X \cup Y)}{support(X)}$.
- **Lift**
	- $lift(X \Rightarrow Y) = \frac{confidence(X \Rightarrow Y)}{support(Y)}$.

Configured parameters in `apriori.py`:

- `MIN_SUPPORT = 0.015` (1.5% of transactions).  
- `MIN_CONFIDENCE = 0.3`.

### 5.4 Algorithm & Optimizations

- Uses the **Apriori** algorithm from `mlxtend` on the one‑hot matrix.
- Post‑processing includes:
	- Adding a `length` column (itemset size) to prioritize larger itemsets.
	- Mapping product IDs to names and SKUs for readable reports.
	- Deduplicating rules by exact (antecedent, consequent) pair, keeping the best rule.
	- Expanding each rule into atomic antecedent → consequent pairs to simplify frontend consumption.

### 5.5 Rule Persistence

- Rules are stored in `itemset`, `itemset_item`, `association_rule`, `rule_antecedente`, `rule_consecuente` in Supabase.
- `association_rule.active` enables soft deletes; inactive rules are excluded from recommendations.

### 5.6 Business Use Cases

- **Product recommendations**: "Customers who bought X also bought Y".
- **Cross‑selling and up‑selling** in the frontend (suggestions on order and product detail views).
- **Assortment optimization**: analysis of frequently co‑purchased product combinations.

---

## 6. Power BI Dashboards

On top of `DW_VENTAS`, a Power BI model is proposed using the SQL Server connector:

- **Core Metrics:**
	- Total sales (`TotalVentas`) by day, month, and year.
	- Units sold (`Cantidad`).
	- Target attainment vs. `MetaVentas.MetaUSD`.

- **Suggested KPIs:**
	- % Target attainment by customer, product, and channel.
	- Average ticket.
	- Product mix by segment.

- **Typical Visuals:**
	- Time series using `DimTiempo`.
	- Slicers by `DimCliente.Pais`, `DimProducto.Categoria`, `DimCanal.Nombre`.
	- Target vs. actual dashboards (traffic‑light style cards).

**Using the PBIX file (not included in this repo):**

1. Open Power BI Desktop.
2. Connect to SQL Server → database `DW_VENTAS`.
3. Import `FactVentas`, `DimTiempo`, `DimCliente`, `DimProducto`, `DimCanal`, `MetaVentas`.
4. Create relationships according to DW foreign keys.
5. Publish the report or share the `.pbix` file within the organization.

---

## 7. Web Pages and Interfaces

### 7.1 Supabase Frontend (`supabase/frontend`)

- **Stack:** React + Vite, `@supabase/supabase-js`.
- **Core features:**
	- List and detail views for **customers**, **products**, and **orders**.
	- **Recommendations** module consuming `association_rule` filtered by `active = true`.
- **User flow:**
	1. User lands on the home page (`App.jsx`) and selects a view (Customers, Products, Orders).
	2. Data is fetched directly from Supabase using `src/services/api.js`.
	3. On product/order views, the user sees recommendations based on Apriori rules.

### 7.2 MongoDB Frontend (`mongoDB/frontend`)

- React + Vite, consuming `mongoDB/backend`.
- Allows browsing customer, product, and order collections.

### 7.3 Neo4j Client (`neo4j/client`)

- React + Vite, consuming `neo4j/server`.
- Exposes graph‑based queries (e.g., products related to a given customer).

> Note: These UIs are designed as demonstration tools to showcase data integration rather than as final production‑grade applications.

---

## 8. Use Cases and Benefits

**Business Problem:**

Retail and e‑commerce companies often need to consolidate sales data spread across multiple systems and derive actionable insights (recommendations, target analysis, customer behavior).

**Target Users:**

- Business and BI analysts.
- Data engineering teams.
- Product managers and marketing.

**Value Proposition:**

- Unified, multi‑channel view of sales in a central DW.
- Recommendation engine based on association rules.
- Reusable infrastructure for integrating new data sources.
- Solid foundation for building performance dashboards and advanced analytics.

**Architecture Justification:**

- Clear separation between OLTP and OLAP using a dimensional DW.
- Industry‑standard technologies (SQL Server, PostgreSQL, Python, React, Power BI).
- Easy to onboard new sources (MongoDB, Neo4j) via the equivalence table and modular ETLs.

---

## 9. Installation and Execution Guide

### 9.1 General Requirements

- **OS:** Windows 10/11 (validated) or equivalent.
- **Python:** 3.10+ recommended.
- **Node.js:** v18+.
- **SQL Server** with ability to create `DW_VENTAS` and `ventas_ms`.
- **MySQL** (optional) for `sales_mysql`.
- **MongoDB** (optional) and **Neo4j Desktop** (optional).

Recommended Python virtual environment at the project root:

```powershell
cd Data_Enviroment
python -m venv .venv
\.venv\Scripts\activate
```

### 9.2 Data Warehouse and FX Job

1. Create the DW in SQL Server by running `dw/ScriptCreaciónDW.sql`.
2. Optionally populate sales targets via `dw/LlenadoMetaVentas.sql`.
3. Configure `.env` for the BCCR job (see `dw/job/env.txt` as reference).
4. Install dependencies and run `dw/job/bccr_exchange_rate.py` as described in the ETL section.

### 9.3 SQL Server – `ventas_ms`

```powershell
cd "sql server"
python -m pip install -r .\requirements.txt
python .\populate_db.py --server localhost --database ventas_ms --trusted

# Run ETL into the DW
python .\ETL_SQLSERVER_TO_DW.py
```

### 9.4 MySQL – `sales_mysql`

```powershell
cd mysql
python -m pip install -r .\requirements_mysql.txt
python .\populate_mysql.py --host localhost --port 3306 --database sales_mysql --user root --password "1234"

# Run ETL into the DW
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

1. Create database `ventas` in Neo4j.
2. Run `llenado.cypher` against the `ventas` database.
3. Configure `.env` under `neo4j/server` and at the Neo4j project root.

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

### 9.7 Supabase – Apriori Backend and Frontend

**Apriori Backend:**

```powershell
cd supabase\backEnd\db\apriori
python .\apriori.py
python .\generarevision.py
```

Requires `supabase/backEnd/.env.local`:

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

**Supabase Frontend:**

```powershell
cd supabase\frontend
npm install
npm run dev
```

Requires `supabase/frontend/.env.local`:

```env
VITE_SUPABASE_URL=...
VITE_SUPABASE_ANON_KEY=...
```

### 9.8 Power BI

1. Make sure `DW_VENTAS` is populated.
2. Open Power BI Desktop → Get data → SQL Server.
3. Connect to the SQL Server instance and select `DW_VENTAS`.
4. Load dimensional and fact tables and build the model.

---

## 10. Technologies

### Languages

- Python (ETL, Apriori, utilities).
- SQL (PostgreSQL, T‑SQL, MySQL).
- JavaScript / TypeScript (Node.js, React, Vite).

### Frameworks & Libraries

- **Backend:** Node.js, Express, Supabase (PostgREST), Neo4j driver.
- **Frontend:** React, Vite, `@supabase/supabase-js`.
- **Data Engineering / Science:** `pandas`, `mlxtend`, `requests`, `python-dotenv`, `pyodbc`.

### Databases

- PostgreSQL (Supabase).
- SQL Server (`ventas_ms`, `DW_VENTAS`).
- MySQL (`sales_mysql`).
- MongoDB.
- Neo4j.

### BI & Tools

- Power BI Desktop.
- Neo4j Desktop.
- Supabase Dashboard.

---

<<<<<<< HEAD
This repository is designed to reflect the work of a professional data engineering team: clear separation of layers, documented ETL pipelines, an explicit dimensional model, and an end‑to‑end integration ready for technical demos or academic review.
=======
Este repositorio está diseñado para reflejar el trabajo de un equipo de ingeniería de datos profesional: separación clara de capas, documentación de ETLs, modelo dimensional explícito y una integración end‑to‑end lista para demo técnica o revisión académica.
>>>>>>> 493f652826bb3d822495b952cef7073499cd6b0a
