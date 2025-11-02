import { useState, useEffect } from 'react'
import { clientesApi } from '../services/api'
import { Edit, Trash2, Plus } from 'lucide-react'

function ClienteForm({ cliente, onSave, onCancel }) {
  const [formData, setFormData] = useState({
    nombre: '',
    email: '',
    genero: 'M',
    pais: 'CR'
  })

  useEffect(() => {
    if (cliente) {
      // map incoming cliente to form shape if needed
      setFormData({
        nombre: cliente.nombre || '',
        email: cliente.email || '',
        genero: cliente.genero || 'M',
        pais: cliente.pais || 'CR'
      })
    }
  }, [cliente])

  const handleSubmit = (e) => {
    e.preventDefault()
    onSave(formData)
  }

  return (
    <div className="card">
      <h3>{cliente ? 'Editar Cliente' : 'Nuevo Cliente'}</h3>
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
          <div className="form-group">
            <label>Email:</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
            />
          </div>
        </div>
        
        <div className="form-row">
          <div className="form-group">
            <label>Género:</label>
            <select
              value={formData.genero}
              onChange={(e) => setFormData({ ...formData, genero: e.target.value })}
            >
              <option value="M">Masculino</option>
              <option value="F">Femenino</option>
            </select>
          </div>
          <div className="form-group">
            <label>País:</label>
            <input
              type="text"
              value={formData.pais}
              onChange={(e) => setFormData({ ...formData, pais: e.target.value.toUpperCase() })}
              maxLength="2"
              required
            />
          </div>
        </div>

        <div>
          <button type="submit" className="btn btn-success">
            {cliente ? 'Actualizar' : 'Crear'}
          </button>
          <button type="button" className="btn btn-secondary" onClick={onCancel}>
            Cancelar
          </button>
        </div>
      </form>
    </div>
  )
}

function ClientesPage() {
  const [clientes, setClientes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editingCliente, setEditingCliente] = useState(null)

  useEffect(() => {
    loadClientes()
  }, [])

  const loadClientes = async () => {
    try {
      setLoading(true)
      const response = await clientesApi.getAll()
      // map Supabase cliente_id to _id for compatibility with the UI
      const mapped = response.data.map(c => ({ ...c, _id: c.cliente_id }))
      setClientes(mapped)
    } catch (error) {
      setError('Error al cargar clientes')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (clienteData) => {
    try {
      const payload = {
        nombre: clienteData.nombre,
        email: clienteData.email,
        genero: clienteData.genero,
        pais: clienteData.pais
      }
      if (editingCliente) {
        await clientesApi.update(editingCliente._id, payload)
      } else {
        await clientesApi.create(payload)
      }
      loadClientes()
      setShowForm(false)
      setEditingCliente(null)
    } catch (error) {
      setError('Error al guardar cliente')
      console.error(error)
    }
  }

  const handleEdit = (cliente) => {
    setEditingCliente(cliente)
    setShowForm(true)
  }

  const handleDelete = async (id) => {
    if (window.confirm('¿Estás seguro de eliminar este cliente?')) {
      try {
        await clientesApi.delete(id)
        loadClientes()
      } catch (error) {
        setError('Error al eliminar cliente')
        console.error(error)
      }
    }
  }

  const handleCancel = () => {
    setShowForm(false)
    setEditingCliente(null)
  }

  if (loading) return <div className="loading">Cargando clientes...</div>

  return (
    <div>
      {error && <div className="error">{error}</div>}
      
      {!showForm && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2>Clientes</h2>
            <button 
              className="btn" 
              onClick={() => setShowForm(true)}
            >
              <Plus size={20} style={{ marginRight: '0.5rem' }} />
              Nuevo Cliente
            </button>
          </div>
          
          <table className="table">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Email</th>
                <th>Género</th>
                <th>País</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {clientes.map(cliente => (
                <tr key={cliente._id}>
                  <td>{cliente.nombre}</td>
                  <td>{cliente.email}</td>
                  <td>{cliente.genero === 'M' ? 'Masculino' : cliente.genero === 'F' ? 'Femenino' : cliente.genero}</td>
                  <td>{cliente.pais}</td>
                  <td>
                    <button 
                      className="btn btn-secondary" 
                      onClick={() => handleEdit(cliente)}
                      style={{ marginRight: '0.5rem' }}
                    >
                      <Edit size={16} />
                    </button>
                    <button 
                      className="btn btn-danger" 
                      onClick={() => handleDelete(cliente._id)}
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
        <ClienteForm 
          cliente={editingCliente}
          onSave={handleSave}
          onCancel={handleCancel}
        />
      )}
    </div>
  )
}

export default ClientesPage
