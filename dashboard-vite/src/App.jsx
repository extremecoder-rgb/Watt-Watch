import { useState, useEffect, useRef } from 'react'
import './App.css'

const API_URL = 'http://localhost:8000'
const WS_URL = API_URL.replace('http', 'ws')

function useRoom(roomId, defaultUrl) {
  const [url, setUrl] = useState(defaultUrl)
  const [connected, setConnected] = useState(false)
  const [connecting, setConnecting] = useState(false)
  const [fps, setFps] = useState(0)
  const [frame, setFrame] = useState(null)
  const [rawFrame, setRawFrame] = useState(null)
  
  const [personCount, setPersonCount] = useState(0)
  const [lightStatus, setLightStatus] = useState('OFF')
  const [fanStatus, setFanStatus] = useState('OFF')
  const [monitorStatus, setMonitorStatus] = useState('OFF')
  const [roomStatus, setRoomStatus] = useState('secure')
  const [processingTime, setProcessingTime] = useState(0)
  
  const [microzoneData, setMicrozoneData] = useState(null)
  
  const wsRef = useRef(null)
  const fpsCounter = useRef({ count: 0, lastTime: Date.now() })
  
  const connect = async () => {
    setConnecting(true)
    try {
      const response = await fetch(`${API_URL}/api/camera/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, room_id: roomId })
      })
      if (!response.ok) { setConnecting(false); return; }
      
      setConnected(true)
      setConnecting(false)
      const ws = new WebSocket(`${WS_URL}/ws/stream/${roomId}`)
      wsRef.current = ws
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.frame) setFrame(data.frame)
          if (data.raw_frame) setRawFrame(data.raw_frame)
          setPersonCount(data.person_count)
          setLightStatus(data.light_status)
          setFanStatus(data.fan_status)
          setMonitorStatus(data.monitor_status || 'OFF')
          
          if (data.processing_time_ms !== undefined) {
            const serverTime = data.timestamp * 1000
            const now = Date.now()
            const realLatency = Math.max(0, now - serverTime)
            setProcessingTime(realLatency)
          }
          if (data.microzone) setMicrozoneData(data.microzone)
          
          const isWaste = data.person_count === 0 && (data.light_status === 'ON' || data.fan_status === 'ON' || data.monitor_status === 'ON')
          setRoomStatus(isWaste ? 'waste' : 'secure')
          
          fpsCounter.current.count++
          const now = Date.now()
          if (now - fpsCounter.current.lastTime >= 1000) {
            setFps(fpsCounter.current.count)
            fpsCounter.current.count = 0
            fpsCounter.current.lastTime = now
          }
        } catch (err) {}
      }
      ws.onclose = () => setConnected(false)
    } catch (err) { setConnecting(false) }
  }

  const disconnect = async () => {
    if (wsRef.current) wsRef.current.close()
    try { 
      await fetch(`${API_URL}/api/camera/disconnect`, { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ room_id: roomId })
      }) 
    } catch (e) {}
    setConnected(false)
    setFrame(null)
  }

  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close()
    }
  }, [])

  return {
    roomId, url, setUrl, connected, connecting, fps, frame, rawFrame,
    personCount, lightStatus, fanStatus, monitorStatus, roomStatus, setRoomStatus, 
    processingTime, microzoneData, connect, disconnect
  }
}


function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [runningTime, setRunningTime] = useState(0)
  
  const room1 = useRoom('room-101', 'http://192.168.0.154:8080/video')
  const room2 = useRoom('room-102', 'http://192.168.0.155:8080/video')
  
  const [demoMode, setDemoMode] = useState(false)
  const [privacyEnabled, setPrivacyEnabled] = useState(true)
  const [showRaw, setShowRaw] = useState(false)
  
  const [alertEvents, setAlertEvents] = useState([])
  const [energyMetrics, setEnergyMetrics] = useState({})
  
  const startTime = useRef(Date.now())

  useEffect(() => {
    const timer = setInterval(() => {
      setRunningTime(Math.floor((Date.now() - startTime.current) / 1000))
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    // Only fetch alerts/metrics if at least one room is connected
    if (!room1.connected && !room2.connected) return
    const fetchData = async () => {
      try {
        const [eventsRes, metricsRes] = await Promise.all([
          fetch(`${API_URL}/api/alerts/events?limit=8`),
          fetch(`${API_URL}/api/energy/metrics`)
        ])
        const eventsData = await eventsRes.json()
        setAlertEvents(eventsData.events || [])
        const metricsData = await metricsRes.json()
        setEnergyMetrics(metricsData.rooms || {})
      } catch (err) {}
    }
    fetchData()
    const interval = setInterval(fetchData, 4000)
    return () => clearInterval(interval)
  }, [room1.connected, room2.connected])

  const formatTime = (seconds) => {
    const hrs = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const startDemo = (scenario) => {
    setDemoMode(true)
    const stat = scenario === 'empty-room-appliances-on' ? 'waste' : 'secure'
    room1.setRoomStatus(stat)
    room2.setRoomStatus(stat)
  }

  const stopDemo = () => setDemoMode(false)

  const renderRoomControls = (room, nameLabel) => (
    <section className="ctrl-group">
      <h4 className="section-title">{nameLabel}</h4>
      <div className="input-row">
        <input type="text" value={room.url} onChange={(e) => room.setUrl(e.target.value)} disabled={room.connected} />
        {!room.connected ? (
          <button className="btn btn-primary" onClick={room.connect} disabled={room.connecting}>{room.connecting ? '...' : 'CONNECT'}</button>
        ) : (
          <button className="btn btn-danger" onClick={room.disconnect}>DISCONNECT</button>
        )}
      </div>
    </section>
  )

  const renderVideoContainer = (room, title) => {
    const isEnergyWaste = room.roomStatus === 'waste'
    const rMetrics = energyMetrics[room.roomId] || {}
    const potentialWatts = isEnergyWaste && rMetrics.estimated_watts ? rMetrics.estimated_watts : 0

    return (
      <div className="video-container">
        <div className="video-header">
          <span className="v-tag">{title}</span>
          <span className={`v-alert ${room.roomStatus}`}>{room.roomStatus === 'waste' ? '!!! WASTE_DETECTED !!!' : 'SECURE'}</span>
        </div>
        <div className="video-frame">
          {room.frame || demoMode ? (
            <img src={showRaw && room.rawFrame ? room.rawFrame : room.frame} alt={`${title} feed`} className="pixel-stream" />
          ) : (
            <div className="placeholder">OFFLINE</div>
          )}
          <div className="scanline" />
          <div className="corner tl" /><div className="corner tr" />
          <div className="corner bl" /><div className="corner br" />
        </div>
        {isEnergyWaste && (
          <div className="ticker-wrap">
            <div className="ticker-text">WASTE_DETECTION_ACTIVE: REDUCE LOAD BY {potentialWatts}W IMMEDIATELY // TERM_IDLE_APPLIANCES</div>
          </div>
        )}
      </div>
    )
  }

  const renderRoomAnalytics = (room, title) => {
    const rMetrics = energyMetrics[room.roomId] || {}
    const estimatedWatts = room.connected && rMetrics.estimated_watts ? rMetrics.estimated_watts : 0
    const cumulativeCost = room.connected && rMetrics.cumulative_cost ? rMetrics.cumulative_cost : 0
    
    return (
      <div className="glass-card" style={{ marginBottom: '12px' }}>
        <h4 className="card-title">◈ {title} STATS</h4>
        <div className="obj-grid" style={{ marginBottom: '8px' }}>
          <div className="obj-item major"><span className="l">OCCUPANTS</span><span className="v">{room.personCount.toString().padStart(2, '0')}</span></div>
          <div className="obj-item"><span className="l">LUMINANCE</span><span className={`v ${room.lightStatus === 'ON' ? 'on' : ''}`}>{room.lightStatus}</span></div>
          <div className="obj-item"><span className="l">VENTILATION</span><span className={`v ${room.fanStatus === 'ON' ? 'on' : ''}`}>{room.fanStatus}</span></div>
        </div>
        <div className="metrics-stack">
          <div className="m-row"><span className="l">LOAD</span><span className="v">{estimatedWatts}W</span></div>
          <div className={`m-row waste ${cumulativeCost > 0 ? 'active' : ''}`}><span className="l">CUMULATIVE_WASTE</span><span className="v">${cumulativeCost.toFixed(4)}</span></div>
        </div>
      </div>
    )
  }

  return (
    <div className="dashboard">
      <header className="main-header">
        <div className="branding">
          <div className="logo-section">
            <span className="logo-main">CAM SENSE</span>
            <span className="logo-sub">INTEL_MONITORING V2.0</span>
          </div>
          <div className="status-badge pulse">SYSTEM_ACTIVE</div>
        </div>

        <div className="telemetry">
          <div className="tele-item">
            <span className="label">UPTIME</span>
            <span className="val">{formatTime(runningTime)}</span>
          </div>
          <div className="tele-item">
            <span className="label">AVG_FPS</span>
            <span className="val">{Math.max(room1.fps, room2.fps)}</span>
          </div>
          <div className="tele-item">
            <span className="label">LATENCY</span>
            <span className="val">{(room1.connected || room2.connected) ? `${Math.max(room1.processingTime, room2.processingTime).toFixed(0)}ms` : '---'}</span>
          </div>
        </div>

        <nav className="header-nav">
          <button className={`nav-btn ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveTab('dashboard')}>◈ MONITOR</button>
          <button className={`nav-btn ${activeTab === 'database' ? 'active' : ''}`} onClick={() => setActiveTab('database')}>◈ DATABASE</button>
        </nav>
      </header>

      {activeTab === 'dashboard' && (
        <div className="dashboard-grid">
          <aside className="sidebar-left">
            {renderRoomControls(room1, 'SOURCE // ROOM_101')}
            {renderRoomControls(room2, 'SOURCE // ROOM_102')}

            <section className="ctrl-group">
              <h4 className="section-title">SECURE_FILTERS</h4>
              <div className={`filter-card ${privacyEnabled ? 'active' : ''}`}>
                <label className="checkbox-wrap">
                  <input type="checkbox" checked={privacyEnabled} onChange={(e) => setPrivacyEnabled(e.target.checked)} />
                  <span className="check-label">GHOST_MODE</span>
                </label>
                <p className="filter-desc">{privacyEnabled ? 'PIXEL_PROTECT_ENABLED' : 'RAW_FEED_EXPOSED'}</p>
              </div>
            </section>

            <section className="ctrl-group">
              <h4 className="section-title">TEST_SEQUENCES</h4>
              <div className="demo-btns">
                <button className="btn btn-outline" onClick={() => startDemo('empty-room-appliances-on')}>EMIT_WASTE</button>
                <button className="btn btn-outline" onClick={() => startDemo('occupied-normal')}>EMIT_NORMAL</button>
              </div>
            </section>
          </aside>

          <main className="main-viewport multi-room">
            {renderVideoContainer(room1, 'ROOM_101 // WEST_WING')}
            {renderVideoContainer(room2, 'ROOM_102 // EAST_WING')}
          </main>

          <aside className="sidebar-right">
            {renderRoomAnalytics(room1, 'ROOM_101')}
            {renderRoomAnalytics(room2, 'ROOM_102')}

            <div className="glass-card history">
              <h4 className="card-title">◈ RECENT_ALERTS</h4>
              <div className="event-list">
                {alertEvents.length > 0 ? alertEvents.map((e, i) => (
                  <div key={i} className="event-item">
                    <span className="t">[{new Date(e.timestamp * 1000).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit', second:'2-digit', hour12:false})}] {e.room_id}</span>
                    <span className="d">{Math.floor(e.duration_seconds)}S</span>
                  </div>
                )) : (
                  <div className="event-item" style={{ borderLeftColor: 'transparent', textAlign: 'center' }}>
                    <span className="t" style={{width: '100%', opacity: 0.5}}>NO ALERTS DETECTED</span>
                  </div>
                )}
              </div>
            </div>
          </aside>
        </div>
      )}
    </div>
  )
}

export default App