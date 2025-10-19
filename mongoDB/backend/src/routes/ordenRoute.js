const express = require('express');
const router = express.Router();
const Orden = require('../models/orden');

router.post('/ordenes', async (req, res) => {
    const orden = new Orden(req.body);
    orden.save()
        .then((data) => res.status(201).json(data))
        .catch((error) => res.status(400).json({ error: error.message || 'Error al crear la orden' }));
});

router.get('/ordenes/:id', async (req, res) => {
    const { id } = req.params;
    Orden.findById(id)
        .then((data) => {
            res.json(data);
        })
        .catch((error) => res.status(404).json({ error: 'Orden no encontrada' }));
});

router.get('/ordenes', async (req, res) => {
    Orden.find()
        .then((data) => {
            res.json(data);
        })
        .catch((error) => res.status(500).json({ error: 'Error al obtener las órdenes' }));
});

router.patch('/ordenes/:id', async (req, res) => {
    const { id } = req.params;
    const { cliente_id, fecha, canal, moneda, total, items, metadatos } = req.body;

    Orden.updateOne({ _id: id }, { $set: { cliente_id, fecha, canal, moneda, total, items, metadatos } })
        .then((data) => {
            if (!data) {
                return res.status(404).json({ error: 'Orden no encontrada' });
            }
            res.json(data);
        })
        .catch((error) => res.status(400).json({ error: error.message || 'Error al actualizar la orden' }));
});

router.delete('/ordenes/:id', async (req, res) => {
    const { id } = req.params;
    Orden.deleteOne({ _id: id })
        .then((data) => {
            res.json(data);
        })
        .catch((error) => res.status(400).json({ error: error.message || 'Error al eliminar la orden' }));
});

module.exports = router;
