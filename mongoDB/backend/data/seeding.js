
const mongoose = require('mongoose');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
require('dotenv').config({ path: path.join(__dirname, '../.env') });

const Cliente = require('../src/models/cliente');
const Producto = require('../src/models/producto');
const Orden = require('../src/models/orden');

// para generar sku del codigo mongo
function generateSkuFromMongoCode(codigoMongo) {
  if (!codigoMongo) return null;
  
  if (codigoMongo.startsWith('MN-')) {
    const numero = codigoMongo.substring(3);
    // Generar letras basado en el número
    const hash = crypto.createHash('md5').update(numero).digest('hex');
    // Tomar los primeros 2 caracteres hexadecimales y convertirlos a letras A-P
    const char1 = String.fromCharCode('A'.charCodeAt(0) + parseInt(hash[0], 16));
    const char2 = String.fromCharCode('A'.charCodeAt(0) + parseInt(hash[1], 16));
    return `PRD-${numero}-${char1}${char2}`;
  } else {
    return `PRD-${codigoMongo.replace('-', '').substring(0, 4).toUpperCase()}-XX`;
  }
}


const datosComunes = JSON.parse(fs.readFileSync(path.join(__dirname, '../../../DatosComunes.json'), 'utf8'));


const nombres = [
  'Ana', 'Carlos', 'María', 'José', 'Carmen', 'Luis', 'Patricia', 'Miguel', 'Isabel', 'Juan',
  'Sofia', 'Diego', 'Valentina', 'Pedro', 'Camila', 'Roberto', 'Andrea', 'Fernando', 'Natalia', 'Alejandro',
  'Daniela', 'Ricardo', 'Gabriela', 'Javier', 'Paola', 'Sergio', 'Claudia', 'Andrés', 'Mónica', 'Raúl',
  'Carolina', 'Guillermo', 'Marcela', 'Eduardo', 'Lucia', 'Francisco', 'Adriana', 'Oscar', 'Veronica', 'Manuel',
  'Sandra', 'Antonio', 'Beatriz', 'Rodrigo', 'Elena', 'Alberto', 'Cristina', 'Mauricio', 'Silvia', 'Jorge'
];

const apellidos = [
  'García', 'Rodríguez', 'González', 'Fernández', 'López', 'Martínez', 'Sánchez', 'Pérez', 'Gómez', 'Martín',
  'Jiménez', 'Ruiz', 'Hernández', 'Díaz', 'Moreno', 'Álvarez', 'Muñoz', 'Romero', 'Alonso', 'Gutiérrez',
  'Navarro', 'Torres', 'Domínguez', 'Vázquez', 'Ramos', 'Gil', 'Ramírez', 'Serrano', 'Blanco', 'Molina',
  'Morales', 'Suárez', 'Ortega', 'Delgado', 'Castro', 'Ortiz', 'Rubio', 'Marín', 'Sanz', 'Iglesias'
];

const dominios = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'empresa.cr', 'universidad.ac.cr'];
const generos = ['Masculino', 'Femenino', 'Otro'];
const canales = [['WEB'], ['TIENDA'], ['WEB', 'TIENDA']];
const cupones = ['DESCUENTO10', 'VERANO2023', 'NAVIDAD2024', 'ESPECIAL25', 'AHORRO15', 'PROMO20', ''];

function generarClientes(cantidad) {
  const clientes = [];
  
  for (let i = 0; i < cantidad; i++) {
    const nombre = nombres[Math.floor(Math.random() * nombres.length)];
    const apellido = apellidos[Math.floor(Math.random() * apellidos.length)];
    const nombreCompleto = `${nombre} ${apellido}`;
    const email = `${nombre.toLowerCase()}.${apellido.toLowerCase()}${i}@${dominios[Math.floor(Math.random() * dominios.length)]}`;
    
    clientes.push({
      nombre: nombreCompleto,
      email: email,
      genero: generos[Math.floor(Math.random() * generos.length)],
      pais: 'CR',
      preferencias: { 
        canal: canales[Math.floor(Math.random() * canales.length)]
      }
    });
  }
  
  return clientes;
}

function generarProductos() {
  const productos = [];
  
 
  datosComunes.rows.forEach((item, index) => {
    const equivalencias = {
      sku: item.SKU  
    };
    
    productos.push({
      codigo_mongo: `MN-${String(index + 1).padStart(4, '0')}`,
      nombre: item.Nombre,
      categoria: item.Categoria,
      equivalencias: equivalencias
    });
  });
  
  // Productos adicionales para llegar a 250, ademas de los comunes
  const productosAdicionales = [
    'Café Premium', 'Chocolate Orgánico', 'Té Verde', 'Miel Natural', 'Azúcar Morena',
    'Vinagre Balsámico', 'Sal Marina', 'Pimienta Negra', 'Canela Molida', 'Vainilla Extract',
    'Harina Integral', 'Avena Natural', 'Quinoa Orgánica', 'Chía Seeds', 'Almendras Tostadas',
    'Nueces Mixtas', 'Yogurt Griego', 'Queso Artesanal', 'Mantequilla Cremosa', 'Huevos Orgánicos',
    'Pollo Fresco', 'Pescado del Día', 'Carne Premium', 'Jamón Serrano', 'Chorizo Español',
    'Pasta Italiana', 'Salsa Tomate', 'Aceitunas Verdes', 'Aceitunas Negras', 'Pesto Basilico',
    'Pan Baguette', 'Croissant Francés', 'Galletas Avena', 'Cereal Integral', 'Granola Casera',
    'Jugo Naranja', 'Agua Mineral', 'Refresco Natural', 'Vino Tinto', 'Cerveza Artesanal',
    'Detergente Eco', 'Jabón Líquido', 'Champú Natural', 'Acondicionador', 'Crema Corporal',
    'Cepillo Dientes', 'Pasta Dental', 'Enjuague Bucal', 'Papel Higiénico', 'Toallas Papel',
    'Cuaderno Escolar', 'Bolígrafos Color', 'Lápices HB', 'Goma Borrar', 'Regla Metálica',
    'Calculadora', 'Folder Archivos', 'Clips Oficina', 'Grapadora', 'Perforadora',
    'Smartphone Pro', 'Tablet Android', 'Laptop Gaming', 'Mouse Inalámbrico', 'Teclado RGB',
    'Monitor 4K', 'Webcam HD', 'Auriculares Bluetooth', 'Parlante Portátil', 'Cargador USB-C',
    'Sartén Antiadherente', 'Olla Presión', 'Batidora Manual', 'Licuadora Pro', 'Microondas Smart'
  ];
  
  const categoriasAdicionales = [
    'Alimentación', 'Bebidas', 'Limpieza', 'Cuidado Personal', 'Oficina', 
    'Electrónica', 'Hogar', 'Cocina', 'Panadería', 'Lácteos'
  ];
  
  for (let i = datosComunes.rows.length; i < 250; i++) {
    const nombre = productosAdicionales[Math.floor(Math.random() * productosAdicionales.length)];
    const categoria = categoriasAdicionales[Math.floor(Math.random() * categoriasAdicionales.length)];
    const codigoMongo = `MN-${String(i + 1).padStart(4, '0')}`;
    
    const equivalencias = {};
    // Solo 60% de los productos adicionales tienen equivalencias
    if (Math.random() > 0.4) {
      // Usar función determinística para generar SKU
      equivalencias.sku = generateSkuFromMongoCode(codigoMongo);
      
      if (Math.random() > 0.6) {
        // Para código alt también usar algo más determinístico
        const altHash = crypto.createHash('md5').update(codigoMongo + 'ALT').digest('hex').substring(0, 6).toUpperCase();
        equivalencias.codigo_alt = `ALT-${altHash}`;
      }
    }
    
    productos.push({
      codigo_mongo: codigoMongo,
      nombre: `${nombre} ${i}`,
      categoria: categoria,
      equivalencias: Object.keys(equivalencias).length > 0 ? equivalencias : undefined
    });
  }
  
  return productos;
}

function generarFechaAleatoria(año) {
  const hoy = new Date();
  const inicio = new Date(año, 0, 1);
  
  // fechas antes que ayer para que tenga sentido
  let fin;
  if (año === hoy.getFullYear()) {
    fin = new Date(hoy.getTime() - 24 * 60 * 60 * 1000); 
  } else {
    fin = new Date(año, 11, 31);
  }
  

  if (inicio > hoy) {
    const añoPasado = hoy.getFullYear() - 1;
    return new Date(añoPasado, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1);
  }
  

  if (fin >= hoy) {
    fin = new Date(hoy.getTime() - 24 * 60 * 60 * 1000); 
  }
  
  const fechaGenerada = new Date(inicio.getTime() + Math.random() * (fin.getTime() - inicio.getTime()));
  
  
  if (fechaGenerada >= hoy) {
    return new Date(hoy.getTime() - 24 * 60 * 60 * 1000); // Ayer
  }
  
  return fechaGenerada;
}

function generarOrdenes(clientes, productos, cantidad) {
  const ordenes = [];
  
  const hoy = new Date();
  const añoActual = hoy.getFullYear();
  const años = [2023, 2024];
  

  if (añoActual === 2025 && hoy.getMonth() > 0) {
    años.push(2025);
  }
  
  for (let i = 0; i < cantidad; i++) {
    const cliente = clientes[Math.floor(Math.random() * clientes.length)];
    const año = años[Math.floor(Math.random() * años.length)];
    const fecha = generarFechaAleatoria(año);
    const canal = Math.random() > 0.5 ? 'WEB' : 'TIENDA';
    
    // 1-4 items por orden
    const numItems = Math.floor(Math.random() * 4) + 1;
    const items = [];
    let total = 0;
    
    for (let j = 0; j < numItems; j++) {
      const producto = productos[Math.floor(Math.random() * productos.length)];
      const cantidad = Math.floor(Math.random() * 3) + 1;
      // Precios en CRC entre 1000 y 150000
      const precioUnit = Math.floor(Math.random() * 149000) + 1000;
      
      items.push({
        producto_id: producto._id,
        cantidad: cantidad,
        precio_unit: precioUnit
      });
      
      total += cantidad * precioUnit;
    }
    
    const cupon = cupones[Math.floor(Math.random() * cupones.length)];
    
    ordenes.push({
      cliente_id: cliente._id,
      fecha: fecha,
      canal: canal,
      moneda: 'CRC',
      total: total,
      items: items,
      metadatos: cupon ? { cupon: cupon } : {}
    });
  }
  
  return ordenes;
}

async function seedDatabase() {
  try {
    console.log('Iniciando seeding masivo...');
    console.log('Conectando a MongoDB...');
    await mongoose.connect(process.env.MONGODB_URI);
    console.log('Conectado a MongoDB');

    console.log('\n Limpiando datos existentes...');
    await Orden.deleteMany({});
    await Producto.deleteMany({});
    await Cliente.deleteMany({});
    console.log('Datos limpiados');

    const clientesData = generarClientes(600);
    const clientesCreados = await Cliente.insertMany(clientesData);

 
    const productosData = generarProductos();
    const productosCreados = await Producto.insertMany(productosData);


    // ordenes en lotes 
    const loteSize = 1000;
    let totalOrdenes = 0;
    
    for (let i = 0; i < 5; i++) {
      const ordenesLote = generarOrdenes(clientesCreados, productosCreados, loteSize);
      await Orden.insertMany(ordenesLote);
      totalOrdenes += ordenesLote.length;
    }


    console.log('\nRESUMEN DEL SEEDING:');
    console.log(`Clientes: ${clientesCreados.length}`);
    console.log(` Productos: ${productosCreados.length}`);
    console.log(` Órdenes: ${totalOrdenes}`);


  } catch (error) {
    console.error(' Error durante el seeding:', error);
  } finally {
    await mongoose.connection.close();
    console.log('\nConexión cerrada');
    process.exit(0);
  }
}

seedDatabase();
