import { useEffect, useState } from 'react'
import api from '../api'

export default function Courier() {
  const [orders, setOrders] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const token = localStorage.getItem('token')
  const decoded = JSON.parse(atob(token.split('.')[1]))
  const courierId = decoded.courier_id

  const fetchData = async () => {
    try {
      setLoading(true)
      const [ordersRes, statsRes] = await Promise.all([
        api.get('/api/orders/my'),
        api.get('/api/orders/my/stats'),
      ])
      setOrders(ordersRes.data)
      setStats(statsRes.data)
    } catch (err) {
      setError('Ошибка загрузки данных')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleDeliver = async (orderId) => {
    try {
      await api.post(`/api/orders/${orderId}/complete`)
      fetchData()
    } catch (err) {
      setError('Не удалось обновить статус заказа')
    }
  }

  const statusLabel = {
    pending: '🕐 Ожидает',
    assigned: '🚴 В доставке',
    completed: '✅ Доставлен',
  }

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Мои заказы (Курьер #{courierId})</h1>

      {/* Блок статистики */}
      {stats && (
        <div style={styles.statsRow}>
          <div style={styles.statCard}>
            <p style={styles.statLabel}>Выполнено заказов</p>
            <p style={styles.statValue}>{stats.completed}</p>
          </div>
          <div style={styles.statCard}>
            <p style={styles.statLabel}>Рейтинг</p>
            <p style={styles.statValue}>
              {stats.rating !== null
                ? <span style={styles.rating}>★ {stats.rating}</span>
                : <span style={styles.noData}>Нет данных</span>}
            </p>
          </div>
          <div style={styles.statCard}>
            <p style={styles.statLabel}>Заработок</p>
            <p style={styles.statValue}>
              <span style={styles.earnings}>
                {stats.earnings.toLocaleString()} ₽
              </span>
            </p>
          </div>
        </div>
      )}

      {error && <p style={styles.error}>{error}</p>}

      {loading ? (
        <p style={styles.hint}>Загрузка...</p>
      ) : orders.length === 0 ? (
        <p style={styles.hint}>У вас нет активных заказов.</p>
      ) : (
        <div style={styles.list}>
          {orders.map((order) => (
            <div key={order.order_id} style={styles.orderCard}>
              <div>
                <h3 style={styles.orderTitle}>Заказ №{order.order_id}</h3>
                <p style={styles.text}><strong>Регион:</strong> {order.region}</p>
                <p style={styles.text}><strong>Вес:</strong> {order.weight} кг</p>
                <p style={styles.text}><strong>Часы доставки:</strong> {order.delivery_hours.join(', ')}</p>
                <p style={styles.text}><strong>Статус:</strong> {statusLabel[order.status] || order.status}</p>
              </div>
              {order.status !== 'completed' && (
                <button
                  onClick={() => handleDeliver(order.order_id)}
                  style={styles.deliverButton}
                >
                  Заказ доставлен
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

const styles = {
  container: { padding: '40px', fontFamily: 'Arial, sans-serif', color: '#fff' },
  title: { marginBottom: '30px' },
  statsRow: {
    display: 'flex', gap: '15px', marginBottom: '30px', flexWrap: 'wrap',
  },
  statCard: {
    background: '#1a1a1a', border: '1px solid #333', borderRadius: '8px',
    padding: '20px 30px', minWidth: '160px', textAlign: 'center',
  },
  statLabel: { color: '#666', fontSize: '13px', margin: '0 0 8px 0' },
  statValue: { margin: 0, fontSize: '22px', fontWeight: 'bold', color: '#fff' },
  rating: { color: '#fbbf24' },
  earnings: { color: '#86efac' },
  noData: { color: '#444', fontSize: '14px' },
  hint: { color: '#aaa' },
  error: { color: '#ff4d4d', marginBottom: '15px' },
  list: { display: 'flex', flexDirection: 'column', gap: '15px' },
  orderCard: {
    background: '#1a1a1a', border: '1px solid #333', padding: '20px',
    borderRadius: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
  },
  orderTitle: { margin: '0 0 10px 0' },
  text: { margin: '5px 0', color: '#ccc' },
  deliverButton: {
    background: '#2e7d32', color: 'white', border: 'none',
    padding: '10px 15px', borderRadius: '5px', cursor: 'pointer',
    fontWeight: 'bold', whiteSpace: 'nowrap',
  },
}