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

  // Determine if we should use VenueRows (grouped by venue and date)
  // Use VenueRows when: multi-venue mode OR multiple venues in data OR multiple dates in data
  const shouldUseVenueRows = useMemo(() => {
    if (isMultiVenueMode) return true
    
    const uniqueVenues = new Set(filteredData.map(item => item.venue_name || item.website))
    const uniqueDates = new Set(filteredData.map(item => item.date).filter(Boolean))
    
    // Use VenueRows if multiple venues or multiple dates
    return uniqueVenues.size > 1 || uniqueDates.size > 1
  }, [isMultiVenueMode, filteredData])

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
        ) : shouldUseVenueRows ? (
          <VenueRows data={filteredData} />
        ) : (
          <DataTable data={filteredData} />
        )}
      </div>
    </div>
  )
}

function VenueRows({ data }) {
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

  const venues = useMemo(() => {
    // Group by venue, then by date within each venue
    const grouped = {}
    data.forEach(item => {
      const venueName = item.venue_name || item.website || 'Unknown'
      const date = item.date || 'Unknown'
      
      if (!grouped[venueName]) {
        grouped[venueName] = {}
      }
      if (!grouped[venueName][date]) {
        grouped[venueName][date] = []
      }
      grouped[venueName][date].push(item)
    })
    
    // Sort dates within each venue (chronologically)
    Object.keys(grouped).forEach(venueName => {
      const dates = Object.keys(grouped[venueName])
      dates.sort((a, b) => {
        if (a === 'Unknown') return 1
        if (b === 'Unknown') return -1
        return new Date(a) - new Date(b)
      })
      // Create sorted object
      const sortedDates = {}
      dates.forEach(date => {
        sortedDates[date] = grouped[venueName][date]
      })
      grouped[venueName] = sortedDates
    })
    
    return grouped
  }, [data])

  return (
    <div className="venue-rows-container">
      {Object.entries(venues).map(([venueName, dates]) => (
        <div key={venueName} className="venue-row">
          <div className="venue-header">{venueName}</div>
          <div className="venue-content">
            {Object.entries(dates).map(([date, slots]) => (
              <div key={`${venueName}-${date}`} className="date-group">
                <div className="date-header">{formatDate(date)}</div>
                <div className="venue-slots">
                  {slots.map((item, idx) => (
                    <SlotCard key={`${venueName}-${date}-${idx}`} item={item} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

export default DataSection

