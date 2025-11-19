const { driver, DATABASE_NAME } = require('../config/neo4j');
const neo4j = require('neo4j-driver');

// GET todos los clientes
exports.getAll = async (req, res) => {
  const session = driver.session({ database: DATABASE_NAME });
  try {
    const limit = neo4j.int(parseInt(req.query.limit) || 100);
    const skip = neo4j.int(parseInt(req.query.skip) || 0);

    const result = await session.run(
      `MATCH (c:Cliente)
       RETURN c.id as id, 
              c.nombre as nombre, 
              c.genero as genero, 
              c.pais as pais
       ORDER BY c.nombre
       SKIP $skip
       LIMIT $limit`,
      { skip, limit }
    );

    const clientes = result.records.map(record => ({
      _id: record.get('id'),
      nombre: record.get('nombre'),
      genero: record.get('genero'),
      pais: record.get('pais')
    }));

    res.json(clientes);
  } catch (error) {
    console.error('❌ Error al obtener clientes:', error);
    res.status(500).json({ 
      error: 'Error al obtener los clientes',
      details: error.message
    });
  } finally {
    await session.close();
  }
};

// GET cliente por ID
exports.getById = async (req, res) => {
  const session = driver.session({ database: DATABASE_NAME });
  try {
    const { id } = req.params;

    const result = await session.run(
      `MATCH (c:Cliente {id: $id})
       OPTIONAL MATCH (c)-[:REALIZO]->(o:Orden)
       RETURN c.id as id,
              c.nombre as nombre,
              c.genero as genero,
              c.pais as pais,
              count(o) as totalOrdenes`,
      { id }
    );

    if (result.records.length === 0) {
      return res.status(404).json({ error: 'Cliente no encontrado' });
    }

    const record = result.records[0];
    const cliente = {
      _id: record.get('id'),
      nombre: record.get('nombre'),
      genero: record.get('genero'),
      pais: record.get('pais'),
      totalOrdenes: record.get('totalOrdenes').toNumber()
    };

    res.json(cliente);
  } catch (error) {
    console.error('❌ Error al obtener cliente:', error);
    res.status(500).json({ error: 'Error al obtener el cliente' });
  } finally {
    await session.close();
  }
};

// POST crear cliente
exports.create = async (req, res) => {
  const session = driver.session({ database: DATABASE_NAME });
  try {
    const { nombre, genero, pais } = req.body;

    if (!nombre || !genero || !pais) {
      return res.status(400).json({ 
        error: 'Los campos nombre, genero y pais son obligatorios' 
      });
    }

    // Generar ID único
    const clienteId = `CLI-${Date.now()}`;

    const result = await session.run(
      `CREATE (c:Cliente {
         id: $clienteId,
         nombre: $nombre,
         genero: $genero,
         pais: $pais
       })
       RETURN c.id as id, c.nombre as nombre, c.genero as genero, c.pais as pais`,
      { clienteId, nombre, genero, pais }
    );

    const record = result.records[0];
    const cliente = {
      _id: record.get('id'),
      nombre: record.get('nombre'),
      genero: record.get('genero'),
      pais: record.get('pais')
    };

    res.status(201).json(cliente);
  } catch (error) {
    console.error('❌ Error al crear cliente:', error);
    res.status(400).json({ 
      error: error.message || 'Error al crear el cliente' 
    });
  } finally {
    await session.close();
  }
};

// PATCH actualizar cliente
exports.update = async (req, res) => {
  const session = driver.session({ database: DATABASE_NAME });
  try {
    const { id } = req.params;
    const { nombre, genero, pais } = req.body;

    const updates = [];
    const params = { id };

    if (nombre !== undefined) {
      updates.push('c.nombre = $nombre');
      params.nombre = nombre;
    }
    if (genero !== undefined) {
      updates.push('c.genero = $genero');
      params.genero = genero;
    }
    if (pais !== undefined) {
      updates.push('c.pais = $pais');
      params.pais = pais;
    }

    if (updates.length === 0) {
      return res.status(400).json({ 
        error: 'No se proporcionaron campos para actualizar' 
      });
    }

    const result = await session.run(
      `MATCH (c:Cliente {id: $id})
       SET ${updates.join(', ')}
       RETURN c.id as id, c.nombre as nombre, c.genero as genero, c.pais as pais`,
      params
    );

    if (result.records.length === 0) {
      return res.status(404).json({ error: 'Cliente no encontrado' });
    }

    const record = result.records[0];
    const cliente = {
      _id: record.get('id'),
      nombre: record.get('nombre'),
      genero: record.get('genero'),
      pais: record.get('pais')
    };

    res.json(cliente);
  } catch (error) {
    console.error('❌ Error al actualizar cliente:', error);
    res.status(400).json({ 
      error: error.message || 'Error al actualizar el cliente' 
    });
  } finally {
    await session.close();
  }
};

// DELETE eliminar cliente
exports.delete = async (req, res) => {
  const session = driver.session({ database: DATABASE_NAME });
  try {
    const { id } = req.params;

    const result = await session.run(
      `MATCH (c:Cliente {id: $id})
       DETACH DELETE c
       RETURN count(c) as deleted`,
      { id }
    );

    const deleted = result.records[0].get('deleted').toNumber();

    if (deleted === 0) {
      return res.status(404).json({ error: 'Cliente no encontrado' });
    }

    res.json({ 
      acknowledged: true,
      deletedCount: deleted
    });
  } catch (error) {
    console.error('❌ Error al eliminar cliente:', error);
    res.status(400).json({ 
      error: error.message || 'Error al eliminar el cliente' 
    });
  } finally {
    await session.close();
  }
};

// EXTRA: Obtener órdenes de un cliente
exports.getOrders = async (req, res) => {
  const session = driver.session({ database: DATABASE_NAME });
  try {
    const { id } = req.params;

    const result = await session.run(
      `MATCH (c:Cliente {id: $id})-[:REALIZO]->(o:Orden)
       RETURN o.id as id,
              o.fecha as fecha,
              o.canal as canal,
              o.total as total
       ORDER BY o.fecha DESC`,
      { id }
    );

    if (result.records.length === 0) {
      const clienteExists = await session.run(
        `MATCH (c:Cliente {id: $id}) RETURN count(c) as count`,
        { id }
      );
      
      if (clienteExists.records[0].get('count').toNumber() === 0) {
        return res.status(404).json({ error: 'Cliente no encontrado' });
      }
      
      return res.json([]);
    }

    const ordenes = result.records.map(record => ({
      _id: record.get('id'),
      fecha: record.get('fecha').toString(),
      canal: record.get('canal'),
      total: record.get('total')
    }));

    res.json(ordenes);
  } catch (error) {
    console.error('❌ Error al obtener órdenes:', error);
    res.status(500).json({ error: 'Error al obtener las órdenes' });
  } finally {
    await session.close();
  }
};

// EXTRA: Estadísticas de un cliente
exports.getStats = async (req, res) => {
  const session = driver.session({ database: DATABASE_NAME });
  try {
    const { id } = req.params;

    const result = await session.run(
      `MATCH (c:Cliente {id: $id})
       OPTIONAL MATCH (c)-[:REALIZO]->(o:Orden)
       RETURN c.nombre as nombre,
              count(o) as totalOrdenes,
              sum(o.total) as totalGastado,
              collect(DISTINCT o.canal) as canalesUsados`,
      { id }
    );

    if (result.records.length === 0) {
      return res.status(404).json({ error: 'Cliente no encontrado' });
    }

    const record = result.records[0];
    const stats = {
      nombre: record.get('nombre'),
      totalOrdenes: record.get('totalOrdenes').toNumber(),
      totalGastado: record.get('totalGastado') || 0,
      canalesUsados: record.get('canalesUsados').filter(c => c !== null)
    };

    res.json(stats);
  } catch (error) {
    console.error('❌ Error al obtener estadísticas:', error);
    res.status(500).json({ error: 'Error al obtener estadísticas' });
  } finally {
    await session.close();
  }
};

// EXTRA: Buscar clientes por nombre, país o género
exports.search = async (req, res) => {
  const session = driver.session({ database: DATABASE_NAME });
  try {
    const { q, pais, genero } = req.query;
    const limit = neo4j.int(parseInt(req.query.limit) || 100);

    let whereClause = [];
    let params = { limit };

    // ✅ FIX: Solo agregar condición si q tiene valor
    if (q && q.trim()) {
      whereClause.push('toLower(c.nombre) CONTAINS toLower($q)');
      params.q = q;
    }
    if (pais && pais.trim()) {
      whereClause.push('c.pais = $pais');
      params.pais = pais;
    }
    if (genero && genero.trim()) {
      whereClause.push('c.genero = $genero');
      params.genero = genero;
    }

    const whereString = whereClause.length > 0 
      ? `WHERE ${whereClause.join(' AND ')}`
      : '';

    console.log('🔍 Búsqueda con filtros:', { q, pais, genero, whereString }); // ✅ DEBUG

    const result = await session.run(
      `MATCH (c:Cliente)
       ${whereString}
       RETURN c.id as id,
              c.nombre as nombre,
              c.genero as genero,
              c.pais as pais
       ORDER BY c.nombre
       LIMIT $limit`,
      params
    );

    console.log(`✅ Encontrados ${result.records.length} clientes`); // ✅ DEBUG

    const clientes = result.records.map(record => ({
      _id: record.get('id'),
      nombre: record.get('nombre'),
      genero: record.get('genero'),
      pais: record.get('pais')
    }));

    res.json(clientes);
  } catch (error) {
    console.error('❌ Error en búsqueda:', error);
    res.status(500).json({ error: 'Error al buscar clientes' });
  } finally {
    await session.close();
  }
};
