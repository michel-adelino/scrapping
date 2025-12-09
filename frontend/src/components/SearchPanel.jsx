import { useState, useEffect } from 'react'

const LAWN_CLUB_TIMES = [
  "6:00 AM", "6:15 AM", "6:30 AM", "6:45 AM",
  "7:00 AM", "7:15 AM", "7:30 AM", "7:45 AM",
  // ... add all times (96 total)
]

const LAWN_CLUB_DURATIONS = [
  "1 hr",
  "1 hr 30 min",
  "2 hr",
  "2 hr 30 min",
  "3 hr"
]

const VENUE_INFO = {
  'swingers_nyc': { name: 'Swingers (NYC)', description: 'Golf club and restaurant offering crazy golf, cocktails, and street food. Can scrape multiple dates if no specific date is selected.' },
  'swingers_london': { name: 'Swingers (London)', description: 'Golf club and restaurant offering crazy golf, cocktails, and street food. Can scrape multiple dates if no specific date is selected.' },
  'electric_shuffle_nyc': { name: 'Electric Shuffle (NYC)', description: 'Shuffleboard bar and restaurant. Requires a specific target date.' },
  'electric_shuffle_london': { name: 'Electric Shuffle (London)', description: 'Shuffleboard bar and restaurant. Requires a specific target date.' },
  'lawn_club_nyc': { name: 'Lawn Club NYC', description: 'Lawn games and activities. Requires a specific target date.' },
  'spin_nyc': { name: 'SPIN (NYC)', description: 'Ping pong bar and restaurant. Requires a specific target date.' },
  'five_iron_golf_nyc': { name: 'Five Iron Golf (NYC)', description: 'Indoor golf and entertainment. Requires a specific target date.' },
  'lucky_strike_nyc': { name: 'Lucky Strike (NYC)', description: 'Bowling alley and entertainment. Requires a specific target date.' },
  'easybowl_nyc': { name: 'Easybowl (NYC)', description: 'Bowling and entertainment. Requires a specific target date.' },
  'fair_game_canary_wharf': { name: 'Fair Game (Canary Wharf)', description: 'Games and entertainment. Requires a specific target date.' },
  'fair_game_city': { name: 'Fair Game (City)', description: 'Games and entertainment. Requires a specific target date.' },
  'clays_bar': { name: 'Clays Bar', description: 'Clay shooting and bar. Requires a specific target date.' },
  'puttshack': { name: 'Puttshack', description: 'Mini golf and entertainment. Requires a specific target date.' },
  'flight_club_darts': { name: 'Flight Club Darts (Bloomsbury)', description: 'Darts and entertainment. Requires a specific target date.' },
  'flight_club_darts_angel': { name: 'Flight Club Darts (Angel)', description: 'Darts and entertainment. Requires a specific target date.' },
  'flight_club_darts_shoreditch': { name: 'Flight Club Darts (Shoreditch)', description: 'Darts and entertainment. Requires a specific target date.' },
  'flight_club_darts_victoria': { name: 'Flight Club Darts (Victoria)', description: 'Darts and entertainment. Requires a specific target date.' },
  'f1_arcade': { name: 'F1 Arcade', description: 'F1 racing simulation. Requires a specific target date.' },
  'all_new_york': { name: 'All New York', description: 'Search all NYC venues at once.' },
  'all_london': { name: 'All London', description: 'Search all London venues at once.' }
}

const VENUE_NAME_MAP = {
  'swingers_nyc': 'Swingers (NYC)',
  'swingers_london': 'Swingers (London)',
  'electric_shuffle_nyc': 'Electric Shuffle (NYC)',
  'electric_shuffle_london': 'Electric Shuffle (London)',
  'lawn_club_nyc': 'Lawn Club NYC',
  'spin_nyc': 'SPIN (NYC)',
  'five_iron_golf_nyc': 'Five Iron Golf (NYC)',
  'lucky_strike_nyc': 'Lucky Strike (NYC)',
  'easybowl_nyc': 'Easybowl (NYC)',
  'fair_game_canary_wharf': 'Fair Game (Canary Wharf)',
  'fair_game_city': 'Fair Game (City)',
  'clays_bar': 'Clays Bar',
  'puttshack': 'Puttshack',
  'flight_club_darts': 'Flight Club Darts (Bloomsbury)',
  'flight_club_darts_angel': 'Flight Club Darts (Angel)',
  'flight_club_darts_shoreditch': 'Flight Club Darts (Shoreditch)',
  'flight_club_darts_victoria': 'Flight Club Darts (Victoria)',
  'f1_arcade': 'F1 Arcade'
}

function SearchPanel({ onSearch, onClear, isLoading = false }) {
  const [location, setLocation] = useState('all_new_york') // 'all_new_york' or 'all_london'
  const [guests, setGuests] = useState(6)
  const [targetDate, setTargetDate] = useState('')
  const [targetDateEnabled, setTargetDateEnabled] = useState(false)
  const [lawnClubOption, setLawnClubOption] = useState('Curling Lawns & Cabins')
  const [lawnClubTime, setLawnClubTime] = useState('')
  const [lawnClubDuration, setLawnClubDuration] = useState('')
  const [spinTime, setSpinTime] = useState('')
  const [claysLocation, setClaysLocation] = useState('Canary Wharf')
  const [puttshackLocation, setPuttshackLocation] = useState('Bank')
  const [f1Experience, setF1Experience] = useState('Team Racing')

  const venueInfo = VENUE_INFO[location] || VENUE_INFO['all_new_york']
  const requiresDate = false // Always false since we're only showing all_new_york or all_london

  const getDefaultDateFilters = () => {
    const today = new Date()
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)
    return {
      date_from: today.toISOString().split('T')[0],
      date_to: tomorrow.toISOString().split('T')[0]
    }
  }

  const handleSearch = (e) => {
    e?.preventDefault()
    const filters = {}
    
    // For "All New York" and "All London", don't apply date filters by default
    // User can still specify a date if they want
    const isMultiVenue = true // Always true since we only have all_new_york or all_london
    
    // For multi-venue searches, only apply date filter if user explicitly selects a date
    if (targetDate && targetDateEnabled) {
      filters.date_from = targetDate
      filters.date_to = targetDate
    }
    // Otherwise, no date filter - show all available slots

    // Add venue/city filter
    if (location === 'all_new_york') {
      filters.city = 'NYC'
      delete filters.venue_name
    } else if (location === 'all_london') {
      filters.city = 'London'
      delete filters.venue_name
    }

    // Add guests filter
    filters.guests = guests

    onSearch(filters, guests, isMultiVenue)
  }

  const handleToday = () => {
    const today = new Date().toISOString().split('T')[0]
    setTargetDate(today)
    setTargetDateEnabled(true)
  }

  const handleTomorrow = () => {
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    setTargetDate(tomorrow.toISOString().split('T')[0])
    setTargetDateEnabled(true)
  }

  useEffect(() => {
    if (requiresDate) {
      setTargetDateEnabled(true)
    }
  }, [requiresDate])

  return (
    <div className="control-panel">
      <form onSubmit={handleSearch}>
        <div className="search-panel">
          <div className="input-card">
            <label>Location</label>
            <div className="location-buttons">
              <button
                type="button"
                className={`location-btn ${location === 'all_new_york' ? 'active' : ''}`}
                onClick={() => setLocation('all_new_york')}
              >
                🗽 New York
              </button>
              <button
                type="button"
                className={`location-btn ${location === 'all_london' ? 'active' : ''}`}
                onClick={() => setLocation('all_london')}
              >
                🇬🇧 London
              </button>
            </div>
          </div>

          <div className="input-card">
            <label htmlFor="targetDate">Date</label>
            <div className="date-row">
              <div className="input-field">
                <span className="icon">📅</span>
                <input
                  type="date"
                  id="targetDate"
                  className="form-control"
                  value={targetDate}
                  onChange={(e) => setTargetDate(e.target.value)}
                  disabled={!targetDateEnabled}
                />
              </div>
              <div className="quick-date-row">
                <button type="button" className="quick-date-btn" onClick={handleToday}>Today</button>
                <button type="button" className="quick-date-btn" onClick={handleTomorrow}>Tomorrow</button>
              </div>
            </div>
          </div>

          <div className="input-card input-card--narrow">
            <label htmlFor="guests">Group Size</label>
            <div className="guest-picker">
              <button
                type="button"
                onClick={() => setGuests(Math.max(1, guests - 1))}
                aria-label="Decrease guests"
              >
                −
              </button>
              <input
                type="number"
                id="guests"
                min="1"
                value={guests}
                readOnly
                required
              />
              <button
                type="button"
                onClick={() => setGuests(guests + 1)}
                aria-label="Increase guests"
              >
                +
              </button>
            </div>
          </div>

          <div className="search-actions">
            <button type="submit" className="primary-btn" disabled={isLoading}>
              <span>{isLoading ? '⏳' : '🔍'}</span>
              {isLoading ? 'Loading...' : 'Search'}
            </button>
            <button type="button" className="ghost-btn" onClick={onClear}>
              <span>🗑️</span>
              Clear
            </button>
          </div>
        </div>

        <div className="target-toggle">
          <input
            type="checkbox"
            id="targetDateEnabled"
            checked={targetDateEnabled}
            onChange={(e) => setTargetDateEnabled(e.target.checked)}
            disabled={requiresDate}
          />
          <label htmlFor="targetDateEnabled">
            Filter by specific date
          </label>
        </div>

        <div className="options-grid">
          {false && location === 'lawn_club_nyc' && (
            <>
              <div className="option-card">
                <label htmlFor="lawnClubOption">Lawn Club Experience</label>
                <select
                  id="lawnClubOption"
                  className="form-control"
                  value={lawnClubOption}
                  onChange={(e) => setLawnClubOption(e.target.value)}
                >
                  <option value="Curling Lawns & Cabins">Curling Lawns & Cabins</option>
                  <option value="Indoor Gaming Lawns">Indoor Gaming Lawns</option>
                  <option value="Croquet Lawns">Croquet Lawns</option>
                </select>
              </div>
            </>
          )}

          {false && location === 'clays_bar' && (
            <div className="option-card">
              <label htmlFor="claysLocation">Clays Bar Location</label>
              <select
                id="claysLocation"
                className="form-control"
                value={claysLocation}
                onChange={(e) => setClaysLocation(e.target.value)}
              >
                <option value="Canary Wharf">Canary Wharf</option>
                <option value="The City">The City</option>
                <option value="Birmingham">Birmingham</option>
                <option value="Soho">Soho</option>
              </select>
            </div>
          )}

          {false && location === 'puttshack' && (
            <div className="option-card">
              <label htmlFor="puttshackLocation">Puttshack Location</label>
              <select
                id="puttshackLocation"
                className="form-control"
                value={puttshackLocation}
                onChange={(e) => setPuttshackLocation(e.target.value)}
              >
                <option value="Bank">Bank</option>
                <option value="Lakeside">Lakeside</option>
                <option value="White City">White City</option>
                <option value="Watford">Watford</option>
              </select>
            </div>
          )}

          {false && location === 'f1_arcade' && (
            <div className="option-card">
              <label htmlFor="f1Experience">F1 Arcade Experience</label>
              <select
                id="f1Experience"
                className="form-control"
                value={f1Experience}
                onChange={(e) => setF1Experience(e.target.value)}
              >
                {guests < 4 ? (
                  <option value="Head to Head">Head to Head</option>
                ) : (
                  <>
                    <option value="Team Racing">Team Racing</option>
                    <option value="Christmas Racing">Christmas Racing</option>
                  </>
                )}
              </select>
            </div>
          )}
        </div>

      </form>
    </div>
  )
}

export default SearchPanel

