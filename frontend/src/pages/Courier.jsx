import { useEffect, useState } from 'react'
import api from '../api'

export default function Courier() {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Достаём courier_id из JWT токена
  const token = localStorage.getItem('token')
  const decoded = JSON.parse(atob(token.split('.')[1]))
  const courierId = decoded.courier_id

  const fetchOrders = async () => {
    try {
      setLoading(true)
      const response = await api.get(`/api/orders/courier/${courierId}`)
      setOrders(response.data)
    } catch (err) {
      setError('Ошибка загрузки заказов')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchOrders()
  }, [])

  const handleDeliver = async (orderId) => {
    try {
      await api.post(`/api/orders/${orderId}/complete`)
      fetchOrders()
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
  container: {
    padding: '40px',
    fontFamily: 'Arial, sans-serif',
    color: '#fff',
  },
  title: {
    marginBottom: '30px',
  },
  hint: {
    color: '#aaa',
  },
  error: {
    color: '#ff4d4d',
    marginBottom: '15px',
  },
  list: {
    display: 'flex',
    flexDirection: 'column',
    gap: '15px',
  },
  orderCard: {
    background: '#1a1a1a',
    border: '1px solid #333',
    padding: '20px',
    borderRadius: '8px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  orderTitle: {
    margin: '0 0 10px 0',
  },
  text: {
    margin: '5px 0',
    color: '#ccc',
  },
  deliverButton: {
    background: '#2e7d32',
    color: 'white',
    border: 'none',
    padding: '10px 15px',
    borderRadius: '5px',
    cursor: 'pointer',
    fontWeight: 'bold',
    whiteSpace: 'nowrap',
  },
}