# Data_Enviroment

## DW
### Diseño
inserte foto del diseño

### Job y Población de Tipo de Cambio
Para llenar DimTiempo con sus respectivos tipos de cambio por día desde hace 3 años, traemos la información desde el BCCR. Esto se hace previo a correr los etls.
Asumiendo que se tiene el .env con sus debidas configuraciones:

Instalamos dependencias
```bash
# Crear entorno virtual, en windows no hace falta pueden solo instalarlo 
python3 -m venv venv
source venv/bin/activate  # mac
# venv\Scripts\activate    # windows

# Instalar dependencias
pip install requests pyodbc python-dotenv
```

Para poblar de datos 
```bash
python3 bccr_exchange_rate.py populate
```

Para hacer el job, si no se pone nada en default está para las 5am, pero acepta un parámetro HH:MM para escoger (recuerden que es 24h!)
```bash
python3 bccr_exchange_rate.py scheduler 
```

Para ya botar el job después 
```bash
python3 bccr_exchange_rate.py remove-scheduler 
```



## MongoDB
Para prender el backend
```bash
cd mongoDB/backend
npm i
npm start
```

Para prender el frontend
```bash
cd mongoDB/frontend
npm i
npm run dev
```

Para ejecutar el etl primero se deben instalar las dependencias, desde Mac hay que recordar primero activar el venv
```bash
cd mongoDB/backend/data
pip install -r requirements_etl.txt
```
Y ejecutamos el etl
```bash
python etl.py
```

## MySQL

## Neo4J

## SQL server

## Supabase