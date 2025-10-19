const express = require('express');
const router = express.Router();
const Cliente = require('../models/cliente');

router.post('/clientes', async (req, res) => {
    const cliente = new Cliente(req.body);
    cliente.save()
        .then((data) => res.status(201).json(data))
        .catch((error) => res.status(400).json({ error: error.message  || 'Error al crear el cliente' }));
});

router.get('/clientes/:id', async (req, res) => {
    const { id } = req.params;
    Cliente.findById(id)
        .then((data) => {
            res.json(data);
        })
        .catch((error) => res.status(404).json({ error: 'Cliente no encontrado' }));
});

router.get('/clientes', async (req, res) => {
    Cliente.find()
        .then((data) => {
            res.json(data);
        })
        .catch((error) => res.status(500).json({ error: 'Error al obtener los clientes' }));
});

router.patch('/clientes/:id', async (req, res) => {
    const { id } = req.params;
    const {nombre , email, genero, pais, preferencias} = req.body;

    Cliente.updateOne({ _id: id }, { $set: {nombre, email, genero, pais, preferencias } })
        .then((data) => {
            if (!data) {
                return res.status(404).json({ error: 'Cliente no encontrado' });
            }
            res.json(data);
        })
        .catch((error) => res.status(400).json({ error: error.message  || 'Error al actualizar el cliente' }));
});

router.delete('/clientes/:id', async (req, res) => {
    const { id } = req.params;
    Cliente.deleteOne({ _id: id })
        .then((data) => {
            res.json(data);
        })
        .catch((error) => res.status(400).json({ error: error.message  || 'Error al eliminar el cliente' }));
});

module.exports = router;
