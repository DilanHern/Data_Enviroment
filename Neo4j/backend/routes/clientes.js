const express = require('express');
const router = express.Router();
const clientesController = require('../controllers/clientesController');

// ⚠️ IMPORTANTE: /search DEBE estar ANTES de /:id
router.get('/search', clientesController.search); 
router.get('/', clientesController.getAll);
router.get('/:id', clientesController.getById);
router.post('/', clientesController.create);
router.patch('/:id', clientesController.update);
router.delete('/:id', clientesController.delete);
router.get('/:id/orders', clientesController.getOrders);
router.get('/:id/stats', clientesController.getStats);

module.exports = router;