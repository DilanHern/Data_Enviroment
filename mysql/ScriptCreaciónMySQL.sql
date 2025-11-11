-- database: sales_mysql
CREATE DATABASE sales_mysql;

USE sales_mysql;

CREATE TABLE Cliente (
	id INT AUTO_INCREMENT PRIMARY KEY,
	nombre VARCHAR(120) NOT NULL,
	correo VARCHAR(150),
	genero ENUM('M','F','X') DEFAULT 'M', -- distinto a SQL Server
	pais VARCHAR(60) NOT NULL,
	created_at VARCHAR(10) NOT NULL -- 'YYYY-MM-DD' (forzará parsing en ETL)
);
CREATE TABLE Producto (
	id INT AUTO_INCREMENT PRIMARY KEY,
	codigo_alt VARCHAR(64) UNIQUE NOT NULL, -- código alterno (no coincide con SKU)
	nombre VARCHAR(150) NOT NULL,
	categoria VARCHAR(80) NOT NULL
);
CREATE TABLE Orden (
	id INT AUTO_INCREMENT PRIMARY KEY,
	cliente_id INT NOT NULL,
	fecha VARCHAR(19) NOT NULL, -- 'YYYY-MM-DD HH:MM:SS'
	canal VARCHAR(20) NOT NULL, -- libre (no controlado)
	moneda CHAR(3) NOT NULL, -- puede ser 'USD' o 'CRC'
	total VARCHAR(20) NOT NULL, -- a veces '1200.50' o '1,200.50'
	FOREIGN KEY (cliente_id) REFERENCES Cliente(id)
);
CREATE TABLE OrdenDetalle (
	id INT AUTO_INCREMENT PRIMARY KEY,
	orden_id INT NOT NULL,
	producto_id INT NOT NULL,
	cantidad INT NOT NULL,
	precio_unit VARCHAR(20) NOT NULL, -- string con comas/puntos
	FOREIGN KEY (orden_id) REFERENCES Orden(id),
	FOREIGN KEY (producto_id) REFERENCES Producto(id)
);
CREATE INDEX IX_Orden_cliente ON Orden(cliente_id);
CREATE INDEX IX_Detalle_producto ON OrdenDetalle(producto_id);