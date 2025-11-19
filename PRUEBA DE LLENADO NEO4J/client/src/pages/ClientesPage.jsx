import { useState, useEffect } from 'react'
import { clientesApi } from '../services/api'
import { Edit, Trash2, Plus } from 'lucide-react'

function ClienteForm({ cliente, onSave, onCancel }) {
  const [formData, setFormData] = useState({
    nombre: '',
    genero: 'Masculino',
    pais: 'CR'
  });

  useEffect(() => {
    if (cliente) {
      // Solo toma las propiedades relevantes
      setFormData({
        nombre: cliente.nombre || '',
        genero: cliente.genero || 'Masculino',
        pais: cliente.pais || 'CR'
      });
    }
  }, [cliente]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(formData);
  };

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
        </div>
        <div className="form-row">
          <div className="form-group">
            <label>Género:</label>
            <select
              value={formData.genero}
              onChange={(e) => setFormData({ ...formData, genero: e.target.value })}
            >
              <option value="Masculino">Masculino</option>
              <option value="M">M</option>
              <option value="Femenino">Femenino</option>
              <option value="F">F</option>
              <option value="Otro">Otro</option>
            </select>
          </div>
          <div className="form-group">
            <label>País:</label>
            <input
              type="text"
              value={formData.pais}
              onChange={(e) => setFormData({ ...formData, pais: e.target.value })}
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
  );
}

function ClientesPage() {
  const [clientes, setClientes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editingCliente, setEditingCliente] = useState(null)
  const [searchId, setSearchId] = useState('')
  const [searchError, setSearchError] = useState('')
  const [createdClientId, setCreatedClientId] = useState(null)

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
        // Usa id o _id según lo que exista
        const clienteId = editingCliente.id || editingCliente._id;
        if (!clienteId) {
          setError('No se encontró el ID del cliente para actualizar');
          return;
        }
        await clientesApi.update(clienteId, clienteData);
      } else {
        const resp = await clientesApi.create(clienteData)
        const newId = resp?.data?.id || null
        if (newId) setCreatedClientId(newId)
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
      {createdClientId && (
        <div className="success" style={{ marginBottom: '1rem' }}>
          Cliente creado: <strong>{createdClientId}</strong>
        </div>
      )}
      
      {!showForm && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2>Clientes</h2>
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
                  const resp = await clientesApi.getById(searchId)
                  setClientes([resp.data])
                } catch (err) {
                  console.error('Error buscando cliente por id:', err)
                  setSearchError('Cliente no encontrado')
                } finally {
                  setLoading(false)
                }
              }}>Buscar</button>
              <button className="btn" onClick={() => { setSearchId(''); setSearchError(''); loadClientes(); }}>Mostrar todos</button>
              <button 
                className="btn" 
                onClick={() => { setCreatedClientId(null); setShowForm(true) }}
              >
                <Plus size={20} style={{ marginRight: '0.5rem' }} />
                Nuevo Cliente
              </button>
            </div>
          </div>
          {searchError && <div className="error" style={{ marginBottom: '1rem' }}>{searchError}</div>}
          
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
              {clientes.map((cliente, idx) => (
                <tr key={cliente.id || cliente._id || idx}>
                  <td>{cliente.id || cliente._id}</td>
                  <td>{cliente.nombre}</td>
                  <td>{cliente.genero}</td>
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
                      onClick={() => handleDelete(cliente.id || cliente._id)}
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
