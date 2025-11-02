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
      setFormData({
        cliente_id: orden.cliente_id,
        fecha: new Date(orden.fecha).toISOString().slice(0, 16),
        canal: orden.canal,
        moneda: orden.moneda,
        total: orden.total,
        items: (orden.orden_detalle || []).map(i => ({
          producto_id: i.producto_id,
          cantidad: i.cantidad,
          precio_unit: i.precio_unit
        })),
        metadatos: orden.metadatos || { cupon: '' }
      })
    }
  }, [orden])

  const loadClientes = async () => {
    try {
      const response = await clientesApi.getAll()
      const mapped = response.data.map(c => ({ ...c, _id: c.cliente_id }))
      setClientes(mapped)
    } catch (error) {
      console.error('Error cargando clientes:', error)
    }
  }

  const loadProductos = async () => {
    try {
      const response = await productosApi.getAll()
      const mapped = response.data.map(p => ({ ...p, _id: p.producto_id }))
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
      const exists = formData.items.some((it, i) => i !== index && it.producto_id === value)
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

  const handleSubmit = (e) => {
    e.preventDefault()
    
    // Convertir fecha a Date object
    // validate duplicate producto_ids
    const productoIds = formData.items.map(it => it.producto_id).filter(Boolean)
    const duplicates = productoIds.filter((id, idx) => productoIds.indexOf(id) !== idx)
    if (duplicates.length > 0) {
      window.alert('Hay productos repetidos en los items. Elimine duplicados antes de guardar.')
      return
    }

    const submitData = {
      ...formData,
      fecha: new Date(formData.fecha).toISOString(),
      total: parseFloat(formData.total),
      items: formData.items.map(item => ({
        producto_id: item.producto_id,
        cantidad: parseInt(item.cantidad, 10),
        precio_unit: parseFloat(item.precio_unit)
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
                <option key={cliente._id} value={cliente._id}>
                  {cliente.nombre} - {cliente.email}
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
            <select
              value={formData.canal}
              onChange={(e) => setFormData({ ...formData, canal: e.target.value })}
            >
              <option value="WEB">WEB</option>
              <option value="TIENDA">TIENDA</option>
            </select>
          </div>
          <div className="form-group">
            <label>Cupón:</label>
            <input
              type="text"
              value={formData.metadatos?.cupon || ''}
              onChange={(e) => setFormData({ 
                ...formData, 
                metadatos: { ...formData.metadatos, cupon: e.target.value }
              })}
              placeholder="Código de cupón (opcional)"
            />
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
                  <label>Precio Unitario (CRC):</label>
                  <input
                    type="number"
                    min="0"
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

  useEffect(() => {
    loadOrdenes()
    loadClientes()
  }, [])

  const loadOrdenes = async () => {
    try {
      setLoading(true)
      const response = await ordenesApi.getAll()
      // map orden_id to _id for UI
      const mapped = response.data.map(o => ({ ...o, _id: o.orden_id }))
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
          
          <table className="table">
            <thead>
              <tr>
                <th>Cliente</th>
                <th>Fecha</th>
                <th>Canal</th>
                <th>Items</th>
                <th>Total (CRC)</th>
                <th>Cupón</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {ordenes.map(orden => (
                <tr key={orden._id}>
                  <td>{getClienteNombre(orden.cliente_id)}</td>
                  <td>{new Date(orden.fecha).toLocaleDateString()}</td>
                  <td>{orden.canal}</td>
                  <td>{orden.orden_detalle?.length || orden.items?.length || 0}</td>
                  <td>₡{orden.total?.toLocaleString()}</td>
                  <td>{orden.metadatos?.cupon || '-'}</td>
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
                      onClick={() => handleDelete(orden._id)}
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
