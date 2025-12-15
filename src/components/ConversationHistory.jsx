import React, { useState, useEffect } from 'react'
import './ConversationHistory.css'

function ConversationHistory({ onSelectSession, currentSessionId }) {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(false)
  const [showHistory, setShowHistory] = useState(false)

  useEffect(() => {
    if (showHistory) {
      loadSessions()
    }
  }, [showHistory])

  const loadSessions = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/conversations/sessions')
      if (response.ok) {
        const data = await response.json()
        setSessions(data.sessions || [])
      }
    } catch (err) {
      console.error('Failed to load sessions:', err)
    } finally {
      setLoading(false)
    }
  }

  if (!showHistory) {
    return (
      <button
        className="toggle-history"
        onClick={() => setShowHistory(true)}
        title="View conversation history"
      >
        💬 History
      </button>
    )
  }

  return (
    <div className="panel conversation-history-panel">
      <div className="history-header">
        <h3>Conversation History</h3>
        <button
          className="close-history"
          onClick={() => setShowHistory(false)}
        >
          ✕
        </button>
      </div>

      <div className="sessions-list">
        {loading ? (
          <div className="loading">Loading sessions...</div>
        ) : sessions.length === 0 ? (
          <div className="empty-state">No conversation history yet</div>
        ) : (
          sessions.map((sessionId) => (
            <div
              key={sessionId}
              className={`session-item ${currentSessionId === sessionId ? 'active' : ''}`}
              onClick={() => {
                if (onSelectSession) {
                  onSelectSession(sessionId)
                }
                setShowHistory(false)
              }}
            >
              <span className="session-id">
                {sessionId.replace('session_', '').substring(0, 15)}...
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default ConversationHistory

