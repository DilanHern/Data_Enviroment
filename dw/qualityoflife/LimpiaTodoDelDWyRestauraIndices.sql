select * from Equivalencias;
select * from DimProducto;
select * from DimCliente;
select * from FactVentas;
select * from DimCanal;
select * from DimTiempo;


Delete dbo.FactVentas;
Delete dbo.DimTiempo;
Delete dbo.DimProducto;
Delete dbo.DimCliente;
Delete dbo.Equivalencias;
DELETE dbo.DimCanal;
DECLARE @table NVARCHAR(255);

DECLARE cur CURSOR FOR
SELECT TABLE_SCHEMA + '.' + TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
AND OBJECTPROPERTY(OBJECT_ID(TABLE_SCHEMA + '.' + TABLE_NAME), 'TableHasIdentity') = 1;

OPEN cur;
FETCH NEXT FROM cur INTO @table;

WHILE @@FETCH_STATUS = 0
BEGIN
    DECLARE @sql NVARCHAR(400);
    SET @sql = 'DBCC CHECKIDENT (''' + @table + ''', RESEED, 0);';
    PRINT @sql;
    EXEC(@sql);

    FETCH NEXT FROM cur INTO @table;
END;

CLOSE cur;
DEALLOCATE cur;