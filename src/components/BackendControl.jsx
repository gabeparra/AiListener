import React, { useState, useEffect } from 'react'
import './BackendControl.css'

function BackendControl({ isConnected, onRefresh }) {
  const [checking, setChecking] = useState(false)
  const [backendStatus, setBackendStatus] = useState(null)
  const [lastCheck, setLastCheck] = useState(null)

  const checkBackend = async () => {
    setChecking(true)
    try {
      const response = await fetch('/api/health')
      const data = await response.json()
      setBackendStatus(data.status === 'ok')
      setLastCheck(new Date())
    } catch (err) {
      setBackendStatus(false)
      setLastCheck(new Date())
    } finally {
      setChecking(false)
    }
  }

  useEffect(() => {
    // Initial check
    checkBackend()
    
    // Check every 10 seconds
    const interval = setInterval(checkBackend, 10000)
    return () => clearInterval(interval)
  }, [])

  const handleRefresh = () => {
    checkBackend()
    if (onRefresh) {
      onRefresh()
    }
  }

  const getStatusDisplay = () => {
    if (checking) {
      return { text: 'Checking...', class: 'checking' }
    }
    
    if (isConnected && backendStatus !== false) {
      return { text: '✓ Backend Connected', class: 'connected' }
    }
    
    return { text: '✗ Backend Disconnected', class: 'disconnected' }
  }

  const status = getStatusDisplay()

  return (
    <div className={`backend-control ${status.class}`}>
      <div className="backend-status">
        <span className="status-text">{status.text}</span>
        {lastCheck && (
          <span className="last-check">
            Last check: {lastCheck.toLocaleTimeString()}
          </span>
        )}
      </div>
      <div className="backend-actions">
        <button 
          onClick={handleRefresh} 
          disabled={checking}
          className="refresh-btn"
          title="Refresh backend connection"
        >
          {checking ? 'Checking...' : 'Refresh'}
        </button>
        {!isConnected && (
          <div className="backend-help">
            <p>Backend not running. Start it with:</p>
            <code>python -m caption_ai --web --port 8000</code>
          </div>
        )}
      </div>
    </div>
  )
}

export default BackendControl

