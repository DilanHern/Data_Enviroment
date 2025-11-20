import { useState, useEffect } from 'react'
import { productosApi, ordenesApi } from '../services/api'
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

  const [submitting, setSubmitting] = useState(false)

  const handleSubmitAsync = async (e) => {
    e.preventDefault()
    if (submitting) return
    setSubmitting(true)
    try {
      await onSave(formData)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="card">
      <h3>{producto ? 'Editar Producto' : 'Nuevo Producto'}</h3>
      <form onSubmit={handleSubmitAsync}>
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
          <button type="submit" className="btn btn-success" disabled={submitting}>
            {submitting ? 'Procesando...' : (producto ? 'Actualizar' : 'Crear')}
          </button>
          <button type="button" className="btn btn-secondary" onClick={onCancel} disabled={submitting}>
            Cancelar
          </button>
        </div>
      </form>
    </div>
  )
}

function ProductosPage() {
  const [productos, setProductos] = useState([])
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [pageInputSide, setPageInputSide] = useState(null)
  const [pageInputValue, setPageInputValue] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editingProducto, setEditingProducto] = useState(null)

  useEffect(() => {
    loadProductos()
  }, [])

  useEffect(() => {
    setPage(1)
  }, [productos, pageSize])

  const totalPages = Math.max(1, Math.ceil(productos.length / pageSize))
  const renderPageButtons = () => {
    if (totalPages <= 1) return null
    const buttons = []
    const left = Math.max(2, page - 2)
    const right = Math.min(totalPages - 1, page + 2)

    buttons.push(<button key={1} className={`btn ${page === 1 && !pageInputSide ? 'active' : ''}`} onClick={() => setPage(1)}>1</button>)
    if (left > 2) {
      if (pageInputSide !== 'left') buttons.push(<button key="left-ellipsis" className={`btn ${pageInputSide === 'left' ? 'active' : ''}`} onClick={() => { setPageInputSide('left'); setPageInputValue(String(page)); }}>...</button>)
      else buttons.push(
        <input
          key="left-ellipsis-input"
          type="text"
          value={pageInputValue}
          onChange={(e) => setPageInputValue(e.target.value)}
          onBlur={() => { const val = parseInt(pageInputValue, 10); if (!isNaN(val) && val >= 1 && val <= totalPages) setPage(val); else alert(`Página inválida (1-${totalPages})`); setPageInputSide(null); }}
          onKeyDown={(e) => { if (e.key === 'Enter') { const val = parseInt(pageInputValue, 10); if (!isNaN(val) && val >= 1 && val <= totalPages) setPage(val); else alert(`Página inválida (1-${totalPages})`); setPageInputSide(null); } else if (e.key === 'Escape') { setPageInputSide(null) } }}
          className="page-input"
          autoFocus
        />
      )
    }
        for (let p = left; p <= right; p++) buttons.push(<button key={p} className={`btn ${page === p && !pageInputSide ? 'active' : ''}`} onClick={() => setPage(p)}>{p}</button>)
        if (right < totalPages - 1) {
          if (pageInputSide !== 'right') buttons.push(<button key="right-ellipsis" className={`btn ${pageInputSide === 'right' ? 'active' : ''}`} onClick={() => { setPageInputSide('right'); setPageInputValue(String(page)); }}>...</button>)
          else buttons.push(
            <input
              key="right-ellipsis-input"
              type="text"
              value={pageInputValue}
              onChange={(e) => setPageInputValue(e.target.value)}
              onBlur={() => { const val = parseInt(pageInputValue, 10); if (!isNaN(val) && val >= 1 && val <= totalPages) setPage(val); else alert(`Página inválida (1-${totalPages})`); setPageInputSide(null); }}
              onKeyDown={(e) => { if (e.key === 'Enter') { const val = parseInt(pageInputValue, 10); if (!isNaN(val) && val >= 1 && val <= totalPages) setPage(val); else alert(`Página inválida (1-${totalPages})`); setPageInputSide(null); } else if (e.key === 'Escape') { setPageInputSide(null) } }}
              className="page-input"
              autoFocus
            />
          )
        }
    if (totalPages > 1) buttons.push(<button key={totalPages} className={`btn ${page === totalPages && !pageInputSide ? 'active' : ''}`} onClick={() => setPage(totalPages)}>{totalPages}</button>)
    return buttons
  }

  const loadProductos = async () => {
    try {
      setLoading(true)
      const response = await productosApi.getAll()
      // deduplicate by producto_id in case backend returns duplicates
      const items = response.data || []
      const byId = new Map()
      items.forEach(p => { if (p && p.producto_id && !byId.has(p.producto_id)) byId.set(p.producto_id, p) })
      const mapped = Array.from(byId.values()).map(p => ({ ...p, _id: String(p.producto_id) }))
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
      return true
    } catch (error) {
      setError('Error al guardar producto')
      console.error(error)
      return false
    }
  }

  const handleEdit = (producto) => {
    setEditingProducto(producto)
    setShowForm(true)
  }

  const handleDelete = async (id) => {
    if (!window.confirm('¿Estás seguro de eliminar este producto?')) return
    try {
      // ensure no order references this product
      const { data: ordenes } = await ordenesApi.getAll()
      const used = (ordenes || []).some(o => (o.orden_detalle || []).some(d => String(d.producto_id) === String(id)))
      if (used) {
        window.alert('No se puede eliminar: existen órdenes que referencian a este producto.')
        return
      }
      await productosApi.delete(id)
      loadProductos()
    } catch (error) {
      setError('Error al eliminar producto')
      console.error(error)
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
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <div>
              Mostrar
              <select value={pageSize} onChange={(e) => setPageSize(parseInt(e.target.value, 10))} style={{ margin: '0 0.5rem' }}>
                <option value={5}>5</option>
                <option value={10}>10</option>
                <option value={25}>25</option>
              </select>
              entradas
            </div>
            <div style={{ fontSize: '0.9rem', color: '#666' }}>{`Mostrando ${Math.min((page-1)*pageSize+1, productos.length)} - ${Math.min(page*pageSize, productos.length)} de ${productos.length}`}</div>
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
              {productos.slice((page-1)*pageSize, page*pageSize).map(producto => (
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
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.5rem' }}>
            <div className="pagination">
              <button className="btn" onClick={() => setPage(p => Math.max(1, p-1))} disabled={page===1}>Anterior</button>
              <div className="page-list">{renderPageButtons()}</div>
              <button className="btn" onClick={() => setPage(p => Math.min(p+1, totalPages))} disabled={page>=totalPages}>Siguiente</button>
            </div>
            <div>
              Página {page} / {totalPages}
            </div>
          </div>
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
