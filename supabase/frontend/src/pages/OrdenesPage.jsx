import { useState, useEffect, useRef } from 'react'
import { ordenesApi, clientesApi, productosApi, recommendationsApi } from '../services/api'
import { Edit, Trash2, Plus, Minus, Eye } from 'lucide-react'

function OrdenForm({ orden, onSave, onCancel }) {
  const [formData, setFormData] = useState({
    cliente_id: '',
    // store fecha as ISO string (UTC) and make it uneditable; submit will use current UTC for new orders
    fecha: new Date().toISOString(),
    canal: 'WEB',
    moneda: 'CRC',
    total: 0,
    items: [{ producto_id: '', cantidad: 1, precio_unit: 0 }]
  })
  const [fechaLocal, setFechaLocal] = useState(() => {
    const now = new Date()
    const pad = (n) => n.toString().padStart(2, '0')
    return `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}`
  })

  // helpers to convert between local input value and ISO UTC
  const localInputToIso = (local) => {
    if (!local) return new Date().toISOString()
    // local format: YYYY-MM-DDTHH:MM
    const [datePart, timePart] = local.split('T')
    const [y, m, d] = datePart.split('-').map(Number)
    const [hh, mm] = (timePart || '').split(':').map(Number)
    const dt = new Date(y, m - 1, d, hh || 0, mm || 0)
    return dt.toISOString()
  }

  const isoToLocalInput = (iso) => {
    try {
      const d = new Date(iso)
      const pad = (n) => n.toString().padStart(2, '0')
      return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
    } catch (e) {
      return fechaLocal
    }
  }

  const isoToReadableUtc = (iso) => {
    try {
      const d = new Date(iso)
      const pad = (n) => n.toString().padStart(2, '0')
      const Y = d.getUTCFullYear()
      const M = pad(d.getUTCMonth() + 1)
      const D = pad(d.getUTCDate())
      const h = pad(d.getUTCHours())
      const min = pad(d.getUTCMinutes())
      return `${Y}-${M}-${D} ${h}:${min} UTC`
    } catch (e) {
      return new Date(iso).toISOString()
    }
  }
  
  const normalizeId = (v) => {
    if (v === null || v === undefined) return v
    const n = Number(v)
    return Number.isNaN(n) ? v : n
  }

  const [clientes, setClientes] = useState([])
  const [productos, setProductos] = useState([])
  const [recommended, setRecommended] = useState([])

  useEffect(() => {
    loadClientes()
    loadProductos()
    if (orden) {
      setFormData({
        cliente_id: String(orden.cliente_id),
        fecha: new Date(orden.fecha).toISOString(),
        canal: orden.canal,
        moneda: orden.moneda,
        total: orden.total,
        // orden.orden_detalle may include a nested `producto` object (from supabase join)
        items: (orden.orden_detalle || []).map(i => ({
          // prefer nested producto.producto_id, fallback to producto_id at root
          producto_id: String(i.producto?.producto_id ?? i.producto_id ?? ''),
          cantidad: i.cantidad ?? i.qty ?? 1,
          precio_unit: i.precio_unit ?? i.precio ?? 0
        })),
        // coupons/medadatos removed — backend does not accept cupon
      })
      // also set local input representation
      setFechaLocal(isoToLocalInput(orden.fecha))
    }
  }, [orden])

  const loadClientes = async () => {
    try {
      const response = await clientesApi.getAll()
      const mapped = (response.data || []).map(c => ({ ...c, _id: String(c.cliente_id) }))
      setClientes(mapped)
    } catch (error) {
      console.error('Error cargando clientes:', error)
    }
  }

  const loadProductos = async () => {
    try {
      const response = await productosApi.getAll()
      const mapped = (response.data || []).map(p => ({ ...p, _id: String(p.producto_id) }))
      setProductos(mapped)
    } catch (error) {
      console.error('Error cargando productos:', error)
    }
  }

  const calculateTotal = () => {
    const total = formData.items.reduce((sum, item) => 
      sum + (item.cantidad * item.precio_unit), 0
    )
    setFormData(prev => ({ ...prev, total }))
  }

  useEffect(() => {
    calculateTotal()
  }, [formData.items])

  const addItem = () => {
    setFormData(prev => ({
      ...prev,
      items: [...prev.items, { producto_id: '', cantidad: 1, precio_unit: 0 }]
    }))
  }

  const removeItem = (index) => {
    if (formData.items.length > 1) {
      setFormData(prev => ({
        ...prev,
        items: prev.items.filter((_, i) => i !== index)
      }))
    }
  }

  const updateItem = (index, field, value) => {
    // Prevent selecting the same producto_id in multiple items
    if (field === 'producto_id' && value) {
      const exists = formData.items.some((it, i) => i !== index && String(it.producto_id) === String(value))
      if (exists) {
        window.alert('Ese producto ya fue añadido en otro item. No puede repetirse.')
        return
      }
    }

    setFormData(prev => ({
      ...prev,
      items: prev.items.map((item, i) => 
        i === index ? { ...item, [field]: value } : item
      )
    }))
  }

  // load recommendations whenever selected product ids change
  useEffect(() => {
    const ids = formData.items.map(it => it.producto_id).filter(Boolean)
    if (ids.length === 0) {
      setRecommended([])
      return
    }

    let cancelled = false
    ;(async () => {
      try {
        const { data } = await recommendationsApi.getForAntecedents(ids)
        if (!cancelled) setRecommended(data || [])
      } catch (err) {
        console.error('Error cargando recomendaciones:', err)
        if (!cancelled) setRecommended([])
      }
    })()
    return () => { cancelled = true }
  }, [formData.items])

  const addRecommendedProduct = (producto_id) => {
    // if already present, increment cantidad
    const existsIndex = formData.items.findIndex(it => String(it.producto_id) === String(producto_id))
    if (existsIndex >= 0) {
      setFormData(prev => ({
        ...prev,
        items: prev.items.map((it, i) => i === existsIndex ? { ...it, cantidad: (Number(it.cantidad)||0) + 1 } : it)
      }))
    } else {
      // append new item with default quantity 1 and precio_unit 0
      setFormData(prev => ({
        ...prev,
        items: [...prev.items, { producto_id: String(producto_id), cantidad: 1, precio_unit: 0 }]
      }))
    }
  }

  // submit handled by handleSubmitAsync below (prevents duplicate clicks)

  const [submitting, setSubmitting] = useState(false)

  const handleSubmitAsync = async (e) => {
    e.preventDefault()
    if (submitting) return
    // perform same validations as before then call onSave
    // validate duplicate producto_ids
    const productoIds = formData.items.map(it => it.producto_id).filter(Boolean)
    const duplicates = productoIds.filter((id, idx) => productoIds.indexOf(id) !== idx)
    if (duplicates.length > 0) {
      window.alert('Hay productos repetidos en los items. Elimine duplicados antes de guardar.')
      return
    }

    // validar que la fecha local no sea futura
    try {
      const selectedIso = localInputToIso(fechaLocal)
      if (new Date(selectedIso).getTime() > Date.now()) {
        window.alert('La fecha local no puede ser futura.')
        return
      }
    } catch (err) {
      console.warn('Error validando fecha local', err)
    }

    if (submitting) return
    setSubmitting(true)
    try {
      const submitData = {
        cliente_id: normalizeId(formData.cliente_id),
        fecha: new Date(formData.fecha).toISOString(),
        canal: formData.canal,
        moneda: formData.moneda,
        total: parseFloat(formData.total),
        items: formData.items.map(item => ({
          producto_id: normalizeId(item.producto_id),
          cantidad: parseInt(item.cantidad, 10),
          precio_unit: parseFloat(item.precio_unit)
        }))
      }

      await onSave(submitData)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="card">
      <h3>{orden ? 'Editar Orden' : 'Nueva Orden'}</h3>
      <form onSubmit={handleSubmitAsync}>
        <div className="form-row">
          <div className="form-group">
            <label>Cliente:</label>
            <select
              value={formData.cliente_id}
              onChange={(e) => setFormData({ ...formData, cliente_id: e.target.value })}
              required
            >
              <option value="">Seleccionar cliente</option>
              {clientes.map(cliente => (
                <option key={cliente._id} value={cliente._id}>
                  {cliente.nombre} - {cliente.email}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Fecha local (puedes editar):</label>
            <input
              type="datetime-local"
              value={fechaLocal}
              onChange={(e) => {
                const local = e.target.value
                setFechaLocal(local)
                const iso = localInputToIso(local)
                setFormData(prev => ({ ...prev, fecha: iso }))
              }}
              required
            />
          </div>

          <div className="form-group">
            <label>Fecha (UTC):</label>
            <input
              type="text"
              value={isoToReadableUtc(formData.fecha)}
              disabled
              style={{ background: '#f8f9fa' }}
            />
          </div>
        </div>
        
        <div className="form-row">
          <div className="form-group">
            <label>Canal:</label>
            <select
              value={formData.canal}
              onChange={(e) => setFormData({ ...formData, canal: e.target.value })}
            >
              <option value="WEB">WEB</option>
              <option value="PARTNER">PARTNER</option>
              <option value="TIENDA">TIENDA</option>
            </select>
          </div>

          <div className="form-group">
            <label>Moneda:</label>
            <select
              value={formData.moneda}
              onChange={(e) => setFormData({ ...formData, moneda: e.target.value })}
            >
              <option value="CRC">CRC</option>
              <option value="USD">USD</option>
            </select>
          </div>

          {/* Cupón removed: backend does not accept coupon field */}
        </div>

        <h4 style={{ marginTop: '1.5rem', marginBottom: '1rem' }}>Items</h4>
        {formData.items.map((item, index) => (
          <div key={index} className="card" style={{ marginBottom: '1rem', padding: '1rem' }}>
            <div className="form-row">
              <div className="form-group">
                <label>Producto:</label>
                <select
                  value={item.producto_id}
                  onChange={(e) => updateItem(index, 'producto_id', e.target.value)}
                  required
                >
                  <option value="">Seleccionar producto</option>
                      {productos.map(producto => (
                        <option key={producto._id} value={producto._id}>
                          {producto.sku ? `${producto.sku} - ${producto.nombre}` : producto.nombre}
                        </option>
                      ))}
                </select>
              </div>
              <div className="form-group">
                <label>Cantidad:</label>
                <input
                  type="number"
                  min="1"
                  value={item.cantidad}
                  onChange={(e) => updateItem(index, 'cantidad', parseInt(e.target.value))}
                  required
                />
              </div>
                <div className="form-group">
                  <label>Precio Unitario ({formData.moneda === 'USD' ? 'USD' : 'CRC'}):</label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={item.precio_unit}
                    onChange={(e) => updateItem(index, 'precio_unit', parseFloat(e.target.value) || 0)}
                    required
                  />
                </div>
              <div className="form-group">
                <label>Subtotal:</label>
                <input
                  type="text"
                  value={formData.moneda === 'USD' ? `$${(item.cantidad * item.precio_unit).toLocaleString()}` : `₡${(item.cantidad * item.precio_unit).toLocaleString()}`}
                  disabled
                  style={{ background: '#f8f9fa' }}
                />
              </div>
            </div>
            {formData.items.length > 1 && (
              <button 
                type="button" 
                className="btn btn-danger"
                onClick={() => removeItem(index)}
                style={{ marginTop: '0.5rem' }}
              >
                <Minus size={16} /> Remover Item
              </button>
            )}
          </div>
        ))}
        
        <button 
          type="button" 
          className="btn btn-secondary"
          onClick={addItem}
          style={{ marginBottom: '1rem' }}
        >
          <Plus size={16} /> Agregar Item
        </button>

        {/* Recomendaciones basadas en reglas de asociación */}
        {recommended && recommended.length > 0 && (
          <div className="card" style={{ marginBottom: '1rem', padding: '1rem' }}>
            <h4>Productos recomendados</h4>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {recommended.slice(0, 8).map(rec => {
                const prod = rec.producto || {}
                return (
                  <div key={rec.producto_id} className="recommended-item" style={{ border: '1px solid #e0e0e0', padding: '0.5rem', borderRadius: '6px', minWidth: '200px' }}>
                    <div style={{ fontWeight: '600' }}>{prod.sku ? `${prod.sku} - ${prod.nombre}` : prod.nombre || rec.producto_id}</div>
                    <div style={{ fontSize: '0.85rem', color: '#666' }}>Score: {Math.round(rec.score*100)/100} · Lift: {Math.round((rec.avg_lift||0)*100)/100}</div>
                    <div style={{ marginTop: '0.5rem' }}>
                      <button type="button" className="btn btn-primary" onClick={() => addRecommendedProduct(rec.producto_id)}>Agregar</button>
                    </div>
                  </div>
                )
              })}
            </div>
            <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: '#666' }}>Las recomendaciones se calculan a partir de reglas de asociación definidas en el backend.</div>
          </div>
        )}

        <div className="form-group">
          <label>Total ({formData.moneda === 'USD' ? 'USD' : 'CRC'}):</label>
          <input
            type="text"
            value={formData.moneda === 'USD' ? `$${formData.total.toLocaleString()}` : `₡${formData.total.toLocaleString()}`}
            disabled
            style={{ background: '#f8f9fa', fontWeight: 'bold', fontSize: '1.2rem' }}
          />
        </div>

        <div>
          <button type="submit" className="btn btn-success" disabled={submitting}>
            {submitting ? (orden ? 'Actualizando...' : 'Creando...') : (orden ? 'Actualizar' : 'Crear')}
          </button>
          <button type="button" className="btn btn-secondary" onClick={onCancel} disabled={submitting}>
            Cancelar
          </button>
        </div>
      </form>
    </div>
  )
}

function OrdenesPage() {
  const [ordenes, setOrdenes] = useState([])
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [pageInputSide, setPageInputSide] = useState(null) // 'left' | 'right' | null
  const [pageInputValue, setPageInputValue] = useState('')
  const [clientes, setClientes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editingOrden, setEditingOrden] = useState(null)
  const [showDetails, setShowDetails] = useState(false)
  const [detailsOrden, setDetailsOrden] = useState(null)
  const detailsRef = useRef(null)

  useEffect(() => {
    loadOrdenes()
    loadClientes()
  }, [])

  useEffect(() => {
    setPage(1) // reset to first page when data changes
  }, [ordenes, pageSize])

  const totalPages = Math.max(1, Math.ceil(ordenes.length / pageSize))
  const renderPageButtons = () => {
    if (totalPages <= 1) return null
    const buttons = []
    const left = Math.max(2, page - 2)
    const right = Math.min(totalPages - 1, page + 2)

    // first page
    buttons.push(
      <button key={1} className={`btn ${page === 1 && !pageInputSide ? 'active' : ''}`} onClick={() => setPage(1)}>1</button>
    )

    if (left > 2) {
      if (pageInputSide !== 'left') {
        buttons.push(
          <button key="left-ellipsis" className={`btn ${pageInputSide === 'left' ? 'active' : ''}`} onClick={() => { setPageInputSide('left'); setPageInputValue(String(page)); }}>...</button>
        )
      } else {
        buttons.push(
          <input
            key="left-ellipsis-input"
            type="text"
            value={pageInputValue}
            onChange={(e) => setPageInputValue(e.target.value)}
            onBlur={() => {
              const val = parseInt(pageInputValue, 10)
              if (!isNaN(val) && val >= 1 && val <= totalPages) setPage(val)
              else alert(`Página inválida (1-${totalPages})`)
              setPageInputSide(null)
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                const val = parseInt(pageInputValue, 10)
                if (!isNaN(val) && val >= 1 && val <= totalPages) setPage(val)
                else alert(`Página inválida (1-${totalPages})`)
                setPageInputSide(null)
              } else if (e.key === 'Escape') {
                setPageInputSide(null)
              }
            }}
            className="page-input"
            autoFocus
          />
        )
      }
    }

    for (let p = left; p <= right; p++) {
      buttons.push(
        <button key={p} className={`btn ${page === p && !pageInputSide ? 'active' : ''}`} onClick={() => setPage(p)}>{p}</button>
      )
    }

    if (right < totalPages - 1) {
      if (pageInputSide !== 'right') {
        buttons.push(<button key="right-ellipsis" className={`btn ${pageInputSide === 'right' ? 'active' : ''}`} onClick={() => { setPageInputSide('right'); setPageInputValue(String(page)); }}>...</button>)
      } else {
        buttons.push(
          <input
            key="right-ellipsis-input"
            type="text"
            value={pageInputValue}
            onChange={(e) => setPageInputValue(e.target.value)}
            onBlur={() => {
              const val = parseInt(pageInputValue, 10)
              if (!isNaN(val) && val >= 1 && val <= totalPages) setPage(val)
              else alert(`Página inválida (1-${totalPages})`)
              setPageInputSide(null)
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                const val = parseInt(pageInputValue, 10)
                if (!isNaN(val) && val >= 1 && val <= totalPages) setPage(val)
                else alert(`Página inválida (1-${totalPages})`)
                setPageInputSide(null)
              } else if (e.key === 'Escape') {
                setPageInputSide(null)
              }
            }}
            className="page-input"
            autoFocus
          />
        )
      }
    }

    if (totalPages > 1) {
      buttons.push(
        <button key={totalPages} className={`btn ${page === totalPages && !pageInputSide ? 'active' : ''}`} onClick={() => setPage(totalPages)}>{totalPages}</button>
      )
    }

    return buttons
  }

  const loadOrdenes = async () => {
    try {
      setLoading(true)
      const response = await ordenesApi.getAll()
      // deduplicate by orden_id in case backend returns duplicates
      const items = response.data || []
      const byId = new Map()
      items.forEach(o => { if (o && o.orden_id && !byId.has(o.orden_id)) byId.set(o.orden_id, o) })
      const mapped = Array.from(byId.values()).map(o => ({ ...o, _id: o.orden_id }))
      setOrdenes(mapped)
    } catch (error) {
      setError('Error al cargar órdenes')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const loadClientes = async () => {
    try {
      const response = await clientesApi.getAll()
      const mapped = response.data.map(c => ({ ...c, _id: c.cliente_id }))
      setClientes(mapped)
    } catch (error) {
      console.error('Error cargando clientes:', error)
    }
  }

  const getClienteNombre = (clienteId) => {
    const cliente = clientes.find(c => c._id === clienteId)
    return cliente ? cliente.nombre : 'Cliente no encontrado'
  }

  const handleSave = async (ordenData) => {
    try {
      if (editingOrden) {
        await ordenesApi.update(editingOrden._id, ordenData)
      } else {
        await ordenesApi.create(ordenData)
      }
      loadOrdenes()
      setShowForm(false)
      setEditingOrden(null)
      return true
    } catch (error) {
      setError('Error al guardar orden')
      console.error(error)
      return false
    }
  }

  const handleEdit = (orden) => {
    setEditingOrden(orden)
    setShowForm(true)
  }

  const handleViewDetails = async (orden) => {
    try {
      // try to fetch full order details from API in case items or field names differ
      const id = orden.orden_id || orden._id || orden.id
      if (id) {
        const { data } = await ordenesApi.getById(id)
        setDetailsOrden(data || orden)
      } else {
        setDetailsOrden(orden)
      }
      setShowDetails(true)
    } catch (err) {
      console.error('Error cargando detalles de la orden:', err)
      setError('Error al cargar detalles de la orden')
      // fallback to passed object
      setDetailsOrden(orden)
      setShowDetails(true)
    }
  }

  const handleCloseDetails = () => {
    setDetailsOrden(null)
    setShowDetails(false)
  }

  useEffect(() => {
    if (showDetails && detailsRef.current) {
      // scroll to the details panel smoothly after it appears
      detailsRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [showDetails, detailsOrden])

  const handleDelete = async (id) => {
    if (window.confirm('¿Estás seguro de eliminar esta orden?')) {
      try {
        await ordenesApi.delete(id)
        loadOrdenes()
      } catch (error) {
        setError('Error al eliminar orden')
        console.error(error)
      }
    }
  }

  const handleCancel = () => {
    setShowForm(false)
    setEditingOrden(null)
  }

  if (loading) return <div className="loading">Cargando órdenes...</div>

  return (
    <div>
      {error && <div className="error">{error}</div>}
      
      {!showForm && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2>Órdenes</h2>
            <button 
              className="btn" 
              onClick={() => setShowForm(true)}
            >
              <Plus size={20} style={{ marginRight: '0.5rem' }} />
              Nueva Orden
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
            <div style={{ fontSize: '0.9rem', color: '#666' }}>{`Mostrando ${Math.min((page-1)*pageSize+1, ordenes.length)} - ${Math.min(page*pageSize, ordenes.length)} de ${ordenes.length}`}</div>
          </div>
          
          <table className="table">
            <thead>
              <tr>
                <th>Cliente</th>
                <th>Fecha</th>
                <th>Canal</th>
                <th>Moneda</th>
                <th>Items</th>
                <th>Total</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {ordenes.slice((page-1)*pageSize, page*pageSize).map(orden => (
                <tr key={orden._id}>
                  <td>{getClienteNombre(orden.cliente_id)}</td>
                  <td>{new Date(orden.fecha).toLocaleDateString()}</td>
                  <td>{orden.canal}</td>
                  <td>{(orden.moneda || 'CRC').toUpperCase()}</td>
                  <td>{orden.orden_detalle?.length || orden.items?.length || 0}</td>
                  <td>{orden.moneda === 'USD' || orden.moneda === 'usd' ? `$${(orden.total || 0).toLocaleString()}` : `₡${(orden.total || 0).toLocaleString()}`}</td>
                  <td>
                    <button 
                      className="btn btn-info" 
                      onClick={() => handleViewDetails(orden)}
                      style={{ marginRight: '0.5rem' }}
                    >
                      <Eye size={14} style={{ marginRight: '0.35rem' }} />
                      Ver detalles
                    </button>
                    <button 
                      className="btn btn-secondary" 
                      onClick={() => handleEdit(orden)}
                      style={{ marginRight: '0.5rem' }}
                    >
                      <Edit size={16} />
                    </button>
                    <button 
                      className="btn btn-danger" 
                      onClick={() => handleDelete(orden._id)}
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {/* Pagination controls */}
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
          {showDetails && detailsOrden && (
            <div ref={detailsRef} className="card" style={{ marginTop: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3>Detalles de la orden</h3>
                <button className="btn" onClick={handleCloseDetails}>Cerrar</button>
              </div>
              <div style={{ marginTop: '0.5rem' }}>
                <div><strong>ID:</strong> {detailsOrden.orden_id || detailsOrden._id}</div>
                <div><strong>Cliente:</strong> {getClienteNombre(detailsOrden.cliente_id)}</div>
                <div><strong>Fecha:</strong> {new Date(detailsOrden.fecha).toLocaleString()}</div>
                <div><strong>Canal:</strong> {detailsOrden.canal}</div>
                <div><strong>Moneda:</strong> {(detailsOrden.moneda || 'CRC').toUpperCase()}</div>
                <div style={{ marginTop: '0.5rem' }}><strong>Items:</strong></div>
                <ul className="details-items">
                  {(detailsOrden.orden_detalle || detailsOrden.items || []).map((it, idx) => {
                    const prod = it.producto || {}
                    const nombre = prod?.nombre || it.nombre || 'Item'
                    const id = prod?.producto_id ?? prod?.id ?? it.producto_id ?? it.id ?? 'N/A'
                    const sku = prod?.sku ?? it.sku ?? 'N/A'
                    const precioUnitRaw = it.precio_unit ?? it.precio ?? it.price ?? 0
                    const cantidad = it.cantidad ?? it.qty ?? 0
                    const subtotalRaw = Number(precioUnitRaw) * Number(cantidad)
                    const isUSD = detailsOrden && String(detailsOrden.moneda).toUpperCase() === 'USD'
                    const formatMoney = (v) => isUSD ? `$${Number(v).toLocaleString()}` : `₡${Number(v).toLocaleString()}`

                    return (
                      <li key={idx} style={{ marginBottom: '0.75rem' }}>
                        <div><strong>{nombre}:</strong></div>
                        <ul>
                          <li><strong>ID:</strong> {id}</li>
                          <li><strong>SKU:</strong> {sku}</li>
                          <li><strong>Precio unitario:</strong> {formatMoney(precioUnitRaw)}</li>
                          <li><strong>Cantidad:</strong> {cantidad}</li>
                          <li><strong>Total de la venta:</strong> {formatMoney(subtotalRaw)}</li>
                        </ul>
                      </li>
                    )
                  })}
                </ul>
                <div><strong>Total:</strong> {detailsOrden.moneda === 'USD' ? `$${(detailsOrden.total || 0).toLocaleString()}` : `₡${(detailsOrden.total || 0).toLocaleString()}`}</div>
              </div>
            </div>
          )}
        </div>
      )}

      {showForm && (
        <OrdenForm 
          orden={editingOrden}
          onSave={handleSave}
          onCancel={handleCancel}
        />
      )}
    </div>
  )
}

export default OrdenesPage
