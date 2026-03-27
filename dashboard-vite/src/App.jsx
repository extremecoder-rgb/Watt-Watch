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
  const [activeTab, setActiveTab] = useState('monitor')
  const [runningTime, setRunningTime] = useState(0)
  const [calibrationData, setCalibrationData] = useState({})
  const [calibrationLoading, setCalibrationLoading] = useState(false)
  const [energyDashboard, setEnergyDashboard] = useState({})
  const [privacyAssurance, setPrivacyAssurance] = useState({})
  
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
    if (activeTab === 'calibration') {
      fetchCalibration()
    }
    if (activeTab === 'dashboard') {
      fetchEnergyDashboard()
    }
    if (activeTab === 'privacy') {
      fetchPrivacyAssurance()
    }
  }, [activeTab])

  const fetchEnergyDashboard = async () => {
    try {
      const res = await fetch(`${API_URL}/api/energy/dashboard`)
      const data = await res.json()
      setEnergyDashboard(data)
    } catch (err) {
      console.error('Failed to fetch energy dashboard:', err)
    }
  }

  const fetchPrivacyAssurance = async () => {
    try {
      const res = await fetch(`${API_URL}/api/privacy/assurance`)
      const data = await res.json()
      setPrivacyAssurance(data)
    } catch (err) {
      console.error('Failed to fetch privacy assurance:', err)
    }
  }

  const fetchCalibration = async () => {
    setCalibrationLoading(true)
    try {
      const res = await fetch(`${API_URL}/api/calibration`)
      const data = await res.json()
      setCalibrationData(data)
    } catch (err) {
      console.error('Failed to fetch calibration:', err)
    }
    setCalibrationLoading(false)
  }

  const updateCalibration = async (roomId, dayDark, dayMedium, nightDark, nightMedium) => {
    try {
      const res = await fetch(`${API_URL}/api/calibration`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          room_id: roomId,
          day_dark: dayDark,
          day_medium: dayMedium,
          night_dark: nightDark,
          night_medium: nightMedium
        })
      })
      const data = await res.json()
      if (data.status === 'success') {
        fetchCalibration()
      }
    } catch (err) {
      console.error('Failed to update calibration:', err)
    }
  }

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
          <div className={`m-row waste ${cumulativeCost > 0 ? 'active' : ''}`}><span className="l">CUMULATIVE_WASTE</span><span className="v">₹{cumulativeCost.toFixed(4)}</span></div>
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
          <button className={`nav-btn ${activeTab === 'monitor' ? 'active' : ''}`} onClick={() => setActiveTab('monitor')}>◈ MONITOR</button>
          <button className={`nav-btn ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveTab('dashboard')}>◈ SUMMARY</button>
          <button className={`nav-btn ${activeTab === 'privacy' ? 'active' : ''}`} onClick={() => setActiveTab('privacy')}>◈ PRIVACY</button>
          <button className={`nav-btn ${activeTab === 'calibration' ? 'active' : ''}`} onClick={() => setActiveTab('calibration')}>◈ CALIBRATE</button>
          <button className={`nav-btn ${activeTab === 'database' ? 'active' : ''}`} onClick={() => setActiveTab('database')}>◈ DATABASE</button>
        </nav>
      </header>

      {activeTab === 'monitor' && (
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

      {activeTab === 'calibration' && (
        <div className="dashboard-grid">
          <aside className="sidebar-left">
            <section className="ctrl-group">
              <h4 className="section-title">INTENSITY_CALIBRATION</h4>
              <p style={{ fontSize: '11px', opacity: 0.7, marginBottom: '12px' }}>
                Adjust brightness thresholds per room for accurate occupancy detection.
              </p>
              <button className="btn btn-primary" onClick={fetchCalibration} style={{ width: '100%' }}>
                REFRESH
              </button>
            </section>
          </aside>

          <main className="main-viewport">
            {calibrationLoading ? (
              <div style={{ padding: '40px', textAlign: 'center' }}>Loading calibration data...</div>
            ) : (
              <div style={{ padding: '20px' }}>
                <div className="glass-card">
                  <h4 className="card-title">◈ GLOBAL_SETTINGS</h4>
                  <div style={{ display: 'flex', gap: '20px', marginBottom: '16px' }}>
                    <div>
                      <span className="l">DAY_START</span>
                      <span className="v">{calibrationData.day_start_hour || 6}:00</span>
                    </div>
                    <div>
                      <span className="l">DAY_END</span>
                      <span className="v">{calibrationData.day_end_hour || 18}:00</span>
                    </div>
                    <div>
                      <span className="l">STATUS</span>
                      <span className={`v ${calibrationData.enabled ? 'on' : ''}`}>
                        {calibrationData.enabled ? 'ENABLED' : 'DISABLED'}
                      </span>
                    </div>
                  </div>
                </div>

                <div style={{ marginTop: '16px' }}>
                  <h4 className="section-title" style={{ marginBottom: '12px' }}>◈ ROOM_THRESHOLDS</h4>
                  {Object.keys(calibrationData.rooms || {}).length > 0 ? (
                    Object.entries(calibrationData.rooms).map(([roomId, calib]) => (
                      <CalibrationCard
                        key={roomId}
                        roomId={roomId}
                        calib={calib}
                        onUpdate={updateCalibration}
                      />
                    ))
                  ) : (
                    <div className="glass-card">
                      <p style={{ textAlign: 'center', opacity: 0.6 }}>
                        No room calibrations configured.<br />
                        Run: python main.py calibrate video.mp4 --room [ROOM_ID]
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </main>

          <aside className="sidebar-right">
            <div className="glass-card">
              <h4 className="card-title">◈ HELP</h4>
              <div style={{ fontSize: '11px', lineHeight: '1.6' }}>
                <p><strong>Dark Threshold:</strong> Below this = empty/low activity</p>
                <p><strong>Medium Threshold:</strong> Below this = normal activity</p>
                <p><strong>Above Medium:</strong> High brightness (occupied)</p>
                <hr style={{ borderColor: 'rgba(255,255,255,0.1)', margin: '12px 0' }} />
                <p style={{ opacity: 0.7 }}>
                  Tip: Use CLI to auto-calibrate from sample videos, then fine-tune here.
                </p>
              </div>
            </div>
          </aside>
        </div>
      )}

      {activeTab === 'dashboard' && (
        <div className="dashboard-grid">
          <aside className="sidebar-left">
            <section className="ctrl-group">
              <h4 className="section-title">ENERGY_SUMMARY</h4>
              <p style={{ fontSize: '11px', opacity: 0.7, marginBottom: '12px' }}>
                Stakeholder one-slide energy impact report
              </p>
              <button className="btn btn-primary" onClick={fetchEnergyDashboard} style={{ width: '100%' }}>
                REFRESH
              </button>
            </section>
          </aside>

          <main className="main-viewport">
            <div style={{ padding: '20px' }}>
              <div className="glass-card" style={{ background: 'linear-gradient(135deg, #1a3a2a 0%, #0d2818 100%)' }}>
                <h4 className="card-title">◈ ANNUAL_PROJECTIONS</h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px', marginTop: '16px' }}>
                  <div style={{ textAlign: 'center', padding: '20px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>
                    <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#4ade80' }}>
                      {energyDashboard.projections?.kwh_per_day || 0}
                    </div>
                    <div style={{ fontSize: '12px', opacity: 0.7, marginTop: '8px' }}>kWh / DAY</div>
                  </div>
                  <div style={{ textAlign: 'center', padding: '20px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>
                    <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#fbbf24' }}>
                      ₹{energyDashboard.projections?.inr_per_year || 0}
                    </div>
                    <div style={{ fontSize: '12px', opacity: 0.7, marginTop: '8px' }}>SAVINGS / YEAR (INR)</div>
                  </div>
                  <div style={{ textAlign: 'center', padding: '20px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>
                    <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#60a5fa' }}>
                      {energyDashboard.projections?.co2_per_year_kg || 0}
                    </div>
                    <div style={{ fontSize: '12px', opacity: 0.7, marginTop: '8px' }}>kg CO₂ / YEAR</div>
                  </div>
                </div>
              </div>

              <div className="glass-card" style={{ marginTop: '16px' }}>
                <h4 className="card-title">◈ LAST_30_DAYS</h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginTop: '12px' }}>
                  <div><span className="l">ENERGY_SAVED</span><span className="v">{energyDashboard.total_energy_saved_kwh || 0} kWh</span></div>
                  <div><span className="l">COST_(INR)</span><span className="v">₹{energyDashboard.total_cost_saved_inr || 0}</span></div>
                  <div><span className="l">COST_(INR)</span><span className="v">₹{energyDashboard.total_cost_saved_inr || 0}</span></div>
                  <div><span className="l">CO2_SAVED</span><span className="v">{energyDashboard.total_co2_saved_kg || 0} kg</span></div>
                </div>
              </div>

              <div style={{ marginTop: '16px' }}>
                <h4 className="section-title" style={{ marginBottom: '12px' }}>◈ BY_ROOM</h4>
                {Object.keys(energyDashboard.rooms || {}).length > 0 ? (
                  Object.entries(energyDashboard.rooms).map(([roomId, data]) => (
                    <div key={roomId} className="glass-card" style={{ marginBottom: '8px', padding: '12px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontWeight: 'bold' }}>{roomId.toUpperCase()}</span>
                        <div style={{ display: 'flex', gap: '20px', fontSize: '11px' }}>
                          <span><span style={{ opacity: 0.6 }}>kWh/d:</span> {data.kwh_per_day}</span>
                          <span><span style={{ opacity: 0.6 }}>₹/yr:</span> ₹{data.inr_per_year}</span>
                          <span><span style={{ opacity: 0.6 }}>CO₂/yr:</span> {data.co2_per_year_kg}kg</span>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="glass-card" style={{ textAlign: 'center', opacity: 0.6 }}>
                    No room data available yet
                  </div>
                )}
              </div>
            </div>
          </main>

          <aside className="sidebar-right">
            <div className="glass-card">
              <h4 className="card-title">◈ CONFIG</h4>
              <div style={{ fontSize: '11px', lineHeight: '1.8' }}>
                <p><span style={{ opacity: 0.6 }}>Rate (INR):</span> ₹{energyDashboard.config?.electricity_rate_inr || 6.50}/kWh</p>
                <p><span style={{ opacity: 0.6 }}>Rate (INR):</span> ₹{energyDashboard.config?.electricity_rate_inr || 6.50}/kWh</p>
                <p><span style={{ opacity: 0.6 }}>CO₂ Factor:</span> {energyDashboard.config?.co2_factor_kg_per_kwh || 0.71} kg/kWh</p>
                <hr style={{ borderColor: 'rgba(255,255,255,0.1)', margin: '12px 0' }} />
                <p><span style={{ opacity: 0.6 }}>Total Load:</span> {energyDashboard.config?.total_appliance_watts || 140}W</p>
                <p style={{ fontSize: '10px', opacity: 0.5 }}>Light: {energyDashboard.config?.wattage_breakdown?.light || 40}W | Fan: {energyDashboard.config?.wattage_breakdown?.ceiling_fan || 65}W | Monitor: {energyDashboard.config?.wattage_breakdown?.monitor || 35}W</p>
              </div>
            </div>
          </aside>
        </div>
      )}

      {activeTab === 'privacy' && (
        <div className="dashboard-grid">
          <aside className="sidebar-left">
            <section className="ctrl-group">
              <h4 className="section-title">PRIVACY_ASSURANCE</h4>
              <p style={{ fontSize: '11px', opacity: 0.7, marginBottom: '12px' }}>
                Stakeholder privacy commitment report
              </p>
              <button className="btn btn-primary" onClick={fetchPrivacyAssurance} style={{ width: '100%' }}>
                REFRESH
              </button>
            </section>
          </aside>

          <main className="main-viewport">
            <div style={{ padding: '20px' }}>
              <div className="glass-card" style={{ background: 'linear-gradient(135deg, #1a2a3a 0%, #0d1828 100%)' }}>
                <h4 className="card-title">◈ PRIVACY_MEASURES</h4>
                <div style={{ marginTop: '16px' }}>
                  {Object.entries(privacyAssurance.measures || {}).map(([key, measure]) => (
                    <div key={key} style={{ display: 'flex', alignItems: 'center', padding: '12px', background: 'rgba(0,0,0,0.2)', borderRadius: '6px', marginBottom: '8px' }}>
                      <span style={{ 
                        width: '10px', height: '10px', borderRadius: '50%', 
                        background: measure.status === 'active' || measure.status === 'enabled' ? '#4ade80' : '#f87171',
                        marginRight: '12px'
                      }} />
                      <div>
                        <div style={{ fontWeight: 'bold', fontSize: '12px' }}>{key.replace('_', ' ').toUpperCase()}</div>
                        <div style={{ fontSize: '11px', opacity: 0.7 }}>{measure.description || measure.status}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="glass-card" style={{ marginTop: '16px' }}>
                <h4 className="card-title">◈ STAKEHOLDER_COMMITMENTS</h4>
                <ul style={{ marginTop: '12px', paddingLeft: '20px', fontSize: '12px', lineHeight: '2' }}>
                  {(privacyAssurance.stakeholder_commitments || []).map((commitment, idx) => (
                    <li key={idx} style={{ color: '#4ade80' }}>✓ {commitment}</li>
                  ))}
                </ul>
              </div>

              <div className="glass-card" style={{ marginTop: '16px' }}>
                <h4 className="card-title">◈ COMPLIANCE</h4>
                <div style={{ display: 'flex', gap: '20px', marginTop: '12px' }}>
                  {Object.entries(privacyAssurance.compliance || {}).map(([key, value]) => (
                    <div key={key} style={{ 
                      padding: '12px 20px', 
                      background: value ? 'rgba(74, 222, 128, 0.2)' : 'rgba(248, 113, 113, 0.2)',
                      borderRadius: '6px',
                      border: `1px solid ${value ? '#4ade80' : '#f87171'}`
                    }}>
                      <span style={{ fontSize: '12px' }}>{key.replace('_', ' ').toUpperCase()}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="glass-card" style={{ marginTop: '16px', background: 'rgba(0,0,0,0.3)' }}>
                <h4 className="card-title">◈ DATA_RETENTION</h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginTop: '12px', fontSize: '11px' }}>
                  <div><span style={{ opacity: 0.6 }}>Raw Images:</span><br /><span style={{ color: '#4ade80' }}>{privacyAssurance.measures?.data_retention?.config?.raw_images || 'Never stored'}</span></div>
                  <div><span style={{ opacity: 0.6 }}>Thumbnails:</span><br /><span>{privacyAssurance.measures?.data_retention?.config?.anonymized_thumbnails || '30 days'}</span></div>
                  <div><span style={{ opacity: 0.6 }}>Detection Logs:</span><br /><span>90 days</span></div>
                </div>
              </div>
            </div>
          </main>

          <aside className="sidebar-right">
            <div className="glass-card">
              <h4 className="card-title">◈ VERIFICATION</h4>
              <div style={{ fontSize: '11px', lineHeight: '1.8' }}>
                <p><span style={{ opacity: 0.6 }}>Status:</span> <span style={{ color: '#4ade80' }}>VERIFIED</span></p>
                <p><span style={{ opacity: 0.6 }}>Last Checked:</span><br />{privacyAssurance.last_verified || 'N/A'}</p>
                <hr style={{ borderColor: 'rgba(255,255,255,0.1)', margin: '12px 0' }} />
                <p style={{ fontSize: '10px', opacity: 0.7 }}>
                  This system processes all data locally with no cloud transmission. 
                  All faces are automatically anonymized before any storage.
                </p>
              </div>
            </div>
          </aside>
        </div>
      )}
    </div>
  )
}

function CalibrationCard({ roomId, calib, onUpdate }) {
  const [dayDark, setDayDark] = useState(calib?.day?.dark_threshold || 80)
  const [dayMedium, setDayMedium] = useState(calib?.day?.medium_threshold || 160)
  const [nightDark, setNightDark] = useState(calib?.night?.dark_threshold || 40)
  const [nightMedium, setNightMedium] = useState(calib?.night?.medium_threshold || 100)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    setDayDark(calib?.day?.dark_threshold || 80)
    setDayMedium(calib?.day?.medium_threshold || 160)
    setNightDark(calib?.night?.dark_threshold || 40)
    setNightMedium(calib?.night?.medium_threshold || 100)
  }, [calib])

  const handleSave = () => {
    onUpdate(roomId, dayDark, dayMedium, nightDark, nightMedium)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="glass-card" style={{ marginBottom: '12px' }}>
      <h4 className="card-title">◈ {roomId.toUpperCase()}</h4>
      {calib?.last_calibrated && (
        <p style={{ fontSize: '10px', opacity: 0.5, marginBottom: '12px' }}>
          Last updated: {calib.last_calibrated}
        </p>
      )}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        <div>
          <p style={{ fontSize: '11px', marginBottom: '8px', color: '#4ade80' }}>DAY THRESHOLDS</p>
          <div className="input-row" style={{ marginBottom: '8px' }}>
            <span style={{ fontSize: '10px', width: '60px' }}>Dark &lt;</span>
            <input
              type="number"
              value={dayDark}
              onChange={(e) => setDayDark(parseInt(e.target.value) || 0)}
              min="0" max="255"
              style={{ width: '60px', padding: '4px' }}
            />
          </div>
          <div className="input-row">
            <span style={{ fontSize: '10px', width: '60px' }}>Medium &lt;</span>
            <input
              type="number"
              value={dayMedium}
              onChange={(e) => setDayMedium(parseInt(e.target.value) || 0)}
              min="0" max="255"
              style={{ width: '60px', padding: '4px' }}
            />
          </div>
        </div>
        <div>
          <p style={{ fontSize: '11px', marginBottom: '8px', color: '#60a5fa' }}>NIGHT THRESHOLDS</p>
          <div className="input-row" style={{ marginBottom: '8px' }}>
            <span style={{ fontSize: '10px', width: '60px' }}>Dark &lt;</span>
            <input
              type="number"
              value={nightDark}
              onChange={(e) => setNightDark(parseInt(e.target.value) || 0)}
              min="0" max="255"
              style={{ width: '60px', padding: '4px' }}
            />
          </div>
          <div className="input-row">
            <span style={{ fontSize: '10px', width: '60px' }}>Medium &lt;</span>
            <input
              type="number"
              value={nightMedium}
              onChange={(e) => setNightMedium(parseInt(e.target.value) || 0)}
              min="0" max="255"
              style={{ width: '60px', padding: '4px' }}
            />
          </div>
        </div>
      </div>
      <button
        className={`btn ${saved ? 'btn-primary' : 'btn-outline'}`}
        onClick={handleSave}
        style={{ marginTop: '12px', width: '100%' }}
      >
        {saved ? 'SAVED!' : 'SAVE THRESHOLDS'}
      </button>
    </div>
  )
}

export default App