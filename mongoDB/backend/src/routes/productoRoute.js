const express = require('express');
const router = express.Router();
const Producto = require('../models/producto');

router.post('/productos', async (req, res) => {
    const producto = new Producto(req.body);
    producto.save()
        .then((data) => res.status(201).json(data))
        .catch((error) => res.status(400).json({ error: error.message || 'Error al crear el producto' }));
});

router.get('/productos/:id', async (req, res) => {
    const { id } = req.params;
    Producto.findById(id)
        .then((data) => {
            res.json(data);
        })
        .catch((error) => res.status(404).json({ error: 'Producto no encontrado' }));
});

router.get('/productos', async (req, res) => {
    Producto.find()
        .then((data) => {
            res.json(data);
        })
        .catch((error) => res.status(500).json({ error: 'Error al obtener los productos' }));
});

router.patch('/productos/:id', async (req, res) => {
    const { id } = req.params;
    const { codigo_mongo, nombre, categoria, equivalencias } = req.body;

    Producto.updateOne({ _id: id }, { $set: { codigo_mongo, nombre, categoria, equivalencias } })
        .then((data) => {
            if (!data) {
                return res.status(404).json({ error: 'Producto no encontrado' });
            }
            res.json(data);
        })
        .catch((error) => res.status(400).json({ error: error.message || 'Error al actualizar el producto' }));
});

router.delete('/productos/:id', async (req, res) => {
    const { id } = req.params;
    Producto.deleteOne({ _id: id })
        .then((data) => {
            res.json(data);
        })
        .catch((error) => res.status(400).json({ error: error.message || 'Error al eliminar el producto' }));
});

module.exports = router;
