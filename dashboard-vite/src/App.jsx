import { useState, useEffect, useRef } from 'react'
import './App.css'

const API_URL = 'http://localhost:8000'
const WS_URL = API_URL.replace('http', 'ws')

function App() {
  const [cameraUrl, setCameraUrl] = useState('http://192.168.1.100:8080/video')
  const [connected, setConnected] = useState(false)
  const [connecting, setConnecting] = useState(false)
  const [runningTime, setRunningTime] = useState(0)
  const [fps, setFps] = useState(0)
  const [frame, setFrame] = useState(null)
  const [rawFrame, setRawFrame] = useState(null)
  
  const [personCount, setPersonCount] = useState(0)
  const [lightStatus, setLightStatus] = useState('OFF')
  const [fanStatus, setFanStatus] = useState('OFF')
  const [roomStatus, setRoomStatus] = useState('secure')
  const [processingTime, setProcessingTime] = useState(0)
  
  const [wasteDetected, setWasteDetected] = useState(0)
  const [demoMode, setDemoMode] = useState(false)
  
  const [privacyEnabled, setPrivacyEnabled] = useState(true)
  const [showRaw, setShowRaw] = useState(false)
  
  const wsRef = useRef(null)
  const fpsCounter = useRef({ count: 0, lastTime: Date.now() })
  const frameRef = useRef(null)
  const startTime = useRef(Date.now())
  const demoInterval = useRef(null)

  useEffect(() => {
    const timer = setInterval(() => {
      setRunningTime(Math.floor((Date.now() - startTime.current) / 1000))
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close()
      if (demoInterval.current) clearInterval(demoInterval.current)
    }
  }, [])

  const formatTime = (seconds) => {
    const hrs = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const connect = async () => {
    setConnecting(true)
    try {
      const response = await fetch(`${API_URL}/api/camera/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: cameraUrl, username: null, password: null })
      })
      
      const data = await response.json()
      
      if (!response.ok) { 
        alert('Failed to connect: ' + (data.detail || 'Unknown error'))
        setConnecting(false) 
        return 
      }
      
      setConnected(true)
      setConnecting(false)
      startTime.current = Date.now()
      
      const ws = new WebSocket(`${WS_URL}/ws/stream`)
      wsRef.current = ws
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.frame) {
            setFrame(data.frame)
            frameRef.current = data.frame
          }
          if (data.raw_frame) {
            setRawFrame(data.raw_frame)
          }
          if (data.privacy_enabled !== undefined) {
            setPrivacyEnabled(data.privacy_enabled)
          }
          
          setPersonCount(data.person_count)
          setLightStatus(data.light_status)
          setFanStatus(data.fan_status)
          setProcessingTime(data.processing_time_ms)
          
          const isWaste = data.person_count === 0 && (data.light_status === 'ON' || data.fan_status === 'ON')
          setRoomStatus(isWaste ? 'waste' : 'secure')
          
          if (isWaste) {
            setWasteDetected(prev => prev + 1)
          }
          
          fpsCounter.current.count++
          const now = Date.now()
          if (now - fpsCounter.current.lastTime >= 1000) {
            setFps(fpsCounter.current.count)
            fpsCounter.current.count = 0
            fpsCounter.current.lastTime = now
          }
        } catch (err) { 
          console.error('Parse error:', err) 
        }
      }
      
      ws.onclose = () => setConnected(false)
    } catch (err) { 
      console.error('Connection error:', err)
      setConnecting(false) 
    }
  }

  const disconnect = async () => {
    if (wsRef.current) wsRef.current.close()
    try { 
      await fetch(`${API_URL}/api/camera/disconnect`, { method: 'POST' }) 
    } catch (e) {}
    setConnected(false)
    frameRef.current = null
    setFrame(null)
  }

  const startDemo = (scenario) => {
    startTime.current = Date.now()
    if (demoInterval.current) clearInterval(demoInterval.current)
    setDemoMode(true)
    
    if (scenario === 'empty-room-appliances-on') {
      setPersonCount(0)
      setLightStatus('ON')
      setFanStatus('ON')
      setRoomStatus('waste')
      setWasteDetected(prev => prev + 1)
    } else {
      setPersonCount(Math.floor(Math.random() * 15) + 1)
      setLightStatus(Math.random() > 0.3 ? 'ON' : 'OFF')
      setFanStatus(Math.random() > 0.5 ? 'ON' : 'OFF')
      setRoomStatus('secure')
    }
    
    demoInterval.current = setInterval(() => {
      if (scenario === 'empty-room-appliances-on') {
        setPersonCount(0)
        setLightStatus('ON')
        setFanStatus('ON')
        setRoomStatus('waste')
      } else {
        setPersonCount(Math.floor(Math.random() * 15) + 1)
        setLightStatus(Math.random() > 0.3 ? 'ON' : 'OFF')
        setFanStatus(Math.random() > 0.5 ? 'ON' : 'OFF')
        setRoomStatus('secure')
      }
      setFps(Math.floor(Math.random() * 5) + 10)
      setProcessingTime(Math.floor(Math.random() * 500) + 100)
    }, 1500)
  }

  const stopDemo = () => {
    if (demoInterval.current) clearInterval(demoInterval.current)
    setDemoMode(false)
  }

  const isEnergyWaste = personCount === 0 && (lightStatus === 'ON' || fanStatus === 'ON')
  
  const estimatedWatts = (lightStatus === 'ON' ? 60 : 0) + (fanStatus === 'ON' ? 75 : 0)
  const costPerHour = estimatedWatts / 1000 * 0.12
  const potentialSavings = roomStatus === 'waste' ? costPerHour : 0

  return (
    <div className="dashboard">
      <header className="header">
        <div className="header-left">
          <h1>⚡ WattWatch</h1>
          <p>Facility Manager Control Room</p>
        </div>
        <div className="header-right">
          <div className="metric-box">
            <span className="metric-label">Running Time</span>
            <span className="metric-value">{formatTime(runningTime)}</span>
          </div>
          <div className="metric-box">
            <span className="metric-label">FPS</span>
            <span className="metric-value">{fps}</span>
          </div>
          <div className="metric-box">
            <span className="metric-label">Latency</span>
            <span className="metric-value">{processingTime > 0 ? `${processingTime.toFixed(0)}ms` : '--'}</span>
          </div>
        </div>
      </header>

      <div className="control-bar">
        <div className="camera-config">
          <input
            type="text"
            placeholder="IP Camera URL (e.g., http://192.168.1.100:8080/video)"
            value={cameraUrl}
            onChange={(e) => setCameraUrl(e.target.value)}
            disabled={connected}
          />
          {!connected ? (
            <button className="btn btn-connect" onClick={connect} disabled={connecting}>
              {connecting ? 'Connecting...' : 'Connect Camera'}
            </button>
          ) : (
            <button className="btn btn-disconnect" onClick={disconnect}>Disconnect</button>
          )}
        </div>
        
        <div className="demo-controls">
          {connected && (
            <div className="privacy-toggle">
              <label className="toggle-label">
                <input
                  type="checkbox"
                  checked={privacyEnabled}
                  onChange={async (e) => {
                    const enabled = e.target.checked
                    setPrivacyEnabled(enabled)
                    try {
                      await fetch(`${API_URL}/api/privacy/toggle`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(enabled)
                      })
                    } catch (err) {
                      console.error('Failed to toggle privacy:', err)
                    }
                  }}
                />
                <span className="toggle-switch"></span>
                <span>🔒 Privacy Mode {privacyEnabled ? 'ON' : 'OFF'}</span>
              </label>
              {privacyEnabled && (
                <label className="toggle-label">
                  <input
                    type="checkbox"
                    checked={showRaw}
                    onChange={(e) => setShowRaw(e.target.checked)}
                  />
                  <span>Show Raw</span>
                </label>
              )}
            </div>
          )}
          <button className="btn btn-demo" onClick={() => startDemo('empty-room-appliances-on')}>
            ▶ Demo: Empty + Appliances ON
          </button>
          <button className="btn btn-demo" onClick={() => startDemo('occupied-normal')}>
            ▶ Demo: Normal Occupancy
          </button>
          {demoMode && (
            <button className="btn btn-stop" onClick={stopDemo}>
              ⏹ Stop Demo
            </button>
          )}
        </div>
      </div>

      <div className="main-content">
        <div className="video-section">
          <div className="video-container">
            {connected || demoMode ? (
              <div className="frame-display">
                <img 
                  id="video-frame" 
                  src={showRaw && rawFrame ? rawFrame : frame} 
                  alt="Live Feed" 
                />
                {privacyEnabled && !showRaw && (
                  <div className="privacy-badge">🔒 Anonymized</div>
                )}
                {showRaw && (
                  <div className="raw-badge">⚠️ Raw Feed</div>
                )}
              </div>
            ) : (
              <div className="no-feed">
                <div className="no-feed-icon">📹</div>
                <p>Connect to camera or start demo</p>
                <p className="no-feed-hint">Use IP Webcam app on your phone</p>
              </div>
            )}
          </div>
          
          <div className="status-banner">
            <div className={`status-indicator ${roomStatus}`}>
              {roomStatus === 'waste' ? '⚠️ ENERGY WASTE DETECTED' : '✓ SECURE - NORMAL'}
            </div>
            {isEnergyWaste && (
              <div className="waste-alert">
                Room is empty but appliances are ON! Potential savings: ${potentialSavings.toFixed(2)}/hr
              </div>
            )}
          </div>
        </div>

        <div className="metrics-section">
          <div className="panel-card main-status">
            <h3>📊 Current Status</h3>
            <div className="status-grid">
              <div className="status-item">
                <span className="status-label">👥 Person Count</span>
                <span className="status-value large">{personCount}</span>
              </div>
              <div className="status-item">
                <span className="status-label">💡 Light</span>
                <span className={`status-value ${lightStatus === 'ON' ? 'on' : 'off'}`}>{lightStatus}</span>
              </div>
              <div className="status-item">
                <span className="status-label">🌀 Ceiling Fan</span>
                <span className={`status-value ${fanStatus === 'ON' ? 'on' : 'off'}`}>{fanStatus}</span>
              </div>
              <div className="status-item">
                <span className="status-label">📈 Room Status</span>
                <span className={`status-value ${roomStatus}`}>{roomStatus.toUpperCase()}</span>
              </div>
            </div>
          </div>

          <div className="panel-card energy-metrics">
            <h3>⚡ Energy Metrics</h3>
            <div className="energy-grid">
              <div className="energy-item">
                <span className="energy-label">Estimated Power</span>
                <span className="energy-value">{estimatedWatts}W</span>
              </div>
              <div className="energy-item">
                <span className="energy-label">Cost/Hour</span>
                <span className="energy-value">${costPerHour.toFixed(2)}</span>
              </div>
              <div className="energy-item">
                <span className="energy-label">Waste Events</span>
                <span className="energy-value warning">{wasteDetected}</span>
              </div>
              <div className="energy-item highlight">
                <span className="energy-label">Potential Savings</span>
                <span className="energy-value">${potentialSavings.toFixed(2)}/hr</span>
              </div>
            </div>
          </div>

          <div className="panel-card system-info">
            <h3>💻 System Info</h3>
            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">Camera</span>
                <span className="info-value">{connected ? 'Connected' : 'Disconnected'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Mode</span>
                <span className="info-value">{demoMode ? 'DEMO' : 'LIVE'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Processing</span>
                <span className="info-value">{processingTime > 0 ? `${processingTime.toFixed(0)}ms` : '--'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Latency Target</span>
                <span className="info-value success">&lt; 3s ✓</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App