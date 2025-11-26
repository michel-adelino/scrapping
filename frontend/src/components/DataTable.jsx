function DataTable({ data }) {
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

  const formatTime = (timestamp) => {
    if (!timestamp) return 'N/A'
    try {
      const ts = new Date(timestamp)
      return ts.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    } catch (err) {
      return 'N/A'
    }
  }

  const getStatusClass = (status) => {
    const statusValue = (status || '').toLowerCase()
    if (statusValue.includes('few')) return 'status-few-left'
    if (statusValue.includes('unavailable') || statusValue.includes('full')) return 'status-unavailable'
    return 'status-available'
  }

  const handleBookingClick = (url) => {
    if (url) {
      window.open(url, '_blank', 'noopener,noreferrer')
    }
  }

  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Website</th>
          <th>Date</th>
          <th>Time</th>
          <th>Price/Length</th>
          <th>Status</th>
          <th>Found At</th>
          <th>Booking</th>
        </tr>
      </thead>
      <tbody>
        {data.map((item, idx) => {
          const venueName = item.venue_name || item.website || '-'
          return (
            <tr key={idx}>
              <td className="website-cell">{venueName}</td>
              <td>{formatDate(item.date)}</td>
              <td>{item.time || '-'}</td>
              <td className="price-cell">{item.price || '-'}</td>
              <td className={getStatusClass(item.status)}>{item.status || '-'}</td>
              <td>{formatTime(item.timestamp)}</td>
              <td>
                {item.booking_url ? (
                  <button
                    className="booking-btn"
                    onClick={() => handleBookingClick(item.booking_url)}
                    type="button"
                    title="Open booking page in new tab"
                  >
                    <span className="booking-btn-text">Book Now</span>
                    <span className="booking-btn-icon">→</span>
                  </button>
                ) : (
                  <span className="no-booking">-</span>
                )}
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}

export default DataTable

