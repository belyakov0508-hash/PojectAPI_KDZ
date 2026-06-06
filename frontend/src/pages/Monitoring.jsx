import { useEffect, useState } from 'react'
import api from '../api'

export default function Monitoring() {
  const [couriers, setCouriers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchCouriers = async () => {
    try {
      setLoading(true)
      const response = await api.get('/api/monitoring/couriers')
      setCouriers(response.data)
    } catch (err) {
      setError('Не удалось загрузить список курьеров')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCouriers()
    const interval = setInterval(fetchCouriers, 10000)
    return () => clearInterval(interval)
  }, [])

  const typeLabel = {
    1: '🚶 Пеший',
    2: '🚲 Велокурьер',
    3: '🚗 Автокурьер',
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>Мониторинг курьеров</h1>
        <button onClick={fetchCouriers} style={styles.refreshBtn}>🔄 Обновить</button>
      </div>

      {error && <p style={styles.error}>{error}</p>}

      {loading ? (
        <p style={styles.hint}>Загрузка...</p>
      ) : (
        <table style={styles.table}>
          <thead>
            <tr style={styles.thRow}>
              <th style={styles.th}>ID</th>
              <th style={styles.th}>Тип курьера</th>
              <th style={styles.th}>Регионы</th>
              <th style={styles.th}>Рабочие часы</th>
              <th style={styles.th}>Email</th>
              <th style={styles.th}>Пароль</th>
            </tr>
          </thead>
          <tbody>
            {couriers.length === 0 ? (
              <tr>
                <td colSpan="6" style={styles.empty}>Курьеры не найдены</td>
              </tr>
            ) : (
              couriers.map((courier) => (
                <tr key={courier.courier_id} style={styles.tr}>
                  <td style={styles.td}>#{courier.courier_id}</td>
                  <td style={styles.td}>
                    <span style={styles.typeBadge}>
                      {typeLabel[courier.courier_type_id] || courier.courier_type_id}
                    </span>
                  </td>
                  <td style={styles.td}>
                    {courier.regions && courier.regions.length > 0
                      ? courier.regions.map(r => r.region).join(', ')
                      : '—'}
                  </td>
                  <td style={styles.td}>
                    {courier.working_hours && courier.working_hours.join(', ')}
                  </td>
                  <td style={styles.td}>{courier.email || '—'}</td>
                  <td style={styles.td}>
                    <span style={styles.password}>{courier.password || '—'}</span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      )}
    </div>
  )
}

const styles = {
  container: { padding: '40px', fontFamily: 'Arial, sans-serif', color: '#fff' },
  header: { display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '30px' },
  title: { margin: 0 },
  refreshBtn: {
    background: '#333', color: '#fff', border: '1px solid #555',
    padding: '8px 14px', borderRadius: '6px', cursor: 'pointer', fontSize: '14px'
  },
  error: { color: '#ff4d4d', marginBottom: '15px' },
  hint: { color: '#aaa' },
  table: { width: '100%', borderCollapse: 'collapse', background: '#1a1a1a', borderRadius: '8px', overflow: 'hidden' },
  thRow: { background: '#242424' },
  th: { padding: '12px 15px', textAlign: 'left', borderBottom: '1px solid #333', color: '#aaa' },
  tr: { borderBottom: '1px solid #222' },
  td: { padding: '12px 15px' },
  empty: { textAlign: 'center', padding: '20px', color: '#aaa' },
  typeBadge: {
    background: '#2a2a4a', color: '#aab4ff',
    padding: '4px 10px', borderRadius: '4px', fontSize: '13px'
  },
  password: {
    background: '#2a2a2a', color: '#aaa',
    padding: '4px 10px', borderRadius: '4px', fontSize: '13px',
    fontFamily: 'monospace'
  }
}