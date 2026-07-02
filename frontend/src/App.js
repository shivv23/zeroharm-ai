import React, { useState, useEffect, useCallback, useRef, lazy, Suspense } from 'react';
import ws from './store/websocketStore';
import ErrorBoundary from './components/ErrorBoundary';
import Toast from './components/Toast';
import MobileDashboard from './components/MobileDashboard';
import PushNotificationManager from './components/PushNotificationManager';
import { PLANT_ZONES, getRiskColor } from './store/plantData';

const GeospatialHeatmap = lazy(() => import('./components/GeospatialHeatmap'));
const RiskPanel = lazy(() => import('./components/RiskPanel'));
const AlertPanel = lazy(() => import('./components/AlertPanel'));
const PermitIntelligence = lazy(() => import('./components/PermitIntelligence'));
const EmergencyResponse = lazy(() => import('./components/EmergencyResponse'));
const IncidentPatterns = lazy(() => import('./components/IncidentPatterns'));
const IncidentInvestigation = lazy(() => import('./components/IncidentInvestigation'));
const ActivityFeed = lazy(() => import('./components/ActivityFeed'));
const RiskTrendChart = lazy(() => import('./components/RiskTrendChart'));
const WhatIfSimulator = lazy(() => import('./components/WhatIfSimulator'));
const CompliancePanel = lazy(() => import('./components/CompliancePanel'));
const SafetyGamification = lazy(() => import('./components/SafetyGamification'));
const PredictiveRiskPanel = lazy(() => import('./components/PredictiveRiskPanel'));
const AnomalyPanel = lazy(() => import('./components/AnomalyPanel'));
const IsometricPlantView = lazy(() => import('./components/IsometricPlantView'));
const CostOfSafetyDashboard = lazy(() => import('./components/CostOfSafetyDashboard'));
const ChatWidget = lazy(() => import('./components/ChatWidget'));
const RootCauseAnalysis = lazy(() => import('./components/RootCauseAnalysis'));
const DigitalTwinDashboard = lazy(() => import('./components/DigitalTwinDashboard'));
const RegulatoryReporter = lazy(() => import('./components/RegulatoryReporter'));
const PersonnelTracker = lazy(() => import('./components/PersonnelTracker'));

import { APP_TABS as TABS, COLORS, LAYOUT, ALERT_AUDIO, TOAST_DURATION } from './store/theme';

const SEVERITY_SCORE = { critical: 4, high: 3, warning: 2, info: 1 };
const NARROW_THRESHOLD = LAYOUT.narrowThreshold;
const MOBILE_THRESHOLD = 768;
const MINI_CHART_WIDTH = LAYOUT.miniChartWidth;
const MINI_CHART_HEIGHT = LAYOUT.miniChartHeight;
const SIDE_PANEL_NARROW = LAYOUT.sidebarNarrow;
const SIDE_PANEL_WIDE = LAYOUT.sidebarWide;
const COLOR_HEALTH_GOOD = COLORS.healthGood;
const COLOR_HEALTH_WARN = COLORS.healthWarn;
const COLOR_HEALTH_CRIT = COLORS.healthCrit;
const COLOR_STATUS_OFFLINE = COLORS.offline;
const COLOR_BG_LOW_RISK = COLORS.bgNormal;
const COLOR_BG_MED_RISK = COLORS.bgWarning;
const COLOR_BG_HIGH_RISK = COLORS.bgCriticalStrong;
const COLOR_BORDER_LOW_RISK = COLORS.borderNormal;
const COLOR_BORDER_MED_RISK = COLORS.borderWarning;
const COLOR_BORDER_HIGH_RISK = COLORS.borderCritical;
const COLOR_TEXT_MUTED = COLORS.textMuted;
const COLOR_TEXT_DIM = COLORS.textDim;
const COLOR_ACCENT_CYAN = COLORS.accent;
const COLOR_BG_PRIMARY = COLORS.bg;
const COLOR_BG_HEADER = COLORS.bgHeader;
const COLOR_BORDER_DARK = COLORS.border;
const COLOR_BORDER_TAB = COLORS.borderTab;

function TabFallback() {
  return <div style={{ padding: 40, textAlign: 'center', color: COLOR_TEXT_MUTED }}>Loading...</div>;
}

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
  const toastId = useRef(0);

  useEffect(() => {
    const onResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const isNarrow = windowWidth < NARROW_THRESHOLD;
  const isMobile = windowWidth < MOBILE_THRESHOLD;
  const prevSeverity = useRef('normal');
  const prevAlertCount = useRef(0);
  const audioCtx = useRef(null);

  const playAlertSound = useCallback(() => {
    try {
      if (!audioCtx.current) audioCtx.current = new (window.AudioContext || window.webkitAudioContext)();
      const ctx = audioCtx.current;
      if (ctx.state === 'suspended') ctx.resume();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.frequency.value = ALERT_AUDIO.frequency;
      osc.type = 'square';
      gain.gain.setValueAtTime(ALERT_AUDIO.gain, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + ALERT_AUDIO.durationS);
      osc.start();
      osc.stop(ctx.currentTime + ALERT_AUDIO.durationS);
    } catch (e) { /* audio not available */ }
  }, []);

  const addToast = useCallback((message, type = 'info', duration = TOAST_DURATION.default) => {
    const id = ++toastId.current;
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), duration);
  }, []);

  useEffect(() => {
    ws.connect();
    const unsub1 = ws.on('connection', (d) => {
      setConnected(d.connected);
      if (!d.connected) addToast('Disconnected from server — showing stale data', 'warning', TOAST_DURATION.warning);
    });
    const unsub2 = ws.on('state_update', (d) => {
      setPlantState(d.plant);
      setRiskData(d.risk);
      if (d.plant?.zone_risk_scores) setZoneRisks(d.plant.zone_risk_scores);
      if (d.risk?.alerts !== undefined) setAlerts(d.risk.alerts);
      if (d.activity_feed !== undefined) setActivityFeed(d.activity_feed);
      if (d.risk_trend !== undefined) setRiskTrend(d.risk_trend);
      if (d.compliance !== undefined) setCompliance(d.compliance);
      if (d.health_index !== undefined) setHealthIndex(d.health_index);
      const severity = d.risk?.severity || 'normal';
      const alertCount = d.risk?.alerts?.length || 0;
      if (severity === 'critical' && prevSeverity.current !== 'critical') {
        addToast('CRITICAL: Compound risk condition detected!', 'critical', TOAST_DURATION.critical);
        playAlertSound();
      }
      if (alertCount > prevAlertCount.current + 2) {
        addToast(`${alertCount} active alerts — review recommended`, 'warning', TOAST_DURATION.warning);
      }
      prevSeverity.current = severity;
      prevAlertCount.current = alertCount;
    });
    const unsub3 = ws.on('emergency_triggered', () => {
      setShowEmergencyModal(true);
      addToast('EMERGENCY RESPONSE ACTIVATED', 'critical', TOAST_DURATION.emergency);
    });
    const unsub4 = ws.on('what_if_applied', (d) => {
      if (d.plant) setPlantState(d.plant);
      if (d.risk) setRiskData(d.risk);
      if (d.activity) setActivityFeed(d.activity);
      addToast('What-If scenario applied', 'warning', TOAST_DURATION.scenario);
    });
    const unsub5 = ws.on('what_if_reset', (d) => {
      if (d.plant) setPlantState(d.plant);
      if (d.risk) setRiskData(d.risk);
      if (d.activity) setActivityFeed(d.activity);
      addToast('Scenario reset — normal operations', 'success', TOAST_DURATION.scenario);
    });
    const unsub6 = ws.on('api_error', (d) => {
      addToast(`API error ${d.status || ''}: ${d.endpoint}`, 'warning', TOAST_DURATION.warning);
    });
    return () => { unsub1(); unsub2(); unsub3(); unsub4(); unsub5(); unsub6(); ws.disconnect(); };
  }, [addToast]);

  // Service worker is registered by PushNotificationManager

  const handleMobileNavigate = useCallback((tab) => {
    setActiveTab(tab);
  }, []);

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

  const renderTab = (tabId) => {
    const content = (() => {
      switch (tabId) {
        case 'heatmap':
          return <GeospatialHeatmap zones={PLANT_ZONES} zoneRisks={zoneRisks}
            selectedZone={selectedZone} onSelectZone={setSelectedZone} plantState={plantState} />;
        case 'alerts':
          return <AlertPanel alerts={alerts} riskData={riskData} />;
        case 'permits':
          return <PermitIntelligence permits={plantState?.active_permits || []} plantState={plantState} />;
        case 'compliance':
          return <CompliancePanel compliance={compliance} />;
        case 'emergency':
          return <EmergencyResponse triggerEmergency={triggerEmergency} resolveEmergency={resolveEmergency}
            showModal={showEmergencyModal} setShowModal={setShowEmergencyModal} plantState={plantState} />;
        case 'scenarios':
          return <WhatIfSimulator plantState={plantState} />;
        case 'feed':
          return <ActivityFeed entries={activityFeed} />;
        case 'patterns':
          return <IncidentPatterns />;
        case 'investigations':
          return <IncidentInvestigation />;
        case 'safety':
          return <SafetyGamification />;
        case 'forecast':
          return <PredictiveRiskPanel riskTrend={riskTrend} />;
        case 'anomalies':
          return <AnomalyPanel />;
        case '3dview':
          return <IsometricPlantView zones={PLANT_ZONES} zoneRisks={zoneRisks}
            selectedZone={selectedZone} onSelectZone={setSelectedZone} />;
        case 'cost':
          return <CostOfSafetyDashboard />;
        case 'rootcause':
          return <RootCauseAnalysis />;
        case 'twindash':
          return <DigitalTwinDashboard />;
        case 'reports':
          return <RegulatoryReporter />;
        case 'personnel':
          return <PersonnelTracker />;
        default:
          return null;
      }
    })();
    return <ErrorBoundary key={tabId}><Suspense fallback={<TabFallback />}>{content}</Suspense></ErrorBoundary>;
  };

  if (isMobile) {
    return (
      <>
        <Toast toasts={toasts} />
        <PushNotificationManager onNavigate={handleMobileNavigate} />
        <MobileDashboard
          plantState={plantState}
          riskData={riskData}
          alerts={alerts}
          healthIndex={healthIndex}
          connected={connected}
          activeTab={activeTab === 'emergency' ? 'emergency' : activeTab === 'alerts' ? 'alerts' : activeTab === 'permits' ? 'permits' : 'dashboard'}
          setActiveTab={setActiveTab}
          triggerEmergency={triggerEmergency}
        />
      </>
    );
  }

  return (
    <div style={styles.container}>
      <Toast toasts={toasts} />
      {!connected && plantState && (
        <div style={styles.disconnectedBanner}>
          {'\u{26A0}\uFE0F'} Disconnected — showing cached data. Reconnecting...
        </div>
      )}
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
              <Suspense fallback={null}><RiskTrendChart data={riskTrend} width={MINI_CHART_WIDTH} height={MINI_CHART_HEIGHT} mini /></Suspense>
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
            {renderTab(activeTab)}
          </div>
        </div>
        <div style={{...styles.sidePanel, width: isNarrow ? SIDE_PANEL_NARROW : SIDE_PANEL_WIDE}}>
          <Suspense fallback={<TabFallback />}>
            <ErrorBoundary>
              <RiskPanel riskData={riskData} zoneRisks={zoneRisks} selectedZone={selectedZone}
                plantState={plantState} riskTrend={riskTrend} compliance={compliance}
                onEmergency={() => setActiveTab('emergency')} />
            </ErrorBoundary>
          </Suspense>
        </div>
      </div>
      <Suspense fallback={null}>
        <ChatWidget plantState={plantState} riskResult={riskData} compliance={compliance}
          healthIndex={healthIndex} riskTrend={riskTrend} alerts={alerts} />
      </Suspense>
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
  disconnectedBanner: {
    background: 'rgba(255,109,0,0.2)', color: '#ffa000', textAlign: 'center',
    padding: '4px 16px', fontSize: 11, fontWeight: 600, borderBottom: '1px solid rgba(255,109,0,0.3)',
  },
  tabContent: { flex: 1, overflow: 'auto', position: 'relative' },
  sidePanel: { flexShrink: 0, borderLeft: `1px solid ${COLOR_BORDER_TAB}`, overflow: 'auto' },
};
