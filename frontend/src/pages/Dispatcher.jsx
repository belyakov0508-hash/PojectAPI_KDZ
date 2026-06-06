import { useState } from 'react'
import api from '../api'

export default function Dispatcher() {
  const [couriersFile, setCouriersFile] = useState(null)
  const [ordersFile, setOrdersFile] = useState(null)

  const [couriersStatus, setCouriersStatus] = useState(null)
  const [ordersStatus, setOrdersStatus] = useState(null)

  const [couriersLoading, setCouriersLoading] = useState(false)
  const [ordersLoading, setOrdersLoading] = useState(false)

  const handleUpload = async (endpoint, file, setStatus, setLoading) => {
    if (!file) {
      setStatus({ type: 'error', message: 'Выберите файл перед отправкой!' })
      return
    }

    if (!file.name.endsWith('.json')) {
      setStatus({ type: 'error', message: 'Файл должен быть в формате .json' })
      return
    }

    const formData = new FormData()
    formData.append('file', file)
    setLoading(true)
    setStatus(null)

    try {
      const response = await api.post(endpoint, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setStatus({ type: 'success', message: response.data.message || 'Файл успешно загружен!' })
    } catch (error) {
      const status = error.response?.status

      if (status === 400) {
        const detail = error.response.data?.detail
        if (Array.isArray(detail)) {
          const messages = detail.map(d => `• ${d.loc?.join(' → ')}: ${d.msg}`).join('\n')
          setStatus({ type: 'error', message: `Ошибка валидации:\n${messages}` })
        } else {
          setStatus({ type: 'error', message: `Ошибка 400: ${detail || 'Неверный формат данных'}` })
        }
      } else if (status === 422) {
        setStatus({ type: 'error', message: 'Ошибка 422: Файл содержит неверную структуру JSON' })
      } else if (status === 500) {
        setStatus({ type: 'error', message: 'Ошибка сервера — проверьте структуру JSON файла' })
      } else if (!error.response) {
        setStatus({ type: 'error', message: 'Нет связи с сервером' })
      } else {
        setStatus({ type: 'error', message: error.response.data?.detail || 'Неизвестная ошибка' })
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Панель Диспетчера</h1>

      <div style={styles.cardContainer}>

        {/* Карточка курьеров */}
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Загрузка JSON курьеров</h3>
          <p style={styles.hint}>Ожидаемые поля:</p>
          <ul style={styles.hintList}>
            <li>courier_id — ID курьера</li>
            <li>courier_type_id — тип (1=пеший, 2=велосипед, 3=авто)</li>
            <li>working_hours — часы работы, например ["09:00-18:00"]</li>
            <li>regions — список регионов, например [1, 2]</li>
            <li>email — почта для входа курьера</li>
            <li>password — пароль для входа курьера</li>
          </ul>
          <input
            type="file"
            accept=".json"
            onChange={(e) => { setCouriersFile(e.target.files[0]); setCouriersStatus(null) }}
            style={styles.fileInput}
          />
          {couriersFile && <p style={styles.fileName}>📄 {couriersFile.name}</p>}
          {couriersStatus && (
            <div style={{ ...styles.statusBox, ...(couriersStatus.type === 'success' ? styles.success : styles.error) }}>
              {couriersStatus.message}
            </div>
          )}
          <button
            onClick={() => handleUpload('/api/monitoring/upload-couriers', couriersFile, setCouriersStatus, setCouriersLoading)}
            style={{ ...styles.button, opacity: couriersLoading ? 0.6 : 1 }}
            disabled={couriersLoading}
          >
            {couriersLoading ? 'Загрузка...' : 'Загрузить курьеров'}
          </button>
        </div>

        {/* Карточка заказов */}
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Загрузка JSON заказов</h3>
          <p style={styles.hint}>Ожидаемые поля:</p>
          <ul style={styles.hintList}>
            <li>order_id — ID заказа</li>
            <li>weight — вес (от 0.01 до 50.00 кг)</li>
            <li>region — регион доставки</li>
            <li>delivery_hours — часы доставки, например ["10:00-14:00"]</li>
          </ul>
          <input
            type="file"
            accept=".json"
            onChange={(e) => { setOrdersFile(e.target.files[0]); setOrdersStatus(null) }}
            style={styles.fileInput}
          />
          {ordersFile && <p style={styles.fileName}>📄 {ordersFile.name}</p>}
          {ordersStatus && (
            <div style={{ ...styles.statusBox, ...(ordersStatus.type === 'success' ? styles.success : styles.error) }}>
              {ordersStatus.message}
            </div>
          )}
          <button
            onClick={() => handleUpload('/api/dispatcher/upload-orders', ordersFile, setOrdersStatus, setOrdersLoading)}
            style={{ ...styles.button, opacity: ordersLoading ? 0.6 : 1 }}
            disabled={ordersLoading}
          >
            {ordersLoading ? 'Загрузка...' : 'Загрузить заказы'}
          </button>
        </div>

      </div>
    </div>
  )
}

const styles = {
  container: { padding: '40px', fontFamily: 'Arial, sans-serif', color: '#fff' },
  title: { marginBottom: '30px' },
  cardContainer: { display: 'flex', gap: '20px', flexWrap: 'wrap' },
  card: { background: '#1a1a1a', padding: '25px', borderRadius: '8px', border: '1px solid #333', width: '320px' },
  cardTitle: { marginTop: 0, marginBottom: '8px' },
  hint: { color: '#666', fontSize: '12px', marginBottom: '4px', marginTop: 0 },
  hintList: { color: '#666', fontSize: '12px', marginTop: 0, marginBottom: '15px', paddingLeft: '18px', lineHeight: '1.8' },
  fileInput: { display: 'block', marginBottom: '10px', color: '#ccc' },
  fileName: { color: '#aaa', fontSize: '13px', marginBottom: '10px' },
  statusBox: { padding: '10px', borderRadius: '6px', fontSize: '13px', marginBottom: '12px', whiteSpace: 'pre-line' },
  success: { background: '#1b3a1f', border: '1px solid #2e7d32', color: '#81c784' },
  error: { background: '#3a1b1b', border: '1px solid #c62828', color: '#ef9a9a' },
  button: { background: '#646cff', color: 'white', padding: '10px 15px', border: 'none', borderRadius: '5px', cursor: 'pointer', fontWeight: 'bold', width: '100%' }
}