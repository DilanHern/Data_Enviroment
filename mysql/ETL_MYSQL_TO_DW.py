"""
ETL para migrar datos de MySQL (sales_mysql) al Data Warehouse (DW_VENTAS)
Basado en la estructura del ETL de SQL Server
- Usa tabla de equivalencias para mapear productos (las equivalencias ya deben estar cargadas)
- Convierte monedas CRC a USD usando tipo de cambio por fecha
- Normaliza géneros y formatos de datos
- Usa log para evitar duplicados en ejecuciones múltiples
"""

import pyodbc
import mysql.connector
import logging
from datetime import datetime
from decimal import Decimal
import platform
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo env.txt
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), 'env.txt'))

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class MySQLToDW_ETL:
    def __init__(self):
        # Configuración de MySQL ORIGEN (sales_mysql)
        self.mysql_host = os.getenv("MYSQL_HOST", "localhost")
        self.mysql_port = int(os.getenv("MYSQL_PORT", "3306"))
        self.mysql_user = os.getenv("MYSQL_USER", "root")
        self.mysql_password = os.getenv("MYSQL_PASSWORD", "")
        self.mysql_database = os.getenv("MYSQL_DATABASE", "sales_mysql")
        
        # Configuración de SQL Server DESTINO (DW_VENTAS)
        self.dw_server = os.getenv("DW_SERVER", "localhost")
        self.dw_database = os.getenv("DW_DATABASE", "DW_VENTAS")
        self.dw_username = os.getenv("DW_USERNAME")
        self.dw_password = os.getenv("DW_PASSWORD")
        
        # Driver según el sistema operativo
        if platform.system() == "Windows":
            self.driver = "ODBC Driver 17 for SQL Server"
        else:
            self.driver = "ODBC Driver 18 for SQL Server"
        
        self.mysql_connection = None
        self.dw_connection = None
        
        # Mapping de género según especificaciones
        self.genero_mapping = {
            'M': 'M',
            'F': 'F',
            'X': 'X'
        }
        
        # Sistema de origen para logging
        self.source_system = 'MYSQL'
        
        # Tipo de cambio por defecto CRC→USD si no se encuentra en la tabla
        self.default_crc_to_usd_rate = 0.0019  # ~520 CRC por USD
    
    def connect_mysql(self):
        """Conecta a la base de datos MySQL origen (sales_mysql)"""
        try:
            self.mysql_connection = mysql.connector.connect(
                host=self.mysql_host,
                port=self.mysql_port,
                user=self.mysql_user,
                password=self.mysql_password,
                database=self.mysql_database
            )
            logging.info(f"Conexión exitosa a MySQL origen: {self.mysql_database}")
        except Exception as e:
            logging.error(f"Error conectando a MySQL origen: {e}")
            raise
    
    def connect_dw(self):
        """Conecta a la base de datos Data Warehouse (DW_VENTAS)"""
        try:
            if self.dw_username and self.dw_password:
                connection_string = (
                    f"DRIVER={{{self.driver}}};"
                    f"SERVER={self.dw_server};"
                    f"DATABASE={self.dw_database};"
                    f"UID={self.dw_username};"
                    f"PWD={self.dw_password};"
                    f"TrustServerCertificate=yes;"
                )
            else:
                # Usar autenticación de Windows
                connection_string = (
                    f"DRIVER={{{self.driver}}};"
                    f"SERVER={self.dw_server};"
                    f"DATABASE={self.dw_database};"
                    f"Trusted_Connection=yes;"
                )
            
            self.dw_connection = pyodbc.connect(connection_string)
            logging.info(f"Conexión exitosa a Data Warehouse: {self.dw_database}")
        except Exception as e:
            logging.error(f"Error conectando a Data Warehouse: {e}")
            raise
    
    def check_if_processed(self, source_key, table_name):
        """
        Verifica si un registro ya fue procesado.
        Retorna True si ya fue procesado, False si no.
        """
        try:
            cursor = self.dw_connection.cursor()
            
            # Para clientes, verificamos por email en DimCliente
            if table_name == 'Cliente':
                query = "SELECT IdCliente FROM DimCliente WHERE Email = ?"
                cursor.execute(query, source_key)
                result = cursor.fetchone()
                return result is not None
            
            # Para productos, verificamos en Equivalencias por CodigoAlt
            elif table_name == 'Producto':
                query = "SELECT Id FROM Equivalencias WHERE CodigoAlt = ?"
                cursor.execute(query, source_key)
                result = cursor.fetchone()
                return result is not None
            
            return False
            
        except Exception as e:
            logging.error(f"Error verificando si fue procesado: {e}")
            return False
    
    def clean_number(self, value_str):
        """
        Limpia un número que viene como string con posibles comas/puntos
        Ejemplos: '1,200.50' → 1200.50, '1200,50' → 1200.50, '1200.50' → 1200.50
        """
        if not value_str:
            return Decimal('0.00')
        
        value_str = str(value_str).strip()
        
        # Si tiene punto Y coma, la coma es separador de miles
        if ',' in value_str and '.' in value_str:
            value_str = value_str.replace(',', '')
        # Si solo tiene coma, es el decimal
        elif ',' in value_str and '.' not in value_str:
            value_str = value_str.replace(',', '.')
        
        try:
            return Decimal(value_str)
        except:
            return Decimal('0.00')
    
    def get_exchange_rate(self, fecha, moneda_origen='CRC', moneda_destino='USD'):
        """
        Obtiene el tipo de cambio para una fecha específica desde DimTiempo.
        Si la moneda origen ya es USD, retorna 1.0
        """
        if moneda_origen == 'USD':
            return Decimal('1.0')
        
        try:
            cursor = self.dw_connection.cursor()
            
            # Buscar tipo de cambio en DimTiempo para esa fecha
            query = "SELECT TOP 1 TipoCambio FROM DimTiempo WHERE Fecha = ?"
            cursor.execute(query, fecha)
            
            result = cursor.fetchone()
            if result and result[0]:
                return Decimal(str(result[0]))
            
            # Si no hay tipo de cambio, usar valor por defecto
            logging.warning(f"No se encontró tipo de cambio para {fecha}, usando tasa por defecto")
            return Decimal(str(self.default_crc_to_usd_rate))
            
        except Exception as e:
            logging.error(f"Error obteniendo tipo de cambio: {e}")
            return Decimal(str(self.default_crc_to_usd_rate))
    
    def get_or_create_cliente(self, cliente_data):
        """
        Obtiene o crea un cliente en DimCliente.
        Usa el email como clave natural para evitar duplicados.
        """
        try:
            cursor = self.dw_connection.cursor()
            
            # Buscar por email
            query = "SELECT IdCliente FROM DimCliente WHERE Email = ?"
            cursor.execute(query, cliente_data['email'])
            result = cursor.fetchone()
            
            if result:
                return result[0]
            
            # Si no existe, crear uno nuevo
            genero_mapeado = self.genero_mapping.get(cliente_data['genero'], 'X')
            
            # Parsear fecha de created_at (viene como 'YYYY-MM-DD')
            fecha_creacion = None
            if cliente_data['created_at']:
                try:
                    fecha_creacion = datetime.strptime(cliente_data['created_at'], '%Y-%m-%d').date()
                except:
                    fecha_creacion = None
            
            insert_query = """
                INSERT INTO DimCliente (Nombre, Email, Genero, Pais, FechaCreacion)
                VALUES (?, ?, ?, ?, ?)
            """
            cursor.execute(insert_query, (
                cliente_data['nombre'],
                cliente_data['email'],
                genero_mapeado,
                cliente_data['pais'],
                fecha_creacion
            ))
            
            cursor.execute("SELECT @@IDENTITY")
            cliente_id = cursor.fetchone()[0]
            self.dw_connection.commit()
            
            logging.info(f"Cliente creado: {cliente_data['email']} - ID: {cliente_id}")
            return int(cliente_id)
            
        except Exception as e:
            logging.error(f"Error procesando cliente: {e}")
            return None
    
    def process_equivalencias_and_get_producto(self, producto_data):
        """
        Procesa equivalencias y obtiene/crea un producto en DimProducto.
        Usa la tabla Equivalencias para mapear codigo_alt a SKU.
        """
        try:
            cursor = self.dw_connection.cursor()
            
            codigo_alt = producto_data['codigo_alt']
            nombre = producto_data['nombre']
            categoria = producto_data['categoria']
            
            # Buscar si ya existe una equivalencia para este codigo_alt
            query = "SELECT Id, SKU, CodigoAlt FROM Equivalencias WHERE CodigoAlt = ?"
            cursor.execute(query, codigo_alt)
            result = cursor.fetchone()
            
            if result:
                equivalencia_id = result[0]
                sku_oficial = result[1]
                logging.info(f"Encontrada equivalencia existente para CodigoAlt: {codigo_alt} -> SKU: {sku_oficial}")
                
                # Buscar el producto por SKU oficial
                query = "SELECT IdProducto FROM DimProducto WHERE SKU = ?"
                cursor.execute(query, sku_oficial)
                result = cursor.fetchone()
                if result:
                    producto_id = result[0]
                    logging.info(f"Encontrado producto existente - ID: {producto_id}")
                    return int(producto_id)
            
            # Si no existe equivalencia, crear una nueva solo con CodigoAlt
            if not result:
                insert_query = """
                    INSERT INTO Equivalencias (SKU, CodigoMongo, CodigoAlt)
                    VALUES (NULL, NULL, ?)
                """
                cursor.execute(insert_query, (codigo_alt,))
                cursor.execute("SELECT @@IDENTITY")
                equivalencia_id = cursor.fetchone()[0]
                logging.info(f"Nueva equivalencia creada - ID: {equivalencia_id}, CodigoAlt: {codigo_alt} (sin SKU)")
                sku_oficial = None
            
            # Si no hay SKU, usar el CodigoAlt como identificador en DimProducto
            if not sku_oficial:
                sku_oficial = codigo_alt
            
            # Buscar el producto por SKU
            query = "SELECT IdProducto FROM DimProducto WHERE SKU = ?"
            cursor.execute(query, sku_oficial)
            result = cursor.fetchone()
            
            if result:
                producto_id = result[0]
            else:
                # Crear el producto si no existe
                insert_query = """
                    INSERT INTO DimProducto (SKU, Nombre, Categoria)
                    VALUES (?, ?, ?)
                """
                cursor.execute(insert_query, (sku_oficial, nombre, categoria))
                cursor.execute("SELECT @@IDENTITY")
                producto_id = cursor.fetchone()[0]
                logging.info(f"Producto creado: {nombre} - ID: {producto_id}, SKU: {sku_oficial}")
            
            self.dw_connection.commit()
            return int(producto_id)
            
        except Exception as e:
            logging.error(f"Error procesando producto/equivalencias: {e}")
            return None
    
    def get_or_create_tiempo(self, fecha):
        """
        Obtiene o crea un registro en DimTiempo para una fecha específica.
        """
        try:
            cursor = self.dw_connection.cursor()
            
            # Convertir a date si es datetime
            fecha_buscar = fecha.date() if hasattr(fecha, 'date') else fecha
            
            query = "SELECT IdTiempo FROM DimTiempo WHERE Fecha = ?"
            cursor.execute(query, fecha_buscar)
            result = cursor.fetchone()
            
            if result:
                return result[0]
            
            # Crear nuevo registro de tiempo
            insert_query = """
                INSERT INTO DimTiempo (Anio, Mes, Dia, Fecha, Semana, DiaSemana, TipoCambio)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            # Si fecha es datetime, usar sus métodos; si es date, también funcionan
            if isinstance(fecha, datetime):
                fecha_obj = fecha
            else:
                # Si es date, convertir a datetime para usar isocalendar
                from datetime import datetime as dt_class
                fecha_obj = dt_class.combine(fecha, dt_class.min.time())
            
            anio = fecha_obj.year
            mes = fecha_obj.month
            dia = fecha_obj.day
            semana = fecha_obj.isocalendar()[1]
            dia_semana = fecha_obj.strftime('%A')
            
            # Obtener tipo de cambio desde DimTiempo si existe, sino usar 1.0
            tipo_cambio = 1.0
            
            cursor.execute(insert_query, (
                anio, mes, dia, fecha_buscar, semana, dia_semana, tipo_cambio
            ))
            
            cursor.execute("SELECT @@IDENTITY")
            tiempo_id = cursor.fetchone()[0]
            self.dw_connection.commit()
            
            logging.info(f"DimTiempo creado para fecha: {fecha_buscar} - ID: {tiempo_id}")
            return int(tiempo_id)
            
        except Exception as e:
            logging.error(f"Error obteniendo/creando DimTiempo: {e}")
            return None
    
    def get_or_create_canal(self, canal_nombre):
        """
        Obtiene o crea un canal en DimCanal.
        """
        try:
            cursor = self.dw_connection.cursor()
            
            # Buscar canal existente
            query = "SELECT IdCanal FROM DimCanal WHERE Nombre = ?"
            cursor.execute(query, canal_nombre)
            result = cursor.fetchone()
            
            if result:
                return result[0]
            
            # Crear nuevo canal
            insert_query = "INSERT INTO DimCanal (Nombre) VALUES (?)"
            cursor.execute(insert_query, canal_nombre)
            cursor.execute("SELECT @@IDENTITY")
            canal_id = cursor.fetchone()[0]
            self.dw_connection.commit()
            
            logging.info(f"Canal creado: {canal_nombre} - ID: {canal_id}")
            return int(canal_id)
            
        except Exception as e:
            logging.error(f"Error obteniendo/creando DimCanal: {e}")
            return None
    
    def process_orders(self, limit=None):
        """
        Procesa las órdenes desde MySQL y las carga en FactVentas.
        Agrupa por cliente, producto y fecha para evitar duplicados.
        """
        try:
            mysql_cursor = self.mysql_connection.cursor(dictionary=True)
            
            # Query para obtener ventas agregadas por cliente/producto/fecha
            query = """
                SELECT 
                    c.id as cliente_id,
                    c.nombre,
                    c.correo,
                    c.genero,
                    c.pais,
                    c.created_at,
                    p.id as producto_id,
                    p.codigo_alt,
                    p.nombre as producto_nombre,
                    p.categoria,
                    DATE(o.fecha) as fecha,
                    o.canal,
                    o.moneda,
                    SUM(od.cantidad) as cantidad_total,
                    AVG(CAST(REPLACE(REPLACE(od.precio_unit, ',', ''), ' ', '') AS DECIMAL(18,2))) as precio_promedio,
                    SUM(od.cantidad * CAST(REPLACE(REPLACE(od.precio_unit, ',', ''), ' ', '') AS DECIMAL(18,2))) as total_ventas
                FROM OrdenDetalle od
                INNER JOIN Orden o ON od.orden_id = o.id
                INNER JOIN Producto p ON od.producto_id = p.id
                INNER JOIN Cliente c ON o.cliente_id = c.id
                GROUP BY 
                    c.id, c.nombre, c.correo, c.genero, c.pais, c.created_at,
                    p.id, p.codigo_alt, p.nombre, p.categoria,
                    DATE(o.fecha), o.canal, o.moneda
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            mysql_cursor.execute(query)
            ventas = mysql_cursor.fetchall()
            
            logging.info(f"Procesando {len(ventas)} registros agregados de ventas desde MySQL")
            
            processed_count = 0
            error_count = 0
            skipped_count = 0
            
            for venta in ventas:
                try:
                    # Extraer datos del cliente
                    cliente_data = {
                        'nombre': venta['nombre'],
                        'email': venta['correo'],
                        'genero': venta['genero'],
                        'pais': venta['pais'],
                        'created_at': venta['created_at']
                    }
                    
                    # Extraer datos del producto
                    producto_data = {
                        'codigo_alt': venta['codigo_alt'],
                        'nombre': venta['producto_nombre'],
                        'categoria': venta['categoria']
                    }
                    
                    # Datos de la venta
                    fecha = venta['fecha']
                    canal = venta['canal']
                    moneda = venta['moneda']
                    cantidad_total = venta['cantidad_total']
                    precio_promedio = Decimal(str(venta['precio_promedio']))
                    total_ventas = Decimal(str(venta['total_ventas']))
                    
                    # Verificar si esta combinación ya fue procesada
                    dw_cursor = self.dw_connection.cursor()
                    check_query = """
                        SELECT COUNT(*) 
                        FROM FactVentas fv
                        INNER JOIN DimCliente c ON fv.IdCliente = c.IdCliente
                        INNER JOIN DimProducto p ON fv.IdProducto = p.IdProducto
                        INNER JOIN DimTiempo t ON fv.IdTiempo = t.IdTiempo
                        INNER JOIN Equivalencias e ON p.SKU = e.SKU
                        WHERE c.Email = ? AND e.CodigoAlt = ? AND t.Fecha = ?
                    """
                    dw_cursor.execute(check_query, (cliente_data['email'], producto_data['codigo_alt'], fecha))
                    count_result = dw_cursor.fetchone()
                    
                    if count_result and count_result[0] > 0:
                        skipped_count += 1
                        if skipped_count % 50 == 0:
                            logging.info(f"Registros omitidos (ya procesados): {skipped_count}")
                        continue
                    
                    # Procesar cliente
                    cliente_id = self.get_or_create_cliente(cliente_data)
                    if not cliente_id:
                        error_count += 1
                        continue
                    
                    # Procesar producto con equivalencias
                    producto_id = self.process_equivalencias_and_get_producto(producto_data)
                    if not producto_id:
                        error_count += 1
                        continue
                    
                    # Procesar tiempo
                    tiempo_id = self.get_or_create_tiempo(fecha)
                    if not tiempo_id:
                        error_count += 1
                        continue
                    
                    # Procesar canal
                    canal_id = self.get_or_create_canal(canal)
                    if not canal_id:
                        error_count += 1
                        continue
                    
                    # Convertir moneda si es necesario
                    if moneda == 'CRC':
                        tipo_cambio = self.get_exchange_rate(fecha, 'CRC', 'USD')
                        precio_usd = precio_promedio * tipo_cambio
                        total_usd = total_ventas * tipo_cambio
                    else:
                        precio_usd = precio_promedio
                        total_usd = total_ventas
                    
                    # Insertar en FactVentas
                    insert_cursor = self.dw_connection.cursor()
                    insert_query = """
                        INSERT INTO FactVentas (IdTiempo, IdProducto, IdCliente, IdCanal, TotalVentas, Cantidad, Precio)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """
                    
                    insert_cursor.execute(insert_query, (
                        tiempo_id,
                        producto_id,
                        cliente_id,
                        canal_id,
                        round(float(total_usd), 2),
                        cantidad_total,
                        round(float(precio_usd), 2)
                    ))
                    
                    processed_count += 1
                    
                    if processed_count % 50 == 0:
                        self.dw_connection.commit()
                        logging.info(f"Procesados {processed_count} registros nuevos...")
                
                except Exception as e:
                    logging.error(f"Error procesando venta: {e}")
                    error_count += 1
                    continue
            
            # Commit final
            self.dw_connection.commit()
            
            logging.info(f"ETL completado:")
            logging.info(f"  - Registros procesados: {processed_count}")
            logging.info(f"  - Registros omitidos (duplicados): {skipped_count}")
            logging.info(f"  - Errores: {error_count}")
            
        except Exception as e:
            logging.error(f"Error en process_orders: {e}")
            raise
    
    def run_etl(self, limit=None):
        """Ejecuta el proceso completo de ETL"""
        try:
            logging.info("="*60)
            logging.info("Iniciando ETL: MySQL (sales_mysql) -> Data Warehouse")
            logging.info("="*60)
            
            # Conectar a ambas bases de datos
            self.connect_mysql()
            self.connect_dw()
            
            # Procesar órdenes
            self.process_orders(limit)
            
            logging.info("="*60)
            logging.info("ETL completado exitosamente")
            logging.info("="*60)
            
        except Exception as e:
            logging.error(f"Error en ETL: {e}")
            raise
        finally:
            # Cerrar conexiones
            if self.mysql_connection:
                self.mysql_connection.close()
                logging.info("Conexión MySQL origen cerrada")
            
            if self.dw_connection:
                self.dw_connection.close()
                logging.info("Conexión Data Warehouse cerrada")


if __name__ == "__main__":
    etl = MySQLToDW_ETL()
    # Ejecutar sin límite para procesar todos los registros
    etl.run_etl()
