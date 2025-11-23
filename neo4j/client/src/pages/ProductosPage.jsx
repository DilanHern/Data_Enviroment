import { useState, useEffect } from 'react'
import { productosApi, categoriasApi } from '../services/api'
import { Edit, Trash2, Plus } from 'lucide-react'

function ProductoForm({ producto, onSave, onCancel }) {
  const [formData, setFormData] = useState({
    nombre: '',
    categoria: '',
    codigo_mongo: '',
    sku: '',
    codigo_alt: ''
  })
  const [categorias, setCategorias] = useState([])

  useEffect(() => {
    // Cargar categorías al montar el form
    const fetchCategorias = async () => {
      try {
        const res = await categoriasApi.getAll()
        setCategorias(res.data)
      } catch (err) {
        setCategorias([])
      }
    }
    fetchCategorias()
  }, [])

  useEffect(() => {
    if (producto) {
      setFormData({
        nombre: producto.nombre || '',
        categoria: producto.categoria || '',
        codigo_mongo: producto.codigo_mongo || '',
        sku: producto.sku || '',
        codigo_alt: producto.codigo_alt || ''
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
            <label>Nombre:</label>
            <input
              type="text"
              value={formData.nombre}
              onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
              required
            />
          </div>
        </div>
        <div className="form-row">
          <div className="form-group">
            <label>Categoría:</label>
            <select
              value={formData.categoria}
              onChange={e => setFormData({ ...formData, categoria: e.target.value })}
              required
            >
              <option value="">Selecciona una categoría</option>
              {categorias.map(cat => (
                <option key={cat.id || cat.nombre} value={cat.nombre}>{cat.nombre}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Código Mongo:</label>
            <input
              type="text"
              value={formData.codigo_mongo}
              onChange={(e) => setFormData({ ...formData, codigo_mongo: e.target.value })}
              required
            />
          </div>
        </div>
        <div className="form-row">
          <div className="form-group">
            <label>SKU:</label>
            <input
              type="text"
              value={formData.sku}
              onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label>Código Alternativo:</label>
            <input
              type="text"
              value={formData.codigo_alt}
              onChange={(e) => setFormData({ ...formData, codigo_alt: e.target.value })}
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
  const [createdProductId, setCreatedProductId] = useState(null)
  const [searchId, setSearchId] = useState('')
  const [searchError, setSearchError] = useState('')

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
      setError('')
      if (editingProducto) {
        await productosApi.update(editingProducto.id, productoData)
      } else {
        const resp = await productosApi.create(productoData)
        const newId = resp?.data?.id || null
        if (newId) setCreatedProductId(newId)
      }
      loadProductos()
      setShowForm(false)
      setEditingProducto(null)
    } catch (error) {
      console.error(error)
      if (error && error.response && error.response.status === 409) {
        const serverMsg = error.response.data && error.response.data.error ? error.response.data.error : 'Algún código ya está en uso';
        setError(serverMsg)
      } else {
        setError('Error al guardar producto')
      }
    }
  }

  const handleEdit = (producto) => {
    setError('')
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
      {createdProductId && (
        <div className="success" style={{ marginBottom: '1rem' }}>
          Producto creado: <strong>{createdProductId}</strong>
        </div>
      )}
      
      {!showForm && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2>Productos</h2>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <input
                type="text"
                placeholder="Buscar por ID"
                value={searchId}
                onChange={(e) => setSearchId(e.target.value)}
                style={{ padding: '0.4rem', borderRadius: '4px', border: '1px solid #ccc' }}
              />
              <button className="btn" onClick={async () => {
                setSearchError('')
                if (!searchId) return setSearchError('Ingrese un ID para buscar')
                try {
                  setLoading(true)
                  const resp = await productosApi.getById(searchId)
                  setProductos([resp.data])
                } catch (err) {
                  console.error('Error buscando producto por id:', err)
                  setSearchError('Producto no encontrado')
                } finally {
                  setLoading(false)
                }
              }}>Buscar</button>
              <button className="btn" onClick={() => { setSearchId(''); setSearchError(''); loadProductos(); }}>Mostrar todos</button>
              <button 
                className="btn" 
                onClick={() => { setCreatedProductId(null); setShowForm(true); setError(''); setEditingProducto(null); }}
              >
                <Plus size={20} style={{ marginRight: '0.5rem' }} />
                Nuevo Producto
              </button>
            </div>
          </div>
          {searchError && <div className="error" style={{ marginBottom: '1rem' }}>{searchError}</div>}
          
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Nombre</th>
                <th>Categoría</th>
                <th>Código Mongo</th>
                <th>SKU</th>
                <th>Código Alt</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {productos.map((producto, idx) => (
                <tr key={producto._id || producto.codigo_mongo || idx}>
                  <td>{producto.id || '-'}</td>
                  <td>{producto.nombre}</td>
                  <td>{producto.categoria || '-'}</td>
                  <td>{producto.codigo_mongo}</td>
                  <td>{producto.sku || '-'}</td>
                  <td>{producto.codigo_alt || '-'}</td>
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
                      onClick={() => handleDelete(producto.id)}
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
