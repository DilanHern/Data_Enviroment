const express = require('express');
const router = express.Router();
const productosController = require('../controllers/productosController');

// Rutas principales (compatibles con MongoDB)
router.get('/', productosController.getAll);                    // GET /api/productos
router.get('/:id', productosController.getById);                // GET /api/productos/:id
router.post('/', productosController.create);                   // POST /api/productos
router.patch('/:id', productosController.update);               // PATCH /api/productos/:id
router.delete('/:id', productosController.delete);              // DELETE /api/productos/:id

// Rutas extras específicas de Neo4j
router.get('/search/codigo', productosController.searchByCodigo);              // GET /api/productos/search/codigo?codigo=SKU-E-1001
router.get('/categoria/:categoria', productosController.getByCategoria);       // GET /api/productos/categoria/Electrónica
router.get('/:id/equivalencias', productosController.getEquivalencias);        // GET /api/productos/:id/equivalencias
router.post('/equivalencias', productosController.createEquivalencia);         // POST /api/productos/equivalencias

module.exports = router;