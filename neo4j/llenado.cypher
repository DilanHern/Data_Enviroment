// Eliminar nodos
MATCH (n)
DETACH DELETE n;
//------------------------------------------------------------------------
//-------- Crear 57 nodos Producto en comun con las demas bases ----------
//------------------------------------------------------------------------
// Constraint para Producto
CREATE CONSTRAINT producto_sku_unique IF NOT EXISTS
FOR (p:Producto) REQUIRE p.sku IS UNIQUE;

CREATE CONSTRAINT producto_codigo_alt_unique IF NOT EXISTS
FOR (p:Producto) REQUIRE p.codigo_alt IS UNIQUE;

CREATE CONSTRAINT producto_codigo_mongo_unique IF NOT EXISTS
FOR (p:Producto) REQUIRE p.codigo_mongo IS UNIQUE;

CREATE CONSTRAINT producto_id IF NOT EXISTS
FOR (p:Producto) REQUIRE p.id IS UNIQUE;

// Crear nodos Categoria
MERGE (c1:Categoria {id: 'cat-bebidas', nombre: 'bebidas'})
MERGE (c2:Categoria {id: 'cat-electronicos', nombre: 'electrónicos'})
MERGE (c3:Categoria {id: 'cat-limpieza', nombre: 'limpieza'})
MERGE (c4:Categoria {id: 'cat-higiene', nombre: 'higiene'})
MERGE (c5:Categoria {id: 'cat-alimentos', nombre: 'alimentos'})
MERGE (c6:Categoria {id: 'cat-libros', nombre: 'libros'})
MERGE (c7:Categoria {id: 'cat-deportes', nombre: 'deportes'})
MERGE (c8:Categoria {id: 'cat-alimentacion', nombre: 'alimentación'})
MERGE (c9:Categoria {id: 'cat-oficina', nombre: 'oficina'})
MERGE (c10:Categoria {id: 'cat-salud', nombre: 'salud'})
MERGE (c11:Categoria {id: 'cat-herramientas', nombre: 'herramientas'})
MERGE (c12:Categoria {id: 'cat-juguetes', nombre: 'juguetes'})
MERGE (c13:Categoria {id: 'cat-electronica', nombre: 'electrónica'})
MERGE (c14:Categoria {id: 'cat-ropa', nombre: 'ropa'})
MERGE (c15:Categoria {id: 'cat-automotriz', nombre: 'automotriz'})
MERGE (c16:Categoria {id: 'cat-hogar', nombre: 'hogar'})
MERGE (c17:Categoria {id: 'cat-belleza', nombre: 'belleza'})
// Crear nodos Producto y relaciones PERTENECE_A
CREATE (p1:Producto {id: 'SKU-4641', nombre: 'Limonada', categoria: 'bebidas', sku: 'SKU-4641', codigo_alt: 'ALT-EI49', codigo_mongo: 'MN-9508'})
CREATE (p1)-[:PERTENECE_A]->(c1)
    
CREATE (p2:Producto {id: 'SKU-8420', nombre: 'Mouse', categoria: 'electronicos', sku: 'SKU-8420', codigo_alt: 'ALT-VP47', codigo_mongo: 'MN-9717'})
CREATE (p2)-[:PERTENECE_A]->(c2)

CREATE (p3:Producto {id: 'SKU-2688', nombre: 'Protector de Pantalla', categoria: 'electronicos', sku: 'SKU-2688', codigo_alt: 'ALT-OL26', codigo_mongo: 'MN-2751'})
CREATE (p3)-[:PERTENECE_A]->(c2)

CREATE (p4:Producto {id: 'SKU-2433', nombre: 'Vinagre', categoria: 'alimentos', sku: 'SKU-2433', codigo_alt: 'ALT-FF55', codigo_mongo: 'MN-1011'})
CREATE (p4)-[:PERTENECE_A]->(c5)

CREATE (p5:Producto {id: 'SKU-9792', nombre: 'Limpiador Multiuso', categoria: 'limpieza', sku: 'SKU-9792', codigo_alt: 'ALT-ZP76', codigo_mongo: 'MN-9340'})
CREATE (p5)-[:PERTENECE_A]->(c3)

CREATE (p6:Producto {id: 'SKU-8684', nombre: 'Pañuelos', categoria: 'higiene', sku: 'SKU-8684', codigo_alt: 'ALT-YC11', codigo_mongo: 'MN-4131'})
CREATE (p6)-[:PERTENECE_A]->(c4)

CREATE (p7:Producto {id: 'SKU-7558', nombre: 'Té', categoria: 'alimentos', sku: 'SKU-7558', codigo_alt: 'ALT-CM43', codigo_mongo: 'MN-3113'})
CREATE (p7)-[:PERTENECE_A]->(c5)

CREATE (p8:Producto {id: 'SKU-4228', nombre: 'Papel Higiénico', categoria: 'higiene', sku: 'SKU-4228', codigo_alt: 'ALT-LU32', codigo_mongo: 'MN-4146'})
CREATE (p8)-[:PERTENECE_A]->(c4)

CREATE (p9:Producto {id: 'SKU-5144', nombre: 'Queso', categoria: 'alimentos', sku: 'SKU-5144', codigo_alt: 'ALT-LD45', codigo_mongo: 'MN-4667'})
CREATE (p9)-[:PERTENECE_A]->(c5)

CREATE (p10:Producto {id: 'SKU-4022', nombre: 'Isotónica', categoria: 'bebidas', sku: 'SKU-4022', codigo_alt: 'ALT-AI78', codigo_mongo: 'MN-9034'})
CREATE (p10)-[:PERTENECE_A]->(c1)

CREATE (p11:Producto {id: 'SKU-6033', nombre: 'Control Remoto', categoria: 'electronicos', sku: 'SKU-6033', codigo_alt: 'ALT-MU56', codigo_mongo: 'MN-4195'})
CREATE (p11)-[:PERTENECE_A]->(c2)

CREATE (p12:Producto {id: 'SKU-2110', nombre: 'Manzana', categoria: 'alimentos', sku: 'SKU-2110', codigo_alt: 'ALT-EV52', codigo_mongo: 'MN-7398'})
CREATE (p12)-[:PERTENECE_A]->(c5)

CREATE (p13:Producto {id: 'SKU-2684', nombre: 'Champú', categoria: 'higiene', sku: 'SKU-2684', codigo_alt: 'ALT-FW73', codigo_mongo: 'MN-7119'})
CREATE (p13)-[:PERTENECE_A]->(c4)

CREATE (p14:Producto {id: 'SKU-4797', nombre: 'Afeitadora', categoria: 'higiene', sku: 'SKU-4797', codigo_alt: 'ALT-OU99', codigo_mongo: 'MN-6291'})
CREATE (p14)-[:PERTENECE_A]->(c4)

CREATE (p15:Producto {id: 'SKU-4902', nombre: 'Cerveza', categoria: 'bebidas', sku: 'SKU-4902', codigo_alt: 'ALT-EQ29', codigo_mongo: 'MN-4595'})
CREATE (p15)-[:PERTENECE_A]->(c1)

CREATE (p16:Producto {id: 'SKU-8311', nombre: 'Limpiador Multiuso', categoria: 'limpieza', sku: 'SKU-8311', codigo_alt: 'ALT-CI87', codigo_mongo: 'MN-5159'})
CREATE (p16)-[:PERTENECE_A]->(c3)

CREATE (p17:Producto {id: 'SKU-2736', nombre: 'Recogedor', categoria: 'limpieza', sku: 'SKU-2736', codigo_alt: 'ALT-PI60', codigo_mongo: 'MN-8935'})
CREATE (p17)-[:PERTENECE_A]->(c3)

CREATE (p18:Producto {id: 'SKU-8402', nombre: 'Cable USB', categoria: 'electronicos', sku: 'SKU-8402', codigo_alt: 'ALT-TI96', codigo_mongo: 'MN-2782'})
CREATE (p18)-[:PERTENECE_A]->(c2)

CREATE (p19:Producto {id: 'SKU-5432', nombre: 'Detergente', categoria: 'limpieza', sku: 'SKU-5432', codigo_alt: 'ALT-NI26', codigo_mongo: 'MN-9849'})
CREATE (p19)-[:PERTENECE_A]->(c3)

CREATE (p20:Producto {id: 'SKU-6393', nombre: 'Escoba', categoria: 'limpieza', sku: 'SKU-6393', codigo_alt: 'ALT-QM84', codigo_mongo: 'MN-6238'})
CREATE (p20)-[:PERTENECE_A]->(c3)

CREATE (p21:Producto {id: 'SKU-9739', nombre: 'Vinagre', categoria: 'alimentos', sku: 'SKU-9739', codigo_alt: 'ALT-HG59', codigo_mongo: 'MN-5347'})
CREATE (p21)-[:PERTENECE_A]->(c5)

CREATE (p22:Producto {id: 'SKU-5678', nombre: 'Sal', categoria: 'alimentos', sku: 'SKU-5678', codigo_alt: 'ALT-WP56', codigo_mongo: 'MN-8987'})
CREATE (p22)-[:PERTENECE_A]->(c5)

CREATE (p23:Producto {id: 'SKU-8657', nombre: 'Cebolla', categoria: 'alimentos', sku: 'SKU-8657', codigo_alt: 'ALT-DE61', codigo_mongo: 'MN-3739'})
CREATE (p23)-[:PERTENECE_A]->(c5)

CREATE (p24:Producto {id: 'SKU-2686', nombre: 'Azúcar', categoria: 'alimentos', sku: 'SKU-2686', codigo_alt: 'ALT-GP65', codigo_mongo: 'MN-9439'})
CREATE (p24)-[:PERTENECE_A]->(c5)

CREATE (p25:Producto {id: 'SKU-1222', nombre: 'Limpiavidrios', categoria: 'limpieza', sku: 'SKU-1222', codigo_alt: 'ALT-LL32', codigo_mongo: 'MN-6533'})
CREATE (p25)-[:PERTENECE_A]->(c3)

CREATE (p26:Producto {id: 'SKU-5163', nombre: 'Desodorante', categoria: 'higiene', sku: 'SKU-5163', codigo_alt: 'ALT-NU64', codigo_mongo: 'MN-2434'})
CREATE (p26)-[:PERTENECE_A]->(c4)

CREATE (p27:Producto {id: 'SKU-6189', nombre: 'Protector Solar', categoria: 'higiene', sku: 'SKU-6189', codigo_alt: 'ALT-OI69', codigo_mongo: 'MN-8472'})
CREATE (p27)-[:PERTENECE_A]->(c4)

CREATE (p28:Producto {id: 'SKU-9810', nombre: 'Jugo Natural', categoria: 'bebidas', sku: 'SKU-9810', codigo_alt: 'ALT-BN95', codigo_mongo: 'MN-3039'})
CREATE (p28)-[:PERTENECE_A]->(c1)

CREATE (p29:Producto {id: 'SKU-6375', nombre: 'Trapo', categoria: 'limpieza', sku: 'SKU-6375', codigo_alt: 'ALT-ZV98', codigo_mongo: 'MN-1528'})
CREATE (p29)-[:PERTENECE_A]->(c3)

CREATE (p30:Producto {id: 'SKU-5342', nombre: 'Refresco Cola', categoria: 'bebidas', sku: 'SKU-5342', codigo_alt: 'ALT-UA53', codigo_mongo: 'MN-2746'})
CREATE (p30)-[:PERTENECE_A]->(c1)

CREATE (p31:Producto {id: 'SKU-7718', nombre: 'Protector de Pantalla', categoria: 'electronicos', sku: 'SKU-7718', codigo_alt: 'ALT-KM38', codigo_mongo: 'MN-3855'})
CREATE (p31)-[:PERTENECE_A]->(c2)

CREATE (p32:Producto {id: 'SKU-9283', nombre: 'Toallas Húmedas', categoria: 'higiene', sku: 'SKU-9283', codigo_alt: 'ALT-CB94', codigo_mongo: 'MN-4348'})
CREATE (p32)-[:PERTENECE_A]->(c4)

CREATE (p33:Producto {id: 'SKU-2996', nombre: 'Teclado', categoria: 'electronicos', sku: 'SKU-2996', codigo_alt: 'ALT-LC53', codigo_mongo: 'MN-8569'})
CREATE (p33)-[:PERTENECE_A]->(c2)

CREATE (p34:Producto {id: 'SKU-1096', nombre: 'Café', categoria: 'alimentos', sku: 'SKU-1096', codigo_alt: 'ALT-FP60', codigo_mongo: 'MN-6026'})
CREATE (p34)-[:PERTENECE_A]->(c5)

CREATE (p35:Producto {id: 'SKU-5428', nombre: 'Funda para Celular', categoria: 'electronicos', sku: 'SKU-5428', codigo_alt: 'ALT-QZ65', codigo_mongo: 'MN-4901'})
CREATE (p35)-[:PERTENECE_A]->(c2)

CREATE (p36:Producto {id: 'SKU-3669', nombre: 'Escoba', categoria: 'limpieza', sku: 'SKU-3669', codigo_alt: 'ALT-YD85', codigo_mongo: 'MN-1887'})
CREATE (p36)-[:PERTENECE_A]->(c3)

CREATE (p37:Producto {id: 'SKU-5444', nombre: 'Esponja', categoria: 'limpieza', sku: 'SKU-5444', codigo_alt: 'ALT-UO11', codigo_mongo: 'MN-6051'})
CREATE (p37)-[:PERTENECE_A]->(c3)

CREATE (p38:Producto {id: 'SKU-8979', nombre: 'Gel de Baño', categoria: 'higiene', sku: 'SKU-8979', codigo_alt: 'ALT-GL80', codigo_mongo: 'MN-1456'})
CREATE (p38)-[:PERTENECE_A]->(c4)

CREATE (p39:Producto {id: 'SKU-8187', nombre: 'Batido', categoria: 'bebidas', sku: 'SKU-8187', codigo_alt: 'ALT-KH59', codigo_mongo: 'MN-5452'})
CREATE (p39)-[:PERTENECE_A]->(c1)

CREATE (p40:Producto {id: 'SKU-7042', nombre: 'Hub USB', categoria: 'electronicos', sku: 'SKU-7042', codigo_alt: 'ALT-DP26', codigo_mongo: 'MN-3789'})
CREATE (p40)-[:PERTENECE_A]->(c2)

CREATE (p41:Producto {id: 'SKU-3735', nombre: 'Toallas Húmedas', categoria: 'higiene', sku: 'SKU-3735', codigo_alt: 'ALT-UJ62', codigo_mongo: 'MN-4581'})
CREATE (p41)-[:PERTENECE_A]->(c4)

CREATE (p42:Producto {id: 'SKU-7151', nombre: 'Hilo Dental', categoria: 'higiene', sku: 'SKU-7151', codigo_alt: 'ALT-CE39', codigo_mongo: 'MN-1356'})
CREATE (p42)-[:PERTENECE_A]->(c4)

CREATE (p43:Producto {id: 'SKU-3727', nombre: 'Recogedor', categoria: 'limpieza', sku: 'SKU-3727', codigo_alt: 'ALT-AU45', codigo_mongo: 'MN-2572'})
CREATE (p43)-[:PERTENECE_A]->(c3)

CREATE (p44:Producto {id: 'SKU-3377', nombre: 'Guantes', categoria: 'limpieza', sku: 'SKU-3377', codigo_alt: 'ALT-FS87', codigo_mongo: 'MN-5304'})
CREATE (p44)-[:PERTENECE_A]->(c3)

CREATE (p45:Producto {id: 'SKU-8789', nombre: 'Pasta', categoria: 'alimentos', sku: 'SKU-8789', codigo_alt: 'ALT-ZY54', codigo_mongo: 'MN-5171'})
CREATE (p45)-[:PERTENECE_A]->(c5)

CREATE (p46:Producto {id: 'SKU-8700', nombre: 'Agua Mineral', categoria: 'bebidas', sku: 'SKU-8700', codigo_alt: 'ALT-KR25', codigo_mongo: 'MN-6319'})
CREATE (p46)-[:PERTENECE_A]->(c1)

CREATE (p47:Producto {id: 'SKU-6430', nombre: 'Manzana', categoria: 'alimentos', sku: 'SKU-6430', codigo_alt: 'ALT-IG49', codigo_mongo: 'MN-5450'})
CREATE (p47)-[:PERTENECE_A]->(c5)

CREATE (p48:Producto {id: 'SKU-5706', nombre: 'Detergente', categoria: 'limpieza', sku: 'SKU-5706', codigo_alt: 'ALT-VY81', codigo_mongo: 'MN-1159'})
CREATE (p48)-[:PERTENECE_A]->(c3)

CREATE (p49:Producto {id: 'SKU-6324', nombre: 'Toallas Húmedas', categoria: 'higiene', sku: 'SKU-6324', codigo_alt: 'ALT-OF97', codigo_mongo: 'MN-8480'})
CREATE (p49)-[:PERTENECE_A]->(c4)

CREATE (p50:Producto {id: 'SKU-6199', nombre: 'Mantequilla', categoria: 'alimentos', sku: 'SKU-6199', codigo_alt: 'ALT-CH33', codigo_mongo: 'MN-3413'})
CREATE (p50)-[:PERTENECE_A]->(c5)

CREATE (p51:Producto {id: 'SKU-8643', nombre: 'Crema Corporal', categoria: 'higiene', sku: 'SKU-8643', codigo_alt: 'ALT-XD94', codigo_mongo: 'MN-2275'})
CREATE (p51)-[:PERTENECE_A]->(c4)

CREATE (p52:Producto {id: 'SKU-2283', nombre: 'Adaptador', categoria: 'electronicos', sku: 'SKU-2283', codigo_alt: 'ALT-ER44', codigo_mongo: 'MN-9573'})
CREATE (p52)-[:PERTENECE_A]->(c2)

CREATE (p53:Producto {id: 'SKU-5654', nombre: 'Trapeador', categoria: 'limpieza', sku: 'SKU-5654', codigo_alt: 'ALT-DB79', codigo_mongo: 'MN-1364'})
CREATE (p53)-[:PERTENECE_A]->(c3)

CREATE (p54:Producto {id: 'SKU-8699', nombre: 'Vino Tinto', categoria: 'bebidas', sku: 'SKU-8699', codigo_alt: 'ALT-KQ27', codigo_mongo: 'MN-2297'})
CREATE (p54)-[:PERTENECE_A]->(c1)

CREATE (p55:Producto {id: 'SKU-9790', nombre: 'Zanahoria', categoria: 'alimentos', sku: 'SKU-9790', codigo_alt: 'ALT-OR44', codigo_mongo: 'MN-1361'})
CREATE (p55)-[:PERTENECE_A]->(c5)

CREATE (p56:Producto {id: 'SKU-8865', nombre: 'Jugo de Manzana', categoria: 'bebidas', sku: 'SKU-8865', codigo_alt: 'ALT-AQ69', codigo_mongo: 'MN-4091'})
CREATE (p56)-[:PERTENECE_A]->(c1)

CREATE (p57:Producto {id: 'SKU-9207', nombre: 'Limpiador Multiuso', categoria: 'limpieza', sku: 'SKU-9207', codigo_alt: 'ALT-VR10', codigo_mongo: 'MN-3222'})
CREATE (p57)-[:PERTENECE_A]->(c3)

// Relaciones EQUIVALE_A entre productos por sus códigos alternos
// (Ejemplo: SKU, codigo_alt, codigo_mongo equivalen entre sí para cada producto)
FOREACH (p IN [p1,p2,p3,p4,p5,p6,p7,p8,p9,p10,p11,p12,p13,p14,p15,p16,p17,p18,p19,p20,p21,p22,p23,p24,p25,p26,p27,p28,p29,p30,p31,p32,p33,p34,p35,p36,p37,p38,p39,p40,p41,p42,p43,p44,p45,p46,p47,p48,p49,p50,p51,p52,p53,p54,p55,p56,p57] |
    MERGE (p)-[:EQUIVALE_A]->(p)
    SET p.fecha = datetime({epochMillis: timestamp() - toInteger(rand() * (timestamp() - datetime('2024-01-01T00:00:00').epochMillis))})
)
//------------------------------------------------------------------------
//-------- Crear 70 nodos Producto adicionales con relaciones ------------
//------------------------------------------------------------------------

WITH [
  {cat: 'cat-electronica', nombre: 'Electrónica', productos: ['Smartphone', 'Laptop', 'Tablet', 'Auriculares', 'Televisor', 'Cámara', 'Smartwatch', 'Monitor', 'Teclado', 'Mouse']},
  {cat: 'cat-ropa', nombre: 'Ropa', productos: ['Camiseta', 'Pantalón', 'Chaqueta', 'Vestido', 'Sudadera', 'Falda', 'Calcetines', 'Zapatos', 'Bufanda', 'Gorra']},
  {cat: 'cat-automotriz', nombre: 'Automotriz', productos: ['Neumático', 'Filtro de aceite', 'Batería', 'Lámpara', 'Cargador', 'GPS', 'Aceite', 'Limpiaparabrisas', 'Amortiguador', 'Radiador']},
  {cat: 'cat-hogar', nombre: 'Hogar', productos: ['Sartén', 'Cuchara', 'Cojín', 'Lámpara', 'Mesa', 'Silla', 'Vaso', 'Taza', 'Cortina', 'Almohada']},
  {cat: 'cat-belleza', nombre: 'Belleza', productos: ['Perfume', 'Esmalte', 'Kit de maquillaje', 'Crema facial', 'Champú', 'Acondicionador', 'Cepillo', 'Secador', 'Plancha de pelo', 'Loción']},
  {cat: 'cat-libros', nombre: 'Libros', productos: ['Novela', 'Guía', 'Libro de cocina', 'Manual', 'Cuento', 'Ensayo', 'Biografía', 'Diccionario', 'Atlas', 'Revista']},
  {cat: 'cat-deportes', nombre: 'Deportes', productos: ['Pelota', 'Zapatilla', 'Camiseta deportiva', 'Raqueta', 'Guante', 'Bicicleta', 'Casco', 'Mancuerna', 'Balón', 'Short']},
  {cat: 'cat-alimentacion', nombre: 'Alimentación', productos: ['Lata', 'Botella', 'Pack', 'Bolsa', 'Caja', 'Barra energética', 'Galletas', 'Cereal', 'Aceite', 'Arroz']},
  {cat: 'cat-oficina', nombre: 'Oficina', productos: ['Bolígrafo', 'Agenda', 'Silla', 'Mesa', 'Lámpara', 'Archivador', 'Cuaderno', 'Grapadora', 'Regla', 'Calculadora']},
  {cat: 'cat-salud', nombre: 'Salud', productos: ['Termómetro', 'Masajeador', 'Suplemento', 'Kit de primeros auxilios', 'Tensiómetro', 'Báscula', 'Gel antibacterial', 'Venda', 'Inhalador', 'Pastillero']}
] AS categorias

UNWIND range(1, 70) AS i
WITH i, categorias[toInteger(rand() * size(categorias))] AS cat
WITH i, cat, cat.productos[toInteger(rand() * size(cat.productos))] AS nombre_producto,
     'PRD-' + toString(2000 + i) AS sku,
     'ALT-' + toString(2000 + i) AS codigo_alt,
     'MNG-' + toString(2000 + i) AS codigo_mongo
MERGE (c:Categoria {id: cat.cat})
CREATE (p:Producto {
    id: sku,
    nombre: nombre_producto,
    categoria: cat.nombre,
    sku: sku,
    codigo_alt: codigo_alt,
    codigo_mongo: codigo_mongo,
    fecha: datetime({epochMillis: timestamp() - toInteger(rand() * (timestamp() - datetime('2024-01-01T00:00:00').epochMillis))})
})
MERGE (p)-[:PERTENECE_A]->(c)
MERGE (p)-[:EQUIVALE_A]->(p);

//------------------------------------------------------------------------
//--------------- Crear 800 nodos Cliente en Neo4j ---------------------
//------------------------------------------------------------------------
CREATE CONSTRAINT cliente_id_unique IF NOT EXISTS 
FOR (c:Cliente) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT cliente_email_unique IF NOT EXISTS
FOR (c:Cliente) REQUIRE c.email IS UNIQUE;

WITH [
    {nombre: 'Juan Pérez', genero: 'M', pais: 'México'},
    {nombre: 'María García', genero: 'F', pais: 'España'},
    {nombre: 'Carlos López', genero: 'Masculino', pais: 'Argentina'},
    {nombre: 'Ana Martínez', genero: 'Femenino', pais: 'Colombia'},
    {nombre: 'Alex Smith', genero: 'Otro', pais: 'Estados Unidos'},
    {nombre: 'Laura Rodríguez', genero: 'F', pais: 'Chile'},
    {nombre: 'Pedro González', genero: 'M', pais: 'Perú'},
    {nombre: 'Sofía Hernández', genero: 'Femenino', pais: 'Venezuela'},
    {nombre: 'Diego Ramírez', genero: 'Masculino', pais: 'Ecuador'},
    {nombre: 'Elena Torres', genero: 'Otro', pais: 'Uruguay'}
] AS clientes_base

UNWIND range(1, 800) AS i
WITH i, clientes_base[toInteger(rand() * size(clientes_base))] AS base
WITH i, base, 
     // Eliminar tildes del nombre para el email
     replace(replace(replace(replace(replace(
       replace(replace(replace(replace(replace(
         base.nombre, 'á', 'a'), 'é', 'e'), 'í', 'i'), 'ó', 'o'), 'ú', 'u'),
         'Á', 'A'), 'É', 'E'), 'Í', 'I'), 'Ó', 'O'), 'Ú', 'U') AS nombre_sin_tildes
CREATE (c:Cliente {
  id: 'CLI' + toString(100000 + i),
  nombre: base.nombre + ' ' + toString(i),
  email: toLower(replace(nombre_sin_tildes + ' ' + toString(i), ' ', '.') + '@example.com'),
  genero: base.genero,
  pais: base.pais,
  fecha: datetime({epochMillis: timestamp() - toInteger(rand() * (timestamp() - datetime('2024-01-01T00:00:00').epochMillis))})
})
RETURN count(c) AS clientes_creados;

//------------------------------------------------------------------------
//--------------- Crear 5000 nodos Orden con relaciones -----------------
//------------------------------------------------------------------------

// Crear índice para fechas de orden
CREATE INDEX orden_fecha IF NOT EXISTS FOR (o:Orden) ON (o.fecha);

// Crear 5000 órdenes con productos y clientes
MATCH (c:Cliente)
WITH collect(c) AS clientes
MATCH (p:Producto)
WITH clientes, collect(p) AS productos

UNWIND range(1, 5000) AS i
WITH i, clientes, productos,
     // Seleccionar cliente aleatorio
     clientes[toInteger(rand() * size(clientes))] AS cliente,
     // Definir canales disponibles
     ['Web', 'Tienda Física', 'Móvil', 'Teléfono', 'Marketplace'] AS canales,
     // Definir monedas (USD y CRC principalmente)
     ['USD', 'CRC', 'USD', 'CRC', 'USD'] AS monedas

WITH i, cliente, productos, canales, monedas,
     canales[toInteger(rand() * size(canales))] AS canal,
     monedas[toInteger(rand() * size(monedas))] AS moneda,
     // Generar fecha aleatoria entre 2024-01-01 y 2025-11-14 CORREGIDO
     datetime({epochMillis: datetime('2024-01-01T00:00:00').epochMillis +
                   toInteger(rand() * (datetime('2025-11-14T23:59:59').epochMillis - datetime('2024-01-01T00:00:00').epochMillis))}) AS fecha

// Crear la orden
CREATE (o:Orden {
    id: 'ORD-' + toString(10000 + i),
    fecha: fecha,
    canal: canal,
    moneda: moneda,
    total: 0.0
})

// Crear relación REALIZO entre Cliente y Orden
MERGE (cliente)-[:REALIZO]->(o)

// Agregar productos a la orden (entre 1 y 5 productos por orden)
WITH o, productos, moneda, toInteger(1 + rand() * 5) AS num_productos
UNWIND range(1, num_productos) AS prod_index

WITH o, productos[toInteger(rand() * size(productos))] AS producto, moneda,
     toInteger(1 + rand() * 3) AS cantidad,
     CASE moneda
         WHEN 'USD' THEN round(10.0 + rand() * 490.0, 2)
         WHEN 'CRC' THEN round(5000.0 + rand() * 245000.0, 2)
         ELSE round(10.0 + rand() * 490.0, 2)
     END AS precio_unit

// Crear relación CONTIENE entre Orden y Producto
MERGE (o)-[r:CONTIENE]->(producto)
ON CREATE SET r.cantidad = cantidad, r.precio_unit = precio_unit
ON MATCH SET r.cantidad = r.cantidad + cantidad

RETURN count(DISTINCT o) AS ordenes_creadas;

// Actualizar el total de cada orden
MATCH (o:Orden)-[r:CONTIENE]->(:Producto)
WITH o, sum(r.cantidad * r.precio_unit) AS total_calculado
SET o.total = round(total_calculado, 2)
RETURN count(o) AS ordenes_actualizadas;