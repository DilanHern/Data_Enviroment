const express = require('express');
const mongoose = require('mongoose');
require('dotenv').config();
const ordenRoutes = require('./routes/ordenRoute');
const productoRoutes = require('./routes/productoRoute');
const clienteRoutes = require('./routes/clienteRoute');

const app = express();
const PORT = process.env.PORT || 3004;

// CORS para conectar con el frontend :)
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');
    
    if (req.method === 'OPTIONS') {
        res.sendStatus(200);
    } else {
        next();
    }
});

app.use(express.json());

app.use('/api', ordenRoutes);
app.use('/api', productoRoutes);
app.use('/api', clienteRoutes);

mongoose
    .connect(process.env.MONGODB_URI)
    .then(() => {
        console.log('Conexión a MongoDB exitosa');
    })
    .catch((error) => {
        console.error('Error al conectar a MongoDB:', error);
    });

app.listen(PORT, () => {
    console.log(`Servidor escuchando en el puerto ${PORT}`);
});