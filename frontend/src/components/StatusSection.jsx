import { useState, useEffect } from 'react'

function StatusSection({ stats }) {
  const [durations, setDurations] = useState({ 
    nyc_today: null, 
    nyc_tomorrow: null, 
    london_today: null, 
    london_tomorrow: null 
  })

  useEffect(() => {
    const fetchDurations = async () => {
      try {
        // Use same host as frontend for API calls
        const apiBase = window.location.hostname === 'localhost' 
          ? 'http://localhost:8010/api' 
          : `http://${window.location.hostname}:8010/api`
        const response = await fetch(`${apiBase}/scraping_durations`)
        if (response.ok) {
          const data = await response.json()
          console.log('Fetched durations:', data)
          setDurations(data)
        } else {
          console.error('Failed to fetch durations:', response.status, response.statusText)
        }
      } catch (error) {
        console.error('Error fetching scraping durations:', error)
      }
    }

    fetchDurations()
    // Refresh every 30 seconds
    const interval = setInterval(fetchDurations, 30000)
    return () => clearInterval(interval)
  }, [])

  const formatDuration = (minutes) => {
    if (!minutes) return '-'
    if (minutes < 1) {
      return `${Math.round(minutes * 60)}s`
    }
    return `${minutes.toFixed(1)}m`
  }

  return (
    <div className="status-section">
      <div className="status-header">
        <div className="status-title">Scraping Status</div>
        <div className="status-badge status-completed">Ready</div>
      </div>

      <div className="progress-bar">
        <div className="progress-fill" style={{ width: '0%' }}></div>
      </div>

      <div className="status-text">
        Background scraping runs automatically every 15 minutes. Use Search Database to view results.
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{stats.totalSlots}</div>
          <div className="stat-label">Total Slots Found</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.currentDate}</div>
          <div className="stat-label">Current Date</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.availableSlots}</div>
          <div className="stat-label">Available Slots</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.currentWebsite}</div>
          <div className="stat-label">Current Website</div>
        </div>
      </div>

      {/* <div className="scraping-durations">
        <h3 style={{ marginTop: '20px', marginBottom: '10px', fontSize: '16px', fontWeight: '600' }}>
          ⏱️ Queue Scraping Durations
        </h3>
        <div className="duration-grid">
          <div className="duration-card">
            <div className="duration-header">
              <span className="duration-icon">🗽</span>
              <span className="duration-label">NYC Today</span>
            </div>
            <div className="duration-value">
              {durations.nyc_today ? formatDuration(durations.nyc_today.duration_minutes) : '-'}
            </div>
            {durations.nyc_today && (
              <div className="duration-details">
                <div>{durations.nyc_today.total_slots} slots found</div>
                {durations.nyc_today.completed_at && (
                  <div style={{ fontSize: '11px', color: '#666', marginTop: '4px' }}>
                    {new Date(durations.nyc_today.completed_at).toLocaleString()}
                  </div>
                )}
              </div>
            )}
          </div>
          <div className="duration-card">
            <div className="duration-header">
              <span className="duration-icon">🗽</span>
              <span className="duration-label">NYC Tomorrow</span>
            </div>
            <div className="duration-value">
              {durations.nyc_tomorrow ? formatDuration(durations.nyc_tomorrow.duration_minutes) : '-'}
            </div>
            {durations.nyc_tomorrow && (
              <div className="duration-details">
                <div>{durations.nyc_tomorrow.total_slots} slots found</div>
                {durations.nyc_tomorrow.completed_at && (
                  <div style={{ fontSize: '11px', color: '#666', marginTop: '4px' }}>
                    {new Date(durations.nyc_tomorrow.completed_at).toLocaleString()}
                  </div>
                )}
              </div>
            )}
          </div>
          <div className="duration-card">
            <div className="duration-header">
              <span className="duration-icon">🇬🇧</span>
              <span className="duration-label">London Today</span>
            </div>
            <div className="duration-value">
              {durations.london_today ? formatDuration(durations.london_today.duration_minutes) : '-'}
            </div>
            {durations.london_today && (
              <div className="duration-details">
                <div>{durations.london_today.total_slots} slots found</div>
                {durations.london_today.completed_at && (
                  <div style={{ fontSize: '11px', color: '#666', marginTop: '4px' }}>
                    {new Date(durations.london_today.completed_at).toLocaleString()}
                  </div>
                )}
              </div>
            )}
          </div>
          <div className="duration-card">
            <div className="duration-header">
              <span className="duration-icon">🇬🇧</span>
              <span className="duration-label">London Tomorrow</span>
            </div>
            <div className="duration-value">
              {durations.london_tomorrow ? formatDuration(durations.london_tomorrow.duration_minutes) : '-'}
            </div>
            {durations.london_tomorrow && (
              <div className="duration-details">
                <div>{durations.london_tomorrow.total_slots} slots found</div>
                {durations.london_tomorrow.completed_at && (
                  <div style={{ fontSize: '11px', color: '#666', marginTop: '4px' }}>
                    {new Date(durations.london_tomorrow.completed_at).toLocaleString()}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div> */}
    </div>
  )
}

export default StatusSection

