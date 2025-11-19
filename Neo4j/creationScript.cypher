// ============================================================
// SCRIPT COMPLETO NEO4J - BASE DE DATOS DE VENTAS
// Proyecto Final - Bases de Datos II
// ============================================================

// ------------------------------------------------------------
// 1. LIMPIAR BASE DE DATOS (OPCIONAL - USAR CON CUIDADO)
// ------------------------------------------------------------
// MATCH (n) DETACH DELETE n;

// ------------------------------------------------------------
// 2. CREAR CONSTRAINTS E ÍNDICES
// ------------------------------------------------------------

// Constraints para unicidad
CREATE CONSTRAINT cliente_id IF NOT EXISTS
FOR (c:Cliente) REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT producto_id IF NOT EXISTS
FOR (p:Producto) REQUIRE p.id IS UNIQUE;

CREATE CONSTRAINT categoria_id IF NOT EXISTS
FOR (c:Categoria) REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT orden_id IF NOT EXISTS
FOR (o:Orden) REQUIRE o.id IS UNIQUE;

// Índices para optimización de búsquedas
CREATE INDEX orden_fecha IF NOT EXISTS FOR (o:Orden) ON (o.fecha);
CREATE INDEX cliente_pais IF NOT EXISTS FOR (c:Cliente) ON (c.pais);
CREATE INDEX producto_categoria IF NOT EXISTS FOR (p:Producto) ON (p.categoria);
CREATE INDEX orden_canal IF NOT EXISTS FOR (o:Orden) ON (o.canal);
CREATE INDEX orden_moneda IF NOT EXISTS FOR (o:Orden) ON (o.moneda);
CREATE INDEX categoria_nombre IF NOT EXISTS FOR (c:Categoria) ON (c.nombre);

// ------------------------------------------------------------
// 3. CREAR CATEGORÍAS (15 categorías)
// ------------------------------------------------------------

CREATE (cat1:Categoria {id: 'CAT-001', nombre: 'Electrónica'}),
       (cat2:Categoria {id: 'CAT-002', nombre: 'Ropa'}),
       (cat3:Categoria {id: 'CAT-003', nombre: 'Alimentos'}),
       (cat4:Categoria {id: 'CAT-004', nombre: 'Hogar'}),
       (cat5:Categoria {id: 'CAT-005', nombre: 'Deportes'}),
       (cat6:Categoria {id: 'CAT-006', nombre: 'Libros'}),
       (cat7:Categoria {id: 'CAT-007', nombre: 'Juguetes'}),
       (cat8:Categoria {id: 'CAT-008', nombre: 'Belleza'}),
       (cat9:Categoria {id: 'CAT-009', nombre: 'Automóvil'}),
       (cat10:Categoria {id: 'CAT-010', nombre: 'Mascotas'}),
       (cat11:Categoria {id: 'CAT-011', nombre: 'Jardín'}),
       (cat12:Categoria {id: 'CAT-012', nombre: 'Oficina'}),
       (cat13:Categoria {id: 'CAT-013', nombre: 'Música'}),
       (cat14:Categoria {id: 'CAT-014', nombre: 'Salud'}),
       (cat15:Categoria {id: 'CAT-015', nombre: 'Bebidas'});

// ------------------------------------------------------------
// 4. CREAR PRODUCTOS (520 productos con códigos heterogéneos)
// ------------------------------------------------------------

// Electrónica (40 productos)
UNWIND range(1, 40) AS i
CREATE (p:Producto {
  id: 'PROD-E-' + toString(i),
  nombre: 'Producto Electrónica ' + toString(i),
  categoria: 'Electrónica',
  sku: CASE WHEN i % 3 = 0 THEN null ELSE 'SKU-E-' + toString(1000 + i) END,
  codigo_alt: CASE WHEN i % 2 = 0 THEN 'ALT-E-' + toString(2000 + i) ELSE null END,
  codigo_mongo: 'MN-E-' + toString(3000 + i)
});

// Ropa (50 productos)
UNWIND range(1, 50) AS i
CREATE (p:Producto {
  id: 'PROD-R-' + toString(i),
  nombre: 'Producto Ropa ' + toString(i),
  categoria: 'Ropa',
  sku: CASE WHEN i % 4 = 0 THEN null ELSE 'SKU-R-' + toString(1100 + i) END,
  codigo_alt: 'ALT-R-' + toString(2100 + i),
  codigo_mongo: CASE WHEN i % 3 = 0 THEN null ELSE 'MN-R-' + toString(3100 + i) END
});

// Alimentos (60 productos)
UNWIND range(1, 60) AS i
CREATE (p:Producto {
  id: 'PROD-A-' + toString(i),
  nombre: 'Producto Alimentos ' + toString(i),
  categoria: 'Alimentos',
  sku: 'SKU-A-' + toString(1200 + i),
  codigo_alt: CASE WHEN i % 2 = 0 THEN 'ALT-A-' + toString(2200 + i) ELSE null END,
  codigo_mongo: 'MN-A-' + toString(3200 + i)
});

// Hogar (45 productos)
UNWIND range(1, 45) AS i
CREATE (p:Producto {
  id: 'PROD-H-' + toString(i),
  nombre: 'Producto Hogar ' + toString(i),
  categoria: 'Hogar',
  sku: CASE WHEN i % 5 = 0 THEN null ELSE 'SKU-H-' + toString(1300 + i) END,
  codigo_alt: 'ALT-H-' + toString(2300 + i),
  codigo_mongo: 'MN-H-' + toString(3300 + i)
});

// Deportes (40 productos)
UNWIND range(1, 40) AS i
CREATE (p:Producto {
  id: 'PROD-D-' + toString(i),
  nombre: 'Producto Deportes ' + toString(i),
  categoria: 'Deportes',
  sku: 'SKU-D-' + toString(1400 + i),
  codigo_alt: CASE WHEN i % 3 = 0 THEN null ELSE 'ALT-D-' + toString(2400 + i) END,
  codigo_mongo: 'MN-D-' + toString(3400 + i)
});

// Libros (35 productos)
UNWIND range(1, 35) AS i
CREATE (p:Producto {
  id: 'PROD-L-' + toString(i),
  nombre: 'Producto Libros ' + toString(i),
  categoria: 'Libros',
  sku: 'SKU-L-' + toString(1500 + i),
  codigo_alt: 'ALT-L-' + toString(2500 + i),
  codigo_mongo: CASE WHEN i % 4 = 0 THEN null ELSE 'MN-L-' + toString(3500 + i) END
});

// Juguetes (40 productos)
UNWIND range(1, 40) AS i
CREATE (p:Producto {
  id: 'PROD-J-' + toString(i),
  nombre: 'Producto Juguetes ' + toString(i),
  categoria: 'Juguetes',
  sku: CASE WHEN i % 3 = 0 THEN null ELSE 'SKU-J-' + toString(1600 + i) END,
  codigo_alt: 'ALT-J-' + toString(2600 + i),
  codigo_mongo: 'MN-J-' + toString(3600 + i)
});

// Belleza (35 productos)
UNWIND range(1, 35) AS i
CREATE (p:Producto {
  id: 'PROD-B-' + toString(i),
  nombre: 'Producto Belleza ' + toString(i),
  categoria: 'Belleza',
  sku: 'SKU-B-' + toString(1700 + i),
  codigo_alt: CASE WHEN i % 2 = 0 THEN 'ALT-B-' + toString(2700 + i) ELSE null END,
  codigo_mongo: 'MN-B-' + toString(3700 + i)
});

// Automóvil (30 productos)
UNWIND range(1, 30) AS i
CREATE (p:Producto {
  id: 'PROD-AU-' + toString(i),
  nombre: 'Producto Automóvil ' + toString(i),
  categoria: 'Automóvil',
  sku: CASE WHEN i % 4 = 0 THEN null ELSE 'SKU-AU-' + toString(1800 + i) END,
  codigo_alt: 'ALT-AU-' + toString(2800 + i),
  codigo_mongo: 'MN-AU-' + toString(3800 + i)
});

// Mascotas (30 productos)
UNWIND range(1, 30) AS i
CREATE (p:Producto {
  id: 'PROD-M-' + toString(i),
  nombre: 'Producto Mascotas ' + toString(i),
  categoria: 'Mascotas',
  sku: 'SKU-M-' + toString(1900 + i),
  codigo_alt: CASE WHEN i % 3 = 0 THEN null ELSE 'ALT-M-' + toString(2900 + i) END,
  codigo_mongo: 'MN-M-' + toString(3900 + i)
});

// Jardín (25 productos)
UNWIND range(1, 25) AS i
CREATE (p:Producto {
  id: 'PROD-JA-' + toString(i),
  nombre: 'Producto Jardín ' + toString(i),
  categoria: 'Jardín',
  sku: CASE WHEN i % 5 = 0 THEN null ELSE 'SKU-JA-' + toString(2000 + i) END,
  codigo_alt: 'ALT-JA-' + toString(3000 + i),
  codigo_mongo: 'MN-JA-' + toString(4000 + i)
});

// Oficina (30 productos)
UNWIND range(1, 30) AS i
CREATE (p:Producto {
  id: 'PROD-OF-' + toString(i),
  nombre: 'Producto Oficina ' + toString(i),
  categoria: 'Oficina',
  sku: 'SKU-OF-' + toString(2100 + i),
  codigo_alt: 'ALT-OF-' + toString(3100 + i),
  codigo_mongo: CASE WHEN i % 4 = 0 THEN null ELSE 'MN-OF-' + toString(4100 + i) END
});

// Música (20 productos)
UNWIND range(1, 20) AS i
CREATE (p:Producto {
  id: 'PROD-MU-' + toString(i),
  nombre: 'Producto Música ' + toString(i),
  categoria: 'Música',
  sku: CASE WHEN i % 3 = 0 THEN null ELSE 'SKU-MU-' + toString(2200 + i) END,
  codigo_alt: 'ALT-MU-' + toString(3200 + i),
  codigo_mongo: 'MN-MU-' + toString(4200 + i)
});

// Salud (20 productos)
UNWIND range(1, 20) AS i
CREATE (p:Producto {
  id: 'PROD-SA-' + toString(i),
  nombre: 'Producto Salud ' + toString(i),
  categoria: 'Salud',
  sku: 'SKU-SA-' + toString(2300 + i),
  codigo_alt: CASE WHEN i % 2 = 0 THEN 'ALT-SA-' + toString(3300 + i) ELSE null END,
  codigo_mongo: 'MN-SA-' + toString(4300 + i)
});

// Bebidas (20 productos)
UNWIND range(1, 20) AS i
CREATE (p:Producto {
  id: 'PROD-BE-' + toString(i),
  nombre: 'Producto Bebidas ' + toString(i),
  categoria: 'Bebidas',
  sku: CASE WHEN i % 4 = 0 THEN null ELSE 'SKU-BE-' + toString(2400 + i) END,
  codigo_alt: 'ALT-BE-' + toString(3400 + i),
  codigo_mongo: 'MN-BE-' + toString(4400 + i)
});

// ------------------------------------------------------------
// 5. CREAR RELACIONES PRODUCTO -> CATEGORIA
// ------------------------------------------------------------
// ✅ CORREGIDO: Evita cartesian product

MATCH (p:Producto)
WHERE p.categoria IS NOT NULL
WITH p
MATCH (c:Categoria {nombre: p.categoria})
CREATE (p)-[:PERTENECE_A]->(c);

// ------------------------------------------------------------
// 6. CREAR CLIENTES (3000 clientes con géneros heterogéneos)
// ------------------------------------------------------------

WITH ['Costa Rica', 'México', 'Colombia', 'Argentina', 'Chile', 'Perú', 'España', 'Estados Unidos', 'Ecuador', 'Uruguay'] AS paises,
     ['M', 'F', 'Masculino', 'Femenino', 'Otro', 'X'] AS generos,
     ['Juan', 'María', 'Carlos', 'Ana', 'Luis', 'Carmen', 'José', 'Laura', 'Pedro', 'Sofia', 'Diego', 'Isabel', 'Miguel', 'Patricia', 'Antonio'] AS nombres,
     ['García', 'Rodríguez', 'Martínez', 'López', 'González', 'Pérez', 'Sánchez', 'Ramírez', 'Torres', 'Flores', 'Rivera', 'Gómez', 'Díaz', 'Cruz', 'Morales'] AS apellidos

UNWIND range(1, 3000) AS i
CREATE (c:Cliente {
  id: 'CLI-' + toString(10000 + i),
  nombre: nombres[i % size(nombres)] + ' ' + apellidos[(i * 7) % size(apellidos)],
  genero: generos[i % size(generos)],
  pais: paises[i % size(paises)]
});

// ------------------------------------------------------------
// 7. CREAR ÓRDENES Y RELACIONES (25000+ órdenes con datos 2024-2025)
// ------------------------------------------------------------

WITH ['WEB', 'TIENDA', 'APP', 'PARTNER'] AS canales,
     ['USD', 'CRC'] AS monedas

MATCH (c:Cliente)
WITH c, canales, monedas, toInteger(rand() * 10) + 5 AS numOrdenes
UNWIND range(1, numOrdenes) AS orderNum

WITH c, canales, monedas, orderNum,
     toInteger(rand() * 730) AS diasAtras,
     toInteger(rand() * 4) AS canalIdx,
     toInteger(rand() * 2) AS monedaIdx,
     toInteger(rand() * 150000) + 10000 AS totalCRC,
     toFloat(rand() * 500) + 20 AS totalUSD

CREATE (o:Orden {
  id: 'ORD-' + c.id + '-' + toString(orderNum),
  fecha: datetime() - duration({days: diasAtras}),
  canal: canales[canalIdx],
  moneda: monedas[monedaIdx],
  total: CASE WHEN monedas[monedaIdx] = 'CRC' THEN totalCRC ELSE round(totalUSD * 100) / 100 END
})
CREATE (c)-[:REALIZO]->(o);

// ------------------------------------------------------------
// 8. CREAR DETALLES DE ORDEN (RELACIÓN ORDEN -> PRODUCTO)
// ------------------------------------------------------------

MATCH (o:Orden)
WITH o, toInteger(rand() * 4) + 1 AS numProductos
MATCH (p:Producto)
WITH o, collect(p) AS todosProductos, numProductos
WITH o, [i IN range(0, numProductos-1) | todosProductos[toInteger(rand() * size(todosProductos))]] AS productosSeleccionados

UNWIND productosSeleccionados AS prod
WITH o, prod, toInteger(rand() * 5) + 1 AS cantidad, toFloat(rand() * 200) + 10 AS precio

MERGE (o)-[r:CONTIENE]->(prod)
ON CREATE SET 
  r.cantidad = cantidad,
  r.precio_unit = round(precio * 100) / 100;

// ------------------------------------------------------------
// 9. CREAR RELACIONES DE EQUIVALENCIA ENTRE PRODUCTOS
// ------------------------------------------------------------

// ✅ EQUIVALENCIAS ELECTRÓNICA (CORREGIDO)
MATCH (p1:Producto)
WHERE p1.categoria = 'Electrónica'
  AND toInteger(substring(p1.id, 7)) <= 10
WITH p1
MATCH (p2:Producto)
WHERE p2.categoria = 'Electrónica'
  AND p2.id <> p1.id
  AND substring(p2.id, 7) = substring(p1.id, 7)
CREATE (p1)-[:EQUIVALE_A {
  razon: 'Mismo producto en diferentes sistemas',
  confidence: 0.95
}]->(p2);

// ✅ EQUIVALENCIAS ROPA (CORREGIDO)
MATCH (p1:Producto)
WHERE p1.categoria = 'Ropa'
  AND toInteger(substring(p1.id, 7)) <= 15
WITH p1
MATCH (p2:Producto)
WHERE p2.categoria = 'Ropa'
  AND p2.id <> p1.id
  AND (toInteger(substring(p1.id, 7)) % 5) = (toInteger(substring(p2.id, 7)) % 5)
  AND toInteger(substring(p2.id, 7)) <= 15
CREATE (p1)-[:EQUIVALE_A {
  razon: 'SKU alternativo',
  confidence: 0.90
}]->(p2);

// ✅ EQUIVALENCIAS ALIMENTOS (CORREGIDO)
MATCH (p1:Producto)
WHERE p1.categoria = 'Alimentos'
  AND toInteger(substring(p1.id, 7)) <= 12
WITH p1
MATCH (p2:Producto)
WHERE p2.categoria = 'Alimentos'
  AND p2.id <> p1.id
  AND (toInteger(substring(p1.id, 7)) % 6) = (toInteger(substring(p2.id, 7)) % 6)
CREATE (p1)-[:EQUIVALE_A {
  razon: 'Código Mongo vinculado',
  confidence: 0.88
}]->(p2);

// ✅ EQUIVALENCIAS CRUZADAS POR CÓDIGOS (CORREGIDO)
MATCH (p1:Producto)
WHERE toInteger(coalesce(substring(p1.sku, 5), substring(p1.codigo_alt, 5), substring(p1.codigo_mongo, 4), '9999')) <= 1050
WITH p1
MATCH (p2:Producto)
WHERE p2.id > p1.id
  AND p2.categoria = p1.categoria
  AND (
    (p1.sku IS NOT NULL AND p2.codigo_alt IS NOT NULL AND substring(p1.sku, 5) = substring(p2.codigo_alt, 5))
    OR (p1.codigo_alt IS NOT NULL AND p2.codigo_mongo IS NOT NULL AND substring(p1.codigo_alt, 5) = substring(p2.codigo_mongo, 4))
    OR (p1.sku IS NOT NULL AND p2.codigo_mongo IS NOT NULL AND substring(p1.sku, 5) = substring(p2.codigo_mongo, 4))
  )
CREATE (p1)-[:EQUIVALE_A {
  razon: 'Códigos coincidentes entre sistemas',
  confidence: 0.92
}]->(p2);

// ✅ EQUIVALENCIAS BIDIRECCIONALES (CORREGIDO)
MATCH (p1:Producto)
WHERE p1.categoria IN ['Electrónica', 'Deportes', 'Hogar']
  AND toInteger(substring(p1.id, 7)) <= 5
WITH p1
MATCH (p2:Producto)
WHERE p2.id <> p1.id
  AND p2.categoria = p1.categoria
  AND toInteger(substring(p2.id, 7)) = toInteger(substring(p1.id, 7))
MERGE (p1)-[:EQUIVALE_A {
  razon: 'Producto estrella - equivalencia confirmada',
  confidence: 1.0,
  validado_por: 'ETL_Admin'
}]->(p2)
MERGE (p2)-[:EQUIVALE_A {
  razon: 'Producto estrella - equivalencia confirmada',
  confidence: 1.0,
  validado_por: 'ETL_Admin'
}]->(p1);

// ------------------------------------------------------------
// 10. VERIFICACIÓN Y ESTADÍSTICAS
// ------------------------------------------------------------

MATCH (c:Cliente) RETURN 'Clientes' AS tipo, count(c) AS cantidad
UNION
MATCH (p:Producto) RETURN 'Productos' AS tipo, count(p) AS cantidad
UNION
MATCH (cat:Categoria) RETURN 'Categorías' AS tipo, count(cat) AS cantidad
UNION
MATCH (o:Orden) RETURN 'Órdenes' AS tipo, count(o) AS cantidad
UNION
MATCH ()-[r:CONTIENE]->() RETURN 'Items en Órdenes' AS tipo, count(r) AS cantidad
UNION
MATCH ()-[r:REALIZO]->() RETURN 'Relaciones Cliente-Orden' AS tipo, count(r) AS cantidad
UNION
MATCH ()-[r:PERTENECE_A]->() RETURN 'Relaciones Producto-Categoría' AS tipo, count(r) AS cantidad
UNION
MATCH ()-[r:EQUIVALE_A]->() RETURN 'Relaciones de Equivalencia' AS tipo, count(r) AS cantidad;

//----------------------------------------------------------------------------------
// ============================================================
// SCRIPT NEO4J - BASE DE DATOS DE VENTAS (VERSIÓN REDUCIDA)
// 100 clientes, 50 productos, ~300 órdenes
// ============================================================

// ------------------------------------------------------------
// 1. LIMPIAR BASE DE DATOS
// ------------------------------------------------------------
MATCH (n) DETACH DELETE n;

// ------------------------------------------------------------
// 2. CREAR CONSTRAINTS E ÍNDICES
// ------------------------------------------------------------

CREATE CONSTRAINT cliente_id IF NOT EXISTS
FOR (c:Cliente) REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT producto_id IF NOT EXISTS
FOR (p:Producto) REQUIRE p.id IS UNIQUE;

CREATE CONSTRAINT categoria_id IF NOT EXISTS
FOR (c:Categoria) REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT orden_id IF NOT EXISTS
FOR (o:Orden) REQUIRE o.id IS UNIQUE;

CREATE INDEX orden_fecha IF NOT EXISTS FOR (o:Orden) ON (o.fecha);
CREATE INDEX cliente_pais IF NOT EXISTS FOR (c:Cliente) ON (c.pais);
CREATE INDEX producto_categoria IF NOT EXISTS FOR (p:Producto) ON (p.categoria);

// ------------------------------------------------------------
// 3. CREAR CATEGORÍAS (10 categorías)
// ------------------------------------------------------------

CREATE (cat1:Categoria {id: 'CAT-001', nombre: 'Electrónica'}),
       (cat2:Categoria {id: 'CAT-002', nombre: 'Ropa'}),
       (cat3:Categoria {id: 'CAT-003', nombre: 'Alimentos'}),
       (cat4:Categoria {id: 'CAT-004', nombre: 'Hogar'}),
       (cat5:Categoria {id: 'CAT-005', nombre: 'Deportes'}),
       (cat6:Categoria {id: 'CAT-006', nombre: 'Libros'}),
       (cat7:Categoria {id: 'CAT-007', nombre: 'Juguetes'}),
       (cat8:Categoria {id: 'CAT-008', nombre: 'Belleza'}),
       (cat9:Categoria {id: 'CAT-009', nombre: 'Tecnología'}),
       (cat10:Categoria {id: 'CAT-010', nombre: 'Mascotas'});

// ------------------------------------------------------------
// 4. CREAR PRODUCTOS (50 productos)
// ------------------------------------------------------------

WITH ['Electrónica', 'Ropa', 'Alimentos', 'Hogar', 'Deportes', 'Libros', 'Juguetes', 'Belleza', 'Tecnología', 'Mascotas'] AS categorias,
     ['Laptop', 'Mouse', 'Teclado', 'Monitor', 'Auriculares', 
      'Camisa', 'Pantalón', 'Zapatos', 'Vestido', 'Chaqueta',
      'Arroz', 'Pasta', 'Aceite', 'Café', 'Leche',
      'Lámpara', 'Silla', 'Mesa', 'Almohada', 'Cortina',
      'Balón', 'Raqueta', 'Pesas', 'Bicicleta', 'Casco',
      'Novela', 'Cómic', 'Revista', 'Diccionario', 'Atlas',
      'Muñeca', 'Carro RC', 'Lego', 'Puzzle', 'Robot',
      'Shampoo', 'Crema', 'Perfume', 'Maquillaje', 'Jabón',
      'Smartphone', 'Tablet', 'Cámara', 'Drone', 'Smartwatch',
      'Comida Perro', 'Arena Gato', 'Juguete Mascota', 'Correa', 'Cama Mascota'] AS productos

UNWIND range(1, 50) AS i
CREATE (p:Producto {
  id: 'PROD-' + toString(10000 + i),
  nombre: productos[(i - 1) % size(productos)],
  categoria: categorias[(i - 1) % size(categorias)],
  sku: CASE WHEN i % 3 = 0 THEN null ELSE 'SKU-' + toString(20000 + i) END,
  codigo_alt: CASE WHEN i % 2 = 0 THEN 'ALT-' + toString(30000 + i) ELSE null END,
  codigo_mongo: 'MN-' + toString(40000 + i),
  precio: toFloat(round((rand() * 490 + 10) * 100) / 100)
});

// ------------------------------------------------------------
// 5. CREAR RELACIONES PRODUCTO -> CATEGORIA
// ------------------------------------------------------------

MATCH (p:Producto)
WHERE p.categoria IS NOT NULL
WITH p
MATCH (c:Categoria {nombre: p.categoria})
CREATE (p)-[:PERTENECE_A]->(c);

// ------------------------------------------------------------
// 6. CREAR CLIENTES (100 clientes)
// ------------------------------------------------------------

WITH ['Costa Rica', 'México', 'Colombia', 'Argentina', 'Chile', 'Perú', 'España', 'Estados Unidos', 'Ecuador', 'Uruguay'] AS paises,
     ['Masculino', 'Femenino', 'M', 'F', 'Otro', 'X'] AS generos,
     ['Ana', 'Carlos', 'María', 'José', 'Laura', 'Pedro', 'Sofia', 'Miguel', 'Carmen', 'Luis', 
      'Isabel', 'Diego', 'Elena', 'Roberto', 'Patricia', 'Fernando', 'Rosa', 'Antonio', 'Marta', 'Jorge'] AS nombres,
     ['García', 'Rodríguez', 'Martínez', 'López', 'González', 'Hernández', 'Pérez', 'Sánchez', 
      'Ramírez', 'Torres', 'Flores', 'Rivera', 'Gómez', 'Díaz', 'Cruz', 'Morales', 'Jiménez', 
      'Reyes', 'Álvarez', 'Romero'] AS apellidos

UNWIND range(1, 100) AS i
CREATE (c:Cliente {
  id: 'CLI-' + toString(10000 + i),
  nombre: nombres[i % size(nombres)] + ' ' + apellidos[(i * 7) % size(apellidos)],
  genero: generos[i % size(generos)],
  pais: paises[i % size(paises)]
});

// ------------------------------------------------------------
// 7. CREAR ÓRDENES Y RELACIONES (~300 órdenes)
// ------------------------------------------------------------

WITH ['Online', 'Tienda Física', 'Teléfono', 'App Móvil'] AS canales,
     ['USD', 'CRC', 'EUR', 'MXN'] AS monedas

MATCH (c:Cliente)
WITH c, canales, monedas, toInteger(rand() * 4) + 2 AS numOrdenes
UNWIND range(1, numOrdenes) AS orderNum

WITH c, canales, monedas, orderNum,
     toInteger(rand() * 365) AS diasAtras,
     canales[toInteger(rand() * size(canales))] AS canal,
     monedas[toInteger(rand() * size(monedas))] AS moneda

CREATE (o:Orden {
  id: 'ORD-' + c.id + '-' + toString(orderNum),
  fecha: date('2024-01-01') + duration({days: diasAtras}),
  canal: canal,
  moneda: moneda,
  total: toFloat(round((rand() * 980 + 20) * 100) / 100)
})

CREATE (c)-[:REALIZO]->(o);

// ------------------------------------------------------------
// 8. CREAR DETALLES DE ORDEN (RELACIÓN ORDEN -> PRODUCTO)
// ------------------------------------------------------------

MATCH (o:Orden)
WITH o
MATCH (p:Producto)
WITH o, collect(p) AS productos, toInteger(rand() * 4) + 1 AS numProductos
WITH o, [i IN range(0, numProductos-1) | productos[toInteger(rand() * size(productos))]] AS productosSeleccionados

UNWIND productosSeleccionados AS prod
WITH DISTINCT o, prod
CREATE (o)-[:CONTIENE {
  cantidad: toInteger(rand() * 5) + 1,
  precio_unitario: toFloat(round((rand() * 190 + 10) * 100) / 100)
}]->(prod);

// ------------------------------------------------------------
// 9. CREAR RELACIONES DE EQUIVALENCIA ENTRE PRODUCTOS
// ------------------------------------------------------------

// Equivalencias por categoría (productos similares)
MATCH (p1:Producto)
WHERE p1.categoria IN ['Electrónica', 'Ropa', 'Deportes']
WITH p1
MATCH (p2:Producto)
WHERE p2.categoria = p1.categoria 
  AND p2.id <> p1.id
  AND toInteger(substring(p1.id, 5)) % 10 = toInteger(substring(p2.id, 5)) % 10
WITH p1, p2
LIMIT 30
CREATE (p1)-[:EQUIVALE_A {
  razon: 'Mismo tipo de producto',
  confidence: 0.85
}]->(p2);

// Equivalencias por códigos coincidentes
MATCH (p1:Producto)
WHERE p1.sku IS NOT NULL
WITH p1
MATCH (p2:Producto)
WHERE p2.id > p1.id
  AND p2.codigo_alt IS NOT NULL
  AND substring(p1.sku, 4) = substring(p2.codigo_alt, 4)
WITH p1, p2
LIMIT 20
CREATE (p1)-[:EQUIVALE_A {
  razon: 'Códigos coincidentes',
  confidence: 0.92
}]->(p2);

// ------------------------------------------------------------
// 10. VERIFICACIÓN Y ESTADÍSTICAS
// ------------------------------------------------------------

MATCH (c:Cliente) 
RETURN 'Clientes' AS tipo, count(c) AS cantidad
UNION
MATCH (p:Producto) 
RETURN 'Productos' AS tipo, count(p) AS cantidad
UNION
MATCH (cat:Categoria) 
RETURN 'Categorías' AS tipo, count(cat) AS cantidad
UNION
MATCH (o:Orden) 
RETURN 'Órdenes' AS tipo, count(o) AS cantidad
UNION
MATCH ()-[r:CONTIENE]->() 
RETURN 'Items en Órdenes' AS tipo, count(r) AS cantidad
UNION
MATCH ()-[r:REALIZO]->() 
RETURN 'Relaciones Cliente-Orden' AS tipo, count(r) AS cantidad
UNION
MATCH ()-[r:PERTENECE_A]->() 
RETURN 'Producto-Categoría' AS tipo, count(r) AS cantidad
UNION
MATCH ()-[r:EQUIVALE_A]->() 
RETURN 'Equivalencias' AS tipo, count(r) AS cantidad
ORDER BY cantidad DESC;