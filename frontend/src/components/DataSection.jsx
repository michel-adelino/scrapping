import { useMemo, useState, useEffect } from 'react'
import SlotCard from './SlotCard'
import DataTable from './DataTable'
import VenueCard from './VenueCard'

function DataSection({ data, isMultiVenueMode }) {
  const [selectedVenue, setSelectedVenue] = useState(null)

  // Reset selected venue when data changes (new search)
  useEffect(() => {
    setSelectedVenue(null)
  }, [data])

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
        {data.length === 0 ? (
          <div className="no-data">
            No data available. Use the search panel to find available slots.
          </div>
        ) : isMultiVenueMode && !selectedVenue ? (
          <VenueList venues={venueSummary} onVenueClick={handleVenueClick} />
        ) : isMultiVenueMode && selectedVenue ? (
          <VenueDetail data={selectedVenueData} venueName={selectedVenue} />
        ) : (
          <DataTable data={data} />
        )}
      </div>
    </div>
  )
}


// Venue list view - shows grid of venue cards
function VenueList({ venues, onVenueClick }) {
  return (
    <div className="venue-list-grid">
      {venues.map(({ venueName, slotCount }) => (
        <VenueCard
          key={venueName}
          venueName={venueName}
          slotCount={slotCount}
          onClick={() => onVenueClick(venueName)}
        />
      ))}
    </div>
  )
}

// Venue detail view - shows slots for selected venue
function VenueDetail({ data, venueName }) {
  const groupedByDate = useMemo(() => {
    const grouped = {}
    data.forEach(item => {
      const date = item.date || 'Unknown Date'
      if (!grouped[date]) {
        grouped[date] = []
      }
      grouped[date].push(item)
    })
    
    return Object.entries(grouped)
      .sort((a, b) => new Date(a[0]) - new Date(b[0])) // Sort dates ascending
      .map(([date, slots]) => ({
        date,
        slots: slots.sort((a, b) => (a.time || '').localeCompare(b.time || '')) // Sort slots by time
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

  return (
    <div className="venue-detail-container">
      <div className="venue-slots">
        {groupedByDate.map(({ date, slots }) => (
          <div key={date} className="venue-date-group">
            <div className="date-divider-text-inline">{formatDate(date)}</div>
            {slots.map((item, idx) => (
              <SlotCard key={`${venueName}-${date}-${idx}`} item={item} />
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

export default DataSection

