import { useMemo, useState, useEffect } from 'react'
import SlotCard from './SlotCard'
import DataTable from './DataTable'
import VenueCard from './VenueCard'
import { formatVenueName, isLawnClubVenue, getLawnClubActivities } from '../utils/venueFormatting'
import { getVenueMetadata } from '../data/venueMetadata'

function DataSection({ data, isMultiVenueMode, isLoading = false }) {
  const [selectedVenue, setSelectedVenue] = useState(null)

  // Reset selected venue when data changes (new search)
  useEffect(() => {
    setSelectedVenue(null)
  }, [data])

  // Extract city from data (assume all items have same city)
  const city = data.length > 0 ? (data[0]?.city || null) : null

  // Group venues and calculate slot counts for list view
  const venueSummary = useMemo(() => {
    const grouped = {}
    data.forEach(item => {
      const venueName = item.venue_name || item.website || 'Unknown Venue'
      if (!grouped[venueName]) {
        grouped[venueName] = 0
      }
      grouped[venueName]++
    })
    
    return Object.entries(grouped)
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([venueName, slotCount]) => ({ venueName, slotCount }))
  }, [data])

  // Filter data for selected venue in detail view
  const selectedVenueData = useMemo(() => {
    if (!selectedVenue) return []
    return data.filter(item => {
      const venueName = item.venue_name || item.website || 'Unknown Venue'
      return venueName === selectedVenue
    })
  }, [data, selectedVenue])

  const handleVenueClick = (venueName) => {
    setSelectedVenue(venueName)
  }

  const handleBackClick = () => {
    setSelectedVenue(null)
  }

  return (
    <div className="data-section">
      <div className="data-header">
        {selectedVenue ? (
          <div className="data-header-with-back">
            <button 
              className="back-button"
              onClick={handleBackClick}
              type="button"
              aria-label="Back to venues"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M19 12H5" />
                <path d="M12 19l-7-7 7-7" />
              </svg>
            </button>
            <div className="data-title">{selectedVenue}</div>
          </div>
        ) : (
          <div className="data-title">Live Availability</div>
        )}
      </div>

      <div className="auto-scroll">
        {isLoading && (
          <div className="loading-overlay">
            <div className="spinner"></div>
          </div>
        )}
        {data.length === 0 ? (
          <div className="no-data">
            No data available. Use the search panel to find available slots.
          </div>
        ) : isMultiVenueMode && !selectedVenue ? (
          <VenueList venues={venueSummary} onVenueClick={handleVenueClick} city={city} />
        ) : isMultiVenueMode && selectedVenue ? (
          <VenueDetail data={selectedVenueData} venueName={selectedVenue} city={city} />
        ) : (
          <DataTable data={data} />
        )}
      </div>
    </div>
  )
}


// Venue list view - shows grid of venue cards
function VenueList({ venues, onVenueClick, city }) {
  return (
    <div className="venue-list-grid">
      {venues.map(({ venueName, slotCount }) => (
        <VenueCard
          key={venueName}
          venueName={venueName}
          slotCount={slotCount}
          city={city}
          onClick={() => onVenueClick(venueName)}
        />
      ))}
    </div>
  )
}

// Venue detail view - shows slots for selected venue
function VenueDetail({ data, venueName, city = null }) {
  // Format venue name and get metadata
  const formattedName = formatVenueName(venueName, city)
  const metadata = getVenueMetadata(venueName)
  const description = metadata?.description || ''
  const isLawnClub = isLawnClubVenue(venueName)
  const activities = isLawnClub ? getLawnClubActivities(venueName) : []
  const groupedByDate = useMemo(() => {
    const grouped = {}
    data.forEach(item => {
      const date = item.date || 'Unknown Date'
      if (!grouped[date]) {
        grouped[date] = []
      }
      grouped[date].push(item)
    })
    
    // Helper function to parse time string to minutes since midnight
    const parseTimeToMinutes = (timeStr) => {
      if (!timeStr) return 0
      const match = timeStr.match(/(\d{1,2}):(\d{2})\s*(AM|PM)/i)
      if (!match) return 0
      
      let hours = parseInt(match[1], 10)
      const minutes = parseInt(match[2], 10)
      const period = match[3].toUpperCase()
      
      // Convert to 24-hour format
      if (period === 'PM' && hours !== 12) {
        hours += 12
      } else if (period === 'AM' && hours === 12) {
        hours = 0
      }
      
      return hours * 60 + minutes
    }
    
    return Object.entries(grouped)
      .sort((a, b) => new Date(a[0]) - new Date(b[0])) // Sort dates ascending
      .map(([date, slots]) => ({
        date,
        slots: slots.sort((a, b) => {
          const timeA = parseTimeToMinutes(a.time || '')
          const timeB = parseTimeToMinutes(b.time || '')
          return timeA - timeB
        })
      }))
  }, [data])

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Unknown Date'
    try {
      const dateParts = dateStr.split('-')
      const date = new Date(
        parseInt(dateParts[0], 10),
        parseInt(dateParts[1], 10) - 1,
        parseInt(dateParts[2], 10)
      )
      return date.toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      })
    } catch (err) {
      return dateStr
    }
  }

  const formatDateHeader = (dateStr) => {
    if (!dateStr) return { weekday: '', date: 'Unknown' }
    try {
      const dateParts = dateStr.split('-')
      const date = new Date(
        parseInt(dateParts[0], 10),
        parseInt(dateParts[1], 10) - 1,
        parseInt(dateParts[2], 10)
      )
      return {
        weekday: date.toLocaleDateString('en-US', { weekday: 'long' }),
        date: date.toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric'
        })
      }
    } catch (err) {
      return { weekday: '', date: dateStr }
    }
  }

  if (data.length === 0) {
    return (
      <div className="venue-detail-empty">
        <p>No available slots found for this venue.</p>
      </div>
    )
  }

  return (
    <div className="venue-detail-container">
      <div className="venue-detail-header">
        {/* <div className="venue-detail-name">{formattedName}</div> */}
        {isLawnClub && activities.length > 0 && (
          <div className="venue-detail-activities">
            {activities.join(', ')}
          </div>
        )}
        {description && (
          <div className="venue-detail-description">{description}</div>
        )}
      </div>
      <div className="venue-detail-content">
        {groupedByDate.map(({ date, slots }) => {
          const dateInfo = formatDateHeader(date)
          return (
            <div key={date} className="venue-date-section">
              <div className="venue-date-header">
                <div className="venue-date-weekday">{dateInfo.weekday}</div>
                <div className="venue-date-full">{dateInfo.date}</div>
                <div className="venue-date-count">{slots.length} {slots.length === 1 ? 'slot' : 'slots'}</div>
              </div>
              <div className="venue-slots-grid">
                {slots.map((item, idx) => (
                  <SlotCard key={`${venueName}-${date}-${idx}`} item={item} />
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default DataSection

