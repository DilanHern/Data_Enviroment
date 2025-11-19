const { driver, DATABASE_NAME } = require('../config/neo4j');
const neo4j = require('neo4j-driver');

// GET todas las órdenes
exports.getAll = async (req, res) => {
  const session = driver.session({ database: DATABASE_NAME });
  try {
    // ✅ FIX: Usar neo4j.int() con validación
    const limitValue = parseInt(req.query.limit, 10);
    const skipValue = parseInt(req.query.skip, 10);
    
    const limit = neo4j.int(isNaN(limitValue) ? 100 : limitValue);
    const skip = neo4j.int(isNaN(skipValue) ? 0 : skipValue);

    const result = await session.run(
      `MATCH (c:Cliente)-[:REALIZO]->(o:Orden)
       RETURN o.id as id, 
              o.fecha as fecha, 
              o.canal as canal,
              o.moneda as moneda,
              o.total as total,
              c.id as cliente_id
       ORDER BY o.fecha DESC
       SKIP $skip
       LIMIT $limit`,
      { skip, limit }
    );

    const ordenes = result.records.map(record => ({
      _id: record.get('id'),
      fecha: record.get('fecha').toString(),
      canal: record.get('canal'),
      moneda: record.get('moneda'),
      total: record.get('total'),
      cliente_id: record.get('cliente_id')
    }));

    res.json(ordenes);
  } catch (error) {
    console.error('Error al obtener órdenes:', error);
    res.status(500).json({ error: 'Error al obtener las órdenes' });
  } finally {
    await session.close();
  }
};

// GET orden por ID
exports.getById = async (req, res) => {
  const session = driver.session({ database: DATABASE_NAME });
  try {
    const { id } = req.params;

    const result = await session.run(
      `MATCH (c:Cliente)-[:REALIZO]->(o:Orden {id: $id})
       OPTIONAL MATCH (o)-[r:CONTIENE]->(p:Producto)
       RETURN o.id as id,
              o.fecha as fecha,
              o.canal as canal,
              o.moneda as moneda,
              o.total as total,
              o.metadatos as metadatos,
              c.id as cliente_id,
              collect({
                producto_id: p.id,
                nombre: p.nombre,
                cantidad: r.cantidad,
                precio_unit: r.precio_unitario
              }) as items`,
      { id }
    );

    if (result.records.length === 0) {
      return res.status(404).json({ error: 'Orden no encontrada' });
    }

    const record = result.records[0];
    
    // ✅ FIX: Parsear metadatos de JSON string a objeto
    let metadatos = {};
    try {
      const metadatosString = record.get('metadatos');
      metadatos = metadatosString ? JSON.parse(metadatosString) : {};
    } catch (e) {
      console.warn('⚠️ Error parseando metadatos:', e);
      metadatos = {};
    }
    
    const total = typeof record.get('total') === 'number' 
      ? record.get('total') 
      : parseFloat(record.get('total') || 0);
    
    const rawItems = record.get('items').filter(item => item.producto_id !== null);
    
    const items = rawItems.map(item => {
      let cantidad = 1;
      let precio_unit = 0;
      
      if (item.cantidad !== null && item.cantidad !== undefined) {
        if (neo4j.isInt(item.cantidad)) {
          cantidad = item.cantidad.toNumber();
        } else if (typeof item.cantidad === 'number') {
          cantidad = item.cantidad;
        } else {
          cantidad = parseInt(item.cantidad, 10) || 1;
        }
      }
      
      if (item.precio_unit !== null && item.precio_unit !== undefined) {
        if (neo4j.isInt(item.precio_unit)) {
          precio_unit = item.precio_unit.toNumber();
        } else if (typeof item.precio_unit === 'number') {
          precio_unit = item.precio_unit;
        } else {
          precio_unit = parseFloat(item.precio_unit) || 0;
        }
      }
      
      return {
        producto_id: item.producto_id,
        nombre: item.nombre,
        cantidad: cantidad,
        precio_unit: parseFloat(precio_unit.toFixed(2))
      };
    });

    const orden = {
      _id: record.get('id'),
      cliente_id: record.get('cliente_id'),
      fecha: record.get('fecha').toString(),
      canal: record.get('canal'),
      moneda: record.get('moneda'),
      total: total,
      items: items,
      metadatos: metadatos // ✅ Ya parseado como objeto
    };

    res.json(orden);
  } catch (error) {
    console.error('❌ Error al obtener orden:', error);
    res.status(500).json({ error: 'Error al obtener la orden' });
  } finally {
    await session.close();
  }
};


// POST crear orden
exports.create = async (req, res) => {
  const session = driver.session({ database: DATABASE_NAME });
  try {
    const { cliente_id, fecha, canal, moneda, total, items, metadatos } = req.body;

    // Validaciones
    if (!cliente_id || !fecha || !canal || !items || items.length === 0) {
      return res.status(400).json({ 
        error: 'Faltan campos requeridos: cliente_id, fecha, canal, items' 
      });
    }

    for (const item of items) {
      if (!item.producto_id || !item.cantidad || item.precio_unit === undefined) {
        return res.status(400).json({
          error: `Item inválido: debe tener producto_id, cantidad y precio_unit`
        });
      }
    }

    const timestamp = new Date(fecha).getTime();
    const ordenId = `ORD-${cliente_id}-${timestamp}`;

    // ✅ FIX: Convertir metadatos a JSON string
    const metadatosString = metadatos ? JSON.stringify(metadatos) : '{}';

    const createOrdenResult = await session.run(
      `CREATE (o:Orden {
        id: $id,
        fecha: datetime($fecha),
        canal: $canal,
        moneda: $moneda,
        total: $total,
        metadatos: $metadatos
      })
       RETURN o.id as id`,
      {
        id: ordenId,
        fecha: new Date(fecha).toISOString(),
        canal,
        moneda: moneda || 'CRC',
        total: parseFloat(total),
        metadatos: metadatosString // ✅ String en lugar de objeto
      }
    );

    await session.run(
      `MATCH (c:Cliente {id: $cliente_id})
       MATCH (o:Orden {id: $orden_id})
       CREATE (c)-[:REALIZO]->(o)`,
      { cliente_id, orden_id: ordenId }
    );

    // Crear relaciones con productos
    for (const item of items) {
      console.log(`✅ Guardando item: ${item.producto_id}, cantidad=${item.cantidad}, precio=${item.precio_unit}`);
      
      await session.run(
        `MATCH (o:Orden {id: $orden_id})
         MATCH (p:Producto {id: $producto_id})
         CREATE (o)-[:CONTIENE {
           cantidad: $cantidad,
           precio_unitario: $precio_unit
         }]->(p)`,
        {
          orden_id: ordenId,
          producto_id: item.producto_id,
          cantidad: neo4j.int(item.cantidad),
          precio_unit: parseFloat(item.precio_unit)
        }
      );
    }

    res.status(201).json({
      message: 'Orden creada exitosamente',
      _id: ordenId
    });
  } catch (error) {
    console.error('❌ Error al crear orden:', error);
    res.status(500).json({ error: 'Error al crear la orden: ' + error.message });
  } finally {
    await session.close();
  }
};

// PATCH actualizar orden
exports.update = async (req, res) => {
  const session = driver.session({ database: DATABASE_NAME });
  try {
    const { id } = req.params;
    const { cliente_id, fecha, canal, moneda, total, items } = req.body;

    // Verificar que la orden existe
    const ordenExists = await session.run(
      `MATCH (o:Orden {id: $id}) RETURN count(o) as count`,
      { id }
    );

    if (ordenExists.records[0].get('count').toNumber() === 0) {
      return res.status(404).json({ error: 'Orden no encontrada' });
    }

    // Construir query dinámicamente solo con campos presentes
    const updates = [];
    const params = { id };

    if (canal !== undefined) {
      updates.push('o.canal = $canal');
      params.canal = canal;
    }
    if (moneda !== undefined) {
      updates.push('o.moneda = $moneda');
      params.moneda = moneda;
    }
    if (total !== undefined) {
      // ✅ FIX: Convertir total a número
      const totalNumerico = typeof total === 'string' ? parseFloat(total) : total;
      updates.push('o.total = $total');
      params.total = totalNumerico;
    }
    if (fecha !== undefined) {
      updates.push('o.fecha = datetime($fecha)');
      params.fecha = new Date(fecha).toISOString();
    }

    // Actualizar campos básicos si hay alguno
    if (updates.length > 0) {
      await session.run(
        `MATCH (o:Orden {id: $id})
         SET ${updates.join(', ')}
         RETURN o.id as id`,
        params
      );
    }

    // Si se proporcionan items, actualizar relaciones CONTIENE
    if (items && Array.isArray(items)) {
      // Eliminar relaciones existentes
      await session.run(
        `MATCH (o:Orden {id: $id})-[r:CONTIENE]->()
         DELETE r`,
        { id }
      );

      // Crear nuevas relaciones
      for (const item of items) {
        const { producto_id, cantidad, precio_unit } = item;

        // Validar que el producto existe
        const productoResult = await session.run(
          `MATCH (p:Producto {id: $producto_id}) RETURN count(p) as count`,
          { producto_id }
        );

        if (productoResult.records[0].get('count').toNumber() === 0) {
          return res.status(400).json({ 
            error: `El producto ${producto_id} no existe` 
          });
        }

        // ✅ FIX: Convertir cantidad y precio_unit a números
        const cantidadNumerica = typeof cantidad === 'string' ? parseInt(cantidad, 10) : cantidad;
        const precioNumerico = typeof precio_unit === 'string' ? parseFloat(precio_unit) : precio_unit;

        await session.run(
          `MATCH (o:Orden {id: $id})
           MATCH (p:Producto {id: $producto_id})
           CREATE (o)-[:CONTIENE {
             cantidad: $cantidad,
             precio_unit: $precio_unit
           }]->(p)`,
          { id, producto_id, cantidad: cantidadNumerica, precio_unit: precioNumerico }
        );
      }
    }

    // Obtener la orden actualizada
    const result = await session.run(
      `MATCH (c:Cliente)-[:REALIZO]->(o:Orden {id: $id})
       OPTIONAL MATCH (o)-[r:CONTIENE]->(p:Producto)
       RETURN o.id as id,
              o.fecha as fecha,
              o.canal as canal,
              o.moneda as moneda,
              o.total as total,
              c.id as cliente_id,
              collect({
                producto_id: p.id,
                cantidad: r.cantidad,
                precio_unit: r.precio_unit
              }) as items`,
      { id }
    );

    const record = result.records[0];
    const orden = {
      _id: record.get('id'),
      cliente_id: record.get('cliente_id'),
      fecha: record.get('fecha').toString(),
      canal: record.get('canal'),
      moneda: record.get('moneda'),
      total: record.get('total'),
      items: record.get('items').filter(item => item.producto_id !== null)
    };

    res.json(orden);
  } catch (error) {
    console.error('Error al actualizar orden:', error);
    res.status(400).json({ 
      error: error.message || 'Error al actualizar la orden' 
    });
  } finally {
    await session.close();
  }
};

// DELETE eliminar orden
exports.delete = async (req, res) => {
  const session = driver.session({ database: DATABASE_NAME });
  try {
    const { id } = req.params;

    // DETACH DELETE elimina el nodo y todas sus relaciones
    const result = await session.run(
      `MATCH (o:Orden {id: $id})
       DETACH DELETE o
       RETURN count(o) as deleted`,
      { id }
    );

    const deleted = result.records[0].get('deleted').toNumber();

    if (deleted === 0) {
      return res.status(404).json({ error: 'Orden no encontrada' });
    }

    res.json({ 
      acknowledged: true,
      deletedCount: deleted
    });
  } catch (error) {
    console.error('Error al eliminar orden:', error);
    res.status(400).json({ 
      error: error.message || 'Error al eliminar la orden' 
    });
  } finally {
    await session.close();
  }
};

// EXTRA: Obtener productos de una orden
exports.getProducts = async (req, res) => {
  const session = driver.session({ database: DATABASE_NAME });
  try {
    const { id } = req.params;

    const result = await session.run(
      `MATCH (o:Orden {id: $id})-[r:CONTIENE]->(p:Producto)
       RETURN p.id as producto_id,
              p.nombre as nombre,
              p.categoria as categoria,
              r.cantidad as cantidad,
              r.precio_unit as precio_unit,
              (r.cantidad * r.precio_unit) as subtotal
       ORDER BY p.nombre`,
      { id }
    );

    if (result.records.length === 0) {
      // Verificar si la orden existe
      const ordenExists = await session.run(
        `MATCH (o:Orden {id: $id}) RETURN count(o) as count`,
        { id }
      );
      
      if (ordenExists.records[0].get('count').toNumber() === 0) {
        return res.status(404).json({ error: 'Orden no encontrada' });
      }
      
      return res.json([]); // Orden existe pero no tiene productos
    }

    const productos = result.records.map(record => ({
      producto_id: record.get('producto_id'),
      nombre: record.get('nombre'),
      categoria: record.get('categoria'),
      cantidad: record.get('cantidad').toNumber(),
      precio_unit: record.get('precio_unit'),
      subtotal: record.get('subtotal')
    }));

    res.json(productos);
  } catch (error) {
    console.error('Error al obtener productos de la orden:', error);
    res.status(500).json({ error: 'Error al obtener los productos' });
  } finally {
    await session.close();
  }
};

// EXTRA: Buscar órdenes por filtros
exports.search = async (req, res) => {
  const session = driver.session({ database: DATABASE_NAME });
  try {
    const { canal, moneda, cliente_id, fecha_desde, fecha_hasta } = req.query;
    
    // ✅ FIX: Usar neo4j.int() para limit
    const limitValue = parseInt(req.query.limit, 10);
    const limit = neo4j.int(isNaN(limitValue) ? 100 : limitValue);

    let whereClause = [];
    let params = { limit };

    if (canal) {
      whereClause.push('o.canal = $canal');
      params.canal = canal;
    }
    if (moneda) {
      whereClause.push('o.moneda = $moneda');
      params.moneda = moneda;
    }
    if (cliente_id) {
      whereClause.push('c.id = $cliente_id');
      params.cliente_id = cliente_id;
    }
    if (fecha_desde) {
      whereClause.push('o.fecha >= datetime($fecha_desde)');
      params.fecha_desde = new Date(fecha_desde).toISOString();
    }
    if (fecha_hasta) {
      whereClause.push('o.fecha <= datetime($fecha_hasta)');
      params.fecha_hasta = new Date(fecha_hasta).toISOString();
    }

    const whereString = whereClause.length > 0 
      ? `WHERE ${whereClause.join(' AND ')}`
      : '';

    const result = await session.run(
      `MATCH (c:Cliente)-[:REALIZO]->(o:Orden)
       ${whereString}
       RETURN o.id as id,
              o.fecha as fecha,
              o.canal as canal,
              o.moneda as moneda,
              o.total as total,
              c.id as cliente_id,
              c.nombre as cliente_nombre
       ORDER BY o.fecha DESC
       LIMIT $limit`,
      params
    );

    const ordenes = result.records.map(record => ({
      _id: record.get('id'),
      fecha: record.get('fecha').toString(),
      canal: record.get('canal'),
      moneda: record.get('moneda'),
      total: record.get('total'),
      cliente_id: record.get('cliente_id'),
      cliente_nombre: record.get('cliente_nombre')
    }));

    res.json(ordenes);
  } catch (error) {
    console.error('Error en búsqueda:', error);
    res.status(500).json({ error: 'Error en la búsqueda' });
  } finally {
    await session.close();
  }
};

// EXTRA: Estadísticas de una orden
exports.getStats = async (req, res) => {
  const session = driver.session({ database: DATABASE_NAME });
  try {
    const { id } = req.params;

    const result = await session.run(
      `MATCH (c:Cliente)-[:REALIZO]->(o:Orden {id: $id})
       OPTIONAL MATCH (o)-[r:CONTIENE]->(p:Producto)
       RETURN o.id as ordenId,
              o.fecha as fecha,
              o.total as total,
              c.nombre as clienteNombre,
              count(DISTINCT p) as totalProductos,
              sum(r.cantidad) as totalItems,
              collect(DISTINCT p.categoria) as categorias`,
      { id }
    );

    if (result.records.length === 0) {
      return res.status(404).json({ error: 'Orden no encontrada' });
    }

    const record = result.records[0];
    const stats = {
      ordenId: record.get('ordenId'),
      fecha: record.get('fecha').toString(),
      total: record.get('total'),
      clienteNombre: record.get('clienteNombre'),
      totalProductos: record.get('totalProductos').toNumber(),
      totalItems: record.get('totalItems')?.toNumber() || 0,
      categorias: record.get('categorias').filter(c => c !== null)
    };

    res.json(stats);
  } catch (error) {
    console.error('Error al obtener estadísticas:', error);
    res.status(500).json({ error: 'Error al obtener estadísticas' });
  } finally {
    await session.close();
  }
};