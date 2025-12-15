import { useState, useEffect, useRef } from 'react'

export function useWebSocket() {
  const [ws, setWs] = useState(null)
  const wsRef = useRef(null)

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = process.env.NODE_ENV === 'development' 
      ? '127.0.0.1:8000' 
      : window.location.host
    const wsUrl = `${protocol}//${host}/ws`

    wsRef.current = new WebSocket(wsUrl)
    setWs(wsRef.current)

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  return ws
}

