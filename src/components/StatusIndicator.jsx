import React from 'react'
import './StatusIndicator.css'

function StatusIndicator({ connected }) {
  return (
    <div className={`status-indicator ${connected ? 'connected' : 'disconnected'}`}>
      <span className="status-dot"></span>
      <span className="status-text">{connected ? 'Connected' : 'Disconnected'}</span>
    </div>
  )
}

export default StatusIndicator

