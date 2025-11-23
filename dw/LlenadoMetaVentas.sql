-- ============================================
-- LLENADO DE METAVENTAS (2023-2025)
-- ============================================
-- Este llenado es necesario para realizar el análisis en PowerBI
-- PREREQUISITOS:
-- 1. Base de datos DW_VENTAS debe existir
-- 2. Tabla MetaVentas debe estar creada
-- 3. Tabla DimProducto debe tener al menos 5 productos
-- 4. Tabla DimCliente debe tener al menos 5 clientes
-- ============================================

USE DW_VENTAS;
GO

INSERT INTO MetaVentas (IdProducto, IdCliente, Anio, Mes, MetaUSD)
SELECT 
    p.IdProducto,
    c.IdCliente,
    a.Anio,
    m.Mes,
    ROUND(
        (5000 + (p.IdProducto * 500) + (c.IdCliente * 300)) * 
        (1 + (a.Anio - 2023) * 0.15) * 
        (1 + (m.Mes * 0.02)) * 
        (1 + ((p.IdProducto * c.IdCliente * a.Anio * m.Mes) % 50) * 0.01),
        2
    ) AS MetaUSD
FROM 
    (SELECT TOP 5 IdProducto FROM DimProducto ORDER BY IdProducto) p
CROSS JOIN 
    (SELECT TOP 5 IdCliente FROM DimCliente ORDER BY IdCliente) c
CROSS JOIN 
    (SELECT 2023 AS Anio UNION SELECT 2024 UNION SELECT 2025) a
CROSS JOIN 
    (SELECT 1 AS Mes UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 
     UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 
     UNION SELECT 9 UNION SELECT 10 UNION SELECT 11 UNION SELECT 12) m;
GO


