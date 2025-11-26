import { useState, useEffect } from 'react'
import { clientesApi } from '../services/api'
import { Edit, Trash2, Plus, Search } from 'lucide-react'

function ClienteForm({ cliente, onSave, onCancel }) {
  const [formData, setFormData] = useState({
    nombre: '',
    email: '',
    genero: 'Masculino',
    pais: 'CR',
    preferencias: { canal: [] }
  })

  useEffect(() => {
    if (cliente) {
      setFormData(cliente)
    }
  }, [cliente])

  const handleSubmit = (e) => {
    e.preventDefault()
    onSave(formData)
  }

  const handleCanalChange = (canal) => {
    const canales = formData.preferencias.canal || []
    const newCanales = canales.includes(canal)
      ? canales.filter(c => c !== canal)
      : [...canales, canal]
    
    setFormData({
      ...formData,
      preferencias: { ...formData.preferencias, canal: newCanales }
    })
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
              <option value="Masculino">Masculino</option>
              <option value="Femenino">Femenino</option>
              <option value="Otro">Otro</option>
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

        <div className="form-group">
          <label>Canales Preferidos:</label>
          <div style={{ 
            display: 'flex', 
            gap: '1.5rem', 
            marginTop: '0.5rem',
            padding: '0.75rem',
            background: '#f8f9fa',
            borderRadius: '8px',
            border: '2px solid #e1e5e9'
          }}>
            <label style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '0.5rem',
              cursor: 'pointer',
              fontWeight: '500'
            }}>
              <input
                type="checkbox"
                checked={formData.preferencias.canal?.includes('WEB') || false}
                onChange={() => handleCanalChange('WEB')}
                style={{ 
                  width: '18px', 
                  height: '18px',
                  cursor: 'pointer'
                }}
              />
              WEB
            </label>
            <label style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '0.5rem',
              cursor: 'pointer',
              fontWeight: '500'
            }}>
              <input
                type="checkbox"
                checked={formData.preferencias.canal?.includes('TIENDA') || false}
                onChange={() => handleCanalChange('TIENDA')}
                style={{ 
                  width: '18px', 
                  height: '18px',
                  cursor: 'pointer'
                }}
              />
              TIENDA
            </label>
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
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    loadClientes()
  }, [])

  const loadClientes = async () => {
    try {
      setLoading(true)
      const response = await clientesApi.getAll()
      setClientes(response.data)
    } catch (error) {
      setError('Error al cargar clientes')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (clienteData) => {
    try {
      if (editingCliente) {
        await clientesApi.update(editingCliente._id, clienteData)
      } else {
        await clientesApi.create(clienteData)
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

  // Filtrar clientes basado en el término de búsqueda
  const filteredClientes = clientes.filter(cliente =>
    cliente.nombre?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    cliente.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    cliente.genero?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    cliente.pais?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    cliente.preferencias?.canal?.some(canal => 
      canal.toLowerCase().includes(searchTerm.toLowerCase())
    )
  )

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
          
          {/* Barra de búsqueda */}
          <div style={{ 
            position: 'relative', 
            marginBottom: '1rem',
            maxWidth: '400px'
          }}>
            <Search 
              size={20} 
              style={{
                position: 'absolute',
                left: '12px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: '#666',
                pointerEvents: 'none'
              }}
            />
            <input
              type="text"
              placeholder="Buscar por nombre, email, género, país o canal..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                width: '100%',
                padding: '12px 12px 12px 45px',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontSize: '14px',
                outline: 'none',
                transition: 'border-color 0.2s ease'
              }}
              onFocus={(e) => e.target.style.borderColor = '#007bff'}
              onBlur={(e) => e.target.style.borderColor = '#ddd'}
            />
          </div>

          {/* Mostrar contador de resultados */}
          <div style={{ 
            marginBottom: '1rem', 
            fontSize: '14px', 
            color: '#666' 
          }}>
            {searchTerm && (
              <span>
                Mostrando {filteredClientes.length} de {clientes.length} clientes
                {searchTerm && (
                  <button
                    onClick={() => setSearchTerm('')}
                    style={{
                      marginLeft: '10px',
                      background: 'none',
                      border: 'none',
                      color: '#007bff',
                      cursor: 'pointer',
                      textDecoration: 'underline',
                      fontSize: '14px'
                    }}
                  >
                    Limpiar búsqueda
                  </button>
                )}
              </span>
            )}
          </div>
          
          <table className="table">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Email</th>
                <th>Género</th>
                <th>País</th>
                <th>Canales</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {filteredClientes.length > 0 ? (
                filteredClientes.map(cliente => (
                  <tr key={cliente._id}>
                    <td>{cliente.nombre}</td>
                    <td>{cliente.email}</td>
                    <td>{cliente.genero}</td>
                    <td>{cliente.pais}</td>
                    <td>{cliente.preferencias?.canal?.join(', ') || 'Ninguno'}</td>
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
                ))
              ) : (
                <tr>
                  <td colSpan="6" style={{ 
                    textAlign: 'center', 
                    padding: '2rem',
                    color: '#666',
                    fontStyle: 'italic'
                  }}>
                    {searchTerm 
                      ? `No se encontraron clientes que coincidan con "${searchTerm}"`
                      : 'No hay clientes registrados'
                    }
                  </td>
                </tr>
              )}
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
