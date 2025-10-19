const { Schema, model, Types } = require('mongoose');

const ItemSchema = new Schema(
  {
    producto_id: { type: Types.ObjectId, ref: 'Producto', required: true },
    cantidad: { type: Number, required: true, min: 1 },
    precio_unit: {
      type: Number,
      required: true,
      min: [0, 'El precio debe ser >= 0'],
      validate: {
        validator: Number.isInteger,
        message: 'precio_unit debe ser entero en CRC',
      },
    },
  },
  { _id: false }
);

const OrdenSchema = new Schema(
  {
    cliente_id: { type: Types.ObjectId, ref: 'Cliente', required: true },
    fecha: { type: Date, required: true, default: Date.now },
    canal: { type: String, enum: ['WEB', 'TIENDA'], required: true },
    moneda: { type: String, enum: ['CRC'], default: 'CRC', required: true },
    total: {
      type: Number,
      required: true,
      min: [0, 'El total debe ser >= 0'],
      validate: {
        validator: Number.isInteger,
        message: 'total debe ser entero en CRC',
      },
    },
    items: {
      type: [ItemSchema],
      required: true,
      validate: [
        {
          validator: (arr) => Array.isArray(arr) && arr.length > 0,
          message: 'Debe incluir al menos un item',
        },
      ],
    },
    metadatos: { type: Schema.Types.Mixed },
  },
  {
    collection: 'ordenes',
  }
);

module.exports = model('Orden', OrdenSchema, 'ordenes');
