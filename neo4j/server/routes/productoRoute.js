const express = require('express');
const router = express.Router();

module.exports = (driver) => {
  const dbOpts = { database: 'ventas' };

  // Crear producto
  router.post('/', async (req, res) => {
    const { nombre, categoria, sku, codigo_alt, codigo_mongo } = req.body;
    const session = driver.session(dbOpts);
    try {
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

      console.log('Crear producto:', { id: idToUse, nombre, categoria, sku, codigo_alt, codigo_mongo });
      await session.run(
        'CREATE (p:Producto {id: $id, nombre: $nombre, categoria: $categoria, sku: $sku, codigo_alt: $codigo_alt, codigo_mongo: $codigo_mongo}) RETURN p',
        { id: idToUse, nombre, categoria, sku, codigo_alt, codigo_mongo }
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
