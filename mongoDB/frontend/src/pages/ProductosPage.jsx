import { useState, useEffect } from 'react'
import { productosApi } from '../services/api'
import { Edit, Trash2, Plus } from 'lucide-react'

function ProductoForm({ producto, onSave, onCancel }) {
  const [formData, setFormData] = useState({
    codigo_mongo: '',
    nombre: '',
    categoria: '',
    equivalencias: {
      sku: '',
      codigo_alt: ''
    }
  })

  useEffect(() => {
    if (producto) {
      setFormData({
        ...producto,
        equivalencias: producto.equivalencias || { sku: '', codigo_alt: '' }
      })
    }
  }, [producto])

  const handleSubmit = (e) => {
    e.preventDefault()
    
    // Limpiar equivalencias vacías
    const cleanData = { ...formData }
    if (!cleanData.equivalencias.sku && !cleanData.equivalencias.codigo_alt) {
      delete cleanData.equivalencias
    } else {
      // Remover campos vacíos de equivalencias
      const equiv = {}
      if (cleanData.equivalencias.sku) equiv.sku = cleanData.equivalencias.sku
      if (cleanData.equivalencias.codigo_alt) equiv.codigo_alt = cleanData.equivalencias.codigo_alt
      cleanData.equivalencias = Object.keys(equiv).length > 0 ? equiv : undefined
    }
    
    onSave(cleanData)
  }

  return (
    <div className="card">
      <h3>{producto ? 'Editar Producto' : 'Nuevo Producto'}</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <div className="form-group">
            <label>Código Mongo:</label>
            <input
              type="text"
              value={formData.codigo_mongo}
              onChange={(e) => setFormData({ ...formData, codigo_mongo: e.target.value })}
              required
            />
          </div>
          <div className="form-group">
            <label>Nombre:</label>
            <input
              type="text"
              value={formData.nombre}
              onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
              required
            />
          </div>
        </div>
        
        <div className="form-group">
          <label>Categoría:</label>
          <input
            type="text"
            value={formData.categoria}
            onChange={(e) => setFormData({ ...formData, categoria: e.target.value })}
            required
          />
        </div>

        <h4 style={{ marginTop: '1.5rem', marginBottom: '1rem' }}>Equivalencias (Opcional)</h4>
        <div className="form-row">
          <div className="form-group">
            <label>SKU:</label>
            <input
              type="text"
              value={formData.equivalencias?.sku || ''}
              onChange={(e) => setFormData({ 
                ...formData, 
                equivalencias: { 
                  ...formData.equivalencias, 
                  sku: e.target.value 
                }
              })}
            />
          </div>
          <div className="form-group">
            <label>Código Alternativo:</label>
            <input
              type="text"
              value={formData.equivalencias?.codigo_alt || ''}
              onChange={(e) => setFormData({ 
                ...formData, 
                equivalencias: { 
                  ...formData.equivalencias, 
                  codigo_alt: e.target.value 
                }
              })}
            />
          </div>
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
      const response = await productosApi.getAll()
      setProductos(response.data)
    } catch (error) {
      setError('Error al cargar productos')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (productoData) => {
    try {
      if (editingProducto) {
        await productosApi.update(editingProducto._id, productoData)
      } else {
        await productosApi.create(productoData)
      }
      loadProductos()
      setShowForm(false)
      setEditingProducto(null)
    } catch (error) {
      setError('Error al guardar producto')
      console.error(error)
    }
  }

  const handleEdit = (producto) => {
    setEditingProducto(producto)
    setShowForm(true)
  }

  const handleDelete = async (id) => {
    if (window.confirm('¿Estás seguro de eliminar este producto?')) {
      try {
        await productosApi.delete(id)
        loadProductos()
      } catch (error) {
        setError('Error al eliminar producto')
        console.error(error)
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
      {error && <div className="error">{error}</div>}
      
      {!showForm && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2>Productos</h2>
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
                <th>Código Mongo</th>
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
                  <td>{producto.codigo_mongo}</td>
                  <td>{producto.nombre}</td>
                  <td>{producto.categoria}</td>
                  <td>{producto.equivalencias?.sku || '-'}</td>
                  <td>{producto.equivalencias?.codigo_alt || '-'}</td>
                  <td>
                    <button 
                      className="btn btn-secondary" 
                      onClick={() => handleEdit(producto)}
                      style={{ marginRight: '0.5rem' }}
                    >
                      <Edit size={16} />
                    </button>
                    <button 
                      className="btn btn-danger" 
                      onClick={() => handleDelete(producto._id)}
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
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
