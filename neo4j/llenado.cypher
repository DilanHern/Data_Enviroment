// Eliminar nodos
MATCH (n)
DETACH DELETE n;
//------------------------------------------------------------------------
//-------- Crear 57 nodos Producto en comun con las demas bases ----------
//------------------------------------------------------------------------
// Constraint para Producto
CREATE CONSTRAINT producto_id IF NOT EXISTS
FOR (p:Producto) REQUIRE p.id IS UNIQUE;

// Crear nodos Categoria
MERGE (c1:Categoria {id: 'cat-electronica', nombre: 'Electrónica'})
MERGE (c2:Categoria {id: 'cat-ropa', nombre: 'Ropa'})
MERGE (c3:Categoria {id: 'cat-automotriz', nombre: 'Automotriz'})
MERGE (c4:Categoria {id: 'cat-hogar', nombre: 'Hogar'})
MERGE (c5:Categoria {id: 'cat-belleza', nombre: 'Belleza'})
MERGE (c6:Categoria {id: 'cat-libros', nombre: 'Libros'})
MERGE (c7:Categoria {id: 'cat-deportes', nombre: 'Deportes'})
MERGE (c8:Categoria {id: 'cat-alimentacion', nombre: 'Alimentación'})
MERGE (c9:Categoria {id: 'cat-oficina', nombre: 'Oficina'})
MERGE (c10:Categoria {id: 'cat-salud', nombre: 'Salud'})
MERGE (c11:Categoria {id: 'cat-herramientas', nombre: 'Herramientas'})
MERGE (c12:Categoria {id: 'cat-juguetes', nombre: 'Juguetes'})

// Crear nodos Producto y relaciones PERTENECE_A
MERGE (p1:Producto {id: 'PRD-3084-CJ', nombre: 'Clásico Tablet', categoria: 'Electrónica', sku: 'PRD-3084-CJ', codigo_alt: '3084CJ', codigo_mongo: 'MNG-3084-CJ'})
MERGE (p1)-[:PERTENECE_A]->(c1)
MERGE (p2:Producto {id: 'PRD-7342-MI', nombre: 'Rápido Pantalón', categoria: 'Ropa', sku: 'PRD-7342-MI', codigo_alt: '7342MI', codigo_mongo: 'MNG-7342-MI'})
MERGE (p2)-[:PERTENECE_A]->(c2)
MERGE (p3:Producto {id: 'PRD-8238-ZU', nombre: 'Eco Neumático', categoria: 'Automotriz', sku: 'PRD-8238-ZU', codigo_alt: '8238ZU', codigo_mongo: 'MNG-8238-ZU'})
MERGE (p3)-[:PERTENECE_A]->(c3)
MERGE (p4:Producto {id: 'PRD-5455-YL', nombre: 'Avanzado Sartén', categoria: 'Hogar', sku: 'PRD-5455-YL', codigo_alt: '5455YL', codigo_mongo: 'MNG-5455-YL'})
MERGE (p4)-[:PERTENECE_A]->(c4)
MERGE (p5:Producto {id: 'PRD-9312-GR', nombre: 'Eco Filtro', categoria: 'Automotriz', sku: 'PRD-9312-GR', codigo_alt: '9312GR', codigo_mongo: 'MNG-9312-GR'})
MERGE (p5)-[:PERTENECE_A]->(c3)
MERGE (p6:Producto {id: 'PRD-4653-QC', nombre: 'Set Plus', categoria: 'Belleza', sku: 'PRD-4653-QC', codigo_alt: '4653QC', codigo_mongo: 'MNG-4653-QC'})
MERGE (p6)-[:PERTENECE_A]->(c5)
MERGE (p7:Producto {id: 'PRD-6289-LZ', nombre: 'Novela Ultra', categoria: 'Libros', sku: 'PRD-6289-LZ', codigo_alt: '6289LZ', codigo_mongo: 'MNG-6289-LZ'})
MERGE (p7)-[:PERTENECE_A]->(c6)
MERGE (p8:Producto {id: 'PRD-2209-SW', nombre: 'Cómodo Zapatilla', categoria: 'Deportes', sku: 'PRD-2209-SW', codigo_alt: '2209SW', codigo_mongo: 'MNG-2209-SW'})
MERGE (p8)-[:PERTENECE_A]->(c7)
MERGE (p9:Producto {id: 'PRD-8849-EP', nombre: 'Botella Pro', categoria: 'Alimentación', sku: 'PRD-8849-EP', codigo_alt: '8849EP', codigo_mongo: 'MNG-8849-EP'})
MERGE (p9)-[:PERTENECE_A]->(c8)
MERGE (p10:Producto {id: 'PRD-4420-FF', nombre: 'Guía Max', categoria: 'Libros', sku: 'PRD-4420-FF', codigo_alt: '4420FF', codigo_mongo: 'MNG-4420-FF'})
MERGE (p10)-[:PERTENECE_A]->(c6)
MERGE (p11:Producto {id: 'PRD-5593-XB', nombre: 'Silla Ultra', categoria: 'Oficina', sku: 'PRD-5593-XB', codigo_alt: '5593XB', codigo_mongo: 'MNG-5593-XB'})
MERGE (p11)-[:PERTENECE_A]->(c9)
MERGE (p12:Producto {id: 'PRD-3719-IL', nombre: 'Compacto Masajeador', categoria: 'Salud', sku: 'PRD-3719-IL', codigo_alt: '3719IL', codigo_mongo: 'MNG-3719-IL'})
MERGE (p12)-[:PERTENECE_A]->(c10)
MERGE (p13:Producto {id: 'PRD-9556-UQ', nombre: 'Lámpara Elite', categoria: 'Hogar', sku: 'PRD-9556-UQ', codigo_alt: '9556UQ', codigo_mongo: 'MNG-9556-UQ'})
MERGE (p13)-[:PERTENECE_A]->(c4)
MERGE (p14:Producto {id: 'PRD-7665-AD', nombre: 'Lata Ultra', categoria: 'Alimentación', sku: 'PRD-7665-AD', codigo_alt: '7665AD', codigo_mongo: 'MNG-7665-AD'})
MERGE (p14)-[:PERTENECE_A]->(c8)
MERGE (p15:Producto {id: 'PRD-0832-OI', nombre: 'Pelota Plus', categoria: 'Deportes', sku: 'PRD-0832-OI', codigo_alt: '0832OI', codigo_mongo: 'MNG-0832-OI'})
MERGE (p15)-[:PERTENECE_A]->(c7)
MERGE (p16:Producto {id: 'PRD-6582-LT', nombre: 'Cómodo Martillo', categoria: 'Herramientas', sku: 'PRD-6582-LT', codigo_alt: '6582LT', codigo_mongo: 'MNG-6582-LT'})
MERGE (p16)-[:PERTENECE_A]->(c11)
MERGE (p17:Producto {id: 'PRD-8259-GL', nombre: 'Puzzle Pro', categoria: 'Juguetes', sku: 'PRD-8259-GL', codigo_alt: '8259GL', codigo_mongo: 'MNG-8259-GL'})
MERGE (p17)-[:PERTENECE_A]->(c12)
MERGE (p18:Producto {id: 'PRD-4797-YB', nombre: 'Rápido Kit', categoria: 'Salud', sku: 'PRD-4797-YB', codigo_alt: '4797YB', codigo_mongo: 'MNG-4797-YB'})
MERGE (p18)-[:PERTENECE_A]->(c10)
MERGE (p19:Producto {id: 'PRD-9640-NE', nombre: 'Bloques Plus', categoria: 'Juguetes', sku: 'PRD-9640-NE', codigo_alt: '9640NE', codigo_mongo: 'MNG-9640-NE'})
MERGE (p19)-[:PERTENECE_A]->(c12)
MERGE (p20:Producto {id: 'PRD-5830-BM', nombre: 'Bolsa Max', categoria: 'Alimentación', sku: 'PRD-5830-BM', codigo_alt: '5830BM', codigo_mongo: 'MNG-5830-BM'})
MERGE (p20)-[:PERTENECE_A]->(c8)
MERGE (p21:Producto {id: 'PRD-1725-BE', nombre: 'Clásico Monitor', categoria: 'Electrónica', sku: 'PRD-1725-BE', codigo_alt: '1725BE', codigo_mongo: 'MNG-1725-BE'})
MERGE (p21)-[:PERTENECE_A]->(c1)
MERGE (p22:Producto {id: 'PRD-6988-TH', nombre: 'Puzzle Smart', categoria: 'Juguetes', sku: 'PRD-6988-TH', codigo_alt: '6988TH', codigo_mongo: 'MNG-6988-TH'})
MERGE (p22)-[:PERTENECE_A]->(c12)
MERGE (p23:Producto {id: 'PRD-3421-VD', nombre: 'Agenda Ultra', categoria: 'Oficina', sku: 'PRD-3421-VD', codigo_alt: '3421VD', codigo_mongo: 'MNG-3421-VD'})
MERGE (p23)-[:PERTENECE_A]->(c9)
MERGE (p24:Producto {id: 'PRD-8028-FI', nombre: 'Eco Pack', categoria: 'Alimentación', sku: 'PRD-8028-FI', codigo_alt: '8028FI', codigo_mongo: 'MNG-8028-FI'})
MERGE (p24)-[:PERTENECE_A]->(c8)
MERGE (p25:Producto {id: 'PRD-4183-YT', nombre: 'Premium Camiseta Sport', categoria: 'Deportes', sku: 'PRD-4183-YT', codigo_alt: '4183YT', codigo_mongo: 'MNG-4183-YT'})
MERGE (p25)-[:PERTENECE_A]->(c7)
MERGE (p26:Producto {id: 'PRD-9043-RX', nombre: 'Taladro Smart', categoria: 'Herramientas', sku: 'PRD-9043-RX', codigo_alt: '9043RX', codigo_mongo: 'MNG-9043-RX'})
MERGE (p26)-[:PERTENECE_A]->(c11)
MERGE (p27:Producto {id: 'PRD-5662-EL', nombre: 'Chaqueta Plus', categoria: 'Ropa', sku: 'PRD-5662-EL', codigo_alt: '5662EL', codigo_mongo: 'MNG-5662-EL'})
MERGE (p27)-[:PERTENECE_A]->(c2)
MERGE (p28:Producto {id: 'PRD-2588-OK', nombre: 'Mini Perfume', categoria: 'Belleza', sku: 'PRD-2588-OK', codigo_alt: '2588OK', codigo_mongo: 'MNG-2588-OK'})
MERGE (p28)-[:PERTENECE_A]->(c5)
MERGE (p29:Producto {id: 'PRD-7316-TQ', nombre: 'Clásico Lata', categoria: 'Alimentación', sku: 'PRD-7316-TQ', codigo_alt: '7316TQ', codigo_mongo: 'MNG-7316-TQ'})
MERGE (p29)-[:PERTENECE_A]->(c8)
MERGE (p30:Producto {id: 'PRD-9343-ZF', nombre: 'Compacto Auricular', categoria: 'Electrónica', sku: 'PRD-9343-ZF', codigo_alt: '9343ZF', codigo_mongo: 'MNG-9343-ZF'})
MERGE (p30)-[:PERTENECE_A]->(c1)
MERGE (p31:Producto {id: 'PRD-8562-EQ', nombre: 'Rápido Libro', categoria: 'Libros', sku: 'PRD-8562-EQ', codigo_alt: '8562EQ', codigo_mongo: 'MNG-8562-EQ'})
MERGE (p31)-[:PERTENECE_A]->(c6)
MERGE (p32:Producto {id: 'PRD-0693-FA', nombre: 'Esmalte Pro', categoria: 'Belleza', sku: 'PRD-0693-FA', codigo_alt: '0693FA', codigo_mongo: 'MNG-0693-FA'})
MERGE (p32)-[:PERTENECE_A]->(c5)
MERGE (p33:Producto {id: 'PRD-5248-MR', nombre: 'Clásico Kit', categoria: 'Salud', sku: 'PRD-5248-MR', codigo_alt: '5248MR', codigo_mongo: 'MNG-5248-MR'})
MERGE (p33)-[:PERTENECE_A]->(c10)
MERGE (p34:Producto {id: 'PRD-6013-WW', nombre: 'Pelota Ultra', categoria: 'Deportes', sku: 'PRD-6013-WW', codigo_alt: '6013WW', codigo_mongo: 'MNG-6013-WW'})
MERGE (p34)-[:PERTENECE_A]->(c7)
MERGE (p35:Producto {id: 'PRD-7055-KI', nombre: 'Botella Plus', categoria: 'Alimentación', sku: 'PRD-7055-KI', codigo_alt: '7055KI', codigo_mongo: 'MNG-7055-KI'})
MERGE (p35)-[:PERTENECE_A]->(c8)
MERGE (p36:Producto {id: 'PRD-3511-NI', nombre: 'Altavoz Plus', categoria: 'Electrónica', sku: 'PRD-3511-NI', codigo_alt: '3511NI', codigo_mongo: 'MNG-3511-NI'})
MERGE (p36)-[:PERTENECE_A]->(c1)
MERGE (p37:Producto {id: 'PRD-4511-ZI', nombre: 'Guía Smart', categoria: 'Libros', sku: 'PRD-4511-ZI', codigo_alt: '4511ZI', codigo_mongo: 'MNG-4511-ZI'})
MERGE (p37)-[:PERTENECE_A]->(c6)
MERGE (p38:Producto {id: 'PRD-0896-BN', nombre: 'Sudadera Ultra', categoria: 'Ropa', sku: 'PRD-0896-BN', codigo_alt: '0896BN', codigo_mongo: 'MNG-0896-BN'})
MERGE (p38)-[:PERTENECE_A]->(c2)
MERGE (p39:Producto {id: 'PRD-8977-OD', nombre: 'Compacto Coche', categoria: 'Juguetes', sku: 'PRD-8977-OD', codigo_alt: '8977OD', codigo_mongo: 'MNG-8977-OD'})
MERGE (p39)-[:PERTENECE_A]->(c12)
MERGE (p40:Producto {id: 'PRD-1993-GM', nombre: 'Mini Cargador', categoria: 'Automotriz', sku: 'PRD-1993-GM', codigo_alt: '1993GM', codigo_mongo: 'MNG-1993-GM'})
MERGE (p40)-[:PERTENECE_A]->(c3)
MERGE (p41:Producto {id: 'PRD-9263-NS', nombre: 'Eco Termómetro', categoria: 'Salud', sku: 'PRD-9263-NS', codigo_alt: '9263NS', codigo_mongo: 'MNG-9263-NS'})
MERGE (p41)-[:PERTENECE_A]->(c10)
MERGE (p42:Producto {id: 'PRD-7742-JN', nombre: 'Cojín Plus', categoria: 'Hogar', sku: 'PRD-7742-JN', codigo_alt: '7742JN', codigo_mongo: 'MNG-7742-JN'})
MERGE (p42)-[:PERTENECE_A]->(c4)
MERGE (p43:Producto {id: 'PRD-3776-UP', nombre: 'Clásico Calcetín', categoria: 'Ropa', sku: 'PRD-3776-UP', codigo_alt: '3776UP', codigo_mongo: 'MNG-3776-UP'})
MERGE (p43)-[:PERTENECE_A]->(c2)
MERGE (p44:Producto {id: 'PRD-2336-SH', nombre: 'Clásico Suplemento', categoria: 'Salud', sku: 'PRD-2336-SH', codigo_alt: '2336SH', codigo_mongo: 'MNG-2336-SH'})
MERGE (p44)-[:PERTENECE_A]->(c10)
MERGE (p45:Producto {id: 'PRD-5590-XV', nombre: 'Rápido Perfume', categoria: 'Belleza', sku: 'PRD-5590-XV', codigo_alt: '5590XV', codigo_mongo: 'MNG-5590-XV'})
MERGE (p45)-[:PERTENECE_A]->(c5)
MERGE (p46:Producto {id: 'PRD-0229-GQ', nombre: 'Pack Plus', categoria: 'Alimentación', sku: 'PRD-0229-GQ', codigo_alt: '0229GQ', codigo_mongo: 'MNG-0229-GQ'})
MERGE (p46)-[:PERTENECE_A]->(c8)
MERGE (p47:Producto {id: 'PRD-4476-YL', nombre: 'Router Max', categoria: 'Electrónica', sku: 'PRD-4476-YL', codigo_alt: '4476YL', codigo_mongo: 'MNG-4476-YL'})
MERGE (p47)-[:PERTENECE_A]->(c1)
MERGE (p48:Producto {id: 'PRD-5635-ZB', nombre: 'Clásico Cuchara', categoria: 'Hogar', sku: 'PRD-5635-ZB', codigo_alt: '5635ZB', codigo_mongo: 'MNG-5635-ZB'})
MERGE (p48)-[:PERTENECE_A]->(c4)
MERGE (p49:Producto {id: 'PRD-1442-DR', nombre: 'Compacto Bolígrafo', categoria: 'Oficina', sku: 'PRD-1442-DR', codigo_alt: '1442DR', codigo_mongo: 'MNG-1442-DR'})
MERGE (p49)-[:PERTENECE_A]->(c9)
MERGE (p50:Producto {id: 'PRD-9584-YR', nombre: 'Premium Novela', categoria: 'Libros', sku: 'PRD-9584-YR', codigo_alt: '9584YR', codigo_mongo: 'MNG-9584-YR'})
MERGE (p50)-[:PERTENECE_A]->(c6)
MERGE (p51:Producto {id: 'PRD-4555-FZ', nombre: 'Chaqueta Plus', categoria: 'Ropa', sku: 'PRD-4555-FZ', codigo_alt: '4555FZ', codigo_mongo: 'MNG-4555-FZ'})
MERGE (p51)-[:PERTENECE_A]->(c2)
MERGE (p52:Producto {id: 'PRD-6368-RF', nombre: 'Cojín Smart', categoria: 'Hogar', sku: 'PRD-6368-RF', codigo_alt: '6368RF', codigo_mongo: 'MNG-6368-RF'})
MERGE (p52)-[:PERTENECE_A]->(c4)
MERGE (p53:Producto {id: 'PRD-8193-AR', nombre: 'Muñeco Max', categoria: 'Juguetes', sku: 'PRD-8193-AR', codigo_alt: '8193AR', codigo_mongo: 'MNG-8193-AR'})
MERGE (p53)-[:PERTENECE_A]->(c12)
MERGE (p54:Producto {id: 'PRD-2142-ZX', nombre: 'Caja Max', categoria: 'Alimentación', sku: 'PRD-2142-ZX', codigo_alt: '2142ZX', codigo_mongo: 'MNG-2142-ZX'})
MERGE (p54)-[:PERTENECE_A]->(c8)
MERGE (p55:Producto {id: 'PRD-3628-PR', nombre: 'Neumático Ultra', categoria: 'Automotriz', sku: 'PRD-3628-PR', codigo_alt: '3628PR', codigo_mongo: 'MNG-3628-PR'})
MERGE (p55)-[:PERTENECE_A]->(c3)
MERGE (p56:Producto {id: 'PRD-7017-RY', nombre: 'Premium Libro', categoria: 'Libros', sku: 'PRD-7017-RY', codigo_alt: '7017RY', codigo_mongo: 'MNG-7017-RY'})
MERGE (p56)-[:PERTENECE_A]->(c6)
MERGE (p57:Producto {id: 'PRD-1424-SC', nombre: 'Lite Camiseta Sport', categoria: 'Deportes', sku: 'PRD-1424-SC', codigo_alt: '1424SC', codigo_mongo: 'MNG-1424-SC'})
MERGE (p57)-[:PERTENECE_A]->(c7)

// Relaciones EQUIVALE_A entre productos por sus códigos alternos
// (Ejemplo: SKU, codigo_alt, codigo_mongo equivalen entre sí para cada producto)
FOREACH (p IN [p1,p2,p3,p4,p5,p6,p7,p8,p9,p10,p11,p12,p13,p14,p15,p16,p17,p18,p19,p20,p21,p22,p23,p24,p25,p26,p27,p28,p29,p30,p31,p32,p33,p34,p35,p36,p37,p38,p39,p40,p41,p42,p43,p44,p45,p46,p47,p48,p49,p50,p51,p52,p53,p54,p55,p56,p57] |
    MERGE (p)-[:EQUIVALE_A]->(p)
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
    codigo_mongo: codigo_mongo
})
MERGE (p)-[:PERTENECE_A]->(c)
MERGE (p)-[:EQUIVALE_A]->(p);

//------------------------------------------------------------------------
//--------------- Crear 800 nodos Cliente en Neo4j ---------------------
//------------------------------------------------------------------------
CREATE CONSTRAINT cliente_id_unique IF NOT EXISTS 
FOR (c:Cliente) REQUIRE c.id IS UNIQUE;

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
CREATE (c:Cliente {
    id: 'CLI' + toString(100000 + i),
    nombre: base.nombre + ' ' + toString(i),
    genero: base.genero,
    pais: base.pais
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
     ['USD', 'CRC', 'USD', 'CRC', 'USD'] AS monedas,
     // Generar fecha aleatoria entre 2024-01-01 y 2025-11-14
     datetime({year: 2024 + toInteger(rand() * 2), 
               month: 1 + toInteger(rand() * 12), 
               day: 1 + toInteger(rand() * 28),
               hour: toInteger(rand() * 24),
               minute: toInteger(rand() * 60),
               second: toInteger(rand() * 60)}) AS fecha

WITH i, cliente, productos, canales, monedas, fecha,
     canales[toInteger(rand() * size(canales))] AS canal,
     monedas[toInteger(rand() * size(monedas))] AS moneda

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