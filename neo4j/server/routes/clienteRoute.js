const express = require('express');
const router = express.Router();

// Recibe el driver de Neo4j como parámetro
module.exports = (driver) => {
  const dbOpts = { database: 'ventas' };

  // Crear cliente
  router.post('/', async (req, res) => {
    const { id, nombre, genero, pais, email } = req.body;
    // Generar un id si no viene en el body
    const idToUse = id || `cli_${Date.now()}_${Math.floor(Math.random() * 10000)}`;
    const session = driver.session(dbOpts);
    try {
      // Generar timestamp UTC con formato similar a "2024-10-25T03:29:51.587000000Z"
      const iso = new Date().toISOString(); // ex: 2024-10-25T03:29:51.587Z
      // Convertir milisegundos (3 decimales) a nanosegundos (9 decimales) llenando con ceros
      const fecha = iso.replace(/(\.\d{3})Z$/, '$1' + '000000Z');

      console.log('Crear cliente:', { id: idToUse, nombre, genero, pais, email, fecha });

      // Verificar si ya existe un cliente con ese email
      if (email) {
        const existing = await session.run(
          'MATCH (c:Cliente {email: $email}) RETURN c LIMIT 1',
          { email }
        );
        if (existing.records.length > 0) {
          return res.status(409).json({ error: 'Ya existe un cliente con ese email' });
        }
      }

      // Create node and set fecha as Neo4j datetime (not a string)
      await session.run(
        'CREATE (c:Cliente {id: $id, nombre: $nombre, genero: $genero, pais: $pais, email: $email}) SET c.fecha = datetime($fecha) RETURN c',
        { id: idToUse, nombre, genero, pais, email, fecha }
      );
      res.status(201).json({ message: 'Cliente creado', id: idToUse });
    } catch (err) {
      console.error('Error creando cliente:', err);
      // Si la excepción proviene de una violación de constraint en Neo4j, devolver 409
      if (err && (err.code && err.code.toString().toLowerCase().includes('constraint') || (err.message && err.message.toLowerCase().includes('constraint')))) {
        return res.status(409).json({ error: 'Email duplicado (constraint violado)' });
      }
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
      // Si la excepción proviene de una violación de constraint en Neo4j, devolver 409
      if (err && (err.code && err.code.toString().toLowerCase().includes('constraint') || (err.message && err.message.toLowerCase().includes('constraint')))) {
        return res.status(409).json({ error: 'Email duplicado (constraint violado)' });
      }
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
    const { nombre, genero, pais, email } = req.body;
    const session = driver.session(dbOpts);
    try {
      // Si se intenta cambiar el email, asegurarse de que no esté en uso por otro cliente
      if (email) {
        const conflict = await session.run(
          'MATCH (c:Cliente {email: $email}) WHERE c.id <> $id RETURN c LIMIT 1',
          { email, id: req.params.id }
        );
        if (conflict.records.length > 0) {
          return res.status(409).json({ error: 'El email ya está en uso por otro cliente' });
        }
      }

      const result = await session.run(
        'MATCH (c:Cliente {id: $id}) SET c.nombre = $nombre, c.genero = $genero, c.pais = $pais, c.email = $email RETURN c',
        { id: req.params.id, nombre, genero, pais, email }
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
