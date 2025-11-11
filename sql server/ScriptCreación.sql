-- Base de datos
CREATE DATABASE ventas_ms;
GO

USE ventas_ms;
GO

-- Esquema: sales_ms
CREATE SCHEMA sales_ms;
GO
CREATE TABLE sales_ms.Cliente (
	ClienteId INT IDENTITY PRIMARY KEY,
	Nombre NVARCHAR(120) NOT NULL,
	Email NVARCHAR(150) UNIQUE,
	Genero NVARCHAR(12) CHECK (Genero IN ('Masculino','Femenino')),
	Pais NVARCHAR(60) NOT NULL,
	FechaRegistro DATE NOT NULL DEFAULT (GETDATE())
);

CREATE TABLE sales_ms.Producto (
	ProductoId INT IDENTITY PRIMARY KEY,
	SKU NVARCHAR(40) UNIQUE NOT NULL, -- SKU “oficial”
	Nombre NVARCHAR(150) NOT NULL,
	Categoria NVARCHAR(80) NOT NULL
);

CREATE TABLE sales_ms.Orden (
	OrdenId INT IDENTITY PRIMARY KEY,
	ClienteId INT NOT NULL FOREIGN KEY REFERENCES sales_ms.Cliente(ClienteId),
	Fecha DATETIME2 NOT NULL DEFAULT (SYSDATETIME()),
	Canal NVARCHAR(20) NOT NULL CHECK (Canal IN ('WEB','TIENDA','APP')),
	Moneda CHAR(3) NOT NULL DEFAULT 'USD', -- homogénea en esta fuente
	Total DECIMAL(18,2) NOT NULL
);

CREATE TABLE sales_ms.OrdenDetalle (
	OrdenDetalleId INT IDENTITY PRIMARY KEY,
	OrdenId INT NOT NULL FOREIGN KEY REFERENCES sales_ms.Orden(OrdenId),
	ProductoId INT NOT NULL FOREIGN KEY REFERENCES
	sales_ms.Producto(ProductoId),
	Cantidad INT NOT NULL CHECK (Cantidad > 0),
	PrecioUnit DECIMAL(18,2) NOT NULL, -- en USD
	DescuentoPct DECIMAL(5,2) NULL
);

-- Índices sugeridos
CREATE INDEX IX_Orden_Fecha ON sales_ms.Orden(Fecha);
CREATE INDEX IX_Detalle_Prod ON sales_ms.OrdenDetalle(ProductoId);
