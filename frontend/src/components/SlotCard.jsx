import { formatPrice } from '../utils/currencyFormatting'

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

  // Normalize time format to consistent style (e.g., "1:00 PM")
  const normalizeTime = (timeStr) => {
    if (!timeStr || timeStr === '-') return '-'
    
    // Try to parse various time formats and convert to "H:MM AM/PM" format
    try {
      // Remove extra spaces and normalize
      let normalized = timeStr.trim()
      
      // First, try to handle 24-hour format (e.g., "13:00", "09:00", "23:30")
      const twentyFourHourPattern = /^(\d{1,2}):(\d{2})$/
      let match = normalized.match(twentyFourHourPattern)
      
      if (match) {
        let hours24 = parseInt(match[1], 10)
        const minutes = match[2]
        
        // Convert 24-hour to 12-hour format
        if (hours24 === 0) {
          return `12:${minutes} AM`
        } else if (hours24 === 12) {
          return `12:${minutes} PM`
        } else if (hours24 < 12) {
          return `${hours24}:${minutes} AM`
        } else {
          return `${hours24 - 12}:${minutes} PM`
        }
      }
      
      // Handle formats like "01:00PM", "1:00PM", "1:00 pm", "01:00 pm", "1:00PM", etc.
      // Match pattern: optional leading zero, hours, colon, minutes, optional space, AM/PM
      const timePattern = /(\d{1,2}):(\d{2})\s*(AM|PM|am|pm|a\.m\.|p\.m\.|A\.M\.|P\.M\.)/i
      match = normalized.match(timePattern)
      
      if (match) {
        let hours = parseInt(match[1], 10)
        const minutes = match[2]
        let ampm = match[3].toUpperCase()
        
        // Normalize AM/PM format (remove periods)
        ampm = ampm.replace(/\./g, '')
        
        // Format as "H:MM AM/PM" (no leading zero on hour)
        return `${hours}:${minutes} ${ampm}`
      }
      
      // Try pattern without colon (e.g., "100PM", "100 PM")
      const noColonPattern = /(\d{1,2})(\d{2})\s*(AM|PM|am|pm|a\.m\.|p\.m\.|A\.M\.|P\.M\.)/i
      match = normalized.match(noColonPattern)
      if (match) {
        let hours = parseInt(match[1], 10)
        const minutes = match[2]
        let ampm = match[3].toUpperCase().replace(/\./g, '')
        return `${hours}:${minutes} ${ampm}`
      }
      
      // If no match, return as-is (might already be in correct format)
      return normalized
    } catch (e) {
      return timeStr
    }
  }

  const normalizedTime = normalizeTime(item.time)

  return (
    <div
      className={`slot-card ${item.booking_url ? 'slot-card-clickable' : ''}`}
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
      <div className="slot-time">{normalizedTime}</div>
      {item.price && item.price !== '-' && (
        <div className="slot-price">{formatPrice(item.price)}</div>
      )}
      <div className={`slot-status ${getStatusClass(item.status)}`}>
        {item.status || 'Available'}
      </div>
      {item.booking_url && (
        <div className="slot-book-hint">Click to book</div>
      )}
    </div>
  )
}

export default SlotCard

