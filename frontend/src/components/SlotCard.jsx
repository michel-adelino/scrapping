function SlotCard({ item }) {
  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A'
    try {
      const dateParts = dateStr.split('-')
      const date = new Date(
        parseInt(dateParts[0], 10),
        parseInt(dateParts[1], 10) - 1,
        parseInt(dateParts[2], 10)
      )
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      })
    } catch (err) {
      return dateStr
    }
  }

  const getStatusClass = (status) => {
    const statusValue = (status || '').toLowerCase()
    if (statusValue.includes('few')) return 'few-left'
    if (statusValue.includes('unavailable') || statusValue.includes('full')) return 'unavailable'
    return 'available'
  }

  const handleClick = (e) => {
    if (item.booking_url) {
      window.open(item.booking_url, '_blank', 'noopener,noreferrer')
    }
  }

  return (
    <div
      className={`slot-card ${item.booking_url ? '' : ''}`}
      onClick={item.booking_url ? handleClick : undefined}
      style={{ cursor: item.booking_url ? 'pointer' : 'default' }}
      role={item.booking_url ? 'button' : undefined}
      tabIndex={item.booking_url ? 0 : undefined}
      onKeyDown={(e) => {
        if (item.booking_url && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault()
          handleClick(e)
        }
      }}
    >
      <div className="slot-time">{item.time || '-'}</div>
      <div className="slot-date">{formatDate(item.date)}</div>
      <div className="slot-price">{item.price || '-'}</div>
      <div className={`slot-status ${getStatusClass(item.status)}`}>
        {item.status || '-'}
      </div>
      {item.booking_url && (
        <div style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '4px' }}>
          Click to book →
        </div>
      )}
    </div>
  )
}

export default SlotCard

