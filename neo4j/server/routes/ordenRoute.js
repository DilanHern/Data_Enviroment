const express = require('express');
const router = express.Router();

module.exports = (driver) => {
  const dbOpts = { database: 'ventas' };

  // Crear orden
  router.post('/', async (req, res) => {
    let { id, canal, moneda, total, cliente_id, items } = req.body;
    items = items || []
    const session = driver.session(dbOpts);
    try {
      // generate id if not provided
      const orderId = id || `ORD-${Date.now()}`

      // Generate automatic UTC timestamp with 9 fractional digits like 2024-10-25T03:29:51.587000000Z
      const iso = new Date().toISOString(); // e.g. 2024-10-25T03:29:51.587Z
      const fecha = iso.replace(/(\.\d{3})Z$/, '$1' + '000000Z');

      // Create order node and set fecha as Neo4j datetime (not a string)
      await session.run(
        'CREATE (o:Orden {id: $id, canal: $canal, moneda: $moneda, total: $total}) SET o.fecha = datetime($fecha) RETURN o',
        { id: orderId, canal, moneda, total, fecha }
      );

      // Link cliente if provided
      if (cliente_id) {
        await session.run(
          'MATCH (c:Cliente {id: $cliente_id}), (o:Orden {id: $id}) MERGE (c)-[:REALIZO]->(o)',
          { cliente_id, id: orderId }
        );
      }

      // Create CONTIENE relations for items
      if (Array.isArray(items) && items.length > 0) {
        await session.run(
          `UNWIND $items AS item
           MATCH (o:Orden {id: $id})
           MATCH (p:Producto {id: item.producto_id})
           MERGE (o)-[:CONTIENE {cantidad: item.cantidad, precio_unit: item.precio_unit}]->(p)`,
          { id: orderId, items }
        );
      }

      res.status(201).json({ message: 'Orden creada', id: orderId });
    } catch (err) {
      console.error('Error creating order:', err)
      res.status(500).json({ error: err.message });
    } finally {
      await session.close();
    }
  });

    // Obtener orden por id con datos del cliente y productos
    router.get('/:id', async (req, res) => {
    const session = driver.session(dbOpts);
    try {
        const result = await session.run(`
        MATCH (c:Cliente)-[:REALIZO]->(o:Orden {id: $id})
        OPTIONAL MATCH (o)-[cont:CONTIENE]->(p:Producto)
        RETURN o, c, collect({
            producto: p,
            cantidad: cont.cantidad,
            precio_unit: cont.precio_unit
        }) as productos
        `, { id: req.params.id });
        
        if (result.records.length === 0) {
        return res.status(404).json({ error: 'Orden no encontrada' });
        }
        
        const record = result.records[0];
        const orden = record.get('o').properties;
        const cliente = record.get('c').properties;
        const productos = record.get('productos').map(item => {
        if (!item.producto) return null;
        return {
            ...item.producto.properties,
            cantidad: item.cantidad,
            precio_unit: item.precio_unit
        };
        }).filter(Boolean);
        
        res.json({ ...orden, cliente, productos });
    } catch (err) {
        res.status(500).json({ error: err.message });
    } finally {
        await session.close();
    }
    });

  // Obtener todas las ordenes con datos del cliente y productos (incluyendo cantidad y precio_unit de la relación CONTIENE)
  router.get('/', async (req, res) => {
    const session = driver.session(dbOpts);
    try {
      const result = await session.run(`
        MATCH (c:Cliente)-[:REALIZO]->(o:Orden)
        OPTIONAL MATCH (o)-[cont:CONTIENE]->(p:Producto)
        RETURN o, c, collect({
          producto: p,
          cantidad: cont.cantidad,
          precio_unit: cont.precio_unit
        }) as productos
        LIMIT 100
      `);
      const ordenes = result.records.map(r => {
        const orden = r.get('o').properties;
        const cliente = r.get('c').properties;
        const productos = r.get('productos').map(item => {
          if (!item.producto) return null;
          return {
            ...item.producto.properties,
            cantidad: item.cantidad,
            precio_unit: item.precio_unit
          };
        }).filter(Boolean);
        return { ...orden, cliente, productos };
      });
      res.json(ordenes);
    } catch (err) {
      res.status(500).json({ error: err.message });
    } finally {
      await session.close();
    }
  });

  // Editar orden (fecha de creación no modificable)
  router.patch('/:id', async (req, res) => {
    // ignore any provided 'fecha' to avoid changing creation timestamp
    const { canal, moneda, total } = req.body;
    const session = driver.session(dbOpts);
    try {
      // Use datetime($fecha) so the property is stored as a Neo4j datetime, not a string
      // Also synchronize CONTIENE relationships: delete existing and recreate from provided items
      const items = req.body.items || []
      const result = await session.run(
        `MATCH (o:Orden {id: $id})
         SET o.canal = $canal, o.moneda = $moneda, o.total = $total
         WITH o
         OPTIONAL MATCH (o)-[r:CONTIENE]->()
         DELETE r
         WITH o
         UNWIND $items AS item
         // collect matched products and pick the first to avoid creating multiple relations if duplicate product nodes exist
         MATCH (p:Producto {id: item.producto_id})
         WITH o, item, collect(p) AS ps
         WITH o, item, CASE WHEN size(ps) > 0 THEN ps[0] ELSE NULL END AS p
         WHERE p IS NOT NULL
         CREATE (o)-[:CONTIENE {cantidad: item.cantidad, precio_unit: item.precio_unit}]->(p)
         RETURN o`,
        { id: req.params.id, canal, moneda, total, items }
      );
      if (result.records.length === 0) {
        return res.status(404).json({ error: 'Orden no encontrada' });
      }
      res.json({ message: 'Orden actualizada' });
    } catch (err) {
      res.status(500).json({ error: err.message });
    } finally {
      await session.close();
    }
  });

  // Borrar orden
  router.delete('/:id', async (req, res) => {
    const session = driver.session(dbOpts);
    try {
      await session.run(
        'MATCH (o:Orden {id: $id}) DETACH DELETE o',
        { id: req.params.id }
      );
      res.json({ message: 'Orden eliminada' });
    } catch (err) {
      res.status(500).json({ error: err.message });
    } finally {
      await session.close();
    }
  });

  return router;
};
