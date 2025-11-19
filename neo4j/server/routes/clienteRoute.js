const express = require('express');
const router = express.Router();

// Recibe el driver de Neo4j como parámetro
module.exports = (driver) => {
  const dbOpts = { database: 'ventas' };

  // Crear cliente
  router.post('/', async (req, res) => {
    const { id, nombre, genero, pais } = req.body;
    // Generar un id si no viene en el body
    const idToUse = id || `cli_${Date.now()}_${Math.floor(Math.random() * 10000)}`;
    const session = driver.session(dbOpts);
    try {
      console.log('Crear cliente:', { id: idToUse, nombre, genero, pais });
      await session.run(
        'CREATE (c:Cliente {id: $id, nombre: $nombre, genero: $genero, pais: $pais}) RETURN c',
        { id: idToUse, nombre, genero, pais }
      );
      res.status(201).json({ message: 'Cliente creado', id: idToUse });
    } catch (err) {
      console.error('Error creando cliente:', err);
      res.status(500).json({ error: err.message });
    } finally {
      await session.close();
    }
  });

  // Buscar cliente por id
  router.get('/:id', async (req, res) => {
    const session = driver.session(dbOpts);
    try {
      const result = await session.run(
        'MATCH (c:Cliente {id: $id}) RETURN c',
        { id: req.params.id }
      );
      if (result.records.length === 0) {
        return res.status(404).json({ error: 'Cliente no encontrado' });
      }
      res.json(result.records[0].get('c').properties);
    } catch (err) {
      res.status(500).json({ error: err.message });
    } finally {
      await session.close();
    }
  });

  // Buscar todos los clientes
  router.get('/', async (req, res) => {
    const session = driver.session(dbOpts);
    try {
      const result = await session.run('MATCH (c:Cliente) RETURN c');
      const clientes = result.records.map(r => r.get('c').properties);
      res.json(clientes);
    } catch (err) {
      res.status(500).json({ error: err.message });
    } finally {
      await session.close();
    }
  });

  // Editar cliente
  router.patch('/:id', async (req, res) => {
    const { nombre, genero, pais } = req.body;
    const session = driver.session(dbOpts);
    try {
      const result = await session.run(
        'MATCH (c:Cliente {id: $id}) SET c.nombre = $nombre, c.genero = $genero, c.pais = $pais RETURN c',
        { id: req.params.id, nombre, genero, pais }
      );
      if (result.records.length === 0) {
        return res.status(404).json({ error: 'Cliente no encontrado' });
      }
      res.json({ message: 'Cliente actualizado' });
    } catch (err) {
      res.status(500).json({ error: err.message });
    } finally {
      await session.close();
    }
  });

  // Borrar cliente
  router.delete('/:id', async (req, res) => {
    const session = driver.session(dbOpts);
    try {
      const result = await session.run(
        'MATCH (c:Cliente {id: $id}) DETACH DELETE c RETURN COUNT(c) AS deleted',
        { id: req.params.id }
      );
      // Neo4j siempre retorna 0 en COUNT(c) después de borrar, así que solo responde OK
      res.json({ message: 'Cliente eliminado' });
    } catch (err) {
      res.status(500).json({ error: err.message });
    } finally {
      await session.close();
    }
  });

  return router;
};
