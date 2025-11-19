const { driver, DATABASE_NAME } = require('../config/neo4j');
const neo4j = require('neo4j-driver');

// GET todos los productos
exports.getAll = async (req, res) => {
  const session = driver.session({ database: DATABASE_NAME });
  try {
    // ✅ FIX: Usar neo4j.int() con validación
    const limitValue = parseInt(req.query.limit, 10);
    const skipValue = parseInt(req.query.skip, 10);
    
    const limit = neo4j.int(isNaN(limitValue) ? 100 : limitValue);
    const skip = neo4j.int(isNaN(skipValue) ? 0 : skipValue);
    
    const categoria = req.query.categoria;

    let whereClause = '';
    let params = { skip, limit };

    if (categoria) {
      whereClause = 'WHERE p.categoria = $categoria';
      params.categoria = categoria;
    }

    const result = await session.run(
      `MATCH (p:Producto)
       ${whereClause}
       RETURN p.id as id, 
              p.nombre as nombre, 
              p.categoria as categoria,
              p.sku as sku,
              p.codigo_alt as codigo_alt,
              p.codigo_mongo as codigo_mongo
       ORDER BY p.nombre
       SKIP $skip
       LIMIT $limit`,
      params
    );

    const productos = result.records.map(record => ({
      _id: record.get('id'),
      nombre: record.get('nombre'),
      categoria: record.get('categoria'),
      codigo_mongo: record.get('codigo_mongo'),
      sku: record.get('sku'),
      codigo_alt: record.get('codigo_alt')
    }));

    res.json(productos);
  } catch (error) {
    console.error('Error al obtener productos:', error);
    res.status(500).json({ error: 'Error al obtener los productos' });
  } finally {
    await session.close();
  }
};

// GET producto por ID
exports.getById = async (req, res) => {
  const session = driver.session({ database: DATABASE_NAME });
  try {
    const { id } = req.params;

    const result = await session.run(
      `MATCH (p:Producto {id: $id})
       OPTIONAL MATCH (p)-[:PERTENECE_A]->(cat:Categoria)
       OPTIONAL MATCH (p)-[eq:EQUIVALE_A]->(pe:Producto)
       RETURN p.id as id,
              p.nombre as nombre,
              p.categoria as categoria,
              p.sku as sku,
              p.codigo_alt as codigo_alt,
              p.codigo_mongo as codigo_mongo,
              cat.nombre as categoriaNombre,
              collect(DISTINCT {
                producto_id: pe.id,
                nombre: pe.nombre,
                razon: eq.razon,
                confidence: eq.confidence
              }) as equivalencias`,
      { id }
    );

    if (result.records.length === 0) {
      return res.status(404).json({ error: 'Producto no encontrado' });
    }

    const record = result.records[0];
    const producto = {
      _id: record.get('id'),
      nombre: record.get('nombre'),
      categoria: record.get('categoria'),
      codigo_mongo: record.get('codigo_mongo'),
      sku: record.get('sku'),
      codigo_alt: record.get('codigo_alt'),
      equivalencias: record.get('equivalencias')
        .filter(eq => eq.producto_id !== null)
        .map(eq => ({
          sistema: 'Neo4j',
          codigo: eq.producto_id,
          nombre: eq.nombre,
          razon: eq.razon,
          confidence: eq.confidence
        }))
    };

    res.json(producto);
  } catch (error) {
    console.error('Error al obtener producto:', error);
    res.status(500).json({ error: 'Error al obtener el producto' });
  } finally {
    await session.close();
  }
};

// POST crear producto
exports.create = async (req, res) => {
  const session = driver.session({ database: DATABASE_NAME });
  try {
    const { nombre, categoria, codigo_mongo, sku, codigo_alt } = req.body;

    // Validación básica
    if (!nombre || !categoria) {
      return res.status(400).json({ 
        error: 'Los campos nombre y categoria son obligatorios' 
      });
    }

    // Validar que la categoría existe
    const categoriaResult = await session.run(
      `MATCH (c:Categoria {nombre: $categoria}) RETURN count(c) as count`,
      { categoria }
    );

    if (categoriaResult.records[0].get('count').toNumber() === 0) {
      return res.status(400).json({ 
        error: `La categoría '${categoria}' no existe` 
      });
    }

    // Generar ID único basado en categoría
    const categoriaPrefix = {
      'Electrónica': 'E',
      'Ropa': 'R',
      'Alimentos': 'A',
      'Hogar': 'H',
      'Deportes': 'D',
      'Libros': 'L',
      'Juguetes': 'J',
      'Belleza': 'B',
      'Automóvil': 'AU',
      'Mascotas': 'M',
      'Jardín': 'JA',
      'Oficina': 'OF',
      'Música': 'MU',
      'Salud': 'SA',
      'Bebidas': 'BE'
    };

    const prefix = categoriaPrefix[categoria] || 'GEN';
    const productoId = `PROD-${prefix}-${Date.now()}`;

    // Crear el producto
    const createResult = await session.run(
      `CREATE (p:Producto {
         id: $productoId,
         nombre: $nombre,
         categoria: $categoria,
         codigo_mongo: $codigo_mongo,
         sku: $sku,
         codigo_alt: $codigo_alt
       })
       RETURN p.id as id`,
      { 
        productoId, 
        nombre, 
        categoria,
        codigo_mongo: codigo_mongo || null,
        sku: sku || null,
        codigo_alt: codigo_alt || null
      }
    );

    // Crear relación con categoría
    await session.run(
      `MATCH (p:Producto {id: $productoId})
       MATCH (c:Categoria {nombre: $categoria})
       CREATE (p)-[:PERTENECE_A]->(c)`,
      { productoId, categoria }
    );

    // Obtener el producto completo
    const result = await session.run(
      `MATCH (p:Producto {id: $productoId})
       OPTIONAL MATCH (p)-[:PERTENECE_A]->(cat:Categoria)
       RETURN p.id as id,
              p.nombre as nombre,
              p.categoria as categoria,
              p.sku as sku,
              p.codigo_alt as codigo_alt,
              p.codigo_mongo as codigo_mongo`,
      { productoId }
    );

    const record = result.records[0];
    const producto = {
      _id: record.get('id'),
      nombre: record.get('nombre'),
      categoria: record.get('categoria'),
      codigo_mongo: record.get('codigo_mongo'),
      sku: record.get('sku'),
      codigo_alt: record.get('codigo_alt')
    };

    res.status(201).json(producto);
  } catch (error) {
    console.error('Error al crear producto:', error);
    res.status(400).json({ 
      error: error.message || 'Error al crear el producto' 
    });
  } finally {
    await session.close();
  }
};

// PATCH actualizar producto
exports.update = async (req, res) => {
  const session = driver.session({ database: DATABASE_NAME });
  try {
    const { id } = req.params;
    const { nombre, categoria, codigo_mongo, sku, codigo_alt } = req.body;

    // Verificar que el producto existe
    const productoExists = await session.run(
      `MATCH (p:Producto {id: $id}) RETURN count(p) as count`,
      { id }
    );

    if (productoExists.records[0].get('count').toNumber() === 0) {
      return res.status(404).json({ error: 'Producto no encontrado' });
    }

    // Construir query dinámicamente solo con campos presentes
    const updates = [];
    const params = { id };

    if (nombre !== undefined) {
      updates.push('p.nombre = $nombre');
      params.nombre = nombre;
    }
    if (categoria !== undefined) {
      // Validar que la categoría existe
      const categoriaResult = await session.run(
        `MATCH (c:Categoria {nombre: $categoria}) RETURN count(c) as count`,
        { categoria }
      );

      if (categoriaResult.records[0].get('count').toNumber() === 0) {
        return res.status(400).json({ 
          error: `La categoría '${categoria}' no existe` 
        });
      }

      updates.push('p.categoria = $categoria');
      params.categoria = categoria;

      // Actualizar relación con categoría
      await session.run(
        `MATCH (p:Producto {id: $id})-[r:PERTENECE_A]->()
         DELETE r`,
        { id }
      );

      await session.run(
        `MATCH (p:Producto {id: $id})
         MATCH (c:Categoria {nombre: $categoria})
         CREATE (p)-[:PERTENECE_A]->(c)`,
        { id, categoria }
      );
    }
    if (codigo_mongo !== undefined) {
      updates.push('p.codigo_mongo = $codigo_mongo');
      params.codigo_mongo = codigo_mongo;
    }
    if (sku !== undefined) {
      updates.push('p.sku = $sku');
      params.sku = sku;
    }
    if (codigo_alt !== undefined) {
      updates.push('p.codigo_alt = $codigo_alt');
      params.codigo_alt = codigo_alt;
    }

    if (updates.length === 0) {
      return res.status(400).json({ 
        error: 'No se proporcionaron campos para actualizar' 
      });
    }

    // Actualizar el producto
    await session.run(
      `MATCH (p:Producto {id: $id})
       SET ${updates.join(', ')}
       RETURN p.id as id`,
      params
    );

    // Obtener el producto actualizado
    const result = await session.run(
      `MATCH (p:Producto {id: $id})
       OPTIONAL MATCH (p)-[:PERTENECE_A]->(cat:Categoria)
       RETURN p.id as id,
              p.nombre as nombre,
              p.categoria as categoria,
              p.sku as sku,
              p.codigo_alt as codigo_alt,
              p.codigo_mongo as codigo_mongo`,
      { id }
    );

    const record = result.records[0];
    const producto = {
      _id: record.get('id'),
      nombre: record.get('nombre'),
      categoria: record.get('categoria'),
      codigo_mongo: record.get('codigo_mongo'),
      sku: record.get('sku'),
      codigo_alt: record.get('codigo_alt')
    };

    res.json(producto);
  } catch (error) {
    console.error('Error al actualizar producto:', error);
    res.status(400).json({ 
      error: error.message || 'Error al actualizar el producto' 
    });
  } finally {
    await session.close();
  }
};

// DELETE eliminar producto
exports.delete = async (req, res) => {
  const session = driver.session({ database: DATABASE_NAME });
  try {
    const { id } = req.params;

    // Verificar si el producto está en órdenes
    const ordenesResult = await session.run(
      `MATCH ()-[r:CONTIENE]->(p:Producto {id: $id})
       RETURN count(r) as count`,
      { id }
    );

    const ordenesCount = ordenesResult.records[0].get('count').toNumber();

    if (ordenesCount > 0) {
      return res.status(400).json({ 
        error: `No se puede eliminar: el producto está en ${ordenesCount} orden(es)` 
      });
    }

    // DETACH DELETE elimina el nodo y todas sus relaciones
    const result = await session.run(
      `MATCH (p:Producto {id: $id})
       DETACH DELETE p
       RETURN count(p) as deleted`,
      { id }
    );

    const deleted = result.records[0].get('deleted').toNumber();

    if (deleted === 0) {
      return res.status(404).json({ error: 'Producto no encontrado' });
    }

    res.json({ 
      acknowledged: true,
      deletedCount: deleted
    });
  } catch (error) {
    console.error('Error al eliminar producto:', error);
    res.status(400).json({ 
      error: error.message || 'Error al eliminar el producto' 
    });
  } finally {
    await session.close();
  }
};

// EXTRA: Obtener equivalencias de un producto
exports.getEquivalencias = async (req, res) => {
  const session = driver.session({ database: DATABASE_NAME });
  try {
    const { id } = req.params;

    const result = await session.run(
      `MATCH (p1:Producto {id: $id})-[eq:EQUIVALE_A]->(p2:Producto)
       RETURN p2.id as producto_id,
              p2.nombre as nombre,
              p2.categoria as categoria,
              p2.sku as sku,
              p2.codigo_alt as codigo_alt,
              p2.codigo_mongo as codigo_mongo,
              eq.razon as razon,
              eq.confidence as confidence,
              eq.validado_por as validado_por
       ORDER BY eq.confidence DESC, p2.nombre`,
      { id }
    );

    if (result.records.length === 0) {
      // Verificar si el producto existe
      const productoExists = await session.run(
        `MATCH (p:Producto {id: $id}) RETURN count(p) as count`,
        { id }
      );
      
      if (productoExists.records[0].get('count').toNumber() === 0) {
        return res.status(404).json({ error: 'Producto no encontrado' });
      }
      
      return res.json([]); // Producto existe pero no tiene equivalencias
    }

    const equivalencias = result.records.map(record => ({
      producto_id: record.get('producto_id'),
      nombre: record.get('nombre'),
      categoria: record.get('categoria'),
      sku: record.get('sku'),
      codigo_alt: record.get('codigo_alt'),
      codigo_mongo: record.get('codigo_mongo'),
      razon: record.get('razon'),
      confidence: record.get('confidence'),
      validado_por: record.get('validado_por')
    }));

    res.json(equivalencias);
  } catch (error) {
    console.error('Error al obtener equivalencias:', error);
    res.status(500).json({ error: 'Error al obtener equivalencias' });
  } finally {
    await session.close();
  }
};

// EXTRA: Buscar productos por código (cualquier sistema)
exports.searchByCodigo = async (req, res) => {
  const session = driver.session({ database: DATABASE_NAME });
  try {
    const { codigo } = req.query;

    if (!codigo) {
      return res.status(400).json({ error: 'Parámetro codigo es requerido' });
    }

    const result = await session.run(
      `MATCH (p:Producto)
       WHERE p.id = $codigo 
          OR p.sku = $codigo 
          OR p.codigo_alt = $codigo 
          OR p.codigo_mongo = $codigo
       RETURN p.id as id,
              p.nombre as nombre,
              p.categoria as categoria,
              p.sku as sku,
              p.codigo_alt as codigo_alt,
              p.codigo_mongo as codigo_mongo`,
      { codigo }
    );

    const productos = result.records.map(record => ({
      _id: record.get('id'),
      nombre: record.get('nombre'),
      categoria: record.get('categoria'),
      codigo_mongo: record.get('codigo_mongo'),
      sku: record.get('sku'),
      codigo_alt: record.get('codigo_alt')
    }));

    res.json(productos);
  } catch (error) {
    console.error('Error en búsqueda:', error);
    res.status(500).json({ error: 'Error en la búsqueda' });
  } finally {
    await session.close();
  }
};

// EXTRA: Crear equivalencia entre productos
exports.createEquivalencia = async (req, res) => {
  const session = driver.session({ database: DATABASE_NAME });
  try {
    const { producto1_id, producto2_id, razon, confidence } = req.body;

    // Validación
    if (!producto1_id || !producto2_id) {
      return res.status(400).json({ 
        error: 'Los campos producto1_id y producto2_id son obligatorios' 
      });
    }

    if (producto1_id === producto2_id) {
      return res.status(400).json({ 
        error: 'No se puede crear equivalencia de un producto consigo mismo' 
      });
    }

    // Validar que ambos productos existen
    const productosResult = await session.run(
      `MATCH (p1:Producto {id: $producto1_id})
       MATCH (p2:Producto {id: $producto2_id})
       RETURN count(p1) as count1, count(p2) as count2`,
      { producto1_id, producto2_id }
    );

    const record = productosResult.records[0];
    if (record.get('count1').toNumber() === 0) {
      return res.status(404).json({ error: `Producto ${producto1_id} no encontrado` });
    }
    if (record.get('count2').toNumber() === 0) {
      return res.status(404).json({ error: `Producto ${producto2_id} no encontrado` });
    }

    // Verificar si ya existe la relación
    const existeResult = await session.run(
      `MATCH (p1:Producto {id: $producto1_id})-[r:EQUIVALE_A]->(p2:Producto {id: $producto2_id})
       RETURN count(r) as count`,
      { producto1_id, producto2_id }
    );

    if (existeResult.records[0].get('count').toNumber() > 0) {
      return res.status(400).json({ 
        error: 'La equivalencia ya existe' 
      });
    }

    // Crear la equivalencia (bidireccional)
    await session.run(
      `MATCH (p1:Producto {id: $producto1_id})
       MATCH (p2:Producto {id: $producto2_id})
       CREATE (p1)-[:EQUIVALE_A {
         razon: $razon,
         confidence: $confidence,
         validado_por: 'API'
       }]->(p2)
       CREATE (p2)-[:EQUIVALE_A {
         razon: $razon,
         confidence: $confidence,
         validado_por: 'API'
       }]->(p1)`,
      { 
        producto1_id, 
        producto2_id, 
        razon: razon || 'Equivalencia manual',
        confidence: confidence || 1.0
      }
    );

    res.status(201).json({ 
      message: 'Equivalencia creada exitosamente',
      producto1_id,
      producto2_id
    });
  } catch (error) {
    console.error('Error al crear equivalencia:', error);
    res.status(400).json({ 
      error: error.message || 'Error al crear equivalencia' 
    });
  } finally {
    await session.close();
  }
};

// EXTRA: Obtener productos de una categoría con estadísticas
exports.getByCategoria = async (req, res) => {
  const session = driver.session({ database: DATABASE_NAME });
  try {
    const { categoria } = req.params;

    // ✅ FIX: Usar neo4j.int() para LIMIT
    const limitValue = parseInt(req.query.limit, 10);
    const limit = neo4j.int(isNaN(limitValue) ? 100 : limitValue);

    const result = await session.run(
      `MATCH (p:Producto {categoria: $categoria})
       OPTIONAL MATCH ()-[r:CONTIENE]->(p)
       RETURN p.id as id,
              p.nombre as nombre,
              p.categoria as categoria,
              p.sku as sku,
              p.codigo_mongo as codigo_mongo,
              count(DISTINCT r) as totalVentas
       ORDER BY totalVentas DESC, p.nombre
       LIMIT $limit`,
      { categoria, limit }
    );

    const productos = result.records.map(record => ({
      _id: record.get('id'),
      nombre: record.get('nombre'),
      categoria: record.get('categoria'),
      codigo_mongo: record.get('codigo_mongo'),
      sku: record.get('sku'),
      totalVentas: record.get('totalVentas').toNumber()
    }));

    res.json(productos);
  } catch (error) {
    console.error('Error al obtener productos por categoría:', error);
    res.status(500).json({ error: 'Error al obtener productos' });
  } finally {
    await session.close();
  }
};