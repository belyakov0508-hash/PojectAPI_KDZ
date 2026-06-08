import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import Navbar from './components/Navbar'
import Auth from './pages/Auth'
import Dispatcher from './pages/Dispatcher'
import Monitoring from './pages/Monitoring'
import Courier from './pages/Courier'
import CourierOrders from './pages/CourierOrders'
import './App.css'

function PrivateRoute({ element, allowedRole }) {
  const token = localStorage.getItem('token')
  const role = parseInt(localStorage.getItem('role'))

  if (!token) return <Navigate to="/login" />
  if (allowedRole && role !== allowedRole) return <Navigate to="/login" />

  return element
}

function Layout() {
  const location = useLocation()
  const showNavbar = location.pathname !== '/login'

  return (
    <>
      {showNavbar && <Navbar />}
      <Routes>
        <Route path="/" element={<Navigate to="/login" />} />
        <Route path="/login" element={<Auth />} />

        {/* Только для диспетчера (role_id = 2) */}
        <Route path="/dispatcher" element={<PrivateRoute element={<Dispatcher />} allowedRole={2} />} />
        <Route path="/monitoring" element={<PrivateRoute element={<Monitoring />} allowedRole={2} />} />
        <Route path="/courier-orders" element={<PrivateRoute element={<CourierOrders />} allowedRole={2} />} />

        {/* Только для курьера (role_id = 1) */}
        <Route path="/courier" element={<PrivateRoute element={<Courier />} allowedRole={1} />} />

        <Route path="*" element={<div style={{ padding: '20px' }}><h2>404 — Не найдено</h2></div>} />
      </Routes>
    </>
  )
}

export default function App() {
  return (
    <Router>
      <Layout />
    </Router>
  )
}
