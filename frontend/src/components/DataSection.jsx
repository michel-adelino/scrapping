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
  const groupedByVenue = useMemo(() => {
    // Group by venue first, then by date
    const grouped = {}
    data.forEach(item => {
      const venueName = item.venue_name || item.website || 'Unknown Venue'
      const date = item.date || 'Unknown Date'
      
      if (!grouped[venueName]) {
        grouped[venueName] = {}
      }
      if (!grouped[venueName][date]) {
        grouped[venueName][date] = []
      }
      grouped[venueName][date].push(item)
    })
    
    // Convert to array format: [{ venueName, dates: [{ date, slots: [] }] }]
    return Object.entries(grouped)
      .sort((a, b) => a[0].localeCompare(b[0])) // Sort venues alphabetically
      .map(([venueName, dates]) => ({
        venueName,
        dates: Object.entries(dates)
          .sort((a, b) => new Date(b[0]) - new Date(a[0])) // Sort dates descending (newest first)
          .map(([date, slots]) => ({
            date,
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

  const getTotalSlots = (dates) => {
    return dates.reduce((sum, dateGroup) => sum + dateGroup.slots.length, 0)
  }

  return (
    <div className="venue-rows-container">
      {groupedByVenue.map(({ venueName, dates }) => {
        const totalSlots = getTotalSlots(dates)
        return (
          <div key={venueName} className="venue-row">
            <div className="venue-header">
              <span className="venue-name">{venueName}</span>
              <span className="venue-slot-count">({totalSlots} slot{totalSlots !== 1 ? 's' : ''})</span>
            </div>
            <div className="venue-slots">
              {dates.map(({ date, slots }, dateIdx) => (
                <div key={`${venueName}-${date}`} className="venue-date-group">
                  {/* Date Divider */}
                  <div className="date-divider-inline">
                    <div className="date-divider-line-inline"></div>
                    <div className="date-divider-text-inline">{formatDate(date)}</div>
                    <div className="date-divider-line-inline"></div>
                  </div>
                  {/* Slots for this date */}
                  <div className="venue-date-slots">
                    {slots.map((item, idx) => (
                      <SlotCard key={`${venueName}-${date}-${idx}`} item={item} />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default DataSection

