const { Schema, model } = require('mongoose');

const PreferenciasSchema = new Schema(
  {
    canal: {
      type: [String],
      enum: ['WEB', 'TIENDA'],
      default: [],
    },
  },
  { _id: false }
);

const ClienteSchema = new Schema(
  {
    nombre: { type: String, required: true, trim: true },
    email: {
      type: String,
      required: true,
      unique: true,
      lowercase: true,
      trim: true,
      match: [/^\S+@\S+\.\S+$/, 'Email inválido'],
    },
    genero: {
      type: String,
      required: true,
      enum: ['Masculino', 'Femenino', 'Otro'],
    },
    pais: {
      type: String,
      required: true,
      uppercase: true,
      minlength: 2,
      maxlength: 2,
      default: 'CR',
    },
    preferencias: { type: PreferenciasSchema, default: () => ({}) },
    creado: { type: Date, default: Date.now },
  },
  {
    collection: 'clientes',
  }
);

module.exports = model('Cliente', ClienteSchema, 'clientes');
