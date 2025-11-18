# Tipos de Cambio BCCR y Dim Tiempo

### Paso 1: Instalar dependencias
```bash
# Crear entorno virtual, creo que en windows no hace falta
python3 -m venv venv
source venv/bin/activate  # En Mac/Linux
# venv\Scripts\activate    # En Windows

# Instalar dependencias
pip install requests pyodbc python-dotenv
```

### Paso 2: Configurar variables de entorno
Crear archivo `.env` con:
```env
# Credenciales BCCR (OBLIGATORIO)
BCCR_USER=tu_email@gmail.com
BCCR_PASSWORD=tu_token_aqui

# Conexión SQL Server
serverenv=localhost
databaseenv=DW_VENTAS
usernameenv=sa
passwordenv=tu_password_aqui

# Configuración del Scheduler (OPCIONAL)
SCHEDULE_HOUR=5        # Hora de ejecución (0-23), por defecto: 5
SCHEDULE_MINUTE=0      # Minuto de ejecución (0-59), por defecto: 0
```


## Para usarlo

### Comandos Disponibles

#### 1. Probar conexión a base de datos
```bash
python3 bccr_exchange_rate.py test
```
**Salida esperada:**
```
2025-11-17 22:36:58,780 - INFO - Probando conexión a base de datos...
2025-11-17 22:36:58,834 - INFO - Conexión a base de datos exitosa
2025-11-17 22:36:58,835 - INFO - Conexión exitosa. Registros en DimTiempo: X
```

#### 2. Poblar datos históricos (3 años)
```bash
python3 bccr_exchange_rate.py populate
```
**Proceso:**
- Obtiene datos desde hace 3 años hasta hoy
- Procesa en chunks de 6 meses para evitar timeouts
- Inserta/actualiza registros en `DimTiempo`
- Pausa de 2 segundos entre chunks

#### 3. Actualización diaria manual
```bash
python3 bccr_exchange_rate.py update
```
**Función:**
- Obtiene el tipo de cambio más reciente disponible
- Actualiza la tabla `DimTiempo` para la fecha correspondiente
Es de prueba, mejor no la usen, solo traemos los históricos y luego el programable.

#### 4. Programador automático (PROGRAMABLE)

**Opción A: Usar configuración del archivo .env**
```bash
python3 bccr_exchange_rate.py scheduler
```

**Opción B: Especificar hora al ejecutar**
```bash
# Ejecutar a las 5:30 AM
python3 bccr_exchange_rate.py scheduler 05:30

# Ejecutar a las 8:00 AM  
python3 bccr_exchange_rate.py scheduler 8

# Ejecutar a las 2:15 PM
python3 bccr_exchange_rate.py scheduler 14:15
```

**Comportamiento:**
- Ejecuta en background
- Verifica cada 30 segundos la hora
- Ejecuta actualización automática a la hora programada
- Solo ejecuta una vez por día
- Se detiene con `Ctrl+C`

## 🔧 Detalles Técnicos

### API BCCR
- **Protocolo**: SOAP XML
- **Endpoint**: `https://gee.bccr.fi.cr/Indicadores/Suscripciones/WS/wsindicadoreseconomicos.asmx`
- **Indicador**: 317 (Tipo de cambio compra USD)
- **Autenticación**: Token en XML SOAP

### Base de Datos
- **Motor**: SQL Server
- **Drivers**: Detección automática (ODBC 17/18)
- **Tabla**: DimTiempo con campo TipoCambio
- **Operaciones**: INSERT/UPDATE automático según fecha existente
