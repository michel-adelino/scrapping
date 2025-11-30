import { useMemo } from 'react'
import SlotCard from './SlotCard'
import DataTable from './DataTable'

function DataSection({ data, searchTerm, onSearchChange, isMultiVenueMode, autoRefresh, onAutoRefreshChange }) {
  const filteredData = useMemo(() => {
    if (!searchTerm) return data
    
    return data.filter(item => {
      const haystack = [
        item.venue_name || item.website,
        item.date,
        item.time,
        item.price,
        item.status
      ].map(part => (part || '').toString().toLowerCase()).join(' ')
      return haystack.includes(searchTerm.toLowerCase())
    })
  }, [data, searchTerm])

  return (
    <div className="data-section">
      <div className="data-header">
        <div className="data-title">Live Availability Data</div>
        <div className="data-actions">
          <label>
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => onAutoRefreshChange(e.target.checked)}
            />
            {' '}Auto-refresh
          </label>
          <div className="data-search">
            <span>🔎</span>
            <input
              type="text"
              placeholder="Search results..."
              aria-label="Search results"
              value={searchTerm}
              onChange={(e) => onSearchChange(e.target.value)}
            />
          </div>
        </div>
      </div>

      <div className="auto-scroll">
        {filteredData.length === 0 ? (
          <div className="no-data">
            {data.length === 0
              ? 'No data available. Start scraping to see live results.'
              : 'No matching results. Try a different search.'}
          </div>
        ) : isMultiVenueMode ? (
          <VenueRows data={filteredData} />
        ) : (
          <DataTable data={filteredData} />
        )}
      </div>
    </div>
  )
}

function VenueRows({ data }) {
  const groupedByDateAndVenue = useMemo(() => {
    // Group by date first, then by venue
    const grouped = {}
    data.forEach(item => {
      const date = item.date || 'Unknown Date'
      const venueName = item.venue_name || item.website || 'Unknown Venue'
      
      if (!grouped[date]) {
        grouped[date] = {}
      }
      if (!grouped[date][venueName]) {
        grouped[date][venueName] = []
      }
      grouped[date][venueName].push(item)
    })
    
    // Convert to array format: [{ date, venues: [{ venueName, slots: [] }] }]
    return Object.entries(grouped)
      .sort((a, b) => new Date(b[0]) - new Date(a[0])) // Sort dates descending (newest first)
      .map(([date, venues]) => ({
        date,
        venues: Object.entries(venues)
          .sort((a, b) => a[0].localeCompare(b[0])) // Sort venues alphabetically
          .map(([venueName, slots]) => ({
            venueName,
            slots: slots.sort((a, b) => (a.time || '').localeCompare(b.time || '')) // Sort slots by time
          }))
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
    <div className="venue-rows-container">
      {groupedByDateAndVenue.map((dateGroup, dateIdx) => (
        <div key={dateGroup.date} className="date-group">
          {/* Date Divider */}
          <div className="date-divider">
            <div className="date-divider-line"></div>
            <div className="date-divider-text">{formatDate(dateGroup.date)}</div>
            <div className="date-divider-line"></div>
          </div>
          
          {/* Venues for this date */}
          {dateGroup.venues.map(({ venueName, slots }) => (
            <div key={`${dateGroup.date}-${venueName}`} className="venue-row">
              <div className="venue-header">
                <span className="venue-name">{venueName}</span>
                <span className="venue-slot-count">({slots.length} slot{slots.length !== 1 ? 's' : ''})</span>
              </div>
              <div className="venue-slots">
                {slots.map((item, idx) => (
                  <SlotCard key={`${dateGroup.date}-${venueName}-${idx}`} item={item} />
                ))}
              </div>
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}

export default DataSection

