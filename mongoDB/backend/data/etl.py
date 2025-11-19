import pymongo
import pyodbc
import logging
from datetime import datetime, timedelta
import platform
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))


logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class MongoToDW_ETL:
    def __init__(self):
        
        self.mongo_uri = os.getenv("MONGODB_URI")
        if not self.mongo_uri:
            raise ValueError("MONGODB_URI no encontrada en variables de entorno")
        
        self.mongo_client = None
        self.mongo_db = None
        
        self.server = os.getenv("serverenv", "localhost")
        self.database = os.getenv("databaseenv", "DW_VENTAS")
        self.username = os.getenv("usernameenv")
        self.password = os.getenv("passwordenv")
        
        if platform.system() == "Windows":
            self.driver = "ODBC Driver 17 for SQL Server"
        else:
            self.driver = "ODBC Driver 18 for SQL Server"
        
        self.sql_connection = None


        self.genero_mapping = {
            'Masculino': 'M',
            'Femenino': 'F',
            'Otro': 'N'  # No especificado
        }
        
    def generate_sku_from_mongo_code(self, codigo_mongo):

        if not codigo_mongo:
            return None
        

        if codigo_mongo.startswith('MN-'):
            numero = codigo_mongo[3:]  
            # Generar letras basado en el número
            # Usar hash del número para generar siempre las mismas letras para el mismo número
            import hashlib
            hash_object = hashlib.md5(numero.encode())
            hash_hex = hash_object.hexdigest()
            # Tomar los primeros 2 caracteres hexadecimales y convertirlos a letras A-P
            char1 = chr(ord('A') + int(hash_hex[0], 16))  # 0-15 -> A-P
            char2 = chr(ord('A') + int(hash_hex[1], 16))  # 0-15 -> A-P
            return f'PRD-{numero}-{char1}{char2}'
        else:
            return f'PRD-{codigo_mongo.replace("-", "")[:4].upper()}-XX'
        
    def connect_mongo(self):
        try:
            self.mongo_client = pymongo.MongoClient(self.mongo_uri)
            self.mongo_db = self.mongo_client.get_database()
            logging.info("Conexión exitosa a MongoDB")
        except Exception as e:
            logging.error(f"Error conectando a MongoDB: {e}")
            raise
    
    def connect_sql_server(self):
        try:
            connection_string = f"DRIVER={{{self.driver}}};SERVER={self.server};DATABASE={self.database};UID={self.username};PWD={self.password};TrustServerCertificate=yes;"
            self.sql_connection = pyodbc.connect(connection_string)
            logging.info("Conexión exitosa a SQL Server DW")
        except Exception as e:
            logging.error(f"Error conectando a SQL Server: {e}")
            raise
    
    def get_exchange_rate_for_date(self, fecha):

        try:
            cursor = self.sql_connection.cursor()
            query = """
                SELECT TipoCambio 
                FROM DimTiempo 
                WHERE Fecha = ?
            """
            cursor.execute(query, fecha.date())
            result = cursor.fetchone()
            
            if result and result[0]:
                return float(result[0])
            else:
                return 500.00  # Valor por defecto
                    
        except Exception as e:
            logging.error(f"Error obteniendo tipo de cambio: {e}")
            return 500.00
    
    def get_or_create_cliente(self, cliente_data):
        try:
            cursor = self.sql_connection.cursor()
            

            query = "SELECT IdCliente FROM DimCliente WHERE Email = ?"
            cursor.execute(query, cliente_data['email'])
            result = cursor.fetchone()
            
            if result:
                return result[0]
            
            # si no lo encuentra crea uno
            genero_mapeado = self.genero_mapping.get(cliente_data['genero'], 'N')
            
            insert_query = """
                INSERT INTO DimCliente (Nombre, Email, Genero, Pais, FechaCreacion)
                VALUES (?, ?, ?, ?, ?)
            """
            cursor.execute(insert_query, (
                cliente_data['nombre'],
                cliente_data['email'],
                genero_mapeado,
                cliente_data['pais'],
                cliente_data['creado'].date()
            ))
            
            cursor.execute("SELECT @@IDENTITY")
            cliente_id = cursor.fetchone()[0]
            self.sql_connection.commit()
            
            logging.info(f"Cliente creado: {cliente_data['email']} - ID: {cliente_id}")
            return int(cliente_id)
            
        except Exception as e:
            logging.error(f"Error procesando cliente: {e}")
            return None
    
    def process_equivalencias_and_get_producto(self, producto_data):
        try:
            cursor = self.sql_connection.cursor()
            
            codigo_mongo = producto_data['codigo_mongo']
            nombre = producto_data['nombre']
            categoria = producto_data['categoria']
            equivalencias = producto_data.get('equivalencias', {})
            
            sku_from_equivalencias = equivalencias.get('sku')
            codigo_alt = equivalencias.get('codigo_alt')
            
            # primero buscamos si ya hay equivalencias para el código mongo
            equivalencia_id = None
            sku_existente = None
            producto_id = None
            
            if codigo_mongo:
                query = "SELECT Id, SKU FROM Equivalencias WHERE CodigoMongo = ?"
                cursor.execute(query, codigo_mongo)
                result = cursor.fetchone()
                if result:
                    equivalencia_id = result[0]
                    sku_existente = result[1]
            
            # si sí, buscamos el product por su sku
            if equivalencia_id and sku_existente:
                sku_final = sku_existente
                logging.info(f"Encontrada equivalencia existente para {codigo_mongo} - SKU: {sku_final}")
                
                
                query = "SELECT IdProducto FROM DimProducto WHERE SKU = ?"
                cursor.execute(query, sku_final)
                result = cursor.fetchone()
                if result:
                    producto_id = result[0]
                    logging.info(f"Encontrado producto existente - ID: {producto_id}")
                    return int(producto_id)
            
            
            if not equivalencia_id:
                # generamos el sku desde el codigo mongo
                sku_generado = self.generate_sku_from_mongo_code(codigo_mongo) if codigo_mongo else None
                sku_final = sku_from_equivalencias or sku_generado
                
                # buscamos por ese sku
                if sku_final:
                    query = "SELECT Id FROM Equivalencias WHERE SKU = ?"
                    cursor.execute(query, sku_final)
                    result = cursor.fetchone()
                    if result:
                        equivalencia_id = result[0]
                        logging.info(f"Encontrada equivalencia por SKU: {sku_final}")
                
                # sino por código alternativo
                if not equivalencia_id and codigo_alt:
                    query = "SELECT Id FROM Equivalencias WHERE CodigoAlt = ?"
                    cursor.execute(query, codigo_alt)
                    result = cursor.fetchone()
                    if result:
                        equivalencia_id = result[0]
                        logging.info(f"Encontrada equivalencia por código alt: {codigo_alt}")
                
                # si no hay, hacemos una nueva equivalencia
                if not equivalencia_id:
                    insert_query = """
                        INSERT INTO Equivalencias (SKU, CodigoMongo, CodigoAlt)
                        VALUES (?, ?, ?)
                    """
                    cursor.execute(insert_query, (sku_final, codigo_mongo, codigo_alt))
                    cursor.execute("SELECT @@IDENTITY")
                    equivalencia_id = cursor.fetchone()[0]
                    logging.info(f"Nueva equivalencia creada - ID: {equivalencia_id}, SKU: {sku_final}")
            else:
                sku_final = sku_existente
            
            # buscamos el producto por su sku
            if sku_final:
                query = "SELECT IdProducto FROM DimProducto WHERE SKU = ?"
                cursor.execute(query, sku_final)
                result = cursor.fetchone()
                if result:
                    producto_id = result[0]
            
            # si no existe el producto, lo creamos
            if not producto_id:
                insert_query = """
                    INSERT INTO DimProducto (SKU, Nombre, Categoria)
                    VALUES (?, ?, ?)
                """
                cursor.execute(insert_query, (sku_final, nombre, categoria))
                cursor.execute("SELECT @@IDENTITY")
                producto_id = cursor.fetchone()[0]
                logging.info(f"Producto creado: {nombre} - ID: {producto_id}, SKU: {sku_final}")
            
            self.sql_connection.commit()
            return int(producto_id)
            
        except Exception as e:
            logging.error(f"Error procesando producto/equivalencias: {e}")
            return None
    
    def check_field_exists(self, table, field, id_value):
        try:
            cursor = self.sql_connection.cursor()
            query = f"SELECT {field} FROM {table} WHERE Id = ?"
            cursor.execute(query, id_value)
            result = cursor.fetchone()
            return result and result[0] is not None
        except:
            return False
    
    def get_tiempo_id(self, fecha):
        try:
            cursor = self.sql_connection.cursor()
            query = "SELECT IdTiempo FROM DimTiempo WHERE Fecha = ?"
            cursor.execute(query, fecha.date())
            result = cursor.fetchone()
            
            if result:
                return result[0]
            else:
                logging.warning(f"No se encontró IdTiempo para fecha {fecha.date()}")
                return None
                
        except Exception as e:
            logging.error(f"Error obteniendo IdTiempo: {e}")
            return None
    
    def process_orders(self, limit=None):
        try:
            ordenes_collection = self.mongo_db['ordenes']
            
        
            pipeline = [
                {
                    '$lookup': {
                        'from': 'clientes',
                        'localField': 'cliente_id',
                        'foreignField': '_id',
                        'as': 'cliente_data'
                    }
                },
                {
                    '$unwind': '$cliente_data'
                },
                {
                    '$unwind': '$items'
                },
                {
                    '$lookup': {
                        'from': 'productos',
                        'localField': 'items.producto_id',
                        'foreignField': '_id',
                        'as': 'producto_data'
                    }
                },
                {
                    '$unwind': '$producto_data'
                },
                {
                    '$addFields': {
                        'fecha_solo': {
                            '$dateToString': {
                                'format': '%Y-%m-%d',
                                'date': '$fecha'
                            }
                        },
                        'total_item': {
                            '$multiply': ['$items.precio_unit', '$items.cantidad']
                        }
                    }
                },
                {
                    '$group': {
                        '_id': {
                            'cliente_id': '$cliente_data._id',
                            'producto_id': '$producto_data._id',
                            'fecha': '$fecha_solo'
                        },
                        'cliente_data': {'$first': '$cliente_data'},
                        'producto_data': {'$first': '$producto_data'},
                        'fecha_original': {'$first': '$fecha'},
                        'cantidad_total': {'$sum': '$items.cantidad'},
                        'precio_unit': {'$first': '$items.precio_unit'},
                        'total_ventas_crc': {'$sum': '$total_item'}
                    }
                }
            ]
            
            if limit:
                pipeline.append({'$limit': limit})
            
            ventas_agregadas = list(ordenes_collection.aggregate(pipeline))
            logging.info(f"Procesando {len(ventas_agregadas)} ventas agregadas por cliente/producto/día")
            
            processed_count = 0
            error_count = 0
            
            for venta in ventas_agregadas:
                try:
                    
                    fecha = venta['fecha_original']
                    cantidad_total = venta['cantidad_total']
                    total_crc = venta['total_ventas_crc']
                    precio_unit_crc = venta['precio_unit']  
                    
                    
                    cliente_id = self.get_or_create_cliente(venta['cliente_data'])
                    if not cliente_id:
                        error_count += 1
                        continue
                    
             
                    producto_id = self.process_equivalencias_and_get_producto(venta['producto_data'])
                    if not producto_id:
                        error_count += 1
                        continue
                    
               
                    tiempo_id = self.get_tiempo_id(fecha)
                    if not tiempo_id:
                        error_count += 1
                        continue
                    
                  
                    tipo_cambio = self.get_exchange_rate_for_date(fecha)
                    precio_unit_usd = precio_unit_crc / tipo_cambio
                    total_usd = total_crc / tipo_cambio
                    
                    
                    cursor = self.sql_connection.cursor()
                    insert_query = """
                        INSERT INTO FactVentas (IdTiempo, IdProducto, IdCliente, TotalVentas, Cantidad, Precio)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """
                    
                    cursor.execute(insert_query, (
                        tiempo_id,
                        producto_id,
                        cliente_id,
                        round(total_usd, 2),
                        cantidad_total,
                        round(precio_unit_usd, 2)
                    ))
                    
                    processed_count += 1
                    
                    if processed_count % 50 == 0:
                        self.sql_connection.commit()
                        logging.info(f"Procesados {processed_count} registros agregados...")
                
                except Exception as e:
                    logging.error(f"Error procesando venta agregada: {e}")
                    error_count += 1
                    continue
            
           
            self.sql_connection.commit()
            
            logging.info(f"ETL completado: {processed_count} registros agregados procesados exitosamente")
            logging.info(f"Errores: {error_count}")
            
        except Exception as e:
            logging.error(f"Error en process_orders: {e}")
            raise
    
    def run_etl(self, limit=None):
        """Ejecuta el proceso completo de ETL"""
        try:
            logging.info("Iniciando ETL MongoDB -> DW")
            
            
            self.connect_mongo()
            self.connect_sql_server()
            
           
            self.process_orders(limit)
            
            logging.info("ETL completado exitosamente")
            
        except Exception as e:
            logging.error(f"Error en ETL: {e}")
            raise
        finally:
            
            if self.mongo_client:
                self.mongo_client.close()
                logging.info("Conexión MongoDB cerrada")
            
            if self.sql_connection:
                self.sql_connection.close()
                logging.info("Conexión SQL Server cerrada")


if __name__ == "__main__":
    etl = MongoToDW_ETL()
    etl.run_etl()
    