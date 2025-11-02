import { useState, useEffect } from 'react'
import { productosApi } from '../services/api'
import { Edit, Trash2, Plus } from 'lucide-react'

function ProductoForm({ producto, onSave, onCancel }) {
  const [formData, setFormData] = useState({
    sku: '',
    nombre: '',
    categoria: ''
  })

  useEffect(() => {
    if (producto) {
      setFormData({
        sku: producto.sku || '',
        nombre: producto.nombre || '',
        categoria: producto.categoria || ''
      })
    }
  }, [producto])

  const handleSubmit = (e) => {
    e.preventDefault()
    
    onSave(formData)
  }

  return (
    <div className="card">
      <h3>{producto ? 'Editar Producto' : 'Nuevo Producto'}</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <div className="form-group">
            <label>SKU (opcional):</label>
            <input
              type="text"
              value={formData.sku}
              onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
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

        {/* SKU already handled above; no extra equivalencias in Supabase schema */}

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
      const mapped = response.data.map(p => ({ ...p, _id: p.producto_id }))
      setProductos(mapped)
    } catch (error) {
      setError('Error al cargar productos')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (productoData) => {
    try {
      const payload = {
        sku: productoData.sku || null,
        nombre: productoData.nombre,
        categoria: productoData.categoria
      }
      if (editingProducto) {
        await productosApi.update(editingProducto._id, payload)
      } else {
        await productosApi.create(payload)
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
                <th>SKU</th>
                <th>Nombre</th>
                <th>Categoría</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {productos.map(producto => (
                <tr key={producto._id}>
                  <td>{producto.sku || '-'}</td>
                  <td>{producto.nombre}</td>
                  <td>{producto.categoria}</td>
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
