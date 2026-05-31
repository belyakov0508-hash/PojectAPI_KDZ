import { useEffect, useState } from 'react'
import api from '../api'

export default function Monitoring() {
  const [couriers, setCouriers] = useState([])

  // useEffect выполняет код ОДИН РАЗ автоматически при открытии вкладки Мониторинг
  useEffect(() => {
    const fetchCouriers = async () => {
      try {
        const response = await api.get('/api/monitoring/couriers')
        setCouriers(response.data) // Записываем массив курьеров из БД в состояние
      } catch (error) {
        console.error('Не удалось загрузить курьеров', error)
      }
    }
    fetchCouriers()
  }, [])

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Мониторинг курьеров</h1>
      <table style={styles.table}>
        <thead>
          <tr style={styles.thRow}>
            <th style={styles.th}>ID</th>
            <th style={styles.th}>Имя курьера</th>
            <th style={styles.th}>Текущий статус</th>
          </tr>
        </thead>
        <tbody>
          {couriers.length === 0 ? (
            <tr><td colSpan="3" style={{textAlign: 'center', padding: '20px', color: '#aaa'}}>Курьеры не найдены</td></tr>
          ) : (
            couriers.map((courier) => (
              <tr key={courier.id} style={styles.tr}>
                <td style={styles.td}>{courier.id}</td>
                <td style={styles.td}>{courier.name}</td>
                <td style={styles.td}>
                  <span style={{
                    ...styles.statusBadge,
                    backgroundColor: courier.status === 'active' ? '#2e7d32' : '#c62828'
                  }}>
                    {courier.status}
                  </span>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}

const styles = {
  container: { padding: '40px', fontFamily: 'Arial, sans-serif', color: '#fff' },
  title: { marginBottom: '30px' },
  table: { width: '100%', borderCollapse: 'collapse', background: '#1a1a1a', borderRadius: '8px', overflow: 'hidden' },
  thRow: { background: '#242424' },
  th: { padding: '12px 15px', textAlign: 'left', borderBottom: '1px solid #333', color: '#aaa' },
  tr: { borderBottom: '1px solid #222' },
  td: { padding: '12px 15px' },
  statusBadge: { padding: '4px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: 'bold' }
}