import { useState, useEffect } from 'react'
import { productosApi } from '../services/api'
import { Plus, Edit, Trash2 } from 'lucide-react'

function ProductoForm({ producto, onSave, onCancel }) {
  const [formData, setFormData] = useState({
    nombre: '',
    categoria: 'Electrónica',
    sku: '',
    codigo_alt: '',
    codigo_mongo: ''
  })

  useEffect(() => {
    if (producto) {
      setFormData({
        nombre: producto.nombre || '',
        categoria: producto.categoria || 'Electrónica',
        sku: producto.sku || '',
        codigo_alt: producto.codigo_alt || '',
        codigo_mongo: producto.codigo_mongo || ''
      })
    }
  }, [producto])

  const handleSubmit = (e) => {
    e.preventDefault()
    
    // Limpiar campos vacíos
    const cleanData = {}
    if (formData.nombre) cleanData.nombre = formData.nombre
    if (formData.categoria) cleanData.categoria = formData.categoria
    if (formData.sku) cleanData.sku = formData.sku
    if (formData.codigo_alt) cleanData.codigo_alt = formData.codigo_alt
    if (formData.codigo_mongo) cleanData.codigo_mongo = formData.codigo_mongo
    
    onSave(cleanData)
  }

  const categorias = [
    'Electrónica', 'Ropa', 'Alimentos', 'Hogar', 'Deportes',
    'Libros', 'Juguetes', 'Belleza', 'Tecnología', 'Mascotas'
  ]

  return (
    <div className="card">
      <h3>{producto ? 'Editar Producto' : 'Nuevo Producto'}</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <div className="form-group">
            <label>Nombre:</label>
            <input
              type="text"
              value={formData.nombre}
              onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
              required
              placeholder="Ej: Laptop HP"
            />
          </div>
          <div className="form-group">
            <label>Categoría:</label>
            <select
              value={formData.categoria}
              onChange={(e) => setFormData({ ...formData, categoria: e.target.value })}
              required
            >
              {categorias.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>
        </div>

        <h4 style={{ marginTop: '1.5rem', marginBottom: '1rem', color: '#666', fontSize: '0.9rem' }}>
          Códigos de Producto (Opcional)
        </h4>
        <div className="form-row">
          <div className="form-group">
            <label>SKU:</label>
            <input
              type="text"
              value={formData.sku}
              onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
              placeholder="Ej: SKU-20001"
            />
          </div>
          <div className="form-group">
            <label>Código Alternativo:</label>
            <input
              type="text"
              value={formData.codigo_alt}
              onChange={(e) => setFormData({ ...formData, codigo_alt: e.target.value })}
              placeholder="Ej: ALT-30001"
            />
          </div>
        </div>
        <div className="form-group">
          <label>Código MongoDB:</label>
          <input
            type="text"
            value={formData.codigo_mongo}
            onChange={(e) => setFormData({ ...formData, codigo_mongo: e.target.value })}
            placeholder="Ej: MN-40001"
          />
        </div>

        <div>
          <button type="submit" className="btn btn-success">
            {producto ? 'Actualizar' : 'Crear'}
          </button>
          <button type="button" className="btn btn-secondary" onClick={onCancel}>
            Cancelar
          </button>
        </div>
      </form>
    </div>
  )
}

function ProductosPage() {
  const [productos, setProductos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editingProducto, setEditingProducto] = useState(null)

  useEffect(() => {
    loadProductos()
  }, [])

  const loadProductos = async () => {
    try {
      setLoading(true)
      setError('')
      const response = await productosApi.getAll()
      console.log('📦 Productos recibidos:', response.data) // ✅ DEBUG
      setProductos(response.data || [])
    } catch (error) {
      setError('Error al cargar productos: ' + (error.response?.data?.error || error.message))
      console.error('❌ Error:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (productoData) => {
    try {
      if (editingProducto) {
        console.log('✏️ Actualizando producto:', editingProducto._id, productoData) // ✅ DEBUG
        await productosApi.update(editingProducto._id, productoData)
      } else {
        console.log('➕ Creando producto:', productoData) // ✅ DEBUG
        await productosApi.create(productoData)
      }
      await loadProductos()
      setShowForm(false)
      setEditingProducto(null)
    } catch (error) {
      setError('Error al guardar producto: ' + (error.response?.data?.error || error.message))
      console.error('❌ Error al guardar:', error)
    }
  }

  const handleEdit = (producto) => {
    console.log('✏️ Editando producto:', producto) // ✅ DEBUG
    setEditingProducto(producto)
    setShowForm(true)
  }

  const handleDelete = async (id) => {
    if (window.confirm('¿Estás seguro de eliminar este producto?')) {
      try {
        console.log('🗑️ Eliminando producto:', id) // ✅ DEBUG
        await productosApi.delete(id)
        await loadProductos()
      } catch (error) {
        setError('Error al eliminar producto: ' + (error.response?.data?.error || error.message))
        console.error('❌ Error al eliminar:', error)
      }
    }
  }

  const handleCancel = () => {
    setShowForm(false)
    setEditingProducto(null)
  }

  if (loading) return <div className="loading">Cargando productos...</div>

  return (
    <div>
      {error && <div className="error" style={{ 
        background: '#fee', 
        border: '1px solid #fcc', 
        color: '#c00',
        padding: '1rem',
        borderRadius: '4px',
        marginBottom: '1rem'
      }}>
        {error}
        <button 
          onClick={() => setError('')}
          style={{ float: 'right', background: 'none', border: 'none', cursor: 'pointer' }}
        >
          ✕
        </button>
      </div>}

      {!showForm && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2>Productos ({productos.length})</h2>
            <button 
              className="btn" 
              onClick={() => setShowForm(true)}
            >
              <Plus size={20} style={{ marginRight: '0.5rem' }} />
              Nuevo Producto
            </button>
          </div>

          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Nombre</th>
                <th>Categoría</th>
                <th>SKU</th>
                <th>Código Alt</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {productos.map(producto => (
                <tr key={producto._id}>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.85rem', color: '#666' }}>
                    {producto._id}
                  </td>
                  <td style={{ fontWeight: '500' }}>{producto.nombre}</td>
                  <td>
                    <span className="badge">{producto.categoria}</span>
                  </td>
                  <td>{producto.sku || '-'}</td>
                  <td>{producto.codigo_alt || '-'}</td>
                  <td>
                    <button 
                      className="btn btn-secondary" 
                      onClick={() => handleEdit(producto)}
                      style={{ marginRight: '0.5rem' }}
                      title="Editar producto"
                    >
                      <Edit size={16} />
                    </button>
                    <button 
                      className="btn btn-danger" 
                      onClick={() => handleDelete(producto._id)}
                      title="Eliminar producto"
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {productos.length === 0 && (
            <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
              No hay productos registrados
            </div>
          )}
        </div>
      )}

      {showForm && (
        <ProductoForm 
          producto={editingProducto}
          onSave={handleSave}
          onCancel={handleCancel}
        />
      )}
    </div>
  )
}

export default ProductosPage