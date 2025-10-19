const { Schema, model } = require('mongoose');

const EquivalenciasSchema = new Schema(
  {
    sku: { type: String, trim: true },
    codigo_alt: { type: String, trim: true },
  },
  { _id: false }
);

const ProductoSchema = new Schema(
  {
    codigo_mongo: { type: String, required: true, unique: true, trim: true },
    nombre: { type: String, required: true, trim: true },
    categoria: { type: String, required: true, trim: true },
    equivalencias: { type: EquivalenciasSchema, default: undefined }, // puede q no esté
  },
  {
    collection: 'productos',
  }
);

module.exports = model('Producto', ProductoSchema, 'productos');
