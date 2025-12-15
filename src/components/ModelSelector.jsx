import React, { useState, useEffect } from 'react'
import './ModelSelector.css'

function ModelSelector({ currentModel, onModelChange }) {
  const [models, setModels] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const commonModels = [
    { name: 'llama3.2:3b', label: 'Fast (llama3.2:3b)', speed: 'fast', quality: 'good' },
    { name: 'mistral-nemo:12b', label: 'Balanced (mistral-nemo:12b)', speed: 'medium', quality: 'very good' },
    { name: 'llama3:70b', label: 'Slow/High Quality (llama3:70b)', speed: 'slow', quality: 'excellent' },
    { name: 'llama3.1:70b', label: 'Slow/Best Quality (llama3.1:70b)', speed: 'slow', quality: 'excellent' },
  ]

  useEffect(() => {
    fetchModels()
    fetchCurrentModel()
  }, [])

  const fetchCurrentModel = async () => {
    try {
      const response = await fetch('/api/models')
      if (response.ok) {
        const data = await response.json()
        if (data.current_model && onModelChange) {
          onModelChange(data.current_model)
        }
      }
    } catch (err) {
      console.error('Failed to fetch current model:', err)
    }
  }

  const fetchModels = async () => {
    try {
      const response = await fetch('/api/models')
      if (response.ok) {
        const data = await response.json()
        setModels(data.models || [])
      }
    } catch (err) {
      console.error('Failed to fetch models:', err)
    }
  }

  const handleModelChange = async (modelName) => {
    if (modelName === currentModel) return

    setLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/models', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ model: modelName }),
      })

      const data = await response.json()

      if (response.ok) {
        onModelChange(modelName)
      } else {
        setError(data.error || 'Failed to change model')
      }
    } catch (err) {
      setError('Failed to change model. Make sure Ollama is running and the model is available.')
    } finally {
      setLoading(false)
    }
  }

  const getModelInfo = (modelName) => {
    return commonModels.find(m => m.name === modelName) || { speed: 'unknown', quality: 'unknown' }
  }

  return (
    <div className="model-selector">
      <h3>Model Selector</h3>
      <div className="current-model">
        <span className="model-label">Current:</span>
        <span className="model-name">{currentModel || 'Not set'}</span>
        {currentModel && (
          <span className={`model-badge ${getModelInfo(currentModel).speed}`}>
            {getModelInfo(currentModel).speed === 'fast' ? '⚡ Fast' :
             getModelInfo(currentModel).speed === 'medium' ? '⚖️ Balanced' :
             '🎯 High Quality'}
          </span>
        )}
      </div>

      {error && (
        <div className="model-error">{error}</div>
      )}

      <div className="model-options">
        <div className="model-section">
          <div className="section-header">⚡ Fast Models</div>
          {commonModels.filter(m => m.speed === 'fast').map(model => (
            <button
              key={model.name}
              className={`model-button ${currentModel === model.name ? 'active' : ''} ${loading ? 'loading' : ''}`}
              onClick={() => handleModelChange(model.name)}
              disabled={loading || currentModel === model.name}
            >
              <div className="model-button-label">{model.label}</div>
              <div className="model-button-desc">Quick responses, good quality</div>
            </button>
          ))}
        </div>

        <div className="model-section">
          <div className="section-header">⚖️ Balanced Models</div>
          {commonModels.filter(m => m.speed === 'medium').map(model => (
            <button
              key={model.name}
              className={`model-button ${currentModel === model.name ? 'active' : ''} ${loading ? 'loading' : ''}`}
              onClick={() => handleModelChange(model.name)}
              disabled={loading || currentModel === model.name}
            >
              <div className="model-button-label">{model.label}</div>
              <div className="model-button-desc">Good balance of speed and quality</div>
            </button>
          ))}
        </div>

        <div className="model-section">
          <div className="section-header">🎯 High Quality Models</div>
          {commonModels.filter(m => m.speed === 'slow').map(model => (
            <button
              key={model.name}
              className={`model-button ${currentModel === model.name ? 'active' : ''} ${loading ? 'loading' : ''}`}
              onClick={() => handleModelChange(model.name)}
              disabled={loading || currentModel === model.name}
            >
              <div className="model-button-label">{model.label}</div>
              <div className="model-button-desc">Best quality, slower responses</div>
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="model-loading">
          <span className="spinner"></span>
          Switching model...
        </div>
      )}
    </div>
  )
}

export default ModelSelector

