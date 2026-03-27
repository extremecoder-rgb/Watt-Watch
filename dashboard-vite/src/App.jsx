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
  const [monitorStatus, setMonitorStatus] = useState('OFF')
  const [roomStatus, setRoomStatus] = useState('secure')
  const [processingTime, setProcessingTime] = useState(0)
  
  const [demoMode, setDemoMode] = useState(false)
  const [privacyEnabled, setPrivacyEnabled] = useState(true)
  const [showRaw, setShowRaw] = useState(false)
  
  const [alertEvents, setAlertEvents] = useState([])
  const [alertStatus, setAlertStatus] = useState({})
  const [wasteDuration, setWasteDuration] = useState(0)
  const [energyMetrics, setEnergyMetrics] = useState({})
  
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

  // Fetch alert and energy status periodically
  useEffect(() => {
    if (!connected) return
    
    const fetchAlertData = async () => {
      try {
        const [statusRes, eventsRes, metricsRes] = await Promise.all([
          fetch(`${API_URL}/api/alerts/status`),
          fetch(`${API_URL}/api/alerts/events?limit=5`),
          fetch(`${API_URL}/api/energy/metrics`)
        ])
        
        const statusData = await statusRes.json()
        setAlertStatus(statusData)
        
        if (statusData.rooms && statusData.rooms['room-101']) {
          setWasteDuration(statusData.rooms['room-101'].waste_duration_seconds || 0)
        }
        
        const eventsData = await eventsRes.json()
        setAlertEvents(eventsData.events || [])
        
        const metricsData = await metricsRes.json()
        setEnergyMetrics(metricsData.rooms?.['room-101'] || {})
      } catch (err) {}
    }
    
    fetchAlertData()
    const interval = setInterval(fetchAlertData, 5000)
    return () => clearInterval(interval)
  }, [connected])

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
          setMonitorStatus(data.monitor_status || 'OFF')
          setProcessingTime(data.processing_time_ms)
          
          const isWaste = data.person_count === 0 && (data.light_status === 'ON' || data.fan_status === 'ON' || data.monitor_status === 'ON')
          setRoomStatus(isWaste ? 'waste' : 'secure')
          
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
      setMonitorStatus('ON')
      setRoomStatus('waste')
    } else {
      setPersonCount(Math.floor(Math.random() * 5) + 1)
      setLightStatus('OFF')
      setFanStatus('ON')
      setMonitorStatus('OFF')
      setRoomStatus('secure')
    }
    
    demoInterval.current = setInterval(() => {
      if (scenario === 'empty-room-appliances-on') {
        setPersonCount(0)
        setLightStatus('ON')
        setFanStatus('ON')
        setMonitorStatus('ON')
        setRoomStatus('waste')
      } else {
        setPersonCount(Math.floor(Math.random() * 5) + 1)
        setLightStatus('OFF')
        setFanStatus('ON')
        setMonitorStatus('OFF')
        setRoomStatus('secure')
      }
      setFps(Math.floor(Math.random() * 5) + 25)
      setProcessingTime(Math.floor(Math.random() * 100) + 50)
    }, 1500)
  }

  const stopDemo = () => {
    if (demoInterval.current) clearInterval(demoInterval.current)
    setDemoMode(false)
    setPersonCount(0)
    setLightStatus('OFF')
    setFanStatus('OFF')
    setMonitorStatus('OFF')
    setRoomStatus('secure')
  }

  const isEnergyWaste = roomStatus === 'waste'
  
  // Use real data from API when connected, fallback to simplified calculation
  const estimatedWatts = connected && energyMetrics.estimated_watts 
    ? energyMetrics.estimated_watts 
    : (lightStatus === 'ON' ? 40 : 0) + (fanStatus === 'ON' ? 65 : 0) + (monitorStatus === 'ON' ? 35 : 0)
    
  const costPerHour = connected && energyMetrics.cost_per_hour 
    ? energyMetrics.cost_per_hour 
    : estimatedWatts / 1000 * 0.12
    
  const cumulativeCost = connected && energyMetrics.cumulative_cost ? energyMetrics.cumulative_cost : 0
  const potentialSavings = connected && energyMetrics.potential_savings_per_hour 
    ? energyMetrics.potential_savings_per_hour 
    : (roomStatus === 'waste' ? costPerHour : 0)

  return (
    <div className="dashboard">
      <header className="header">
        <div className="header-left">
          <h1>⚡ CAM SENSE</h1>
          <p>INTEL MONITORING v1.0.4 - PIXEL GRID ACTIVE</p>
        </div>
        <div className="header-right">
          <div className="metric-box">
            <span className="metric-label">UPTIME</span>
            <span className="metric-value">{formatTime(runningTime)}</span>
          </div>
          <div className="metric-box">
            <span className="metric-label">STREAM_FPS</span>
            <span className="metric-value">{fps}</span>
          </div>
          <div className="metric-box">
            <span className="metric-label">NET_LATENCY</span>
            <span className="metric-value">{processingTime > 0 ? `${processingTime.toFixed(0)}MS` : '---'}</span>
          </div>
        </div>
      </header>

      <div className="control-bar">
        <div className="camera-config">
          <input
            type="text"
            placeholder="VID_SOURCE_URL (HTTP/RTSP)"
            value={cameraUrl}
            onChange={(e) => setCameraUrl(e.target.value)}
            disabled={connected}
          />
          {!connected ? (
            <button className="btn btn-connect" onClick={connect} disabled={connecting}>
              {connecting ? 'INITIALIZING...' : '> CON_CAMERA'}
            </button>
          ) : (
            <button className="btn btn-disconnect" onClick={disconnect}>X DISCONNECT</button>
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
                      await fetch(`${API_URL}/api/privacy/toggle?enabled=${enabled}`, { method: 'POST' })
                    } catch (err) {}
                  }}
                />
                <span className="toggle-switch"></span>
                <span>GHOST_MODE: {privacyEnabled ? 'ACTIVE' : 'OFF'}</span>
              </label>
              {privacyEnabled && (
                <label className="toggle-label">
                  <input
                    type="checkbox"
                    checked={showRaw}
                    onChange={(e) => setShowRaw(e.target.checked)}
                  />
                  <span>SHOW_RAW</span>
                </label>
              )}
            </div>
          )}
          <button className="btn btn-demo" onClick={() => startDemo('empty-room-appliances-on')}>
            [ DEMO: WASTE ]
          </button>
          <button className="btn btn-demo" onClick={() => startDemo('occupied-normal')}>
            [ DEMO: NORMAL ]
          </button>
          {demoMode && (
            <button className="btn btn-stop" onClick={stopDemo}>
              TERMINATE_DEMO
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
                  alt="Live Pixel Feed" 
                />
                {privacyEnabled && !showRaw && (
                  <div className="privacy-badge">PRIVACY PROTECTION ENABLED</div>
                )}
                {showRaw && (
                  <div className="raw-badge">RAW VIDEO FEED EXPOSED</div>
                )}
              </div>
            ) : (
              <div className="no-feed">
                <div className="no-feed-icon">00101</div>
                <p>WAITING FOR SOURCE...</p>
                <p className="no-feed-hint">Ready for input stream.</p>
              </div>
            )}
          </div>
          
          <div className="status-banner">
            <div className={`status-indicator ${roomStatus}`}>
              {roomStatus === 'waste' ? '!!! ENERGY WASTE DETECTED !!!' : 'SYSTEM SECURE - ALL CLEAR'}
            </div>
            {isEnergyWaste && (
              <div className="waste-alert">
                Anomalous power usage in empty zone. Est. Savings: ${potentialSavings.toFixed(2)}/hr
              </div>
            )}
          </div>
        </div>

        <div className="metrics-section">
          <div className="panel-card">
            <h3>OBJECT_LOG / ROOM_101</h3>
            <div className="status-grid">
              <div className="status-item">
                <span className="status-label">OCCUPANTS</span>
                <span className="status-value large">{personCount.toString().padStart(2, '0')}</span>
              </div>
              <div className="status-item">
                <span className="status-label">LUMINANCE</span>
                <span className={`status-value ${lightStatus === 'ON' ? 'on' : 'off'}`}>{lightStatus}</span>
              </div>
              <div className="status-item">
                <span className="status-label">VENTILATION</span>
                <span className={`status-value ${fanStatus === 'ON' ? 'on' : 'off'}`}>{fanStatus}</span>
              </div>
              <div className="status-item">
                <span className="status-label">DISPLAY_UNIT</span>
                <span className={`status-value ${monitorStatus === 'ON' ? 'on' : 'off'}`}>{monitorStatus}</span>
              </div>
              <div className="status-item" style={{gridColumn: 'span 2'}}>
                <span className="status-label">THREAT_LEVEL</span>
                <span className={`status-value ${roomStatus}`} style={{fontSize: '1.2rem'}}>{roomStatus === 'waste' ? 'CRITICAL' : 'ZERO'}</span>
              </div>
            </div>
          </div>

          <div className="panel-card">
            <h3>ENERGY_CONSUMPTION_DATA</h3>
            <div className="energy-grid">
              <div className="energy-item">
                <span className="energy-label">LOAD_WATTS</span>
                <span className="energy-value">{estimatedWatts}W</span>
              </div>
              <div className="energy-item">
                <span className="energy-label">RATE_USD/H</span>
                <span className="energy-value">${costPerHour.toFixed(2)}</span>
              </div>
              <div className="energy-item highlight">
                <span className="energy-label">TOTAL_CUMULATIVE_WASTE</span>
                <span className="energy-value">${cumulativeCost.toFixed(4)}</span>
              </div>
              <div className="energy-item">
                <span className="energy-label">WASTE_TIMER</span>
                <span className="energy-value">{Math.floor(wasteDuration / 60)}M {Math.floor(wasteDuration % 60)}S</span>
              </div>
            </div>
          </div>

          {alertEvents.length > 0 && (
            <div className="panel-card alert-panel">
              <h3>SYSTEM_ALERTS_HISTORY</h3>
              <div className="alert-events">
                {alertEvents.map((event, i) => (
                  <div key={i} className="alert-event">
                    <span className="event-time">[{new Date(event.timestamp * 1000).toLocaleTimeString([], {hour12: false})}]</span>
                    <span className="event-room">{event.room_name}</span>
                    <span className="event-duration">{Math.floor(event.duration_seconds)}S WASTE</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="panel-card">
            <h3>CORE_SPECS</h3>
            <div className="status-grid">
              <div className="status-item">
                <span className="status-label">STATUS</span>
                <span className="status-value" style={{fontSize: '0.9rem', color: connected ? '#00ff9d' : '#94a3b8'}}>{connected ? 'ONLINE' : 'OFFLINE'}</span>
              </div>
              <div className="status-item">
                <span className="status-label">MODE</span>
                <span className="status-value" style={{fontSize: '0.9rem'}}>{demoMode ? 'TEST' : 'LIVE'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App