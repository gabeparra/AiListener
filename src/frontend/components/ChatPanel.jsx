import React, { useState, useEffect, useRef } from 'react'
import './ChatPanel.css'

function ChatPanel({ onSendMessage, ws }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
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
    onSendMessage(input.trim())
    setInput('')
    inputRef.current?.focus()
  }

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

