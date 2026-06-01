import { useState } from 'react'
import api from '../api'

export default function Dispatcher() {
  const [couriersFile, setCouriersFile] = useState(null)
  const [ordersFile, setOrdersFile] = useState(null)

  const handleUpload = async (e, endpoint, file) => {
    e.preventDefault()
    if (!file) return alert('Выберите файл перед отправкой!')

    // Файлы на бэкенд передаются через специальный объект FormData
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await api.post(endpoint, formData, {
        headers: {
          'Content-Type': 'multipart/form-data', // Axios поймет, что это файл
        },
      })
      alert(response.data.message || 'Файл успешно загружен!')
    } catch (error) {
      alert(error.response?.data?.detail || 'Ошибка при загрузке файла')
    }
  }

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Панель Диспетчера</h1>

      <div style={styles.cardContainer}>
        {/* Форма для курьеров */}
        <div style={styles.card}>
          <h3>Загрузка JSON курьеров</h3>
          <input
            type="file"
            accept=".json"
            onChange={(e) => setCouriersFile(e.target.files[0])}
            style={styles.fileInput}
          />
          <button
            onClick={(e) => handleUpload(e, '/api/monitoring/upload-couriers', couriersFile)}
            style={styles.button}
          >
            Загрузить курьеров
          </button>
        </div>

        {/* Форма для заказов */}
        <div style={styles.card}>
          <h3>Загрузка JSON заказов</h3>
          <input
            type="file"
            accept=".json"
            onChange={(e) => setOrdersFile(e.target.files[0])}
            style={styles.fileInput}
          />
          <button
            onClick={(e) => handleUpload(e, '/api/dispatcher/upload-orders', ordersFile)}
            style={styles.button}
          >
            Загрузить заказы
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
  card: { background: '#1a1a1a', padding: '25px', borderRadius: '8px', border: '1px solid #333', width: '300px' },
  fileInput: { display: 'block', marginBottom: '20px', color: '#ccc' },
  button: { background: '#646cff', color: 'white', padding: '10px 15px', border: 'none', borderRadius: '5px', cursor: 'pointer', fontWeight: 'bold' }
}