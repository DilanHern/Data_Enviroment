const express = require('express');
const router = express.Router();
const ordenesController = require('../controllers/ordenesController');

// Rutas principales (compatibles con MongoDB)
router.get('/', ordenesController.getAll);           // GET /api/ordenes
router.get('/:id', ordenesController.getById);       // GET /api/ordenes/:id
router.post('/', ordenesController.create);          // POST /api/ordenes
router.patch('/:id', ordenesController.update);      // PATCH /api/ordenes/:id
router.delete('/:id', ordenesController.delete);     // DELETE /api/ordenes/:id

// Rutas extras específicas de Neo4j
router.get('/search', ordenesController.search);          // GET /api/ordenes/search?canal=WEB
router.get('/:id/productos', ordenesController.getProducts); // GET /api/ordenes/:id/productos
router.get('/:id/stats', ordenesController.getStats);     // GET /api/ordenes/:id/stats

module.exports = router;