import { useMemo } from 'react'
import SlotCard from './SlotCard'
import DataTable from './DataTable'

function DataSection({ data, isMultiVenueMode }) {
  return (
    <div className="data-section">
      <div className="data-header">
        <div className="data-title">Live Availability</div>
      </div>

      <div className="auto-scroll">
        {data.length === 0 ? (
          <div className="no-data">
            No data available. Use the search panel to find available slots.
          </div>
        ) : isMultiVenueMode ? (
          <VenueRows data={data} />
        ) : (
          <DataTable data={data} />
        )}
      </div>
    </div>
  )
}

// Map venue names to image filenames in the public folder
const VENUE_IMAGE_MAP = {
  'Swingers (NYC)': 'Swingers.webp',
  'Swingers (London)': 'Swingers.webp',
  'Electric Shuffle (NYC)': 'Electric Shuffle.webp',
  'Electric Shuffle (London)': 'Electric Shuffle.webp',
  'Lawn Club (Indoor Gaming)': 'LawnClub.webp',
  'Lawn Club (Curling Lawns)': 'LawnClub.webp',
  'Lawn Club (Croquet Lawns)': 'LawnClub.webp',
  'SPIN (NYC)': 'sample.webp', // Add image if available
  'Five Iron Golf (NYC - FiDi)': 'FiveIron.webp',
  'Five Iron Golf (NYC - Flatiron)': 'FiveIron.webp',
  'Five Iron Golf (NYC - Grand Central)': 'FiveIron.webp',
  'Five Iron Golf (NYC - Herald Square)': 'FiveIron.webp',
  'Five Iron Golf (NYC - Long Island City)': 'FiveIron.webp',
  'Five Iron Golf (NYC - Upper East Side)': 'FiveIron.webp',
  'Five Iron Golf (NYC - Rockefeller Center)': 'FiveIron.webp',
  'Lucky Strike (NYC)': 'sample.webp', // Add image if available
  'Easybowl (NYC)': 'sample.webp', // Add image if available
  'Fair Game (Canary Wharf)': 'Fairgame.webp',
  'Fair Game (City)': 'Fairgame.webp',
  'Clays Bar (Canary Wharf)': 'Clays.webp', // Add image if available
  'Clays Bar (The City)': 'Clays.webp', // Add image if available
  'Clays Bar (Birmingham)': 'Clays.webp', // Add image if available
  'Clays Bar (Soho)': 'Clays.webp', // Add image if available
  'Puttshack (Bank)': 'Puttshack.webp',
  'Puttshack (Lakeside)': 'Puttshack.webp',
  'Puttshack (White City)': 'Puttshack.webp',
  'Puttshack (Watford)': 'Puttshack.webp',
  'Flight Club Darts (Angel)': 'Flight Club.webp',
  'Flight Club Darts (Bloomsbury)': 'Flight Club.webp',
  'Flight Club Darts (Shoreditch)': 'Flight Club.webp',
  'Flight Club Darts (Victoria)': 'Flight Club.webp',
  'F1 Arcade': 'F1 Arcade.webp',
  'Chelsea Piers Golf': 'daysmart.webp',
  'Topgolf Chigwell': 'topgolfchigwell.webp',
  'T-Squared Social': 'tsquaredsocial.webp',
  'Hijingo': 'hijingo.webp',
  'Bounce': 'Bounce.webp',
  'Puttery (NYC)': 'Puttery.webp',
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
          .sort((a, b) => new Date(a[0]) - new Date(b[0])) // Sort dates ascending (oldest first - today to 30 days later)
          .map(([date, slots]) => ({
            date,
            slots: slots.sort((a, b) => (a.time || '').localeCompare(b.time || '')) // Sort slots by time
          }))
      }))
  }, [data])

  // Helper function to get image path for a venue
  const getVenueImage = (venueName) => {
    const imageFile = VENUE_IMAGE_MAP[venueName] || 'sample.webp'
    return `/${imageFile}`
  }

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
      {groupedByVenue.map(({ venueName, dates }) => {
        return (
          <div key={venueName} className="venue-row">
            <div className="venue-header">
              <span className="venue-name">{venueName}</span>
              <img 
                src={getVenueImage(venueName)} 
                alt={venueName}
                className="venue-image"
                onError={(e) => {
                  // Fallback to sample image if the specific image fails to load
                  e.target.src = '/sample.webp'
                }}
              />
            </div>
            <div className="venue-slots">
              {dates.map(({ date, slots }, dateIdx) => (
                <div key={`${venueName}-${date}`} className="venue-date-group">
                  {/* Date Divider - inline with slots */}
                  <div className="date-divider-text-inline">{formatDate(date)}</div>
                  {/* Slots for this date */}
                  {slots.map((item, idx) => (
                    <SlotCard key={`${venueName}-${date}-${idx}`} item={item} />
                  ))}
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

