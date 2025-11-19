const neo4j = require('neo4j-driver');
require('dotenv').config();

const driver = neo4j.driver(
  process.env.NEO4J_URI || 'bolt://localhost:7687',
  neo4j.auth.basic(
    process.env.NEO4J_USER || 'neo4j',
    process.env.NEO4J_PASSWORD || 'password'
  )
);

//FORZAR base de datos "ventas"
const DATABASE_NAME = 'ventas';

// Verificar conexión
async function verifyConnection() {
  const session = driver.session({ database: DATABASE_NAME }); 
  try {
    const result = await session.run('RETURN 1 as test');
    console.log(`Conectado a Neo4j - Base de datos: ${DATABASE_NAME}`);
    
    // Mostrar ejemplos de nombres
    const sample = await session.run(
      `MATCH (c:Cliente) 
       RETURN c.nombre 
       ORDER BY c.id 
       LIMIT 5`
    );
    
    console.log('Primeros 5 clientes en la base:');
    sample.records.forEach(r => console.log(`   - ${r.get('c.nombre')}`));
    
  } catch (error) {
    console.error('Error:', error.message);
  } finally {
    await session.close();
  }
}

verifyConnection();

module.exports = { driver, DATABASE_NAME };