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
        
        
        self.schedule_hour = int(os.getenv("SCHEDULE_HOUR", "5"))  # default: 5 AM
        self.schedule_minute = int(os.getenv("SCHEDULE_MINUTE", "0"))  # 5:00
     
    
        if platform.system() == "Windows":
            self.driver = "ODBC Driver 17 for SQL Server"
        else:
            self.driver = "ODBC Driver 18 for SQL Server"
        
        
        self.base_url = "https://gee.bccr.fi.cr/Indicadores/Suscripciones/WS/wsindicadoreseconomicos.asmx"
        self.indicador = "317"  # compra del dolar
    
    def get_exchange_rate_data(self, start_date, end_date):
        """
        Obtiene datos de tipo de cambio del BCCR usando API SOAP
        """
       
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
        """
        Conecta a la base de datos SQL Server usando variables de entorno
        """
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
        """
        Actualiza el tipo de cambio en DimTiempo para una fecha específica
        """
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
        """
        Poblar datos históricos de los últimos 3 años
        """
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
    
    def update_daily_rate(self):
        """
        Actualiza el tipo de cambio del día actual
        """
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
        """
        Job programable que actualiza el tipo de cambio cada día a la hora configurada
        Args:
            custom_hour: Hora personalizada (0-23), si no se especifica usa la configuración
            custom_minute: Minuto personalizado (0-59), si no se especifica usa la configuración
        """
        import threading
        
        
        target_hour = custom_hour if custom_hour is not None else self.schedule_hour
        target_minute = custom_minute if custom_minute is not None else self.schedule_minute
        
    
        if not (0 <= target_hour <= 23):
            logging.error(f"Hora inválida: {target_hour}. Debe estar entre 0-23")
            return
        if not (0 <= target_minute <= 59):
            logging.error(f"Minuto inválido: {target_minute}. Debe estar entre 0-59")
            return
        
        def daily_update():
            last_execution_date = None
            while True:
                now = datetime.datetime.now()
                current_date = now.date()
                
                
                if (now.hour == target_hour and 
                    now.minute == target_minute and 
                    last_execution_date != current_date):
                    
                    logging.info(f"Ejecutando actualización programada ({target_hour:02d}:{target_minute:02d})...")
                    self.update_daily_rate()
                    last_execution_date = current_date
                    time.sleep(60)  
                else:
                    time.sleep(30) 
        
        
        thread = threading.Thread(target=daily_update, daemon=True)
        thread.start()
        
        logging.info(f"Job iniciado. Actualizaciones programadas para las {target_hour:02d}:{target_minute:02d}")
        
        
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            logging.info("Job detenido por el usuario")

    def test_connection(self):
        """
        Prueba la conexión a la base de datos
        """
        logging.info("Probando conexión a base de datos...")
        connection = self.connect_to_database()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("SELECT COUNT(*) FROM DimTiempo")
                count = cursor.fetchone()[0]
                logging.info(f"Conexión exitosa. Registros en DimTiempo: {count}")
                return True
            except Exception as e:
                logging.error(f"Error consultando DimTiempo: {e}")
                return False
            finally:
                connection.close()
        else:
            logging.error("No se pudo conectar a la base de datos")
            return False

def main():
    """
    Función principal
    """
    import sys
    
    bccr = BCCRExchangeRate()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            # Probar conexión a base de datos
            bccr.test_connection()
        elif command == "populate":
            # Poblar datos históricos
            bccr.populate_historical_data()
        elif command == "update":
            # Actualizar tipo de cambio diario
            bccr.update_daily_rate()
        elif command == "scheduler":
            # Iniciar programador (con hora opcional)
            if len(sys.argv) >= 3:
                # Formato: scheduler HH:MM o scheduler HH
                time_arg = sys.argv[2]
                try:
                    if ":" in time_arg:
                        hour, minute = map(int, time_arg.split(":"))
                        bccr.start_scheduler(custom_hour=hour, custom_minute=minute)
                    else:
                        hour = int(time_arg)
                        bccr.start_scheduler(custom_hour=hour, custom_minute=0)
                except ValueError:
                    print("Error: Formato de hora inválido. Use HH:MM o HH")
                    print("Ejemplo: scheduler 05:30 o scheduler 5")
            else:
                bccr.start_scheduler()
        else:
            print("Comandos disponibles: test, populate, update, scheduler")
    else:
        print("Uso:")
        print("  python bccr_exchange_rate.py test                # Probar conexión a base de datos")
        print("  python bccr_exchange_rate.py populate            # Poblar datos históricos (3 años)")
        print("  python bccr_exchange_rate.py update              # Actualizar tipo de cambio actual")
        print("  python bccr_exchange_rate.py scheduler           # Iniciar programador (5 am)")
        print("  python bccr_exchange_rate.py scheduler HH:MM     # Iniciar programador (hora específica)")
        print("  python bccr_exchange_rate.py scheduler HH        # Iniciar programador (hora:00)")

if __name__ == "__main__":
    main()
