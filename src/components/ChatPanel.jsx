import React, { useState, useEffect, useRef } from 'react'
import './ChatPanel.css'

function ChatPanel({ onSendMessage, ws }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    if (ws) {
      const handleMessage = (event) => {
        const data = JSON.parse(event.data)
        
        if (data.type === 'chat_response') {
          setIsTyping(false)
          setMessages(prev => [...prev, {
            type: 'assistant',
            content: data.response,
            timestamp: new Date(),
          }])
        }
      }

      ws.addEventListener('message', handleMessage)
      return () => ws.removeEventListener('message', handleMessage)
    }
  }, [ws])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!input.trim() || !ws || ws.readyState !== WebSocket.OPEN) return

    const userMessage = {
      type: 'user',
      content: input.trim(),
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setIsTyping(true)
    
    // Send message with session ID
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ 
        type: 'chat', 
        message: input.trim(),
        session_id: sessionId
      }))
    }
    
    setInput('')
    inputRef.current?.focus()
  }

  useEffect(() => {
    // Load conversation history on mount
    const loadHistory = async () => {
      try {
        const response = await fetch(`/api/conversations?session_id=${sessionId}&limit=50`)
        if (response.ok) {
          const data = await response.json()
          if (data.conversations && data.conversations.length > 0) {
            const historyMessages = data.conversations.map(conv => ({
              type: conv.role === 'user' ? 'user' : 'assistant',
              content: conv.message,
              timestamp: new Date(conv.created_at),
            }))
            setMessages(historyMessages)
          }
        }
      } catch (err) {
        console.error('Failed to load conversation history:', err)
      }
    }
    
    loadHistory()
  }, [sessionId])

  const formatTime = (date) => {
    return new Date(date).toLocaleTimeString()
  }

  return (
    <div className="panel chat-panel">
      <h2>Chat with Glup</h2>
      
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="empty-state">
            Start a conversation with Glup...
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx} className={`chat-message ${msg.type}`}>
              <div className="message-header">
                <span className="message-sender">
                  {msg.type === 'user' ? 'You' : 'Glup'}
                </span>
                <span className="message-time">{formatTime(msg.timestamp)}</span>
              </div>
              <div className="message-content">{msg.content}</div>
            </div>
          ))
        )}
        
        {isTyping && (
          <div className="chat-message assistant typing">
            <div className="message-header">
              <span className="message-sender">Glup</span>
            </div>
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="chat-input-form">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          className="chat-input"
          disabled={!ws || ws.readyState !== WebSocket.OPEN}
        />
        <button
          type="submit"
          className="chat-send-button"
          disabled={!input.trim() || !ws || ws.readyState !== WebSocket.OPEN}
        >
          Send
        </button>
      </form>
    </div>
  )
}

export default ChatPanel

