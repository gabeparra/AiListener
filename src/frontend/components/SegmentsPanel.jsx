import React from 'react'
import './SegmentsPanel.css'

function SegmentsPanel({ segments }) {
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString()
  }

  return (
    <div className="panel segments-panel">
      <h2>Conversation Segments</h2>
      <div className="segments-list">
        {segments.length === 0 ? (
          <div className="empty-state">Awaiting conversation data...</div>
        ) : (
          segments.map((segment, idx) => (
            <div key={idx} className="segment">
              <div className="segment-time">{formatTime(segment.timestamp)}</div>
              <div className="segment-speaker">{segment.speaker || 'Speaker'}</div>
              <div className="segment-text">{segment.text}</div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default SegmentsPanel

