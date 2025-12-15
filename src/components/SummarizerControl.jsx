import React, { useState, useEffect } from 'react'
import './SummarizerControl.css'

function SummarizerControl({ ws }) {
  const [isRunning, setIsRunning] = useState(true)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    // Fetch initial state
    fetchSummarizerState()
  }, [])

  const fetchSummarizerState = async () => {
    try {
      const response = await fetch('/api/summarizer/status')
      if (response.ok) {
        const data = await response.json()
        setIsRunning(data.running)
      }
    } catch (err) {
      console.error('Failed to fetch summarizer state:', err)
    }
  }

  const toggleSummarizer = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/summarizer/toggle', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ running: !isRunning }),
      })

      if (response.ok) {
        const data = await response.json()
        setIsRunning(data.running)
        
        // Broadcast to WebSocket if connected
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({
            type: 'summarizer_state',
            running: data.running,
          }))
        }
      }
    } catch (err) {
      console.error('Failed to toggle summarizer:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={`summarizer-control ${isRunning ? 'running' : 'paused'}`}>
      <div className="summarizer-status">
        <span className="status-indicator"></span>
        <span className="status-text">
          {isRunning ? 'Processing Segments' : 'Segment Processing Paused'}
        </span>
      </div>
      <button
        onClick={toggleSummarizer}
        disabled={loading}
        className={`toggle-btn ${isRunning ? 'pause' : 'resume'}`}
      >
        {loading ? (
          'Updating...'
        ) : isRunning ? (
          <>
            <span className="btn-icon">⏸</span>
            Pause Processing
          </>
        ) : (
          <>
            <span className="btn-icon">▶</span>
            Resume Processing
          </>
        )}
      </button>
      <div className="summarizer-info">
        {isRunning ? (
          <p>Glup is analyzing conversation segments and generating summaries</p>
        ) : (
          <p>Segment processing paused. New segments will still be captured but not analyzed.</p>
        )}
      </div>
    </div>
  )
}

export default SummarizerControl

