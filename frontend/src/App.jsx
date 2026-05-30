import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import Navbar from './components/Navbar'
import Auth from './pages/Auth' // Импортируем нашу форму
import Dispatcher from './pages/Dispatcher'
import Monitoring from './pages/Monitoring'
import Courier from './pages/Courier'
import './App.css'

// Вспомогательный компонент: скрывает Navbar на странице логина
function Layout() {
  const location = useLocation()

  // Если мы на странице авторизации, меню сверху показывать НЕ нужно
  const showNavbar = location.pathname !== '/login'

  return (
    <>
      {showNavbar && <Navbar />}
      <Routes>
        {/* Теперь главная страница отправляет пользователя сначала ЗАЛОГИНИТЬСЯ */}
        <Route path="/" element={<Navigate to="/login" />} />

        <Route path="/login" element={<Auth />} />
        <Route path="/dispatcher" element={<Dispatcher />} />
        <Route path="/monitoring" element={<Monitoring />} />
        <Route path="/courier" element={<Courier />} />

        <Route path="*" element={<div style={{padding: '20px'}}><h2>404 — Не найдено</h2></div>} />
      </Routes>
    </>
  )
}

function App() {
  return (
    <Router>
      <Layout />
    </Router>
  )
}

export default App