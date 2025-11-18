import requests
import xml.etree.ElementTree as ET
import pyodbc
import datetime
import os
import time
import logging
import platform
from dotenv import load_dotenv

# en las variables de entorno está todo lo del sql server y bccr
load_dotenv()


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BCCRExchangeRate:
    def __init__(self):
        
        self.bccr_user = os.getenv("BCCR_USER")
        self.bccr_password = os.getenv("BCCR_PASSWORD")

        
        self.server = os.getenv("serverenv", "localhost")
        self.database = os.getenv("databaseenv", "DW_VENTAS")
        self.username = os.getenv("usernameenv")
        self.password = os.getenv("passwordenv")
     
    
        if platform.system() == "Windows":
            self.driver = "ODBC Driver 17 for SQL Server"
        else:
            self.driver = "ODBC Driver 18 for SQL Server"
        
        
        self.base_url = "https://gee.bccr.fi.cr/Indicadores/Suscripciones/WS/wsindicadoreseconomicos.asmx"
        self.indicador = "317"  # compra del dolar
    
    def get_exchange_rate_data(self, start_date, end_date):

       
        soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <ObtenerIndicadoresEconomicosXML xmlns="http://ws.sdde.bccr.fi.cr">
      <Indicador>{self.indicador}</Indicador>
      <FechaInicio>{start_date.strftime('%d/%m/%Y')}</FechaInicio>
      <FechaFinal>{end_date.strftime('%d/%m/%Y')}</FechaFinal>
      <Nombre>{self.bccr_user}</Nombre>
      <SubNiveles>N</SubNiveles>
      <CorreoElectronico>{self.bccr_user}</CorreoElectronico>
      <Token>{self.bccr_password}</Token>
    </ObtenerIndicadoresEconomicosXML>
  </soap:Body>
</soap:Envelope>"""

        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': '"http://ws.sdde.bccr.fi.cr/ObtenerIndicadoresEconomicosXML"'
        }
        
        logging.info(f"Consultando BCCR desde {start_date} hasta {end_date}")
        
        try:
            response = requests.post(self.base_url, data=soap_body, headers=headers)
            response.raise_for_status()
            
            # Parsear XML response SOAP
            root = ET.fromstring(response.content)
            
            # Buscar el resultado XML dentro del SOAP
            soap_result = root.find('.//{http://ws.sdde.bccr.fi.cr}ObtenerIndicadoresEconomicosXMLResult')
            
            if soap_result is not None and soap_result.text:
               
                inner_xml = soap_result.text
                inner_root = ET.fromstring(inner_xml)
                
                
                exchange_rates = []
                for datos in inner_root.findall('.//INGC011_CAT_INDICADORECONOMIC'):
                    fecha_str = datos.find('DES_FECHA').text if datos.find('DES_FECHA') is not None else None
                    valor_str = datos.find('NUM_VALOR').text if datos.find('NUM_VALOR') is not None else None
                    
                    if fecha_str and valor_str:
                        try:
                            fecha = datetime.datetime.strptime(fecha_str, '%Y-%m-%dT%H:%M:%S%z').date()
                            valor = float(valor_str)
                            exchange_rates.append({'fecha': fecha, 'tipo_cambio': valor})
                        except ValueError as e:
                            logging.warning(f"Error parsing date/value: {e}")
                            continue
                
                logging.info(f"Obtenidos {len(exchange_rates)} registros de tipos de cambio")
                return exchange_rates
            else:
                logging.warning("No se encontró resultado XML en la respuesta SOAP")
                return []
        
        except requests.RequestException as e:
            logging.error(f"Error al obtener datos del BCCR: {e}")
            return []
        except ET.ParseError as e:
            logging.error(f"Error al parsear XML: {e}")
            return []
    
    def connect_to_database(self):
        try:
            if self.username and self.password:
                
                connection_string = (
                    f'DRIVER={{{self.driver}}};'
                    f'SERVER={self.server};'
                    f'DATABASE={self.database};'
                    f'UID={self.username};'
                    f'PWD={self.password};'
                    'TrustServerCertificate=yes;'
                )
                logging.info(f"Conectando a SQL Server: {self.server}/{self.database} con usuario {self.username}")
            else:
                
                connection_string = (
                    f'DRIVER={{{self.driver}}};'
                    f'SERVER={self.server};'
                    f'DATABASE={self.database};'
                    'Trusted_Connection=yes;'
                    'TrustServerCertificate=yes;'
                )
                logging.info(f"Conectando a SQL Server: {self.server}/{self.database} con autenticación Windows")
            
            connection = pyodbc.connect(connection_string)
            logging.info("Conexión a base de datos exitosa")
            return connection
        except pyodbc.Error as e:
            logging.error(f"Error conectando a la base de datos: {e}")
            return None
    
    def update_dim_tiempo_exchange_rate(self, fecha, tipo_cambio):
        connection = self.connect_to_database()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            
            
            cursor.execute("SELECT IdTiempo FROM DimTiempo WHERE Fecha = ?", fecha)
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute(
                    "UPDATE DimTiempo SET TipoCambio = ? WHERE Fecha = ?",
                    tipo_cambio, fecha
                )
                logging.info(f"Actualizado tipo de cambio para {fecha}: {tipo_cambio}")
            else:
                cursor.execute("""
                    INSERT INTO DimTiempo (Anio, Mes, Dia, Fecha, Semana, DiaSemana, TipoCambio)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, 
                    fecha.year, fecha.month, fecha.day, fecha, 
                    fecha.isocalendar()[1], fecha.strftime('%A'), tipo_cambio
                )
                logging.info(f"Insertado nuevo registro para {fecha}: {tipo_cambio}")
            
            connection.commit()
            return True
            
        except pyodbc.Error as e:
            logging.error(f"Error actualizando base de datos: {e}")
            connection.rollback()
            return False
        finally:
            connection.close()
    
    def populate_historical_data(self):

        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=3*365)  # 3 años antes 
        
        logging.info(f"Obteniendo datos históricos desde {start_date} hasta {end_date}")
        
        # Obtener datos de 6 meses en 6 meses para que no se caiga
        current_date = start_date
        
        while current_date < end_date:
            chunk_end = min(current_date + datetime.timedelta(days=180), end_date)
            
            logging.info(f"Procesando chunk: {current_date} a {chunk_end}")
            exchange_rates = self.get_exchange_rate_data(current_date, chunk_end)
            
            for rate_data in exchange_rates:
                self.update_dim_tiempo_exchange_rate(
                    rate_data['fecha'], 
                    rate_data['tipo_cambio']
                )
            
            current_date = chunk_end + datetime.timedelta(days=1)
            time.sleep(2)  
        
        logging.info("Población de datos históricos completada")
    
    def update_current_rate(self):
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        
        logging.info(f"Actualizando tipo de cambio para {today}")
        
        exchange_rates = self.get_exchange_rate_data(yesterday, today)
        
        if exchange_rates:
            latest_rate = max(exchange_rates, key=lambda x: x['fecha'])
            self.update_dim_tiempo_exchange_rate(
                latest_rate['fecha'], 
                latest_rate['tipo_cambio']
            )
            logging.info(f"Tipo de cambio actualizado: {latest_rate['tipo_cambio']}")
        else:
            logging.warning("No se pudo obtener el tipo de cambio actual")
    
    def start_scheduler(self, custom_hour=None, custom_minute=None):

        import subprocess
        import sys
        
 
        target_hour = custom_hour if custom_hour is not None else 5  # 5:00 am si no se indica lo contrario
        target_minute = custom_minute if custom_minute is not None else 0
        
       
        if not (0 <= target_hour <= 23):
            logging.error(f"Hora inválida: {target_hour}. Debe estar entre 0-23")
            return
        if not (0 <= target_minute <= 59):
            logging.error(f"Minuto inválido: {target_minute}. Debe estar entre 0-59")
            return
        

        script_path = os.path.abspath(__file__)
        python_path = sys.executable
        
        if platform.system() == "Windows":
            self._create_windows_task(target_hour, target_minute, python_path, script_path)
        else:
            self._create_unix_cron(target_hour, target_minute, python_path, script_path)
    
    def _create_windows_task(self, hour, minute, python_path, script_path):
        import subprocess
        
        task_name = "BCCR_Exchange_Rate_Update"
        
        try:
            # si ya exsiste la borra
            subprocess.run([
                "schtasks", "/delete", "/tn", task_name, "/f"
            ], capture_output=True, text=True)
            
            # nueva tarea 
            command = f'"{python_path}" "{script_path}" update-current'
            time_str = f"{hour:02d}:{minute:02d}"
            
            result = subprocess.run([
                "schtasks", "/create",
                "/tn", task_name,
                "/tr", command,
                "/sc", "daily",
                "/st", time_str,
                "/ru", "SYSTEM",
                "/rl", "HIGHEST"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logging.info(f" Job creado para las {hour:02d}:{minute:02d}")

            else:
                logging.error(f"Error creando tarea de Windows: {result.stderr}")
                
        except Exception as e:
            logging.error(f"Error configurando Task Scheduler: {e}")
    
    def _create_unix_cron(self, hour, minute, python_path, script_path):
        import subprocess
        import tempfile
        
        try:
            # ver los jobs que tengo
            result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
            current_cron = result.stdout if result.returncode == 0 else ""
            
            # crear nueva línea
            cron_line = f"{minute} {hour} * * * {python_path} {script_path} update-current\n"
            cron_comment = "# BCCR Exchange Rate Update\n"
            
            # quitamos jobs que corran el mismo script
            lines = current_cron.split('\n')
            filtered_lines = [line for line in lines 
                            if not (script_path in line and 'update-current' in line)]
            
            #  nuevo job
            new_cron = '\n'.join(filtered_lines).strip()
            if new_cron:
                new_cron += '\n'
            new_cron += cron_comment + cron_line
            
            #  nuevo crontab
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cron') as f:
                f.write(new_cron)
                temp_file = f.name
            
            result = subprocess.run(["crontab", temp_file], capture_output=True, text=True)
            os.unlink(temp_file) 
            
            if result.returncode == 0:
                logging.info(f" Job creado para las {hour:02d}:{minute:02d}")
            else:
                logging.error(f"Error creando cron job: {result.stderr}")
                
        except Exception as e:
            logging.error(f"Error configurando cron: {e}")
    
    def remove_scheduler(self):
        if platform.system() == "Windows":
            self._remove_windows_task()
        else:
            self._remove_unix_cron()
    
    def _remove_windows_task(self):
        import subprocess
        
        task_name = "BCCR_Exchange_Rate_Update"
        
        try:
            result = subprocess.run([
                "schtasks", "/delete", "/tn", task_name, "/f"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logging.info(f" Tarea de Windows eliminada: '{task_name}'")
            else:
                logging.warning(f"La tarea '{task_name}' no existía o no se pudo eliminar")
                
        except Exception as e:
            logging.error(f"Error eliminando tarea de Windows: {e}")
    
    def _remove_unix_cron(self):
        import subprocess
        import tempfile
        
        try:
            result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
            current_cron = result.stdout if result.returncode == 0 else ""
            
            lines = current_cron.split('\n')
            filtered_lines = []
            script_path = os.path.abspath(__file__)
            
            for line in lines:
                if not (script_path in line and 'update-current' in line):
                    if not line.strip().startswith('# BCCR Exchange Rate Update'):
                        filtered_lines.append(line)
            
            new_cron = '\n'.join(filtered_lines).strip()
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cron') as f:
                f.write(new_cron + '\n' if new_cron else '')
                temp_file = f.name
            
            result = subprocess.run(["crontab", temp_file], capture_output=True, text=True)
            os.unlink(temp_file)
            
            if result.returncode == 0:
                logging.info(f" Cron job de BCCR eliminado")
            else:
                logging.error(f"Error eliminando cron job: {result.stderr}")
                
        except Exception as e:
            logging.error(f"Error eliminando cron: {e}")

def main():

    import sys
    
    bccr = BCCRExchangeRate()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "populate":
            bccr.populate_historical_data()
        elif command == "update-current":
            bccr.update_current_rate()
        elif command == "scheduler":
            if len(sys.argv) >= 3:
                time_arg = sys.argv[2]
                try:
                    if ":" in time_arg:
                        hour, minute = map(int, time_arg.split(":"))
                        bccr.start_scheduler(custom_hour=hour, custom_minute=minute)
                    else:
                        print("Use formato HH:MM")
                except ValueError:
                    print("Use formato HH:MM")
            else:
                bccr.start_scheduler()
        elif command == "remove-scheduler":
            bccr.remove_scheduler()
        else:
            print("Comandos disponibles: populate, scheduler, remove-scheduler")
    else:
        print("  python bccr_exchange_rate.py populate")
        print("  python bccr_exchange_rate.py scheduler") # por default 5 am
        print("  python bccr_exchange_rate.py scheduler HH:MM") 
        print("  python bccr_exchange_rate.py remove-scheduler")

if __name__ == "__main__":
    main()
