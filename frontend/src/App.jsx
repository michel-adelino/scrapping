import { useState, useEffect, useCallback } from 'react'
import SearchPanel from './components/SearchPanel'
import DataSection from './components/DataSection'
import ToastContainer from './components/ToastContainer'
import './App.css'

// Use environment variable or detect from current host
const getApiBase = () => {
  // If VITE_API_BASE is set, use it (for production builds)
  if (import.meta.env.VITE_API_BASE) {
    return import.meta.env.VITE_API_BASE
  }
  // For development, use current host (works for both localhost and IP access)
  const host = window.location.hostname
  return `http://${host}:8010/api`
}

const API_BASE = getApiBase()

function App() {
  const [tableData, setTableData] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [isMultiVenueMode, setIsMultiVenueMode] = useState(false)
  const [currentFilters, setCurrentFilters] = useState({})
  const [currentGuestsFilter, setCurrentGuestsFilter] = useState(null)
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [toasts, setToasts] = useState([])
  const [isLoading, setIsLoading] = useState(false)

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
    setIsLoading(true)
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
    } catch (error) {
      console.error('Error fetching data:', error)
      const errorMessage = error.message || 'Unknown error occurred'
      showToast(`Error loading data: ${errorMessage}`, 'error')
    } finally {
      setIsLoading(false)
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

  // Initial load - load All NYC data without date filter, with default 6 guests
  useEffect(() => {
    const defaultFilters = { city: 'NYC' } // Load All NYC without date selection
    setIsMultiVenueMode(true) // Set multi-venue mode for All NYC
    fetchData(defaultFilters, 6) // Default to 6 guests
  }, [fetchData])

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
          <span>Live Availability</span>
        </div>
        <h1>Find venues with available slots in seconds</h1>
        <p>Choose a city, set your date and group size, then search for available slots.</p>
      </header>

      <SearchPanel onSearch={handleSearch} onClear={handleClearData} isLoading={isLoading} />

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

