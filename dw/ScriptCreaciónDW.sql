-- CREACIÓN DE BASE DE DATOS
CREATE DATABASE DW_VENTAS;
GO

USE DW_VENTAS;
GO

-- TABLA DIMENSION TIEMPO
CREATE TABLE DimTiempo (
    IdTiempo INT IDENTITY(1,1) PRIMARY KEY,
    Anio INT NOT NULL,
    Mes INT NOT NULL,
    Dia INT NOT NULL,
    Fecha DATE NOT NULL,
    Semana INT,
    DiaSemana VARCHAR(15),
    TipoCambio DECIMAL(10,2)
);
GO

-- TABLA DIMENSION CLIENTE
CREATE TABLE DimCliente (
    IdCliente INT IDENTITY(1,1) PRIMARY KEY,
    Nombre VARCHAR(100) NOT NULL,
    Email VARCHAR(150),
    Genero CHAR(1),
    Pais VARCHAR(100),
    FechaCreacion DATE
);
GO

-- TABLA DIMENSION PRODUCTO
CREATE TABLE DimProducto (
    IdProducto INT IDENTITY(1,1) PRIMARY KEY,
    SKU VARCHAR(50) NOT NULL,
    Nombre VARCHAR(100) NOT NULL,
    Categoria VARCHAR(100)
);
GO

-- TABLA HECHOS: FACTVENTAS
CREATE TABLE FactVentas (
    IdFactVentas INT IDENTITY(1,1) PRIMARY KEY,
    IdTiempo INT NOT NULL,
    IdProducto INT NOT NULL,
    IdCliente INT NOT NULL,
    TotalVentas DECIMAL(18,2),
    Cantidad INT,
    Precio DECIMAL(18,2),

    CONSTRAINT FK_FactVentas_Tiempo FOREIGN KEY (IdTiempo)
        REFERENCES DimTiempo(IdTiempo),

    CONSTRAINT FK_FactVentas_Producto FOREIGN KEY (IdProducto)
        REFERENCES DimProducto(IdProducto),

    CONSTRAINT FK_FactVentas_Cliente FOREIGN KEY (IdCliente)
        REFERENCES DimCliente(IdCliente)
);
GO

-- TABLA METAVENTAS
CREATE TABLE MetaVentas (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    IdProducto INT NOT NULL,
    IdCliente INT NOT NULL,
    Anio INT NOT NULL,
    Mes INT NOT NULL,
    MetaUSD DECIMAL(18,2),

    CONSTRAINT FK_MetaVentas_Producto FOREIGN KEY (IdProducto)
        REFERENCES DimProducto(IdProducto),

    CONSTRAINT FK_MetaVentas_Cliente FOREIGN KEY (IdCliente)
        REFERENCES DimCliente(IdCliente)
);
GO

-- TABLA EQUIVALENCIAS
CREATE TABLE Equivalencias (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    SKU VARCHAR(10) NULL,
    CodigoMongo VARCHAR(10) NULL,
    CodigoAlt VARCHAR(10) NULL
);
GO
