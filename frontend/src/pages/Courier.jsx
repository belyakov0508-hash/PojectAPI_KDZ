import { useEffect, useState } from 'react'
import api from '../api'

export default function Courier() {
  const [orders, setOrders] = useState([])

  // Для простоты жестко зашьем ID курьера = 1 (в реальном приложении он берется после логина)
  const courierId = 1

  const fetchOrders = async () => {
    try {
      const response = await api.get(`/api/orders/courier/${courierId}`)
      setOrders(response.data)
    } catch (error) {
      console.error('Ошибка загрузки заказов курьера')
    }
  }

  useEffect(() => {
    fetchOrders()
  }, [])

  const handleDeliver = async (orderId) => {
    try {
      // Бьем по эндпоинту смены статуса заказа
      await api.post(`/api/orders/${orderId}/complete`)
      alert('Статус обновлен: Заказ доставлен!')
      fetchOrders() // Перезагружаем список, чтобы увидеть изменения
    } catch (error) {
      alert('Не удалось обновить статус заказа')
    }
  }

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Мои заказы (Курьер #{courierId})</h1>
      <div style={styles.list}>
        {orders.length === 0 ? (
          <p style={{color: '#aaa'}}>У вас нет активных заказов на доставку.</p>
        ) : (
          orders.map((order) => (
            <div key={order.order_id} style={styles.orderCard}>
              <div>
                <h3>Заказ №{order.order_id}</h3>
                <p style={styles.text}><strong>Товар:</strong> {order.brand} {order.product_name}</p>
                <p style={styles.text}><strong>Регион:</strong> {order.region}</p>
                <p style={styles.text}><strong>Вес:</strong> {order.weight} кг</p>
                <p style={styles.text}><strong>Статус:</strong> {order.status}</p>
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
          ))
        )}
      </div>
    </div>
  )
}

const styles = {
  container: { padding: '40px', fontFamily: 'Arial, sans-serif', color: '#fff' },
  title: { marginBottom: '30px' },
  list: { display: 'flex', flexDirection: 'column', gap: '15px' },
  orderCard: { background: '#1a1a1a', border: '1px solid #333', padding: '20px', borderRadius: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  text: { margin: '5px 0', color: '#ccc' },
  deliverButton: { background: '#2e7d32', color: 'white', border: 'none', padding: '10px 15px', borderRadius: '5px', cursor: 'pointer', fontWeight: 'bold' }
}