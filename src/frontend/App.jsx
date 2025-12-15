import React, { useState, useEffect, useRef } from 'react'
import ChatPanel from './components/ChatPanel'
import SegmentsPanel from './components/SegmentsPanel'
import SummaryPanel from './components/SummaryPanel'
import StatusIndicator from './components/StatusIndicator'
import { useWebSocket } from './utils/useWebSocket'
import './App.css'

function App() {
  const [segments, setSegments] = useState([])
  const [summary, setSummary] = useState(null)
  const [isConnected, setIsConnected] = useState(false)
  const ws = useWebSocket()

  useEffect(() => {
    if (ws) {
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        
        if (data.type === 'segment') {
          setSegments(prev => [data.segment, ...prev])
        } else if (data.type === 'summary') {
          setSummary(data.summary)
        } else if (data.type === 'init') {
          if (data.segments) {
            setSegments(data.segments)
          }
          if (data.summary) {
            setSummary(data.summary)
          }
        } else if (data.type === 'chat_response') {
          // Handle chat response - will be added to chat component
        }
      }

      ws.onopen = () => {
        setIsConnected(true)
        ws.send(JSON.stringify({ type: 'init' }))
      }

      ws.onclose = () => {
        setIsConnected(false)
      }

      ws.onerror = () => {
        setIsConnected(false)
      }
    }

    return () => {
      if (ws) {
        ws.close()
      }
    }
  }, [ws])

  const sendChatMessage = async (message) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'chat', message }))
    }
  }

  return (
    <div className="app">
      <StatusIndicator connected={isConnected} />
      <header className="app-header">
        <h1>GLUP</h1>
        <div className="subtitle">Advanced Meeting Intelligence | Neural Processing Active</div>
      </header>
      
      <div className="main-content">
        <div className="left-panel">
          <ChatPanel onSendMessage={sendChatMessage} ws={ws} />
        </div>
        
        <div className="right-panel">
          <SegmentsPanel segments={segments} />
          <SummaryPanel summary={summary} />
        </div>
      </div>
    </div>
  )
}

export default App

