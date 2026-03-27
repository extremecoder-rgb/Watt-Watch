import { useState, useEffect, useRef } from 'react'
import './App.css'

const API_URL = 'http://localhost:8000'
const WS_URL = API_URL.replace('http', 'ws')

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [cameraUrl, setCameraUrl] = useState('http://192.168.0.154:8080/video')
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
  const [wasteDuration, setWasteDuration] = useState(0)
  const [energyMetrics, setEnergyMetrics] = useState({})
  const [microzoneData, setMicrozoneData] = useState(null)
  
  // Database dashboard state
  const [dbInfo, setDbInfo] = useState(null)
  const [privacyVerify, setPrivacyVerify] = useState(null)
  
  const wsRef = useRef(null)
  const fpsCounter = useRef({ count: 0, lastTime: Date.now() })
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

  useEffect(() => {
    if (activeTab !== 'database') return
    const fetchDbInfo = async () => {
      try {
        const [dbRes, pvRes] = await Promise.all([
          fetch(`${API_URL}/api/database/info`),
          fetch(`${API_URL}/api/privacy/verify`)
        ])
        setDbInfo(await dbRes.json())
        setPrivacyVerify(await pvRes.json())
      } catch (err) {}
    }
    fetchDbInfo()
  }, [activeTab])

  useEffect(() => {
    if (!connected) return
    const fetchData = async () => {
      try {
        const [eventsRes, metricsRes] = await Promise.all([
          fetch(`${API_URL}/api/alerts/events?limit=8`),
          fetch(`${API_URL}/api/energy/metrics`)
        ])
        const eventsData = await eventsRes.json()
        setAlertEvents(eventsData.events || [])
        const metricsData = await metricsRes.json()
        setEnergyMetrics(metricsData.rooms?.['room-101'] || {})
      } catch (err) {}
    }
    fetchData()
    const interval = setInterval(fetchData, 4000)
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
        body: JSON.stringify({ url: cameraUrl })
      })
      if (!response.ok) { setConnecting(false); return; }
      setConnected(true)
      setConnecting(false)
      const ws = new WebSocket(`${WS_URL}/ws/stream`)
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
            // Real latency = time it took from server capture/process to client receive
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
    try { await fetch(`${API_URL}/api/camera/disconnect`, { method: 'POST' }) } catch (e) {}
    setConnected(false)
    setFrame(null)
  }

  const startDemo = (scenario) => {
    setDemoMode(true)
    setRoomStatus(scenario === 'empty-room-appliances-on' ? 'waste' : 'secure')
  }

  const stopDemo = () => setDemoMode(false)

  const isEnergyWaste = roomStatus === 'waste'
  const estimatedWatts = connected && energyMetrics.estimated_watts ? energyMetrics.estimated_watts : 0
  const costPerHour = connected && energyMetrics.cost_per_hour ? energyMetrics.cost_per_hour : 0
  const cumulativeCost = connected && energyMetrics.cumulative_cost ? energyMetrics.cumulative_cost : 0
  const potentialSavings = connected && energyMetrics.potential_savings_per_hour ? energyMetrics.potential_savings_per_hour : 0
  const potentialWatts = roomStatus === 'waste' ? estimatedWatts : 0

  return (
    <div className="dashboard">
      <header className="main-header">
        <div className="branding">
          <div className="logo-section">
            <span className="logo-main">CAM SENSE</span>
            <span className="logo-sub">INTEL_MONITORING V1.0.4</span>
          </div>
          <div className="status-badge pulse">SYSTEM_ACTIVE</div>
        </div>

        <div className="telemetry">
          <div className="tele-item">
            <span className="label">UPTIME</span>
            <span className="val">{formatTime(runningTime)}</span>
          </div>
          <div className="tele-item">
            <span className="label">STREAM_FPS</span>
            <span className="val">{fps}</span>
          </div>
          <div className="tele-item">
            <span className="label">LATENCY</span>
            <span className="val">{connected ? `${processingTime.toFixed(0)}ms` : '---'}</span>
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
            <section className="ctrl-group">
              <h4 className="section-title">SYSTEM_SOURCE</h4>
              <div className="input-row">
                <input type="text" value={cameraUrl} onChange={(e) => setCameraUrl(e.target.value)} disabled={connected} />
                {!connected ? (
                  <button className="btn btn-primary" onClick={connect} disabled={connecting}>{connecting ? '...' : 'CONNECT'}</button>
                ) : (
                  <button className="btn btn-danger" onClick={disconnect}>DISCONNECT</button>
                )}
              </div>
            </section>

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

          <main className="main-viewport">
            <div className="video-container">
              <div className="video-header">
                <span className="v-tag">ROOM_101 // LVL_GRID</span>
                <span className={`v-alert ${roomStatus}`}>{roomStatus === 'waste' ? '!!! WASTE_DETECTED !!!' : 'SECURE'}</span>
              </div>
              <div className="video-frame">
                {frame || demoMode ? (
                  <img src={showRaw && rawFrame ? rawFrame : frame} alt="Live feed" className="pixel-stream" />
                ) : (
                  <div className="placeholder">WAITING_FOR_UPLINK</div>
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
          </main>

          <aside className="sidebar-right">
            <div className="glass-card">
              <h4 className="card-title">◈ OBJECT_LOG</h4>
              <div className="obj-grid">
                <div className="obj-item major"><span className="l">OCCUPANTS</span><span className="v">{personCount.toString().padStart(2, '0')}</span></div>
                <div className="obj-item"><span className="l">LUMINANCE</span><span className={`v ${lightStatus === 'ON' ? 'on' : ''}`}>{lightStatus}</span></div>
                <div className="obj-item"><span className="l">VENTILATION</span><span className={`v ${fanStatus === 'ON' ? 'on' : ''}`}>{fanStatus}</span></div>
              </div>
            </div>

            <div className="glass-card">
              <h4 className="card-title">◈ ANALYTICS</h4>
              <div className="metrics-stack">
                <div className="m-row"><span className="l">LOAD</span><span className="v">{estimatedWatts}W</span></div>
                <div className={`m-row waste ${cumulativeCost > 0 ? 'active' : ''}`}><span className="l">CUMULATIVE_WASTE</span><span className="v">${cumulativeCost.toFixed(4)}</span></div>
              </div>
            </div>

            {microzoneData && (
              <div className="glass-card">
                <h4 className="card-title">◈ MICRO_INTEL</h4>
                <div className="heat-grid" style={{ gridTemplateColumns: `repeat(${microzoneData.cols || 4}, 1fr)` }}>
                  {microzoneData.heatmap && microzoneData.heatmap.flat().map((v, i) => (
                    <div key={i} className="heat-cell" style={{ background: `hsla(${240 - v * 240}, 80%, 40%, ${v * 0.75})` }} />
                  ))}
                </div>
                <div className="efficiency-box">
                  <label>EFFICIENCY_SCORE</label>
                  <div className="progress-bg"><div className="progress-fg" style={{ width: `${microzoneData.efficiency_score}%` }} /></div>
                </div>
              </div>
            )}

            <div className="glass-card history">
              <h4 className="card-title">◈ ALERT_HISTORY</h4>
              <div className="event-list">
                {alertEvents.map((e, i) => (
                  <div key={i} className="event-item">
                    <span className="t">[{new Date(e.timestamp * 1000).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit', second:'2-digit', hour12:false})}]</span>
                    <span className="d">{Math.floor(e.duration_seconds)}S_WASTE</span>
                  </div>
                ))}
              </div>
            </div>
          </aside>
        </div>
      )}
    </div>
  )
}

export default App