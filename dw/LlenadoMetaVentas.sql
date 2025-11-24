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
    fv.IdProducto,
    fv.IdCliente,
    t.Anio,
    t.Mes,
    ROUND(
        -- Meta = 80% del promedio de ventas reales de esa combinación cliente-producto-mes
        -- Esto garantiza cumplimientos entre 80% y 120% aproximadamente
        AVG(fv.TotalVentas) * 0.8 * 
        -- Variabilidad: 0.9 a 1.1 para diversificar cumplimientos
        (0.9 + ((fv.IdProducto * 7 + fv.IdCliente * 11 + t.Mes * 3) % 20) * 0.01),
        2
    ) AS MetaUSD
FROM FactVentas fv
INNER JOIN DimTiempo t ON fv.IdTiempo = t.IdTiempo
WHERE t.Anio IN (2023, 2024, 2025)
    AND fv.IdProducto <= 50  -- Solo primeros 50 productos
    AND fv.IdCliente <= 50   -- Solo primeros 50 clientes
GROUP BY fv.IdProducto, fv.IdCliente, t.Anio, t.Mes
HAVING AVG(fv.TotalVentas) > 0;  -- Solo donde hay ventas
GO


