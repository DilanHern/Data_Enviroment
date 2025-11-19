# Tipos de Cambio BCCR y Dim Tiempo

### Instalar dependencias
```bash
# Crear entorno virtual, en windows no hace falta pueden solo instalarlo 
python3 -m venv venv
source venv/bin/activate  # mac
# venv\Scripts\activate    # windows

# Instalar dependencias
pip install requests pyodbc python-dotenv
```

### ojo que hay que tener el .env ya listo!


#### Poblar datos históricos (3 años)
```bash MAC
python3 bccr_exchange_rate.py populate
```
```bash WINDOWS
python bccr_exchange_rate.py populate
```

### Job
```bash MAC
python3 bccr_exchange_rate.py scheduler 
```
```bash WINDOWS se debe de abrir una PowerShell elevada
Start-Process powershell -Verb RunAs 
python bccr_exchange_rate.py scheduler 
```

opcionalmente poner hora en formato HH:MM si se quiere que sea a una hora distinta de las 5am



### Quitar job 
```bash MAC
python3 bccr_exchange_rate.py remove-scheduler 
```
```bash WINDOWS
python bccr_exchange_rate.py remove-scheduler 
```


### Ver mis jobs
Mac:
```bash
crontab -l
```

Windows:
Programador de tareas de Windows
o (consultar la tarea en especifico)
```bash
schtasks /Query /TN "BCCR_Exchange_Rate_Update" /V /FO LIST
```
