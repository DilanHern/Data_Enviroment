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
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadClientes()
    loadProductos()
    if (orden) {
      loadOrdenCompleta(orden._id)
    }
  }, [orden])

  const loadOrdenCompleta = async (ordenId) => {
    try {
      setLoading(true)
      const response = await ordenesApi.getById(ordenId)
      console.log('📦 Orden completa:', response.data) // ✅ DEBUG
      console.log('📦 Items recibidos:', response.data.items) // ✅ DEBUG ITEMS
      
      // Mapear items correctamente
      const mappedItems = response.data.items && response.data.items.length > 0
        ? response.data.items.map(item => ({
            producto_id: item.producto_id || item.producto?.id || '',
            cantidad: Number(item.cantidad) || 1,
            precio_unit: Number(item.precio_unit) || Number(item.precio_unitario) || 0
          }))
        : [{ producto_id: '', cantidad: 1, precio_unit: 0 }]
      
      console.log('📦 Items mapeados:', mappedItems) // ✅ DEBUG
      
      setFormData({
        cliente_id: response.data.cliente_id || '',
        fecha: new Date(response.data.fecha).toISOString().slice(0, 16),
        canal: response.data.canal || 'WEB',
        moneda: response.data.moneda || 'CRC',
        total: Number(response.data.total) || 0,
        items: mappedItems,
        metadatos: response.data.metadatos || { cupon: '' }
      })
    } catch (error) {
      console.error('❌ Error cargando orden:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadClientes = async () => {
    try {
      const response = await clientesApi.getAll()
      setClientes(response.data || [])
    } catch (error) {
      console.error('Error cargando clientes:', error)
    }
  }

  const loadProductos = async () => {
    try {
      const response = await productosApi.getAll()
      setProductos(response.data || [])
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
    const submitData = {
      ...formData,
      fecha: new Date(formData.fecha),
      total: parseFloat(formData.total),
      items: formData.items.map(item => ({
        ...item,
        cantidad: parseInt(item.cantidad),
        precio_unit: parseFloat(item.precio_unit)
      }))
    }
    
    console.log('💾 Enviando orden:', submitData) // ✅ DEBUG
    onSave(submitData)
  }

  if (loading) {
    return (
      <div className="card">
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          Cargando orden...
        </div>
      </div>
    )
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
                  {cliente.nombre}
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
            <label>Moneda:</label>
            <select
              value={formData.moneda}
              onChange={(e) => setFormData({ ...formData, moneda: e.target.value })}
            >
              <option value="CRC">CRC (Colones)</option>
              <option value="USD">USD (Dólares)</option>
            </select>
          </div>
        </div>

        <h4 style={{ marginTop: '1.5rem', marginBottom: '1rem' }}>Items</h4>
        {formData.items.map((item, index) => (
          <div key={index} className="card" style={{ marginBottom: '1rem', padding: '1rem', background: '#f8f9fa' }}>
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
                      {producto._id} - {producto.nombre}
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
                  onChange={(e) => updateItem(index, 'cantidad', parseInt(e.target.value) || 1)}
                  required
                />
              </div>
              <div className="form-group">
                <label>Precio Unitario:</label>
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
                  value={`₡${(item.cantidad * item.precio_unit).toLocaleString('es-CR', { minimumFractionDigits: 2 })}`}
                  disabled
                  style={{ background: '#fff', fontWeight: '500' }}
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
          <label>Total ({formData.moneda}):</label>
          <input
            type="text"
            value={`₡${formData.total.toLocaleString('es-CR', { minimumFractionDigits: 2 })}`}
            disabled
            style={{ background: '#f8f9fa', fontWeight: 'bold', fontSize: '1.2rem', color: '#28a745' }}
          />
        </div>

        <div>
          <button type="submit" className="btn btn-success">
            {orden ? '✓ Actualizar' : '✓ Crear'}
          </button>
          <button type="button" className="btn btn-secondary" onClick={onCancel}>
            ✕ Cancelar
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
      setError('')
      const response = await ordenesApi.getAll()
      console.log('📋 Órdenes:', response.data) // ✅ DEBUG
      setOrdenes(response.data || [])
    } catch (error) {
      setError('Error al cargar órdenes: ' + (error.response?.data?.error || error.message))
      console.error('❌ Error:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadClientes = async () => {
    try {
      const response = await clientesApi.getAll()
      setClientes(response.data || [])
    } catch (error) {
      console.error('Error cargando clientes:', error)
    }
  }

  const getClienteNombre = (clienteId) => {
    const cliente = clientes.find(c => c._id === clienteId)
    return cliente ? cliente.nombre : clienteId || 'Desconocido'
  }

  const handleSave = async (ordenData) => {
    try {
      console.log('💾 Guardando orden:', ordenData) // ✅ DEBUG
      
      if (editingOrden) {
        await ordenesApi.update(editingOrden._id, ordenData)
      } else {
        await ordenesApi.create(ordenData)
      }
      
      await loadOrdenes()
      setShowForm(false)
      setEditingOrden(null)
      setError('')
    } catch (error) {
      setError('Error al guardar orden: ' + (error.response?.data?.error || error.message))
      console.error('❌ Error al guardar:', error)
    }
  }

  const handleEdit = (orden) => {
    console.log('✏️ Editando orden:', orden) // ✅ DEBUG
    setEditingOrden(orden)
    setShowForm(true)
  }

  const handleDelete = async (id) => {
    if (window.confirm('¿Estás seguro de eliminar esta orden?')) {
      try {
        await ordenesApi.delete(id)
        await loadOrdenes()
        setError('')
      } catch (error) {
        setError('Error al eliminar orden: ' + (error.response?.data?.error || error.message))
        console.error('❌ Error al eliminar:', error)
      }
    }
  }

  const handleCancel = () => {
    setShowForm(false)
    setEditingOrden(null)
    setError('')
  }

  if (loading) return <div className="loading">Cargando órdenes...</div>

  return (
    <div>
      {error && (
        <div className="error" style={{ 
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
            style={{ float: 'right', background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.2rem' }}
          >
            ✕
          </button>
        </div>
      )}
      
      {!showForm && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2>Órdenes ({ordenes.length})</h2>
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
                <th>ID</th>
                <th>Cliente</th>
                <th>Fecha</th>
                <th>Canal</th>
                <th>Total</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {ordenes.map(orden => (
                <tr key={orden._id}>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.85rem', color: '#666' }}>
                    {orden._id}
                  </td>
                  <td>{getClienteNombre(orden.cliente_id)}</td>
                  <td>{new Date(orden.fecha).toLocaleDateString('es-CR', { 
                    year: 'numeric', 
                    month: 'short', 
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}</td>
                  <td>
                    <span className="badge">{orden.canal}</span>
                  </td>
                  <td style={{ fontWeight: '600', color: '#28a745' }}>
                    ₡{orden.total?.toLocaleString('es-CR', { minimumFractionDigits: 2 })}
                  </td>
                  <td>
                    <button 
                      className="btn btn-secondary" 
                      onClick={() => handleEdit(orden)}
                      style={{ marginRight: '0.5rem' }}
                      title="Editar orden"
                    >
                      <Edit size={16} />
                    </button>
                    <button 
                      className="btn btn-danger" 
                      onClick={() => handleDelete(orden._id)}
                      title="Eliminar orden"
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {ordenes.length === 0 && (
            <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
              No hay órdenes registradas
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