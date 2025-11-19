const express = require('express');
const router = express.Router();

module.exports = (driver) => {
	const dbOpts = { database: 'ventas' };

	// Mostrar todas las categorías
	router.get('/', async (req, res) => {
		const session = driver.session(dbOpts);
		try {
			const result = await session.run('MATCH (c:Categoria) RETURN c');
			const categorias = result.records.map(r => r.get('c').properties);
			res.json(categorias);
		} catch (err) {
			res.status(500).json({ error: err.message });
		} finally {
			await session.close();
		}
	});

	return router;
};
