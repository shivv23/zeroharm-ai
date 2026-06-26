import React, { useState, useEffect, useCallback, useRef } from 'react';
import ws from './store/websocketStore';
import GeospatialHeatmap from './components/GeospatialHeatmap';
import RiskPanel from './components/RiskPanel';
import AlertPanel from './components/AlertPanel';
import PermitIntelligence from './components/PermitIntelligence';
import EmergencyResponse from './components/EmergencyResponse';
import IncidentPatterns from './components/IncidentPatterns';
import ActivityFeed from './components/ActivityFeed';
import RiskTrendChart from './components/RiskTrendChart';
import WhatIfSimulator from './components/WhatIfSimulator';
import CompliancePanel from './components/CompliancePanel';
import Toast from './components/Toast';
import { PLANT_ZONES, getRiskColor } from './store/plantData';

const TABS = [
  { id: 'heatmap', label: 'Heatmap', icon: '\u{1F3E0}' },
  { id: 'alerts', label: 'Alerts', icon: '\u{26A0}\uFE0F' },
  { id: 'permits', label: 'Permits', icon: '\u{1F4CB}' },
  { id: 'compliance', label: 'Audit', icon: '\u{1F4DD}' },
  { id: 'emergency', label: 'Emergency', icon: '\u{1F6A8}' },
  { id: 'scenarios', label: 'What-If', icon: '\u{1F9E9}' },
  { id: 'feed', label: 'Agents', icon: '\u{1F916}' },
  { id: 'patterns', label: 'Patterns', icon: '\u{1F50D}' },
];

const SEVERITY_SCORE = { critical: 4, high: 3, warning: 2, info: 1 };
const ALERT_FREQUENCY_HZ = 880;
const ALERT_GAIN = 0.1;
const ALERT_DURATION_S = 0.5;
const TOAST_DEFAULT_DURATION = 5000;
const TOAST_SUCCESS_DURATION = 3000;
const TOAST_CRITICAL_DURATION = 8000;
const TOAST_WARNING_DURATION = 5000;
const TOAST_EMERGENCY_DURATION = 10000;
const TOAST_SCENARIO_DURATION = 4000;
const NARROW_THRESHOLD = 1100;
const MINI_CHART_WIDTH = 80;
const MINI_CHART_HEIGHT = 24;
const SIDE_PANEL_NARROW = 240;
const SIDE_PANEL_WIDE = 340;

const COLOR_HEALTH_GOOD = '#00e676';
const COLOR_HEALTH_WARN = '#ffa000';
const COLOR_HEALTH_CRIT = '#ff1744';
const COLOR_STATUS_OFFLINE = '#6b7280';
const COLOR_BG_LOW_RISK = 'rgba(0,230,118,0.15)';
const COLOR_BG_MED_RISK = 'rgba(255,160,0,0.2)';
const COLOR_BG_HIGH_RISK = 'rgba(255,23,68,0.2)';
const COLOR_BORDER_LOW_RISK = 'rgba(0,230,118,0.3)';
const COLOR_BORDER_MED_RISK = 'rgba(255,160,0,0.4)';
const COLOR_BORDER_HIGH_RISK = 'rgba(255,23,68,0.4)';
const COLOR_TEXT_MUTED = '#6b7280';
const COLOR_TEXT_DIM = '#4b5563';
const COLOR_ACCENT_CYAN = '#00e5ff';
const COLOR_BG_PRIMARY = '#080c16';
const COLOR_BG_HEADER = '#0d1520';
const COLOR_BORDER_DARK = '#1f2937';
const COLOR_BORDER_TAB = '#1a2332';

let toastId = 0;

export default function App() {
  const [connected, setConnected] = useState(false);
  const [plantState, setPlantState] = useState(null);
  const [riskData, setRiskData] = useState(null);
  const [zoneRisks, setZoneRisks] = useState({});
  const [selectedZone, setSelectedZone] = useState(null);
  const [activeTab, setActiveTab] = useState('heatmap');
  const [alerts, setAlerts] = useState([]);
  const [showEmergencyModal, setShowEmergencyModal] = useState(false);
  const [activityFeed, setActivityFeed] = useState([]);
  const [riskTrend, setRiskTrend] = useState([]);
  const [compliance, setCompliance] = useState(null);
  const [healthIndex, setHealthIndex] = useState(null);
  const [toasts, setToasts] = useState([]);
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);

  useEffect(() => {
    const onResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const isNarrow = windowWidth < NARROW_THRESHOLD;
  const prevSeverity = useRef('normal');
  const prevAlertCount = useRef(0);
  const audioCtx = useRef(null);

  const playAlertSound = useCallback(() => {
    try {
      if (!audioCtx.current) audioCtx.current = new (window.AudioContext || window.webkitAudioContext)();
      const ctx = audioCtx.current;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.frequency.value = ALERT_FREQUENCY_HZ;
      osc.type = 'square';
      gain.gain.setValueAtTime(ALERT_GAIN, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + ALERT_DURATION_S);
      osc.start();
      osc.stop(ctx.currentTime + ALERT_DURATION_S);
    } catch (e) { /* audio not available */ }
  }, []);

  const addToast = useCallback((message, type = 'info', duration = TOAST_DEFAULT_DURATION) => {
    const id = ++toastId;
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), duration);
  }, []);

  useEffect(() => {
    ws.connect();
    const unsub1 = ws.on('connection', (d) => {
      setConnected(d.connected);
      if (d.connected) addToast('Connected to ZeroHarm AI platform', 'success', TOAST_SUCCESS_DURATION);
    });
    const unsub2 = ws.on('state_update', (d) => {
      setPlantState(d.plant);
      setRiskData(d.risk);
      if (d.plant?.zone_risk_scores) setZoneRisks(d.plant.zone_risk_scores);
      if (d.risk?.alerts) setAlerts(d.risk.alerts);
      if (d.activity_feed) setActivityFeed(d.activity_feed);
      if (d.risk_trend) setRiskTrend(d.risk_trend);
      if (d.compliance) setCompliance(d.compliance);
      if (d.health_index) setHealthIndex(d.health_index);
      const severity = d.risk?.severity || 'normal';
      const alertCount = d.risk?.alerts?.length || 0;
      if (severity === 'critical' && prevSeverity.current !== 'critical') {
        addToast('CRITICAL: Compound risk condition detected!', 'critical', TOAST_CRITICAL_DURATION);
        playAlertSound();
      }
      if (alertCount > prevAlertCount.current + 2) {
        addToast(`${alertCount} active alerts — review recommended`, 'warning', TOAST_WARNING_DURATION);
      }
      prevSeverity.current = severity;
      prevAlertCount.current = alertCount;
    });
    const unsub3 = ws.on('emergency_triggered', () => {
      setShowEmergencyModal(true);
      addToast('EMERGENCY RESPONSE ACTIVATED', 'critical', TOAST_EMERGENCY_DURATION);
    });
    const unsub4 = ws.on('what_if_applied', (d) => {
      if (d.plant) setPlantState(d.plant);
      if (d.risk) setRiskData(d.risk);
      if (d.activity) setActivityFeed(d.activity);
      addToast('What-If scenario applied', 'warning', TOAST_SCENARIO_DURATION);
    });
    const unsub5 = ws.on('what_if_reset', (d) => {
      if (d.plant) setPlantState(d.plant);
      if (d.risk) setRiskData(d.risk);
      if (d.activity) setActivityFeed(d.activity);
      addToast('Scenario reset — normal operations', 'success', TOAST_SCENARIO_DURATION);
    });
    return () => { unsub1(); unsub2(); unsub3(); unsub4(); unsub5(); ws.disconnect(); };
  }, [addToast]);

  const triggerEmergency = useCallback((type, context = {}) => {
    ws.send({ action: 'trigger_emergency', type, context });
  }, []);

  const resolveEmergency = useCallback((id, notes = '') => {
    ws.send({ action: 'resolve_emergency', emergency_id: id, notes });
  }, []);

  const topAlert = alerts.length > 0 ? alerts.reduce((a, b) => {
    return (SEVERITY_SCORE[a.severity] || 0) > (SEVERITY_SCORE[b.severity] || 0) ? a : b;
  }) : null;

  const riskScore = riskData?.risk_score ?? 0;
  const severity = riskData?.severity ?? 'normal';

  return (
    <div style={styles.container}>
      <Toast toasts={toasts} />
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <div style={styles.logo}>
            <div style={styles.shieldIcon}>{'\u{1F6E1}\uFE0F'}</div>
            <div>
              <div style={styles.title}>ZeroHarm AI</div>
              <div style={styles.subtitle}>Industrial Safety Intelligence Platform</div>
            </div>
          </div>
          <div style={styles.headerDivider} />
          <div style={styles.healthBadge}>
            <div style={{
              ...styles.healthDot,
              background: healthIndex ? (healthIndex.overall >= 70 ? COLOR_HEALTH_GOOD : healthIndex.overall >= 50 ? COLOR_HEALTH_WARN : COLOR_HEALTH_CRIT) : COLOR_STATUS_OFFLINE
            }} />
            <span style={styles.healthText}>
              {healthIndex ? `${healthIndex.overall}% ${healthIndex.label}` : 'Loading...'}
            </span>
          </div>
        </div>
        <div style={styles.headerRight}>
          {riskTrend.length > 1 && (
            <div style={{ width: MINI_CHART_WIDTH, height: MINI_CHART_HEIGHT }}>
              <RiskTrendChart data={riskTrend} width={MINI_CHART_WIDTH} height={MINI_CHART_HEIGHT} mini />
            </div>
          )}
          <div style={styles.headerDivider} />
          <div style={{
            ...styles.riskIndicator,
            background: riskScore > 0.6 ? COLOR_BG_HIGH_RISK : riskScore > 0.3 ? COLOR_BG_MED_RISK : COLOR_BG_LOW_RISK,
            border: `1px solid ${riskScore > 0.6 ? COLOR_BORDER_HIGH_RISK : riskScore > 0.3 ? COLOR_BORDER_MED_RISK : COLOR_BORDER_LOW_RISK}`,
          }}>
            <span style={{ fontSize: 13, fontWeight: 700, color: getRiskColor(riskScore) }}>{(riskScore * 100).toFixed(0)}</span>
            <span style={{ fontSize: 9, color: COLOR_TEXT_MUTED, marginLeft: 2 }}>/100</span>
          </div>
          <div style={styles.connectionStatus}>
            <div style={{ ...styles.statusDot, background: connected ? COLOR_HEALTH_GOOD : COLOR_HEALTH_CRIT,
                          boxShadow: connected ? '0 0 8px rgba(0,230,118,0.5)' : 'none' }} />
            <span style={styles.statusText}>{connected ? 'Live' : 'Offline'}</span>
          </div>
          {topAlert && topAlert.severity === 'critical' && (
            <div style={styles.criticalBadge}>
              {'\u{26A0}\uFE0F'} CRITICAL
            </div>
          )}
        </div>
      </div>

      <div style={styles.main}>
        <div style={styles.contentArea}>
          <div style={styles.tabBar}>
            {TABS.map(t => (
              <div key={t.id}
                   style={{ ...styles.tab, ...(activeTab === t.id ? styles.activeTab : {}),
                            ...(t.id === 'emergency' ? { color: activeTab === 'emergency' ? COLOR_HEALTH_CRIT : COLOR_TEXT_MUTED } : {}) }}
                   onClick={() => setActiveTab(t.id)}>
                <span style={{ marginRight: 5 }}>{t.icon}</span>
                {t.label}
              </div>
            ))}
          </div>
          <div style={styles.tabContent}>
            {activeTab === 'heatmap' && (
              <GeospatialHeatmap zones={PLANT_ZONES} zoneRisks={zoneRisks}
                selectedZone={selectedZone} onSelectZone={setSelectedZone} plantState={plantState} />
            )}
            {activeTab === 'alerts' && <AlertPanel alerts={alerts} riskData={riskData} />}
            {activeTab === 'permits' && <PermitIntelligence permits={plantState?.active_permits || []} plantState={plantState} />}
            {activeTab === 'compliance' && <CompliancePanel compliance={compliance} />}
            {activeTab === 'emergency' && <EmergencyResponse triggerEmergency={triggerEmergency} resolveEmergency={resolveEmergency}
              showModal={showEmergencyModal} setShowModal={setShowEmergencyModal} plantState={plantState} />}
            {activeTab === 'scenarios' && <WhatIfSimulator plantState={plantState} />}
            {activeTab === 'feed' && <ActivityFeed entries={activityFeed} />}
            {activeTab === 'patterns' && <IncidentPatterns />}
          </div>
        </div>
        <div style={{...styles.sidePanel, width: isNarrow ? SIDE_PANEL_NARROW : SIDE_PANEL_WIDE}}>
          <RiskPanel riskData={riskData} zoneRisks={zoneRisks} selectedZone={selectedZone}
            plantState={plantState} riskTrend={riskTrend} compliance={compliance}
            onEmergency={() => setActiveTab('emergency')} />
        </div>
      </div>
    </div>
  );
}

const styles = {
  container: { display: 'flex', flexDirection: 'column', height: '100vh', background: COLOR_BG_PRIMARY, color: '#e0e5ec' },
  header: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '0 20px', background: 'linear-gradient(135deg, #0d1520 0%, #111827 100%)',
    borderBottom: `1px solid ${COLOR_BORDER_DARK}`, height: 50, flexShrink: 0,
  },
  headerLeft: { display: 'flex', alignItems: 'center', gap: 16 },
  logo: { display: 'flex', alignItems: 'center', gap: 10 },
  shieldIcon: { fontSize: 24 },
  title: { fontSize: 17, fontWeight: 700, background: 'linear-gradient(90deg, #00e5ff, #00bcd4)',
           WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', letterSpacing: 0.5 },
  subtitle: { fontSize: 10, color: COLOR_TEXT_DIM },
  headerDivider: { width: 1, height: 28, background: COLOR_BORDER_DARK },
  healthBadge: { display: 'flex', alignItems: 'center', gap: 6, padding: '4px 10px',
                 background: 'rgba(0,0,0,0.3)', borderRadius: 12, border: `1px solid ${COLOR_BORDER_DARK}` },
  healthDot: { width: 6, height: 6, borderRadius: '50%' },
  healthText: { fontSize: 11, color: '#9ca3af' },
  headerRight: { display: 'flex', alignItems: 'center', gap: 12 },
  riskIndicator: { display: 'flex', alignItems: 'center', gap: 2, padding: '4px 10px', borderRadius: 8 },
  connectionStatus: { display: 'flex', alignItems: 'center', gap: 6 },
  statusDot: { width: 7, height: 7, borderRadius: '50%' },
  statusText: { fontSize: 11, color: COLOR_TEXT_MUTED },
  criticalBadge: {
    background: 'linear-gradient(135deg, #ff1744, #d50000)', color: '#fff',
    padding: '2px 10px', borderRadius: 10, fontSize: 10, fontWeight: 700,
    animation: 'pulse 1.5s infinite',
  },
  main: { display: 'flex', flex: 1, overflow: 'hidden' },
  contentArea: { flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 },
  tabBar: {
    display: 'flex', background: COLOR_BG_HEADER, borderBottom: `1px solid ${COLOR_BORDER_TAB}`,
    padding: '0 8px', gap: 1, flexShrink: 0, overflowX: 'auto',
  },
  tab: {
    padding: '9px 14px', cursor: 'pointer', fontSize: 12, color: COLOR_TEXT_DIM,
    borderBottom: '2px solid transparent', transition: 'all 0.2s', userSelect: 'none',
    display: 'flex', alignItems: 'center', whiteSpace: 'nowrap',
    fontFamily: "'SF Mono', 'Fira Code', monospace",
  },
  activeTab: {
    color: COLOR_ACCENT_CYAN, borderBottomColor: COLOR_ACCENT_CYAN,
    background: 'linear-gradient(0deg, rgba(0,229,255,0.06) 0%, transparent 100%)',
  },
  tabContent: { flex: 1, overflow: 'auto', position: 'relative' },
  sidePanel: { flexShrink: 0, borderLeft: `1px solid ${COLOR_BORDER_TAB}`, overflow: 'auto' },
};
