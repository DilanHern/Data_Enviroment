import { useState, useEffect } from 'react'
import { clientesApi } from '../services/api'
import { Edit, Trash2, Plus, Search } from 'lucide-react'

function ClienteForm({ cliente, onSave, onCancel }) {
  const [formData, setFormData] = useState({
    nombre: '',
    genero: 'Masculino',
    pais: 'Costa Rica' // ✅ Cambio: valor por defecto al nombre completo
  })

  useEffect(() => {
    if (cliente) {
      setFormData({
        nombre: cliente.nombre,
        genero: cliente.genero,
        pais: cliente.pais // Ya viene como "Costa Rica", "México", etc.
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
              placeholder="Ej: Juan Pérez"
            />
          </div>
        </div>
        
        <div className="form-row">
          <div className="form-group">
            <label>Género:</label>
            <select
              value={formData.genero}
              onChange={(e) => setFormData({ ...formData, genero: e.target.value })}
              required
            >
              <option value="Masculino">Masculino</option>
              <option value="Femenino">Femenino</option>
              <option value="M">M</option>
              <option value="F">F</option>
              <option value="Otro">Otro</option>
              <option value="X">X</option>
            </select>
          </div>
          <div className="form-group">
            <label>País:</label>
            <select
              value={formData.pais}
              onChange={(e) => setFormData({ ...formData, pais: e.target.value })}
              required
            >
              <option value="Costa Rica">🇨🇷 Costa Rica</option>
              <option value="México">🇲🇽 México</option>
              <option value="Colombia">🇨🇴 Colombia</option>
              <option value="Argentina">🇦🇷 Argentina</option>
              <option value="Chile">🇨🇱 Chile</option>
              <option value="Perú">🇵🇪 Perú</option>
              <option value="España">🇪🇸 España</option>
              <option value="Estados Unidos">🇺🇸 Estados Unidos</option>
              <option value="Ecuador">🇪🇨 Ecuador</option>
              <option value="Uruguay">🇺🇾 Uruguay</option>
            </select>
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

function SearchBar({ onSearch, onClear }) {
  const [filters, setFilters] = useState({
    q: '',
    pais: '',
    genero: ''
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    onSearch(filters)
  }

  const handleClear = () => {
    setFilters({ q: '', pais: '', genero: '' })
    onClear()
  }

  return (
    <div className="card" style={{ marginBottom: '1.5rem' }}>
      <form onSubmit={handleSubmit}>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: '2fr 1fr 1fr auto auto', 
          gap: '1rem',
          alignItems: 'end'
        }}>
          <div className="form-group" style={{ margin: 0 }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
              Nombre
            </label>
            <input
              type="text"
              placeholder="Buscar por nombre..."
              value={filters.q}
              onChange={(e) => setFilters({ ...filters, q: e.target.value })}
              style={{ width: '100%' }}
            />
          </div>
          
          <div className="form-group" style={{ margin: 0 }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
              País
            </label>
            <select
              value={filters.pais}
              onChange={(e) => setFilters({ ...filters, pais: e.target.value })}
              style={{ width: '100%' }}
            >
              <option value="">Todos</option>
              <option value="Costa Rica">Costa Rica</option>
              <option value="México">México</option>
              <option value="Colombia">Colombia</option>
              <option value="Argentina">Argentina</option>
              <option value="Chile">Chile</option>
              <option value="Perú">Perú</option>
              <option value="España">España</option>
              <option value="Estados Unidos">Estados Unidos</option>
              <option value="Ecuador">Ecuador</option>
              <option value="Uruguay">Uruguay</option>
            </select>
          </div>

          <div className="form-group" style={{ margin: 0 }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
              Género
            </label>
            <select
              value={filters.genero}
              onChange={(e) => setFilters({ ...filters, genero: e.target.value })}
              style={{ width: '100%' }}
            >
              <option value="">Todos</option>
              <option value="Masculino">Masculino</option>
              <option value="Femenino">Femenino</option>
              <option value="M">M</option>
              <option value="F">F</option>
              <option value="Otro">Otro</option>
              <option value="X">X</option>
            </select>
          </div>

          <button 
            type="submit" 
            className="btn"
            style={{ 
              whiteSpace: 'nowrap',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
          >
            <Search size={16} />
            Buscar
          </button>
          
          <button 
            type="button" 
            onClick={handleClear} 
            className="btn btn-secondary"
            style={{ whiteSpace: 'nowrap' }}
          >
            Limpiar
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
  const [isSearching, setIsSearching] = useState(false)

  useEffect(() => {
    loadClientes()
  }, [])

  const loadClientes = async () => {
    try {
      setLoading(true)
      setError('')
      const response = await clientesApi.getAll()
      setClientes(response.data || response)
      setIsSearching(false)
    } catch (error) {
      setError('Error al cargar clientes: ' + (error.response?.data?.error || error.message))
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async (filters) => {
    try {
      setLoading(true)
      setError('')
      
      // Construir query params (solo agregar si tienen valor)
      const params = new URLSearchParams()
      if (filters.q && filters.q.trim()) params.append('q', filters.q.trim()) // ✅ FIX: Validar que no esté vacío
      if (filters.pais && filters.pais.trim()) params.append('pais', filters.pais.trim()) // ✅ FIX
      if (filters.genero && filters.genero.trim()) params.append('genero', filters.genero.trim()) // ✅ FIX
      
      const queryString = params.toString()
      
      console.log('🔍 Query string:', queryString) // ✅ DEBUG
      
      // Si hay filtros, usar search; si no, cargar todos
      const response = queryString 
        ? await clientesApi.search(`?${queryString}`)
        : await clientesApi.getAll()
      
      setClientes(response.data || response)
      setIsSearching(!!queryString) // ✅ FIX: Solo marcar como búsqueda si hay filtros
    } catch (error) {
      setError('Error en la búsqueda: ' + (error.response?.data?.error || error.message))
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleClearSearch = () => {
    loadClientes()
  }

  const handleSave = async (clienteData) => {
    try {
      setError('')
      if (editingCliente) {
        await clientesApi.update(editingCliente._id, clienteData)
      } else {
        await clientesApi.create(clienteData)
      }
      await loadClientes()
      setShowForm(false)
      setEditingCliente(null)
    } catch (error) {
      setError('Error al guardar cliente: ' + (error.response?.data?.error || error.message))
      console.error(error)
    }
  }

  const handleEdit = (cliente) => {
    setEditingCliente(cliente)
    setShowForm(true)
  }

  const handleDelete = async (id) => {
    if (window.confirm('¿Estás seguro de eliminar este cliente? Esto eliminará también todas sus órdenes.')) {
      try {
        setError('')
        await clientesApi.delete(id)
        await loadClientes()
      } catch (error) {
        setError('Error al eliminar cliente: ' + (error.response?.data?.error || error.message))
        console.error(error)
      }
    }
  }

  const handleCancel = () => {
    setShowForm(false)
    setEditingCliente(null)
    setError('')
  }


  if (loading && !isSearching) return <div className="loading">Cargando clientes...</div>

  return (
    <div>
      {error && (
        <div className="error" style={{ 
          background: '#fee', 
          border: '1px solid #fcc',
          padding: '1rem',
          borderRadius: '8px',
          marginBottom: '1rem',
          color: '#c33'
        }}>
          {error}
        </div>
      )}
      
      {!showForm && (
        <>
          <SearchBar onSearch={handleSearch} onClear={handleClearSearch} />
          
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <div>
                <h2>Clientes</h2>
                <p style={{ color: '#666', fontSize: '0.9rem', marginTop: '0.25rem' }}>
                  {isSearching ? 'Resultados de búsqueda' : 'Mostrando todos los clientes'} 
                  ({clientes.length} registros)
                </p>
              </div>
              <button 
                className="btn" 
                onClick={() => setShowForm(true)}
              >
                <Plus size={20} style={{ marginRight: '0.5rem' }} />
                Nuevo Cliente
              </button>
            </div>
            
            {loading ? (
              <div style={{ textAlign: 'center', padding: '2rem' }}>
                Cargando...
              </div>
            ) : clientes.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
                {isSearching ? 'No se encontraron clientes con los filtros aplicados' : 'No hay clientes registrados'}
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table className="table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Nombre</th>
                      <th>Género</th>
                      <th>País</th>
                      <th>Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {clientes.map(cliente => (
                      <tr key={cliente._id}>
                        <td style={{ fontFamily: 'monospace', fontSize: '0.85rem', color: '#666' }}>
                          {cliente._id}
                        </td>
                        <td style={{ fontWeight: '500' }}>{cliente.nombre}</td>
                        <td>{cliente.genero}</td>
                        <td>{cliente.pais}</td>
                        <td>
                          <button 
                            className="btn btn-secondary" 
                            onClick={() => handleEdit(cliente)}
                            style={{ marginRight: '0.5rem' }}
                            title="Editar cliente"
                          >
                            <Edit size={16} />
                          </button>
                          <button 
                            className="btn btn-danger" 
                            onClick={() => handleDelete(cliente._id)}
                            title="Eliminar cliente"
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
          </div>
        </>
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