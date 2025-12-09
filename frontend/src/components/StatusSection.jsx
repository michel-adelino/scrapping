function StatusSection({ stats }) {

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
    </div>
  )
}

export default StatusSection

