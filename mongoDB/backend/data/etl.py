import pymongo
import pyodbc
from datetime import datetime, timedelta
import platform
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

class MongoToDW_ETL:
    def __init__(self):
        
        self.mongo_uri = os.getenv("MONGODB_URI")
        if not self.mongo_uri:
            raise ValueError("Falta poner el MONGODB_URI en el .env ")
        
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

    
        self.log_file_path = os.path.join(os.path.dirname(__file__), 'etl_execution.log')
        
        
        self.skus_generados = set()

        self.genero_mapping = {
            'Masculino': 'M',
            'Femenino': 'F',
            'Otro': 'N'  
        }
        
    def mongo_a_sku(self, codigo_mongo):
        #si tenemos el codigo de mongo pero no el sku lo tenemos que generar para ponerlo en el dimproducto

        if not codigo_mongo:
            return None
        
        # agarramos y ponemos los números al revés
        if codigo_mongo.startswith('MN-'):
            numero = codigo_mongo[3:]  
            numero_invertido = numero[::-1]
            sku = f'SKU-{numero_invertido}'
            
            # si ya existe, sumamos 1 hasta encontrar uno nuevo
            contador = 0
            sku_original = sku
            while sku in self.skus_generados:
                contador += 1
                numero_modificado = str(int(numero_invertido) + contador).zfill(4)
                sku = f'SKU-{numero_modificado}'
            
            self.skus_generados.add(sku)
            return sku
        else:
            # lo mismo pero para códigos que no siguen el formato MN-XXXX
            numero_limpio = ''.join(filter(str.isdigit, codigo_mongo))  
            if numero_limpio:
                numero_invertido = numero_limpio[::-1]
                sku = f'SKU-{numero_invertido.zfill(4)}'
                
                s
                contador = 0
                while sku in self.skus_generados:
                    contador += 1
                    numero_modificado = str(int(numero_invertido) + contador).zfill(4)
                    sku = f'SKU-{numero_modificado}'
                
                self.skus_generados.add(sku)
                return sku
            return 'SKU-0000'
        
    def ultima_ejecucion(self):
        # esta es la parte que evita que metamos duplicados o así
        try:
            if not os.path.exists(self.log_file_path):
                return None
            
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    if last_line:
                        try:
                            last_date = datetime.strptime(last_line, '%Y-%m-%d').date()
                            print(f"Última fecha procesada encontrada: {last_date}")
                            return last_date
                        except ValueError:
                            print(f"Formato de fecha inválido en log: {last_line}")
                            return None
            
            print("No se encontraron fechas previas en el log")
            return None
                
        except Exception as e:
            print(f"Error leyendo archivo de log: {e}")
            return None
    
    def registrar_log(self, ultima_fecha_procesada):
        try:
            with open(self.log_file_path, 'w', encoding='utf-8') as f:
                f.write(ultima_fecha_procesada.strftime('%Y-%m-%d'))
                
            print(f"Fecha registrada en log: {ultima_fecha_procesada}")
            
        except Exception as e:
            print(f"Error escribiendo en archivo de log: {e}")
    
    def connect_mongo(self):
        try:
            self.mongo_client = pymongo.MongoClient(self.mongo_uri)
            self.mongo_db = self.mongo_client.get_database()
            print("Conexión exitosa a MongoDB")
        except Exception as e:
            print(f"Error conectando a MongoDB: {e}")
            raise
    
    def connect_sql_server(self):
        try:
            connection_string = f"DRIVER={{{self.driver}}};SERVER={self.server};DATABASE={self.database};UID={self.username};PWD={self.password};TrustServerCertificate=yes;"
            self.sql_connection = pyodbc.connect(connection_string)
            print("Conexión exitosa a SQL Server DW")
        except Exception as e:
            print(f"Error conectando a SQL Server: {e}")
            raise
    
    def tc_dia(self, fecha):

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
                return 500.00 
                    
        except Exception as e:
            print(f"Error obteniendo tipo de cambio: {e}")
            return 500.00
    
    def obtener_cliente(self, cliente_data):
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
            
           
            return int(cliente_id)
            
        except Exception as e:
            print(f"Error procesando cliente: {e}")
            return None
    
    def obtener_producto(self, producto_data):
        try:
            cursor = self.sql_connection.cursor()
            
            codigo_mongo = producto_data.get('codigo_mongo')
            nombre = producto_data.get('nombre', 'Sin Nombre')
            categoria = producto_data.get('categoria', 'Sin Categoria')
            equivalencias = producto_data.get('equivalencias', {})
            
            
            if not codigo_mongo:
                return None
            
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
                
                
                
                query = "SELECT IdProducto FROM DimProducto WHERE SKU = ?"
                cursor.execute(query, sku_final)
                result = cursor.fetchone()
                if result:
                    producto_id = result[0]
                    return int(producto_id)
            
            
            if not equivalencia_id:
                # generamos el sku desde el codigo mongo
                sku_generado = self.mongo_a_sku(codigo_mongo) if codigo_mongo else None
                sku_final = sku_from_equivalencias or sku_generado
                
                # buscamos por ese sku
                if sku_final:
                    query = "SELECT Id FROM Equivalencias WHERE SKU = ?"
                    cursor.execute(query, sku_final)
                    result = cursor.fetchone()
                    if result:
                        equivalencia_id = result[0]
                        
                
                # sino por código alternativo
                if not equivalencia_id and codigo_alt:
                    query = "SELECT Id FROM Equivalencias WHERE CodigoAlt = ?"
                    cursor.execute(query, codigo_alt)
                    result = cursor.fetchone()
                    if result:
                        equivalencia_id = result[0]
                        
                
                # si no hay, hacemos una nueva equivalencia
                if not equivalencia_id:
                    insert_query = """
                        INSERT INTO Equivalencias (SKU, CodigoMongo, CodigoAlt)
                        VALUES (?, ?, ?)
                    """
                    cursor.execute(insert_query, (sku_final, codigo_mongo, codigo_alt))
                    cursor.execute("SELECT @@IDENTITY")
                    equivalencia_id = cursor.fetchone()[0]
                    
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
                
            
            self.sql_connection.commit()
            return int(producto_id)
            
        except Exception as e:
            print(f"Error procesando producto: {e}")
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
                return None
                
        except Exception as e:
            print(f"Error obteniendo IdTiempo: {e}")
            return None
    
    def obtener_canal(self, canal_nombre):
        try:
            cursor = self.sql_connection.cursor()
            
        
            query = "SELECT IdCanal FROM DimCanal WHERE Nombre = ?"
            cursor.execute(query, canal_nombre)
            result = cursor.fetchone()
            
            if result:
                return result[0]
            
            # si no existe, hay que crear uno nuevo
            insert_query = """
                INSERT INTO DimCanal (Nombre)
                VALUES (?)
            """
            cursor.execute(insert_query, canal_nombre)
            
            cursor.execute("SELECT @@IDENTITY")
            canal_id = cursor.fetchone()[0]
            self.sql_connection.commit()
            
            return int(canal_id)
            
        except Exception as e:
            print(f"Error procesando canal: {e}")
            return None

    def procesar_ordenes(self, limit=None):
        try:
            
            last_execution_date = self.ultima_ejecucion()
            
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
                }
            ]
            
            # para no meter repetidos!!!!
            if last_execution_date:
                next_day = last_execution_date + timedelta(days=1)
                date_filter = {
                    '$match': {
                        'fecha': {
                            '$gte': datetime.combine(next_day, datetime.min.time())
                        }
                    }
                }
                pipeline.insert(0, date_filter)  
                print(f"Analizando órdenes posteriores al: {next_day}")
            else:
                print("Primera ejecución")
            
           
            pipeline.extend([
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
                            'fecha': '$fecha_solo',
                            'canal': '$canal'
                        },
                        'cliente_data': {'$first': '$cliente_data'},
                        'producto_data': {'$first': '$producto_data'},
                        'fecha_original': {'$first': '$fecha'},
                        'canal': {'$first': '$canal'},
                        'cantidad_total': {'$sum': '$items.cantidad'},
                        'precio_unit_promedio': {'$avg': '$items.precio_unit'},
                        'total_ventas_crc': {'$sum': '$total_item'}
                    }
                }
            ])
            
            if limit:
                pipeline.append({'$limit': limit})
            
            ventas_agregadas = list(ordenes_collection.aggregate(pipeline))
            
            if not ventas_agregadas:
                return 0, None
            
           
            
            processed_count = 0
            error_count = 0
            ultima_fecha_procesada = None
            
            for venta in ventas_agregadas:
                try:
                    
                    fecha = venta['fecha_original']
                    cantidad_total = venta['cantidad_total']
                    total_crc = venta['total_ventas_crc']
                    precio_unit_crc = venta['precio_unit_promedio'] 
                    canal = venta['canal']
                    
                    
                    if not ultima_fecha_procesada or fecha.date() > ultima_fecha_procesada:
                        ultima_fecha_procesada = fecha.date()
                    
                    
                    cliente_id = self.obtener_cliente(venta['cliente_data'])
                    if not cliente_id:
                        error_count += 1
                        continue
                    
             
                    producto_id = self.obtener_producto(venta['producto_data'])
                    if not producto_id:
                        error_count += 1
                        continue
                    
                   
                    canal_id = self.obtener_canal(canal)
                    if not canal_id:
                        error_count += 1
                        continue
                    
               
                    tiempo_id = self.get_tiempo_id(fecha)
                    if not tiempo_id:
                        error_count += 1
                        continue
                    
                  
                    tipo_cambio = self.tc_dia(fecha)
                    precio_unit_usd = precio_unit_crc / tipo_cambio
                    total_usd = total_crc / tipo_cambio
                    
                    
                    cursor = self.sql_connection.cursor()
                    insert_query = """
                        INSERT INTO FactVentas (IdTiempo, IdProducto, IdCliente, IdCanal, TotalVentas, Cantidad, Precio)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """
                    
                    cursor.execute(insert_query, (
                        tiempo_id,
                        producto_id,
                        cliente_id,
                        canal_id,
                        round(total_usd, 2),
                        cantidad_total,
                        round(precio_unit_usd, 2)
                    ))
                    
                    processed_count += 1
                    
                    if processed_count % 50 == 0:
                        self.sql_connection.commit()
                        
                
                except Exception as e:
                    print(f"Error procesando venta agregada: {e}")
                    error_count += 1
                    continue
            
           
            self.sql_connection.commit()
            
            
            print(f"Errores: {error_count}")
            
            return processed_count, ultima_fecha_procesada
            
        except Exception as e:
            print(f"Error en procesar_ordenes: {e}")
            raise
    
    def run_etl(self, limit=None):
        processed_count = 0
        ultima_fecha_procesada = None
        
        try:
            print("Iniciando ETL MongoDB -> DW")
        
            self.connect_mongo()
            self.connect_sql_server()
            
            
            self.cargar_skus_existentes()
            
            
            processed_count, ultima_fecha_procesada = self.procesar_ordenes(limit)
            
            if processed_count > 0:
                self.registrar_log(ultima_fecha_procesada)
                print(f"ETL completado exitosamente - {processed_count} registros procesados")
            else:
                print("No hay datos nuevos para procesar")
            
        except Exception as e:
            print(f"Error en ETL: {e}")
            raise
        finally:
            
            if self.mongo_client:
                self.mongo_client.close()
                print("Conexión MongoDB cerrada")
            
            if self.sql_connection:
                self.sql_connection.close()
                print("Conexión SQL Server cerrada")
    
 
    def cargar_skus_existentes(self):
        
        try:
            cursor = self.sql_connection.cursor()
            cursor.execute("SELECT SKU FROM DimProducto")
            skus_existentes = cursor.fetchall()
            
            for sku_row in skus_existentes:
                if sku_row[0]:
                    self.skus_generados.add(sku_row[0])
            
            
            cursor.execute("SELECT SKU FROM Equivalencias WHERE SKU IS NOT NULL")
            skus_equivalencias = cursor.fetchall()
            
            for sku_row in skus_equivalencias:
                if sku_row[0]:
                    self.skus_generados.add(sku_row[0])
            
            
        except Exception as e:
            print(f"Error cargando SKUs existentes: {e}")

if __name__ == "__main__":
    etl = MongoToDW_ETL()
    
    etl.run_etl()
