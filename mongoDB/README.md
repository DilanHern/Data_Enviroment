# MongoDB

## Backend
```bash
cd mongoDB/backend
npm i
npm start
```

## ETL a Data Warehouse
Para transferir datos de MongoDB al Data Warehouse:

### Dependencias Python
```bash
cd mongoDB/backend/data
pip install -r requirements_etl.txt
```

### Ejecutar ETL
```bash
python etl.py
```

## Frontend
```bash
cd mongoDB/frontend
npm i
npm run dev
```