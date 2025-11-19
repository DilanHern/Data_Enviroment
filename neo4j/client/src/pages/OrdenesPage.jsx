import { useState, useEffect } from 'react'
import { ordenesApi, clientesApi, productosApi } from '../services/api'
import { Edit, Trash2, Plus, Minus } from 'lucide-react'

function OrdenForm({ orden, onSave, onCancel }) {
  const [formData, setFormData] = useState({
    cliente_id: '',
    fecha: new Date().toISOString().slice(0, 16),
    canal: 'WEB',
    moneda: 'CRC',
    total: 0,
    items: [{ producto_id: '', cantidad: 1, precio_unit: 0 }],
    metadatos: { cupon: '' }
  })
  
  const [clientes, setClientes] = useState([])
  const [productos, setProductos] = useState([])

useEffect(() => {
    loadClientes()
    loadProductos()
    if (orden) {
      // Normalizar fecha
      let fechaValue = ''
      if (orden.fecha) {
        if (typeof orden.fecha === 'string' || orden.fecha instanceof Date) {
          fechaValue = new Date(orden.fecha)
        } else if (
          typeof orden.fecha === 'object' &&
          (orden.fecha.year || orden.fecha.year === 0) &&
          (orden.fecha.month || orden.fecha.month === 0) &&
          (orden.fecha.day || orden.fecha.day === 0)
        ) {
          // Extraer valores .low o usar el valor directo, y asegurar que existan
          const getVal = v => (typeof v === 'object' && v !== null && 'low' in v) ? v.low : v ?? 0
          const year = getVal(orden.fecha.year)
          const month = getVal(orden.fecha.month) // API retorna 1-12, input datetime-local usa 1-12
          const day = getVal(orden.fecha.day)
          const hour = getVal(orden.fecha.hour)
          const minute = getVal(orden.fecha.minute)
          // Crear fecha con formato ISO para datetime-local (usa mes 1-12)
          const monthStr = String(month).padStart(2, '0')
          const dayStr = String(day).padStart(2, '0')
          const hourStr = String(hour).padStart(2, '0')
          const minuteStr = String(minute).padStart(2, '0')
          fechaValue = `${year}-${monthStr}-${dayStr}T${hourStr}:${minuteStr}`
        }
      }
      
      // Transformar productos a items si vienen de la API
      let items = [{ producto_id: '', cantidad: 1, precio_unit: 0 }]
      if (Array.isArray(orden.productos) && orden.productos.length > 0) {
        items = orden.productos.map(prod => ({
          producto_id: prod.id || prod._id || '',
          cantidad: typeof prod.cantidad === 'object' && prod.cantidad.low !== undefined 
            ? prod.cantidad.low 
            : prod.cantidad || 1,
          precio_unit: prod.precio_unit || 0
        }))
      } else if (Array.isArray(orden.items) && orden.items.length > 0) {
        items = orden.items
      }
      
      setFormData({
        ...orden,
        cliente_id: orden.cliente_id
          ? String(orden.cliente_id)
          : orden.cliente && orden.cliente.id
            ? String(orden.cliente.id)
            : '',
        fecha: typeof fechaValue === 'string'
          ? fechaValue
          : (fechaValue && !isNaN(fechaValue.getTime()))
            ? fechaValue.toISOString().slice(0, 16)
            : new Date().toISOString().slice(0, 16),
        metadatos: orden.metadatos || {},
        items: items
      })
    }
  }, [orden])
  
  const loadClientes = async () => {
    try {
      const response = await clientesApi.getAll()
      setClientes(response.data)
    } catch (error) {
      console.error('Error cargando clientes:', error)
    }
  }

  const loadProductos = async () => {
    try {
      const response = await productosApi.getAll()
      setProductos(response.data)
    } catch (error) {
      console.error('Error cargando productos:', error)
    }
  }

  const calculateTotal = () => {
    const total = formData.items.reduce((sum, item) =>
      sum + (Number(item.cantidad || 0) * Number(item.precio_unit || 0)), 0
    , 0)
    // round to 2 decimals
    const rounded = Math.round((total + Number.EPSILON) * 100) / 100
    setFormData(prev => ({ ...prev, total: rounded }))
  }

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
    setFormData(prev => {
      const items = prev.items.map((item, i) => {
        if (i !== index) return item
        const newItem = { ...item }
        // Keep raw input while editing to allow typing (empty string, partial numbers)
        if (field === 'precio_unit') {
          newItem.precio_unit = value
        } else if (field === 'cantidad') {
          newItem.cantidad = value
        } else {
          newItem[field] = value
        }
        return newItem
      })
      return { ...prev, items }
    })
  }

  // Recalculate total whenever items change (reactive, avoids timing issues)
  useEffect(() => {
    calculateTotal()
  }, [formData.items])

  const handleSubmit = (e) => {
    e.preventDefault()
    
    // Convertir fecha a ISO sin milisegundos (ej. 2025-03-27T16:02:07Z)
    const fechaObj = new Date(formData.fecha)
    const fechaIsoNoMs = isNaN(fechaObj.getTime())
      ? new Date().toISOString().replace(/\.\d{3}Z$/, 'Z')
      : fechaObj.toISOString().replace(/\.\d{3}Z$/, 'Z')

    const submitData = {
      ...formData,
      fecha: fechaIsoNoMs,
      // recalcular total con decimales por seguridad
      total: formData.items.reduce((s, it) => s + (Number(it.cantidad) * Number(it.precio_unit || 0)), 0),
      items: formData.items.map(item => ({
        ...item,
        cantidad: parseInt(item.cantidad, 10) || 0,
        precio_unit: parseFloat(item.precio_unit) || 0
      }))
    }

    onSave(submitData)
  }

  return (
    <div className="card">
      <h3>{orden ? 'Editar Orden' : 'Nueva Orden'}</h3>
      <form onSubmit={handleSubmit}>
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
                <option key={cliente.id || cliente._id} value={String(cliente.id || cliente._id)}>
                  {cliente.nombre} {cliente.email ? `- ${cliente.email}` : ''}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Fecha:</label>
            <input
              type="datetime-local"
              value={formData.fecha}
              onChange={(e) => setFormData({ ...formData, fecha: e.target.value })}
              required
            />
          </div>
        </div>
        
        <div className="form-row">
          <div className="form-group">
            <label>Canal:</label>
            <input
              type="text"
              value={formData.canal}
              onChange={(e) => setFormData({ ...formData, canal: e.target.value })}
              required
              placeholder="Canal de la orden"
            />
          </div>
          <div className="form-group">
            <label>Moneda:</label>
            <select
              value={formData.moneda}
              onChange={(e) => setFormData({ ...formData, moneda: e.target.value })}
              required
            >
              <option value="CRC">CRC</option>
              <option value="USD">USD</option>
            </select>
          </div>
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
                    <option key={producto.id || producto._id} value={producto.id || producto._id}>
                      {producto.codigo_mongo} - {producto.nombre}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Cantidad:</label>
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={item.cantidad}
                  onChange={(e) => updateItem(index, 'cantidad', e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>Precio Unitario (CRC):</label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={item.precio_unit}
                  onChange={(e) => updateItem(index, 'precio_unit', e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>Subtotal:</label>
                <input
                  type="text"
                  value={`₡${(item.cantidad * item.precio_unit).toLocaleString()}`}
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

        <div className="form-group">
          <label>Total (CRC):</label>
          <input
            type="text"
            value={`₡${formData.total.toLocaleString()}`}
            disabled
            style={{ background: '#f8f9fa', fontWeight: 'bold', fontSize: '1.2rem' }}
          />
        </div>

        <div>
          <button type="submit" className="btn btn-success">
            {orden ? 'Actualizar' : 'Crear'}
          </button>
          <button type="button" className="btn btn-secondary" onClick={onCancel}>
            Cancelar
          </button>
        </div>
      </form>
    </div>
  )
}

function OrdenesPage() {
  const [ordenes, setOrdenes] = useState([])
  const [clientes, setClientes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editingOrden, setEditingOrden] = useState(null)
  const [createdOrderId, setCreatedOrderId] = useState(null)
  const [searchId, setSearchId] = useState('')
  const [searchError, setSearchError] = useState('')

  useEffect(() => {
    loadOrdenes()
    loadClientes()
  }, [])

  const loadOrdenes = async () => {
    try {
      setLoading(true)
      const response = await ordenesApi.getAll()
      setOrdenes(response.data)
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
      setClientes(response.data)
    } catch (error) {
      console.error('Error cargando clientes:', error)
    }
  }

  const handleSearchById = async () => {
    setSearchError('')
    if (!searchId || searchId.trim() === '') return setSearchError('Ingrese un ID para buscar')
    try {
      setLoading(true)
      const resp = await ordenesApi.getById(searchId.trim())
      setOrdenes(resp.data ? [resp.data] : [])
    } catch (err) {
      console.error('Error buscando orden por id:', err)
      setSearchError('Orden no encontrada')
      setOrdenes([])
    } finally {
      setLoading(false)
    }
  }

  const handleShowAll = () => {
    setSearchId('')
    setSearchError('')
    loadOrdenes()
  }

  const getClienteNombre = (clienteId) => {
    const cliente = clientes.find(c => c._id === clienteId)
    return cliente ? cliente.nombre : 'Cliente no encontrado'
  }

  const handleSave = async (ordenData) => {
    try {
      if (editingOrden) {
        const idToUpdate = editingOrden.id || editingOrden._id
        await ordenesApi.update(idToUpdate, ordenData)
      } else {
        const resp = await ordenesApi.create(ordenData)
        const newId = resp?.data?.id || null
        if (newId) setCreatedOrderId(newId)
      }
      loadOrdenes()
      setShowForm(false)
      setEditingOrden(null)
    } catch (error) {
      setError('Error al guardar orden')
      console.error(error)
    }
  }

  const handleEdit = (orden) => {
    setEditingOrden(orden)
    setShowForm(true)
  }

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
      {createdOrderId && (
        <div className="success" style={{ marginBottom: '1rem' }}>
          Orden creada: <strong>{createdOrderId}</strong>
        </div>
      )}
      
      {!showForm && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2>Órdenes</h2>
            
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <input
              type="text"
              placeholder="Buscar por ID"
              value={searchId}
              onChange={(e) => setSearchId(e.target.value)}
              style={{ padding: '0.4rem', borderRadius: '4px', border: '1px solid #ccc' }}
            />
            <button className="btn" onClick={async () => { setSearchError(''); await handleSearchById(); }}>
              Buscar
            </button>
            <button className="btn" onClick={() => { setSearchId(''); setSearchError(''); handleShowAll(); }}>Mostrar todos</button>
            <button 
              className="btn" 
              onClick={() => { setCreatedOrderId(null); setShowForm(true) }}
            >
              <Plus size={20} style={{ marginRight: '0.5rem' }} />
              Nueva Orden
            </button>
          </div>
          {searchError && <div className="error" style={{ marginBottom: '1rem' }}>{searchError}</div>}
          
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Canal</th>
                <th>Moneda</th>
                <th>Total</th>
                <th>Fecha</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {ordenes.map(orden => (
                <tr key={orden.id || orden._id}>
                  <td>{orden.id || orden._id || '-'}</td>
                  <td>{orden.canal || '-'}</td>
                  <td>{orden.moneda || '-'}</td>
                  <td>{orden.total != null ? `₡${orden.total.toLocaleString()}` : '-'}</td>
                  <td>
                    {orden.fecha && orden.fecha.year
                      ? `${orden.fecha.year.low}-${String(orden.fecha.month.low).padStart(2, '0')}-${String(orden.fecha.day.low).padStart(2, '0')} ${String(orden.fecha.hour.low).padStart(2, '0')}:${String(orden.fecha.minute.low).padStart(2, '0')}`
                      : '-'}
                  </td>
                  <td>
                    <button 
                      className="btn btn-secondary" 
                      onClick={() => handleEdit(orden)}
                      style={{ marginRight: '0.5rem' }}
                    >
                      <Edit size={16} />
                    </button>
                    <button 
                      className="btn btn-danger" 
                      onClick={() => handleDelete(orden.id || orden._id)}
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
