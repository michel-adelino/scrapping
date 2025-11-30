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
  const venues = useMemo(() => {
    const grouped = {}
    data.forEach(item => {
      const venueName = item.venue_name || item.website || 'Unknown'
      if (!grouped[venueName]) {
        grouped[venueName] = []
      }
      grouped[venueName].push(item)
    })
    return grouped
  }, [data])

  return (
    <div className="venue-rows-container">
      {Object.entries(venues).map(([venueName, slots]) => (
        <div key={venueName} className="venue-row">
          <div className="venue-header">{venueName}</div>
          <div className="venue-slots">
            {slots.map((item, idx) => (
              <SlotCard key={idx} item={item} />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

export default DataSection

