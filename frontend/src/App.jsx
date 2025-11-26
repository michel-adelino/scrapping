import { useState, useEffect, useCallback } from 'react'
import SearchPanel from './components/SearchPanel'
import StatusSection from './components/StatusSection'
import DataSection from './components/DataSection'
import ToastContainer from './components/ToastContainer'
import './App.css'

const API_BASE = 'http://localhost:8010/api'

function App() {
  const [tableData, setTableData] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [isMultiVenueMode, setIsMultiVenueMode] = useState(false)
  const [currentFilters, setCurrentFilters] = useState({})
  const [currentGuestsFilter, setCurrentGuestsFilter] = useState(null)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [stats, setStats] = useState({
    totalSlots: 0,
    availableSlots: 0,
    currentDate: '-',
    currentWebsite: '-'
  })
  const [toasts, setToasts] = useState([])

  const showToast = useCallback((message, type = 'error', duration = 5000) => {
    const id = Date.now() + Math.random()
    setToasts(prev => [...prev, { id, message, type, duration }])
  }, [])

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(toast => toast.id !== id))
  }, [])

  const getDefaultDateFilters = useCallback(() => {
    const today = new Date()
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)
    return {
      date_from: today.toISOString().split('T')[0],
      date_to: tomorrow.toISOString().split('T')[0]
    }
  }, [])

  const buildQueryUrl = useCallback((filters = {}) => {
    const params = new URLSearchParams()
    Object.entries(filters).forEach(([key, value]) => {
      if (value) {
        params.append(key, value)
      }
    })
    const queryString = params.toString()
    return queryString ? `${API_BASE}/data?${queryString}` : `${API_BASE}/data`
  }, [])

  const fetchData = useCallback(async (filters = {}, guests = null) => {
    try {
      // Guests filter is now handled by backend, but we can also filter client-side as fallback
      const url = buildQueryUrl(filters)
      console.log('Fetching data from:', url) // Debug log
      
      const response = await fetch(url)
      
      // Check if response is ok before trying to parse JSON
      if (!response.ok) {
        // Try to get error message from response
        let errorMsg = `HTTP error! status: ${response.status}`
        try {
          const errorData = await response.json()
          errorMsg = errorData.error || errorData.message || errorMsg
        } catch (e) {
          // If response is not JSON, get text
          try {
            const text = await response.text()
            errorMsg = text || errorMsg
          } catch (e2) {
            // If we can't read response, use status
            errorMsg = `Server error: ${response.status} ${response.statusText}`
          }
        }
        throw new Error(errorMsg)
      }
      
      // Parse JSON response
      let result
      try {
        const text = await response.text()
        if (!text) {
          throw new Error('Empty response from server')
        }
        result = JSON.parse(text)
      } catch (parseError) {
        console.error('Failed to parse JSON:', parseError)
        throw new Error('Invalid response from server. Please check the backend logs.')
      }
      
      console.log('Received data:', result) // Debug log

      let data = result.data || []
      
      // Additional client-side filter by guest count (backend should handle this, but keep as fallback)
      if (guests && data.length > 0) {
        const guestsInt = parseInt(guests, 10)
        data = data.filter(item => item.guests === guestsInt)
      }

      setTableData(data)
      setCurrentFilters(filters)
      setCurrentGuestsFilter(guests ? parseInt(guests, 10) : null)

      // Update stats
      const availableCount = data.filter(item => 
        (item.status || '').toLowerCase() === 'available'
      ).length
      
      // Get unique venues for display
      const uniqueVenues = [...new Set(data.map(item => item.venue_name || item.website || 'Unknown'))]
      const venueDisplay = uniqueVenues.length > 0 
        ? (uniqueVenues.length === 1 ? uniqueVenues[0] : `${uniqueVenues.length} venues`)
        : '-'
      
      setStats({
        totalSlots: data.length,
        availableSlots: availableCount,
        currentDate: data.length > 0 ? data[0].date : '-',
        currentWebsite: venueDisplay
      })
    } catch (error) {
      console.error('Error fetching data:', error)
      const errorMessage = error.message || 'Unknown error occurred'
      showToast(`Error loading data: ${errorMessage}`, 'error')
    }
  }, [buildQueryUrl, showToast])

  const handleSearch = useCallback((filters, guests, isMultiVenue) => {
    setIsMultiVenueMode(isMultiVenue)
    fetchData(filters, guests)
  }, [fetchData])

  const handleClearData = useCallback(async () => {
    // Use a simple confirmation without blocking alert
    const confirmed = window.confirm('Are you sure you want to clear all data?')
    if (!confirmed) return

    try {
      await fetch(`${API_BASE}/clear_data`, { method: 'POST' })
      setTableData([])
      setStats({
        totalSlots: 0,
        availableSlots: 0,
        currentDate: '-',
        currentWebsite: '-'
      })
      showToast('Data cleared successfully', 'success', 3000)
    } catch (error) {
      showToast(`Error clearing data: ${error.message}`, 'error')
    }
  }, [showToast])

  // Auto-refresh effect
  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(() => {
      const filters = Object.keys(currentFilters).length > 0 
        ? currentFilters 
        : getDefaultDateFilters()
      fetchData(filters, currentGuestsFilter)
    }, 5000)

    return () => clearInterval(interval)
  }, [autoRefresh, currentFilters, currentGuestsFilter, fetchData, getDefaultDateFilters])

  // Initial load - load today and tomorrow data with default 6 guests
  useEffect(() => {
    const defaultFilters = getDefaultDateFilters()
    fetchData(defaultFilters, 6) // Default to 6 guests
  }, [fetchData, getDefaultDateFilters])

  const filteredData = searchTerm
    ? tableData.filter(item => {
        const haystack = [
          item.venue_name || item.website,
          item.date,
          item.time,
          item.price,
          item.status
        ].map(part => (part || '').toString().toLowerCase()).join(' ')
        return haystack.includes(searchTerm.toLowerCase())
      })
    : tableData

  return (
    <div className="app-shell">
      <header className="page-header">
        <div className="page-eyebrow">
          <span>🍽️</span>
          <span>Live Availability Scraper</span>
        </div>
        <h1>Find venues with available slots in seconds</h1>
        <p>Choose a city, set your date and group size, then let the scraper do the work.</p>
      </header>

      <SearchPanel onSearch={handleSearch} onClear={handleClearData} />

      <StatusSection stats={stats} />

      <DataSection
        data={filteredData}
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        isMultiVenueMode={isMultiVenueMode}
        autoRefresh={autoRefresh}
        onAutoRefreshChange={setAutoRefresh}
      />

      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  )
}

export default App

