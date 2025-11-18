// seeding por mientras para ver bien el front

const mongoose = require('mongoose');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../.env') });


const Cliente = require('../src/models/cliente');
const Producto = require('../src/models/producto');
const Orden = require('../src/models/orden');


const clientesData = [
  {
    nombre: "Ana Rojas",
    email: "ana@ejemplo.com",
    genero: "Otro",
    pais: "CR",
    preferencias: { canal: ["WEB", "TIENDA"] }
  },
  {
    nombre: "Carlos Mendez",
    email: "carlos@ejemplo.com",
    genero: "Masculino",
    pais: "CR",
    preferencias: { canal: ["WEB"] }
  },
  {
    nombre: "María González",
    email: "maria@ejemplo.com",
    genero: "Femenino",
    pais: "CR",
    preferencias: { canal: ["TIENDA"] }
  },
  {
    nombre: "José Pérez",
    email: "jose@ejemplo.com",
    genero: "Masculino",
    pais: "CR",
    preferencias: { canal: ["WEB", "TIENDA"] }
  }
];

const productosData = [
  {
    codigo_mongo: "MN-9981",
    nombre: "Tomate grande",
    categoria: "Alimentos",
    equivalencias: {
      sku: "SKU-1002",
      codigo_alt: "ALT-AB12"
    }
  },
  {
    codigo_mongo: "MN-9982",
    nombre: "Arroz integral 1kg",
    categoria: "Alimentos",
    equivalencias: {
      sku: "SKU-1003"
    }
  },
  {
    codigo_mongo: "MN-9983",
    nombre: "Leche deslactosada",
    categoria: "Lácteos"
    
  },
  {
    codigo_mongo: "MN-9984",
    nombre: "Pan integral",
    categoria: "Panadería",
    equivalencias: {
      codigo_alt: "ALT-PAN01"
    }
  },
  {
    codigo_mongo: "MN-9985",
    nombre: "Aceite de oliva",
    categoria: "Condimentos",
    equivalencias: {
      sku: "SKU-1004",
      codigo_alt: "ALT-ACE01"
    }
  }
];

async function seedDatabase() {
  try {
    
    console.log('Conectando a MongoDB...');
    await mongoose.connect(process.env.MONGODB_URI);
    console.log('✅ Conectado a MongoDB');

    
    console.log('\n🧹 Limpiando datos existentes...');
    await Orden.deleteMany({});
    await Producto.deleteMany({});
    await Cliente.deleteMany({});
    console.log('✅ Datos limpiados');

   
    console.log('\n👥 Insertando clientes...');
    const clientesCreados = await Cliente.insertMany(clientesData);
    console.log(`✅ ${clientesCreados.length} clientes creados`);

    
    console.log('\n📦 Insertando productos...');
    const productosCreados = await Producto.insertMany(productosData);
    console.log(`✅ ${productosCreados.length} productos creados`);

    
    console.log('\n🛒 Creando órdenes...');
    
    const ordenesData = [
      {
        cliente_id: clientesCreados[0]._id, // Ana
        fecha: new Date('2025-04-10T13:20:00Z'),
        canal: "WEB",
        moneda: "CRC",
        total: 84500,
        items: [
          { 
            producto_id: productosCreados[0]._id, // Tomate
            cantidad: 2, 
            precio_unit: 12000 
          },
          { 
            producto_id: productosCreados[4]._id, // Aceite
            cantidad: 1, 
            precio_unit: 60500 
          }
        ],
        metadatos: { cupon: "ABRIL10" }
      },
      {
        cliente_id: clientesCreados[1]._id, // Carlos
        fecha: new Date('2025-04-12T09:15:00Z'),
        canal: "TIENDA",
        moneda: "CRC",
        total: 8500,
        items: [
          { 
            producto_id: productosCreados[1]._id, // Arroz
            cantidad: 1, 
            precio_unit: 3500 
          },
          { 
            producto_id: productosCreados[3]._id, // Pan
            cantidad: 2, 
            precio_unit: 2500 
          }
        ],
        metadatos: {}
      },
      {
        cliente_id: clientesCreados[2]._id, // María
        fecha: new Date('2025-04-15T16:30:00Z'),
        canal: "WEB",
        moneda: "CRC",
        total: 15750,
        items: [
          { 
            producto_id: productosCreados[2]._id, // Leche
            cantidad: 3, 
            precio_unit: 2250 
          },
          { 
            producto_id: productosCreados[0]._id, // Tomate
            cantidad: 1, 
            precio_unit: 9000 
          }
        ],
        metadatos: { cupon: "DESCUENTO5" }
      },
      {
        cliente_id: clientesCreados[3]._id, // José
        fecha: new Date('2025-04-18T11:45:00Z'),
        canal: "TIENDA",
        moneda: "CRC",
        total: 125000,
        items: [
          { 
            producto_id: productosCreados[4]._id, // Aceite
            cantidad: 2, 
            precio_unit: 60000 
          },
          { 
            producto_id: productosCreados[1]._id, // Arroz
            cantidad: 1, 
            precio_unit: 3500 
          },
          { 
            producto_id: productosCreados[3]._id, // Pan
            cantidad: 1, 
            precio_unit: 1500 
          }
        ],
        metadatos: {}
      }
    ];

    const ordenesCreadas = await Orden.insertMany(ordenesData);
    console.log(`✅ ${ordenesCreadas.length} órdenes creadas`);

    
    console.log('\n📊 RESUMEN DEL SEEDING:');
    console.log(`👥 Clientes: ${clientesCreados.length}`);
    console.log(`📦 Productos: ${productosCreados.length}`);
    console.log(`🛒 Órdenes: ${ordenesCreadas.length}`);
    
    console.log('\n🎉 Seeding completado exitosamente!');
    console.log('\n💡 Ahora puedes usar tu frontend para ver y gestionar estos datos.');

  } catch (error) {
    console.error('❌ Error durante el seeding:', error);
  } finally {
    
    await mongoose.connection.close();
    console.log('\n🔌 Conexión cerrada');
    process.exit(0);
  }
}


seedDatabase();
