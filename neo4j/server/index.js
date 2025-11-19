const express = require('express');
const neo4j = require('neo4j-driver');
const cors = require('cors');

const app = express();
const port = 3000;

// Configura la conexión a Neo4j (ajusta usuario y contraseña si es necesario)
const driver = neo4j.driver(
  'neo4j://localhost:7687',
  neo4j.auth.basic('neo4j', 'dilan2005'), // Cambia 'password' por tu contraseña real
  { database: 'ventas' }
);

app.use(cors());
app.use(express.json());

// Endpoint de prueba para verificar conexión a Neo4j
app.get('/api/health', async (req, res) => {
  const session = driver.session({ database: 'ventas' });
  try {
    await session.run('RETURN 1');
    res.json({ status: 'ok', neo4j: 'connected' });
  } catch (err) {
    res.status(500).json({ status: 'error', error: err.message });
  } finally {
    await session.close();
  }
});

const clienteRoute = require('./routes/clienteRoute')(driver);
const productoRoute = require('./routes/productoRoute')(driver);
const ordenRoute = require('./routes/ordenRoute')(driver);
const categoriaRoute = require('./routes/categoriaRoute')(driver);

app.use('/api/clientes', clienteRoute);
app.use('/api/productos', productoRoute);
app.use('/api/ordenes', ordenRoute);
app.use('/api/categorias', categoriaRoute);

app.listen(port, () => { 
  console.log(`API escuchando en http://localhost:${port}`);
});
