import pyodbc
import logging
from datetime import datetime
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

class SQLServerToDW_ETL:
    def __init__(self):
        # Configuración de SQL Server ORIGEN (ventas_ms)
        self.source_server = os.getenv("SOURCE_SERVER", "localhost")
        self.source_database = os.getenv("SOURCE_DATABASE", "ventas_ms")
        self.source_username = os.getenv("SOURCE_USERNAME")
        self.source_password = os.getenv("SOURCE_PASSWORD")
        
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
        
        self.source_connection = None
        self.dw_connection = None
        
        # Mapping de género según especificaciones
        self.genero_mapping = {
            'Masculino': 'M',
            'M': 'M',
            'Femenino': 'F',
            'F': 'F',
            'Otro': 'X',
            'X': 'X'
        }
        
        # Sistema de origen para logging
        self.source_system = 'SQLSERVER'
        
        # Tipo de cambio por defecto CRC→USD si no se encuentra en la tabla
        self.default_crc_to_usd_rate = 0.0019  # ~520 CRC por USD
        
    def connect_source(self):
        """Conecta a la base de datos SQL Server origen (ventas_ms)"""
        try:
            if self.source_username and self.source_password:
                connection_string = (
                    f"DRIVER={{{self.driver}}};"
                    f"SERVER={self.source_server};"
                    f"DATABASE={self.source_database};"
                    f"UID={self.source_username};"
                    f"PWD={self.source_password};"
                    f"TrustServerCertificate=yes;"
                )
            else:
                # Usar autenticación de Windows
                connection_string = (
                    f"DRIVER={{{self.driver}}};"
                    f"SERVER={self.source_server};"
                    f"DATABASE={self.source_database};"
                    f"Trusted_Connection=yes;"
                )
            
            self.source_connection = pyodbc.connect(connection_string)
            logging.info(f"Conexión exitosa a SQL Server origen: {self.source_database}")
        except Exception as e:
            logging.error(f"Error conectando a SQL Server origen: {e}")
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
        Verifica si un registro ya fue procesado usando la tabla Equivalencias como log.
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
            
            # Para productos, verificamos en Equivalencias
            elif table_name == 'Producto':
                query = "SELECT Id FROM Equivalencias WHERE SKU = ?"
                cursor.execute(query, source_key)
                result = cursor.fetchone()
                return result is not None
            
            # Para órdenes, verificamos si existe una venta con esos datos
            # (esto se maneja diferente en process_orders)
            return False
            
        except Exception as e:
            logging.error(f"Error verificando si fue procesado: {e}")
            return False
    
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
            
            # Convertir fecha_registro a date si es datetime
            fecha_reg = cliente_data['fecha_registro']
            if hasattr(fecha_reg, 'date'):
                fecha_reg = fecha_reg.date()
            
            insert_query = """
                INSERT INTO DimCliente (Nombre, Email, Genero, Pais, FechaCreacion)
                VALUES (?, ?, ?, ?, ?)
            """
            cursor.execute(insert_query, (
                cliente_data['nombre'],
                cliente_data['email'],
                genero_mapeado,
                cliente_data['pais'],
                fecha_reg
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
        Usa la tabla Equivalencias para mapear SKU de diferentes fuentes.
        """
        try:
            cursor = self.dw_connection.cursor()
            
            sku = producto_data['sku']
            nombre = producto_data['nombre']
            categoria = producto_data['categoria']
            
            # Buscar si ya existe una equivalencia para este SKU
            query = "SELECT Id, SKU FROM Equivalencias WHERE SKU = ?"
            cursor.execute(query, sku)
            result = cursor.fetchone()
            
            if result:
                equivalencia_id = result[0]
                sku_oficial = result[1]
                logging.info(f"Encontrada equivalencia existente para SKU: {sku_oficial}")
                
                # Buscar el producto por SKU oficial
                query = "SELECT IdProducto FROM DimProducto WHERE SKU = ?"
                cursor.execute(query, sku_oficial)
                result = cursor.fetchone()
                if result:
                    producto_id = result[0]
                    logging.info(f"Encontrado producto existente - ID: {producto_id}")
                    return int(producto_id)
            
            # Si no existe equivalencia, crear una nueva
            if not result:
                insert_query = """
                    INSERT INTO Equivalencias (SKU, CodigoMongo, CodigoAlt)
                    VALUES (?, NULL, NULL)
                """
                cursor.execute(insert_query, sku)
                cursor.execute("SELECT @@IDENTITY")
                equivalencia_id = cursor.fetchone()[0]
                sku_oficial = sku
                logging.info(f"Nueva equivalencia creada - ID: {equivalencia_id}, SKU: {sku_oficial}")
            
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
            tipo_cambio = 1.0  # USD por defecto
            
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
    
    def process_orders(self, limit=None):
        """
        Procesa las órdenes desde SQL Server origen y las carga en FactVentas.
        Agrupa por cliente, producto y fecha para evitar duplicados.
        """
        try:
            source_cursor = self.source_connection.cursor()
            
            # Query para obtener ventas agregadas por cliente/producto/fecha
            query = """
                SELECT 
                    c.ClienteId,
                    c.Nombre,
                    c.Email,
                    c.Genero,
                    c.Pais,
                    c.FechaRegistro,
                    p.ProductoId,
                    p.SKU,
                    p.Nombre as ProductoNombre,
                    p.Categoria,
                    CAST(o.Fecha AS DATE) as Fecha,
                    SUM(od.Cantidad) as CantidadTotal,
                    AVG(od.PrecioUnit) as PrecioUnitPromedio,
                    SUM(od.Cantidad * od.PrecioUnit * (1 - ISNULL(od.DescuentoPct, 0) / 100)) as TotalVentas
                FROM sales_ms.OrdenDetalle od
                INNER JOIN sales_ms.Orden o ON od.OrdenId = o.OrdenId
                INNER JOIN sales_ms.Producto p ON od.ProductoId = p.ProductoId
                INNER JOIN sales_ms.Cliente c ON o.ClienteId = c.ClienteId
                GROUP BY 
                    c.ClienteId, c.Nombre, c.Email, c.Genero, c.Pais, c.FechaRegistro,
                    p.ProductoId, p.SKU, p.Nombre, p.Categoria,
                    CAST(o.Fecha AS DATE)
            """
            
            if limit:
                query += f" ORDER BY o.Fecha DESC OFFSET 0 ROWS FETCH NEXT {limit} ROWS ONLY"
            
            source_cursor.execute(query)
            ventas = source_cursor.fetchall()
            
            logging.info(f"Procesando {len(ventas)} registros agregados de ventas")
            
            processed_count = 0
            error_count = 0
            skipped_count = 0
            
            for venta in ventas:
                try:
                    # Extraer datos del cliente
                    cliente_data = {
                        'nombre': venta[1],
                        'email': venta[2],
                        'genero': venta[3],
                        'pais': venta[4],
                        'fecha_registro': venta[5]
                    }
                    
                    # Extraer datos del producto
                    producto_data = {
                        'sku': venta[7],
                        'nombre': venta[8],
                        'categoria': venta[9]
                    }
                    
                    # Datos de la venta (todos los montos están en USD)
                    fecha = venta[10]
                    cantidad_total = venta[11]
                    precio_unit_promedio = venta[12]
                    total_ventas = venta[13]
                    
                    # Verificar si esta combinación ya fue procesada
                    dw_cursor = self.dw_connection.cursor()
                    check_query = """
                        SELECT COUNT(*) 
                        FROM FactVentas fv
                        INNER JOIN DimCliente c ON fv.IdCliente = c.IdCliente
                        INNER JOIN DimProducto p ON fv.IdProducto = p.IdProducto
                        INNER JOIN DimTiempo t ON fv.IdTiempo = t.IdTiempo
                        WHERE c.Email = ? AND p.SKU = ? AND t.Fecha = ?
                    """
                    dw_cursor.execute(check_query, (cliente_data['email'], producto_data['sku'], fecha))
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
                    
                    # Insertar en FactVentas (montos ya están en USD)
                    insert_cursor = self.dw_connection.cursor()
                    insert_query = """
                        INSERT INTO FactVentas (IdTiempo, IdProducto, IdCliente, TotalVentas, Cantidad, Precio)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """
                    
                    insert_cursor.execute(insert_query, (
                        tiempo_id,
                        producto_id,
                        cliente_id,
                        round(total_ventas, 2),
                        cantidad_total,
                        round(precio_unit_promedio, 2)
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
    
    def load_exchange_rates_from_file(self, filepath='tipos_cambio.csv'):
        """
        Carga tipos de cambio desde un archivo CSV.
        Formato esperado: Fecha,MonedaOrigen,MonedaDestino,Tasa
        Ejemplo: 2025-01-01,CRC,USD,0.0019
        """
        try:
            import csv
            from datetime import datetime as dt
            
            if not os.path.exists(filepath):
                logging.warning(f"Archivo {filepath} no encontrado, saltando carga de tipos de cambio")
                return
            
            cursor = self.dw_connection.cursor()
            inserted = 0
            
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        fecha = dt.strptime(row['Fecha'], '%Y-%m-%d').date()
                        moneda_origen = row['MonedaOrigen']
                        moneda_destino = row['MonedaDestino']
                        tasa = float(row['Tasa'])
                        
                        # Verificar si ya existe
                        check_query = """
                            SELECT COUNT(*) FROM dbo.TipoCambio 
                            WHERE Fecha = ? AND MonedaOrigen = ? AND MonedaDestino = ?
                        """
                        cursor.execute(check_query, (fecha, moneda_origen, moneda_destino))
                        if cursor.fetchone()[0] == 0:
                            insert_query = """
                                INSERT INTO dbo.TipoCambio (Fecha, MonedaOrigen, MonedaDestino, Tasa)
                                VALUES (?, ?, ?, ?)
                            """
                            cursor.execute(insert_query, (fecha, moneda_origen, moneda_destino, tasa))
                            inserted += 1
                    except Exception as e:
                        logging.warning(f"Error insertando tipo de cambio: {e}")
                        continue
            
            self.dw_connection.commit()
            logging.info(f"Tipos de cambio cargados desde archivo: {inserted} registros nuevos")
            
        except Exception as e:
            logging.error(f"Error cargando tipos de cambio desde archivo: {e}")
    
    def run_etl(self, limit=None, load_exchange_rates=True):
        """Ejecuta el proceso completo de ETL"""
        try:
            logging.info("="*60)
            logging.info("Iniciando ETL: SQL Server (ventas_ms) -> Data Warehouse")
            logging.info("="*60)
            
            # Conectar a ambas bases de datos
            self.connect_source()
            self.connect_dw()
            
            # Cargar tipos de cambio si está habilitado
            if load_exchange_rates:
                self.load_exchange_rates_from_file()
            
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
            if self.source_connection:
                self.source_connection.close()
                logging.info("Conexión SQL Server origen cerrada")
            
            if self.dw_connection:
                self.dw_connection.close()
                logging.info("Conexión Data Warehouse cerrada")


if __name__ == "__main__":
    etl = SQLServerToDW_ETL()
    # Ejecutar sin límite para procesar todos los registros
    etl.run_etl()
