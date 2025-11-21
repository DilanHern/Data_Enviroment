import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import ClientesPage from './pages/ClientesPage'
import ProductosPage from './pages/ProductosPage'
import OrdenesPage from './pages/OrdenesPage'

function Navigation() {
  const location = useLocation()
  
  return (
    <nav className="nav">
      <Link 
        to="/clientes" 
        className={`nav-button ${location.pathname === '/clientes' ? 'active' : ''}`}
      >
        Clientes
      </Link>
      <Link 
        to="/productos" 
        className={`nav-button ${location.pathname === '/productos' ? 'active' : ''}`}
      >
        Productos
      </Link>
      <Link 
        to="/ordenes" 
        className={`nav-button ${location.pathname === '/ordenes' ? 'active' : ''}`}
      >
        Órdenes
      </Link>
    </nav>
  )
}

function App() {
  return (
    <Router>
      <div className="App">
        <header className="header">
          <div className="container">
            <div className="app-title">
              <h1>SUPABASE</h1>
              <div className="subtitle">CR E-commerce</div>
            </div>
            <Navigation />
          </div>
        </header>
        
        <div className="container">
          <Routes>
            <Route path="/" element={<ClientesPage />} />
            <Route path="/clientes" element={<ClientesPage />} />
            <Route path="/productos" element={<ProductosPage />} />
            <Route path="/ordenes" element={<OrdenesPage />} />
          </Routes>
        </div>
      </div>
    </Router>
  )
}

export default App
