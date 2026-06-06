import { useEffect, useState } from 'react'
import api from '../api'

const WEIGHT_LIMIT = { 1: 10, 2: 15, 3: 50 }
const TYPE_LABEL = { 1: '🚶 Пеший', 2: '🚲 Велокурьер', 3: '🚗 Автокурьер' }

export default function CourierOrders() {
  const [orders, setOrders] = useState([])
  const [couriers, setCouriers] = useState([])
  const [selectedOrder, setSelectedOrder] = useState(null)
  const [selectedCourier, setSelectedCourier] = useState(null)
  const [loadingOrders, setLoadingOrders] = useState(true)
  const [loadingCouriers, setLoadingCouriers] = useState(false)
  const [assigning, setAssigning] = useState(false)
  const [error, setError] = useState('')
  const [successMsg, setSuccessMsg] = useState('')

  const fetchOrders = async () => {
    try {
      setLoadingOrders(true)
      setError('')
      const res = await api.get('/api/monitoring/available-orders')
      setOrders(res.data)
    } catch {
      setError('Не удалось загрузить заказы')
    } finally {
      setLoadingOrders(false)
    }
  }

  useEffect(() => { fetchOrders() }, [])

  const handleSelectOrder = async (order) => {
    setSelectedOrder(order)
    setSelectedCourier(null)
    setCouriers([])
    setSuccessMsg('')
    setError('')
    try {
      setLoadingCouriers(true)
      const res = await api.get(`/api/monitoring/available-couriers?weight=${order.weight}`)
      setCouriers(res.data)
    } catch {
      setError('Не удалось загрузить курьеров')
    } finally {
      setLoadingCouriers(false)
    }
  }

  const handleAssign = async () => {
    if (!selectedOrder || !selectedCourier) return
    try {
      setAssigning(true)
      setError('')
      await api.request(
        'PATCH',
        `/api/orders/${selectedOrder.order_id}/assign?courier_id=${selectedCourier.courier_id}`
      )
      setSuccessMsg(`Заказ #${selectedOrder.order_id} назначен курьеру #${selectedCourier.courier_id}`)
      setSelectedOrder(null)
      setSelectedCourier(null)
      setCouriers([])
      await fetchOrders()
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка при назначении')
    } finally {
      setAssigning(false)
    }
  }

  const canAssign = selectedOrder && selectedCourier

  return (
    <div style={s.page}>
      <div style={s.header}>
        <h1 style={s.title}>Назначение заказов</h1>
        <button onClick={fetchOrders} style={s.refreshBtn}>🔄 Обновить</button>
      </div>

      {error && <div style={s.error}>{error}</div>}
      {successMsg && <div style={s.success}>{successMsg}</div>}

      <div style={s.layout}>

        {/* Левая панель — заказы */}
        <div style={s.panel}>
          <div style={s.panelHeader}>
            <span style={s.panelTitle}>Доступные заказы</span>
            <span style={s.badge}>{orders.length}</span>
          </div>
          {loadingOrders ? (
            <p style={s.hint}>Загрузка...</p>
          ) : orders.length === 0 ? (
            <p style={s.hint}>Нет доступных заказов</p>
          ) : (
            <table style={s.table}>
              <thead>
                <tr style={s.thRow}>
                  <th style={s.th}>ID</th>
                  <th style={s.th}>Вес, кг</th>
                  <th style={s.th}>Регион</th>
                  <th style={s.th}>Часы доставки</th>
                </tr>
              </thead>
              <tbody>
                {orders.map(order => {
                  const isSelected = selectedOrder?.order_id === order.order_id
                  return (
                    <tr
                      key={order.order_id}
                      style={{ ...s.tr, ...(isSelected ? s.trSelected : {}) }}
                      onClick={() => handleSelectOrder(order)}>
                      <td style={s.td}>#{order.order_id}</td>
                      <td style={s.td}>
                        <span style={s.weightBadge}>{order.weight} кг</span>
                      </td>
                      <td style={s.td}>{order.region}</td>
                      <td style={s.td}>{order.delivery_hours.join(', ')}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* Правая панель — курьеры */}
        <div style={s.panel}>
          <div style={s.panelHeader}>
            <span style={s.panelTitle}>
              {selectedOrder
                ? Курьеры для заказа #${selectedOrder.order_id} (${selectedOrder.weight} кг)
                : 'Выберите заказ'}
            </span>
            {couriers.length > 0 && <span style={s.badge}>{couriers.length}</span>}
          </div>

          {!selectedOrder ? (
            <p style={s.hint}>Кликните на заказ слева, чтобы увидеть подходящих курьеров</p>
          ) : loadingCouriers ? (
            <p style={s.hint}>Загрузка курьеров...</p>
          ) : couriers.length === 0 ? (
            <p style={s.hint}>Нет курьеров, способных доставить этот заказ</p>
          ) : (
            <table style={s.table}>
              <thead>
                <tr style={s.thRow}>
                  <th style={s.th}>ID</th>
                  <th style={s.th}>Тип</th>
                  <th style={s.th}>Регионы</th>
                  <th style={s.th}>Рейтинг</th>
                  <th style={s.th}>Зарплата</th>
                </tr>
              </thead>
              <tbody>
                {couriers.map(courier => {
                  const isSelected = selectedCourier?.courier_id === courier.courier_id
                  return (
                    <tr
                      key={courier.courier_id}
                      style={{ ...s.tr, ...(isSelected ? s.trSelected : {}) }}
                      onClick={() => setSelectedCourier(courier)}
                    >
                      <td style={s.td}>#{courier.courier_id}</td>
                      <td style={s.td}>
                        <span style={s.typeBadge}>
                          {TYPE_LABEL[courier.courier_type_id] || courier.courier_type_id}
                        </span>
                      </td>
                      <td style={s.td}>{courier.regions.join(', ') || '—'}</td>
                      <td style={s.td}>
                        {courier.rating !== null
                          ? <span style={s.rating}>★ {courier.rating}</span>
                          : <span style={s.noData}>—</span>}
                      </td>
                      <td style={s.td}>
                        {courier.earnings !== null
                          ? <span style={s.earnings}>{courier.earnings.toLocaleString()} ₸</span>
                          : <span style={s.noData}>—</span>}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}

          {selectedOrder && (
            <div style={s.assignRow}>
              <button
                onClick={handleAssign}
                disabled={!canAssign || assigning}
                style={{ ...s.assignBtn, opacity: canAssign && !assigning ? 1 : 0.4 }}
              >
                {assigning ? 'Назначение...' : '✓ Назначить'}
              </button>
              {selectedCourier && (
                <span style={s.assignHint}>
                  Курьер #{selectedCourier.courier_id} · {TYPE_LABEL[selectedCourier.courier_type_id]}
                  · макс. {WEIGHT_LIMIT[selectedCourier.courier_type_id]} кг
                </span>
              )}
            </div>
          )}
        </div>

      </div>
    </div>
  )
}
const s = {
  page: { padding: '40px', fontFamily: 'Arial, sans-serif', color: '#fff' },
  header: { display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '30px' },
  title: { margin: 0, fontSize: '24px' },
  refreshBtn: { background: '#333', color: '#fff', border: '1px solid #555', padding: '8px 14px', borderRadius: '6px', cursor: 'pointer', fontSize: '14px' },
  error: { background: '#3a1b1b', border: '1px solid #c62828', color: '#ef9a9a', padding: '10px 14px', borderRadius: '6px', marginBottom: '20px', fontSize: '14px' },
  success: { background: '#1b3a1f', border: '1px solid #2e7d32', color: '#81c784', padding: '10px 14px', borderRadius: '6px', marginBottom: '20px', fontSize: '14px' },
  layout: { display: 'flex', gap: '20px', alignItems: 'flex-start' },
  panel: { flex: 1, background: '#1a1a1a', borderRadius: '8px', border: '1px solid #333', overflow: 'hidden', minWidth: 0 },
  panelHeader: { display: 'flex', alignItems: 'center', gap: '10px', padding: '14px 16px', borderBottom: '1px solid #333', background: '#242424' },
  panelTitle: { fontSize: '14px', fontWeight: 'bold', color: '#ccc' },
  badge: { background: '#333', color: '#aaa', fontSize: '12px', padding: '2px 8px', borderRadius: '10px' },
  hint: { color: '#555', fontSize: '13px', padding: '30px 16px', textAlign: 'center', margin: 0 },
  table: { width: '100%', borderCollapse: 'collapse' },
  thRow: { background: '#242424' },
  th: { padding: '10px 14px', textAlign: 'left', fontSize: '12px', color: '#666', borderBottom: '1px solid #2a2a2a', fontWeight: 'normal' },
  tr: { borderBottom: '1px solid #222', cursor: 'pointer', transition: 'background 0.15s' },
  trSelected: { background: '#1e1a2e', outline: '1px solid #646cff' },
  td: { padding: '10px 14px', fontSize: '13px' },
  weightBadge: { background: '#2a2a2a', color: '#ccc', padding: '3px 8px', borderRadius: '4px', fontSize: '12px' },
  typeBadge: { background: '#2a2a4a', color: '#aab4ff', padding: '3px 8px', borderRadius: '4px', fontSize: '12px' },
  rating: { color: '#fbbf24', fontSize: '13px' },
  earnings: { color: '#86efac', fontSize: '13px' },
  noData: { color: '#444' },
  assignRow: { padding: '14px 16px', borderTop: '1px solid #2a2a2a', display: 'flex', alignItems: 'center', gap: '14px' },
  assignBtn: { background: '#646cff', color: '#fff', border: 'none', padding: '10px 20px', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', fontSize: '14px' },
  assignHint: { color: '#666', fontSize: '12px' },
}