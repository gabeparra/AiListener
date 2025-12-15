import React, { useState, useEffect } from 'react'
import './CodeBrowser.css'

function CodeBrowser() {
  const [files, setFiles] = useState([])
  const [selectedFile, setSelectedFile] = useState(null)
  const [fileContent, setFileContent] = useState(null)
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [showBrowser, setShowBrowser] = useState(false)

  useEffect(() => {
    if (showBrowser) {
      loadFiles()
    }
  }, [showBrowser])

  const loadFiles = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/code/files?max_depth=3')
      if (response.ok) {
        const data = await response.json()
        setFiles(data.files || [])
      }
    } catch (err) {
      console.error('Failed to load files:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleFileSelect = async (filePath) => {
    setLoading(true)
    setSelectedFile(filePath)
    try {
      const response = await fetch(`/api/code/read?file_path=${encodeURIComponent(filePath)}`)
      if (response.ok) {
        const data = await response.json()
        setFileContent(data)
      } else {
        setFileContent(null)
      }
    } catch (err) {
      console.error('Failed to read file:', err)
      setFileContent(null)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    
    setLoading(true)
    try {
      const response = await fetch(`/api/code/search?query=${encodeURIComponent(searchQuery)}`)
      if (response.ok) {
        const data = await response.json()
        // For now, just show first result
        if (data.results && data.results.length > 0) {
          handleFileSelect(data.results[0].file)
        }
      }
    } catch (err) {
      console.error('Search failed:', err)
    } finally {
      setLoading(false)
    }
  }

  const filteredFiles = files.filter(file =>
    file.path.toLowerCase().includes(searchQuery.toLowerCase())
  )

  if (!showBrowser) {
    return (
      <button
        className="toggle-code-browser"
        onClick={() => setShowBrowser(true)}
        title="Browse code files"
      >
        📁 Code Browser
      </button>
    )
  }

  return (
    <div className="panel code-browser-panel">
      <div className="code-browser-header">
        <h2>Code Browser</h2>
        <button
          className="close-browser"
          onClick={() => setShowBrowser(false)}
        >
          ✕
        </button>
      </div>

      <div className="code-browser-content">
        <div className="code-browser-sidebar">
          <div className="code-search-box">
            <input
              type="text"
              placeholder="Search files..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
            <button onClick={handleSearch}>Search</button>
          </div>

          <div className="file-list">
            {loading && !fileContent && <div className="loading">Loading files...</div>}
            {filteredFiles.slice(0, 50).map((file) => (
              <div
                key={file.path}
                className={`file-item ${selectedFile === file.path ? 'selected' : ''}`}
                onClick={() => handleFileSelect(file.path)}
                title={file.path}
              >
                <span className="file-icon">
                  {file.extension === '.py' ? '🐍' :
                   file.extension === '.js' || file.extension === '.jsx' ? '📜' :
                   file.extension === '.ts' || file.extension === '.tsx' ? '📘' :
                   file.extension === '.css' ? '🎨' : '📄'}
                </span>
                <span className="file-name">{file.name}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="code-viewer">
          {loading && fileContent === null && (
            <div className="loading">Loading file...</div>
          )}
          
          {fileContent && (
            <div className="file-content">
              <div className="file-header">
                <span className="file-path">{fileContent.path}</span>
                {fileContent.truncated && (
                  <span className="truncated-warning">
                    (Showing first {fileContent.total_lines} lines)
                  </span>
                )}
              </div>
              <pre className="code-block">
                <code>{fileContent.content}</code>
              </pre>
            </div>
          )}

          {!fileContent && !loading && (
            <div className="empty-state">
              Select a file to view its contents
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default CodeBrowser

