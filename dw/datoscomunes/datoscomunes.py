import os
import json
import uuid
import platform
import logging
from dotenv import load_dotenv

try:
	import pyodbc
except Exception:
	pyodbc = None

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def _get_driver_name():
	if platform.system() == "Windows":
		return "ODBC Driver 17 for SQL Server"
	return "ODBC Driver 18 for SQL Server"


def connect_to_database():
	"""Crear y devolver una conexión pyodbc usando variables de entorno.

	Variables usadas: `serverenv`, `databaseenv`, `usernameenv`, `passwordenv`.
	"""
	if pyodbc is None:
		logging.error("pyodbc no está instalado. Instale pyodbc en el entorno virtual antes de ejecutar.")
		return None

	server = os.getenv("serverenv", "localhost")
	database = os.getenv("databaseenv", "DW_VENTAS")
	username = os.getenv("usernameenv")
	password = os.getenv("passwordenv")
	driver = _get_driver_name()

	try:
		if username and password:
			connection_string = (
				f'DRIVER={{{driver}}};'
				f'SERVER={server};'
				f'DATABASE={database};'
				f'UID={username};'
				f'PWD={password};'
				'TrustServerCertificate=yes;'
			)
			logging.info(f"Conectando a SQL Server: {server}/{database} con usuario {username}")
		else:
			connection_string = (
				f'DRIVER={{{driver}}};'
				f'SERVER={server};'
				f'DATABASE={database};'
				'Trusted_Connection=yes;'
				'TrustServerCertificate=yes;'
			)
			logging.info(f"Conectando a SQL Server: {server}/{database} con autenticación Windows")

		conn = pyodbc.connect(connection_string)
		return conn
	except Exception as e:
		logging.error(f"Error conectando a la base de datos: {e}")
		return None


def load_json_to_equivalencias(json_path: str, upsert=True):
	if not os.path.exists(json_path):
		logging.error(f"Archivo no encontrado: {json_path}")
		return False

	try:
		with open(json_path, 'r', encoding='utf-8') as f:
			data = json.load(f)

		rows = data if isinstance(data, list) else data.get('rows', [])

		if not rows:
			logging.warning("No se encontraron filas en el JSON")
			return True

		conn = connect_to_database()
		if not conn:
			logging.error("No se pudo establecer conexión a la BD. Abortando carga.")
			return False

		cursor = conn.cursor()
		inserted = 0
		updated = 0

		for r in rows:
			sku = r.get('SKU') or r.get('sku')
			if not sku:
				continue

			# Campos adicionales para DimProducto (si vienen en el JSON)
			nombre = r.get('Nombre') or r.get('nombre') or r.get('NombreProducto') or r.get('nombreProducto')
			categoria = r.get('Categoria') or r.get('categoria') or r.get('CategoriaProducto') or r.get('categoriaProducto')

			# No generar datos que no estén en el JSON.
			codigo_mongo = r.get('CodigoMongo') or r.get('codigoMongo') or r.get('codigo_mongo')
			codigo_alt = r.get('CodigoAlt') or r.get('codigoAlt') or r.get('codigo_alt')

			try:
				cursor.execute("SELECT Id FROM Equivalencias WHERE SKU = ?", sku)
				existing = cursor.fetchone()
			except Exception as e:
				logging.error(f"Error consultando Equivalencias SKU={sku}: {e}")
				continue

			# Si existe la equivalencia y se permite upsert, actualizar campos que vengan
			if existing:
				if upsert:
					sets = []
					params = []
					if codigo_mongo is not None:
						sets.append("CodigoMongo = ?")
						params.append(codigo_mongo)
					if codigo_alt is not None:
						sets.append("CodigoAlt = ?")
						params.append(codigo_alt)

					if sets:
						sql = f"UPDATE Equivalencias SET {', '.join(sets)} WHERE SKU = ?"
						params.append(sku)
						try:
							cursor.execute(sql, *params)
							updated += 1
						except Exception as e:
							logging.error(f"Error actualizando Equivalencias SKU={sku}: {e}")
							# no abortar: intentar sync de producto aun si fallo la equivalencia
					# sincronizar DimProducto si vienen datos de producto
					if nombre is not None or categoria is not None:
						try:
							cursor.execute("SELECT IdProducto FROM DimProducto WHERE SKU = ?", sku)
							prod = cursor.fetchone()
						except Exception as e:
							logging.error(f"Error consultando DimProducto SKU={sku}: {e}")
							prod = None

						if prod:
							psets = []
							pparams = []
							if nombre is not None:
								psets.append("Nombre = ?")
								pparams.append(nombre)
							if categoria is not None:
								psets.append("Categoria = ?")
								pparams.append(categoria)
							if psets:
								psql = f"UPDATE DimProducto SET {', '.join(psets)} WHERE SKU = ?"
								pparams.append(sku)
								try:
									cursor.execute(psql, *pparams)
								except Exception as e:
									logging.error(f"Error actualizando DimProducto SKU={sku}: {e}")
						else:
							# insertar nuevo producto con columnas disponibles
							pcols = ["SKU"]
							pplaceholders = ["?"]
							pparams = [sku]
							if nombre is not None:
								pcols.append("Nombre")
								pplaceholders.append("?")
								pparams.append(nombre)
							if categoria is not None:
								pcols.append("Categoria")
								pplaceholders.append("?")
								pparams.append(categoria)
							psql = f"INSERT INTO DimProducto ({', '.join(pcols)}) VALUES ({', '.join(pplaceholders)})"
							try:
								cursor.execute(psql, *pparams)
							except Exception as e:
								logging.error(f"Error insertando DimProducto SKU={sku}: {e}")

			else:
				# Insertar en Equivalencias
				cols = ["SKU"]
				placeholders = ["?"]
				params = [sku]
				if codigo_mongo is not None:
					cols.append("CodigoMongo")
					placeholders.append("?")
					params.append(codigo_mongo)
				if codigo_alt is not None:
					cols.append("CodigoAlt")
					placeholders.append("?")
					params.append(codigo_alt)

				sql = f"INSERT INTO Equivalencias ({', '.join(cols)}) VALUES ({', '.join(placeholders)})"
				try:
					cursor.execute(sql, *params)
					inserted += 1
				except Exception as e:
					logging.error(f"Error insertando Equivalencias SKU={sku}: {e}")
					# continuar con siguiente registro; no abortar por fallo en Equivalencias

				# Al crear Equivalencias, también crear DimProducto si no existe y hay datos
				try:
					cursor.execute("SELECT IdProducto FROM DimProducto WHERE SKU = ?", sku)
					prod = cursor.fetchone()
				except Exception as e:
					logging.error(f"Error verificando DimProducto SKU={sku}: {e}")
					prod = None

				if not prod and (nombre is not None or categoria is not None):
					pcols = ["SKU"]
					pplaceholders = ["?"]
					pparams = [sku]
					if nombre is not None:
						pcols.append("Nombre")
						pplaceholders.append("?")
						pparams.append(nombre)
					if categoria is not None:
						pcols.append("Categoria")
						pplaceholders.append("?")
						pparams.append(categoria)
					psql = f"INSERT INTO DimProducto ({', '.join(pcols)}) VALUES ({', '.join(pplaceholders)})"
					try:
						cursor.execute(psql, *pparams)
					except Exception as e:
						logging.error(f"Error insertando DimProducto SKU={sku}: {e}")

		conn.commit()
		cursor.close()
		conn.close()

		logging.info(f"Carga finalizada. Insertados: {inserted}, Actualizados: {updated}")
		return True

	except json.JSONDecodeError as e:
		logging.error(f"Error leyendo JSON: {e}")
		return False
	except Exception as e:
		logging.error(f"Error durante la carga: {e}")
		return False


def find_default_json_path():
	BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
	candidates = [
		# Prefer the repository root `equivalencias.json`
		os.path.join(BASE_DIR, "equivalencias.json"),
		# Try current working directory
		os.path.join(os.getcwd(), "equivalencias.json"),
		# Try one level above repository root
		os.path.join(BASE_DIR, "..", "equivalencias.json"),
		# Try relative to this package
		os.path.join(os.path.dirname(__file__), "..", "..", "equivalencias.json"),
	]

	for c in candidates:
		if os.path.exists(c):
			return c

	# fallback to first candidate (repo root path)
	return candidates[0]


def main():
	import argparse

	parser = argparse.ArgumentParser(description='Cargar equivalencias.json en tabla Equivalencias')
	parser.add_argument('json_path', nargs='?', default=None,
						help='Ruta al JSON (por defecto busca en rutas relativas al proyecto)')
	parser.add_argument('--no-upsert', dest='upsert', action='store_false', help='No actualizar registros existentes')

	args = parser.parse_args()

	# Determinar BASE_DIR relativo al paquete (dos niveles arriba de este archivo)
	BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

	# Intentar cargar .env.local en BASE_DIR si existe, si no cargar variables de entorno del entorno actual
	dotenv_path = os.path.join(BASE_DIR, ".env.local")
	if os.path.isfile(dotenv_path):
		load_dotenv(dotenv_path)
	else:
		load_dotenv()

	json_path = args.json_path or find_default_json_path()
	if not os.path.exists(json_path):
		logging.warning(f"No se encontró 'equivalencias.json' en rutas candidatas. Se usará por defecto: {json_path}")

	success = load_json_to_equivalencias(json_path, upsert=args.upsert)
	if not success:
		raise SystemExit(1)


if __name__ == '__main__':
	main()

