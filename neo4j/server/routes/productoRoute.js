const express = require('express');
const router = express.Router();

module.exports = (driver) => {
  const dbOpts = { database: 'ventas' };

  // Crear producto
  router.post('/', async (req, res) => {
    const { nombre, categoria, sku, codigo_alt, codigo_mongo } = req.body;
    const session = driver.session(dbOpts);
    try {
      // Verificar conflictos por sku, codigo_alt o codigo_mongo
      const conflictQuery = `
        MATCH (p:Producto)
        WHERE ($sku IS NOT NULL AND p.sku = $sku)
           OR ($codigo_alt IS NOT NULL AND p.codigo_alt = $codigo_alt)
           OR ($codigo_mongo IS NOT NULL AND p.codigo_mongo = $codigo_mongo)
        RETURN p LIMIT 1
      `;
      const conflictRes = await session.run(conflictQuery, { sku, codigo_alt, codigo_mongo });
      if (conflictRes.records.length > 0) {
        const existing = conflictRes.records[0].get('p').properties;
        // Determinar qué campo causó el conflicto
        let message = 'Ya existe un producto con algún código duplicado';
        if (sku && existing.sku === sku) message = 'El SKU ya está en uso';
        else if (codigo_mongo && existing.codigo_mongo === codigo_mongo) message = 'El código Mongo ya está en uso';
        else if (codigo_alt && existing.codigo_alt === codigo_alt) message = 'El código alternativo ya está en uso';
        return res.status(409).json({ error: message });
      }
      // Si no se envía id desde el cliente, generar uno con prefijo PRO y número incremental
      const maxRes = await session.run(
        'MATCH (p:Producto) WHERE p.id STARTS WITH $prefix RETURN max(toInteger(replace(p.id, $prefix, ""))) AS maxNum',
        { prefix: 'PRO' }
      );
      let maxNum = 0;
      if (maxRes.records.length > 0) {
        const val = maxRes.records[0].get('maxNum');
        if (val !== null && typeof val === 'object' && typeof val.toNumber === 'function') {
          maxNum = val.toNumber();
        } else if (val !== null) {
          maxNum = Number(val);
        }
      }
      const base = 100000;
      const nextNum = Math.max(maxNum, base - 1) + 1;
      const idToUse = `PRO${nextNum}`;

      // Generar timestamp UTC con formato similar a "2024-10-25T03:29:51.587000000Z"
      const iso = new Date().toISOString(); // ex: 2024-10-25T03:29:51.587Z
      const fecha = iso.replace(/(\.\d{3})Z$/, '$1' + '000000Z');

      console.log('Crear producto:', { id: idToUse, nombre, categoria, sku, codigo_alt, codigo_mongo, fecha });
      // Create product and set fecha as Neo4j datetime (not a string)
      await session.run(
        'CREATE (p:Producto {id: $id, nombre: $nombre, categoria: $categoria, sku: $sku, codigo_alt: $codigo_alt, codigo_mongo: $codigo_mongo}) SET p.fecha = datetime($fecha) RETURN p',
        { id: idToUse, nombre, categoria, sku, codigo_alt, codigo_mongo, fecha }
      );
      res.status(201).json({ message: 'Producto creado', id: idToUse });
    } catch (err) {
      console.error('Error creando producto:', err);
      res.status(500).json({ error: err.message });
    } finally {
      await session.close();
    }
  });

  // Obtener producto por id
  router.get('/:id', async (req, res) => {
    const session = driver.session(dbOpts);
    try {
      const result = await session.run(
        'MATCH (p:Producto {id: $id}) RETURN p',
        { id: req.params.id }
      );
      if (result.records.length === 0) {
        return res.status(404).json({ error: 'Producto no encontrado' });
      }
      res.json(result.records[0].get('p').properties);
    } catch (err) {
      res.status(500).json({ error: err.message });
    } finally {
      await session.close();
    }
  });

  // Obtener todos los productos
  router.get('/', async (req, res) => {
    const session = driver.session(dbOpts);
    try {
      const result = await session.run('MATCH (p:Producto) RETURN p');
      const productos = result.records.map(r => r.get('p').properties);
      res.json(productos);
    } catch (err) {
      res.status(500).json({ error: err.message });
    } finally {
      await session.close();
    }
  });

  // Editar producto
  router.patch('/:id', async (req, res) => {
    const { nombre, categoria, sku, codigo_alt, codigo_mongo } = req.body;
    const session = driver.session(dbOpts);
    try {
      // Verificar conflictos con otros productos (mismo sku/codigo_alt/codigo_mongo y distinto id)
      const conflictQuery = `
        MATCH (p:Producto)
        WHERE ( ($sku IS NOT NULL AND p.sku = $sku)
             OR ($codigo_alt IS NOT NULL AND p.codigo_alt = $codigo_alt)
             OR ($codigo_mongo IS NOT NULL AND p.codigo_mongo = $codigo_mongo) )
          AND p.id <> $id
        RETURN p LIMIT 1
      `;
      const conflictRes = await session.run(conflictQuery, { sku, codigo_alt, codigo_mongo, id: req.params.id });
      if (conflictRes.records.length > 0) {
        const existing = conflictRes.records[0].get('p').properties;
        let message = 'El código ya está en uso por otro producto';
        if (sku && existing.sku === sku) message = 'El SKU ya está en uso por otro producto';
        else if (codigo_mongo && existing.codigo_mongo === codigo_mongo) message = 'El código Mongo ya está en uso por otro producto';
        else if (codigo_alt && existing.codigo_alt === codigo_alt) message = 'El código alternativo ya está en uso por otro producto';
        return res.status(409).json({ error: message });
      }
      const result = await session.run(
        'MATCH (p:Producto {id: $id}) SET p.nombre = $nombre, p.categoria = $categoria, p.sku = $sku, p.codigo_alt = $codigo_alt, p.codigo_mongo = $codigo_mongo RETURN p',
        { id: req.params.id, nombre, categoria, sku, codigo_alt, codigo_mongo }
      );
      if (result.records.length === 0) {
        return res.status(404).json({ error: 'Producto no encontrado' });
      }
      res.json({ message: 'Producto actualizado' });
    } catch (err) {
      res.status(500).json({ error: err.message });
    } finally {
      await session.close();
    }
  });

  // Eliminar producto
  router.delete('/:id', async (req, res) => {
    const session = driver.session(dbOpts);
    try {
      await session.run(
        'MATCH (p:Producto {id: $id}) DETACH DELETE p',
        { id: req.params.id }
      );
      res.json({ message: 'Producto eliminado' });
    } catch (err) {
      res.status(500).json({ error: err.message });
    } finally {
      await session.close();
    }
  });

  return router;
};
