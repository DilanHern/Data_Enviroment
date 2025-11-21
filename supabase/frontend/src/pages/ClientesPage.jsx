import { useState, useEffect } from 'react'
import { clientesApi, ordenesApi } from '../services/api'
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
      <h3>{cliente ? 'Editar Cliente' : 'Nuevo Cliente'}</h3>
      <form onSubmit={handleSubmitAsync}>
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
              onChange={(e) => setFormData({ ...formData, pais: e.target.value })}
              required
            />
          </div>
        </div>

        <div>
          <button type="submit" className="btn btn-success" disabled={submitting}>
            {submitting ? 'Procesando...' : (cliente ? 'Actualizar' : 'Crear')}
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
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [pageInputSide, setPageInputSide] = useState(null)
  const [pageInputValue, setPageInputValue] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editingCliente, setEditingCliente] = useState(null)

  useEffect(() => {
    loadClientes()
  }, [])

  useEffect(() => {
    setPage(1)
  }, [clientes, pageSize])

  const totalPages = Math.max(1, Math.ceil(clientes.length / pageSize))
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

  const loadClientes = async () => {
    try {
      setLoading(true)
      const response = await clientesApi.getAll()
      // map Supabase cliente_id to string _id for compatibility with the UI
      const mapped = (response.data || []).map(c => ({ ...c, _id: String(c.cliente_id) }))
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
      return true
    } catch (error) {
      setError('Error al guardar cliente')
      console.error(error)
      return false
    }
  }

  const handleEdit = (cliente) => {
    setEditingCliente(cliente)
    setShowForm(true)
  }

  const handleDelete = async (id) => {
    if (!window.confirm('¿Estás seguro de eliminar este cliente?')) return
    try {
      // check referential integrity: does any order reference this cliente?
      const { data: ordenes } = await ordenesApi.getAll()
      const used = (ordenes || []).some(o => String(o.cliente_id) === String(id))
      if (used) {
        window.alert('No se puede eliminar: existen órdenes que referencian a este cliente.')
        return
      }
      await clientesApi.delete(id)
      loadClientes()
    } catch (error) {
      setError('Error al eliminar cliente')
      console.error(error)
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
            <div style={{ fontSize: '0.9rem', color: '#666' }}>{`Mostrando ${Math.min((page-1)*pageSize+1, clientes.length)} - ${Math.min(page*pageSize, clientes.length)} de ${clientes.length}`}</div>
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
              {clientes.slice((page-1)*pageSize, page*pageSize).map(cliente => (
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
