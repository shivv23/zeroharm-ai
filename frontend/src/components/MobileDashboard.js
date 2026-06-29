import React, { useState, useRef, useEffect, useCallback } from 'react';
import { COLORS, EMERGENCY_TYPES } from '../store/theme';
import { getRiskColor } from '../store/plantData';
import ws from '../store/websocketStore';

const styles = {
  container: {
    display: 'flex', flexDirection: 'column', height: '100vh',
    background: COLORS.bg, color: COLORS.text, overflow: 'hidden',
  },
  offlineBar: {
    background: COLORS.bgHighStronger, color: COLORS.riskElevated, textAlign: 'center',
    padding: '6px 16px', fontSize: 12, fontWeight: 600,
    borderBottom: `1px solid ${COLORS.borderHigh}`,
  },
  header: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '12px 16px', background: COLORS.bgHeader,
    borderBottom: `1px solid ${COLORS.border}`, flexShrink: 0,
  },
  headerTitle: {
    fontSize: 16, fontWeight: 700,
    background: COLORS.gradientTitle,
    WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
  },
  headerSub: { fontSize: 10, color: COLORS.textDim, marginTop: 1 },
  statusDot: { width: 8, height: 8, borderRadius: '50%' },
  content: { flex: 1, overflow: 'auto', WebkitOverflowScrolling: 'touch', padding: '0 12px' },
  statCard: {
    background: COLORS.bgCard, borderRadius: 10, border: `1px solid ${COLORS.border}`,
    padding: '14px 16px', minHeight: 44,
  },
  statLabel: { fontSize: 10, color: COLORS.textMuted, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 4 },
  statValue: { fontSize: 24, fontWeight: 700 },
  statSub: { fontSize: 11, color: COLORS.textDim, marginTop: 2 },
  emergencyBtn: {
    width: '100%', minHeight: 52, borderRadius: 10, border: 'none',
    background: COLORS.gradientCritical,
    color: COLORS.text, fontSize: 16, fontWeight: 700, cursor: 'pointer',
    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
    boxShadow: `0 4px 20px ${COLORS.borderCriticalStrong}`,
    WebkitTapHighlightColor: 'transparent', touchAction: 'manipulation',
  },
  emergencyTypeBtn: {
    flex: 1, minHeight: 44, borderRadius: 8, border: `1px solid ${COLORS.border}`,
    background: COLORS.bgCard, color: COLORS.text, fontSize: 11, fontWeight: 600,
    cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center',
    justifyContent: 'center', gap: 2, transition: 'all 0.2s',
    WebkitTapHighlightColor: 'transparent', touchAction: 'manipulation',
  },
  alertItem: {
    minHeight: 44, padding: '10px 12px', background: COLORS.bgCard,
    borderRadius: 8, border: `1px solid ${COLORS.border}`,
    display: 'flex', alignItems: 'flex-start', gap: 8, cursor: 'pointer',
    transition: 'transform 0.2s',
  },
  bottomNav: {
    display: 'flex', background: COLORS.bgHeader,
    borderTop: `1px solid ${COLORS.border}`, flexShrink: 0, paddingBottom: 'env(safe-area-inset-bottom)',
  },
  navItem: {
    flex: 1, minHeight: 48, display: 'flex', flexDirection: 'column',
    alignItems: 'center', justifyContent: 'center', gap: 1, cursor: 'pointer',
    fontSize: 9, color: COLORS.textDim, border: 'none', background: 'transparent',
    WebkitTapHighlightColor: 'transparent', touchAction: 'manipulation',
    transition: 'color 0.2s',
  },
  navItemActive: { color: COLORS.accent },
  navIcon: { fontSize: 20, lineHeight: 1 },
  permitAction: {
    minHeight: 44, padding: '8px 12px', borderRadius: 8,
    background: COLORS.bgInfo, border: `1px solid ${COLORS.border}`,
    display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer',
    WebkitTapHighlightColor: 'transparent', touchAction: 'manipulation',
  },
  approveBtn: {
    padding: '6px 14px', borderRadius: 6, border: 'none',
    background: COLORS.bgNormalMedium, color: COLORS.riskNormal,
    fontSize: 11, fontWeight: 600, cursor: 'pointer',
    WebkitTapHighlightColor: 'transparent', touchAction: 'manipulation',
  },
  sectionTitle: {
    fontSize: 13, fontWeight: 600, color: COLORS.text, marginBottom: 8, marginTop: 16,
  },
  sectionSub: { fontSize: 10, color: COLORS.textMuted, marginBottom: 8 },
};

const NAV_TABS = [
  { id: 'dashboard', label: 'Dashboard', icon: '\u{1F3E0}' },
  { id: 'alerts', label: 'Alerts', icon: '\u{26A0}\uFE0F' },
  { id: 'permits', label: 'Permits', icon: '\u{1F4CB}' },
  { id: 'emergency', label: 'Emergency', icon: '\u{1F6A8}' },
];

function AlertItem({ alert, onDismiss }) {
  const [swiping, setSwiping] = useState(false);
  const [offsetX, setOffsetX] = useState(0);
  const startX = useRef(0);

  const handleTouchStart = (e) => {
    startX.current = e.touches[0].clientX;
    setSwiping(true);
  };

  const handleTouchMove = (e) => {
    if (!swiping) return;
    const diff = e.touches[0].clientX - startX.current;
    if (diff < 0) setOffsetX(diff);
  };

  const handleTouchEnd = () => {
    if (offsetX < -80) onDismiss(alert.id || alert.timestamp);
    setSwiping(false);
    setOffsetX(0);
  };

  const bgColors = { critical: COLORS.bgCritical, high: COLORS.bgHigh, warning: COLORS.bgWarning, info: COLORS.bgInfo };
  const borderColors = { critical: COLORS.borderCritical, high: COLORS.borderHigh, warning: COLORS.borderWarning, info: COLORS.borderInfo };

  return (
    <div
      style={{
        ...styles.alertItem,
        transform: `translateX(${offsetX}px)`,
        background: bgColors[alert.severity] || bgColors.info,
        border: `1px solid ${borderColors[alert.severity] || borderColors.info}`,
        marginBottom: 6,
      }}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      <span style={{ flexShrink: 0, fontSize: 14 }}>
        {alert.severity === 'critical' ? '\u{1F525}' : '\u{26A0}\uFE0F'}
      </span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: COLORS.text, lineHeight: 1.3 }}>{alert.message}</div>
        {alert.zone_name && <div style={{ fontSize: 10, color: COLORS.textDim, marginTop: 2 }}>{'\u{1F3E0}'} {alert.zone_name}</div>}
      </div>
      {offsetX < -40 && <span style={{ fontSize: 10, color: COLORS.riskCritical, flexShrink: 0 }}>Dismiss</span>}
    </div>
  );
}

export default function MobileDashboard({ plantState, riskData, alerts, healthIndex, connected, activeTab, setActiveTab, triggerEmergency }) {
  const [refreshing, setRefreshing] = useState(false);
  const [dismissedAlerts, setDismissedAlerts] = useState(new Set());
  const [showEmergencyPicker, setShowEmergencyPicker] = useState(false);
  const [selectedEmergencyType, setSelectedEmergencyType] = useState(EMERGENCY_TYPES[0].id);
  const touchStartY = useRef(0);
  const contentRef = useRef(null);
  const [pullDistance, setPullDistance] = useState(0);

  const handleTouchStart = (e) => {
    if (contentRef.current && contentRef.current.scrollTop === 0) {
      touchStartY.current = e.touches[0].clientY;
    }
  };

  const handleTouchMove = (e) => {
    if (touchStartY.current === 0) return;
    const diff = e.touches[0].clientY - touchStartY.current;
    if (diff > 0) {
      setPullDistance(Math.min(diff * 0.4, 60));
    }
  };

  const handleTouchEnd = () => {
    if (pullDistance > 40) {
      setRefreshing(true);
      ws.send({ action: 'sync_state' });
      setTimeout(() => {
        setRefreshing(false);
        setPullDistance(0);
      }, 1500);
    }
    setPullDistance(0);
    touchStartY.current = 0;
  };

  const filteredAlerts = alerts.filter(a => !dismissedAlerts.has(a.id || a.timestamp));
  const activePermits = plantState?.active_permits || [];
  const pendingPermits = activePermits.filter(p => p.status === 'pending_approval');

  const handleEmergency = () => {
    const zoneId = plantState?.active_permits?.[0]?.zone_id || 'Z01';
    triggerEmergency(selectedEmergencyType, {
      zone_id: zoneId,
      zone_name: plantState?.active_permits?.[0]?.zone_name || 'Unknown',
      sensor_snapshot: plantState?.sensors || {},
      permit_snapshot: activePermits,
      personnel_in_zone: [],
    });
    setShowEmergencyPicker(false);
  };

  const handleApprovePermit = (permitId) => {
    ws.send({ action: 'approve_permit', permit_id: permitId });
  };

  const dismissAlert = (id) => {
    setDismissedAlerts(prev => new Set([...prev, id]));
    setTimeout(() => {
      ws.send({ action: 'dismiss_alert', alert_id: id });
    }, 300);
  };

  const renderDashboardTab = () => (
    <div style={styles.content} ref={contentRef} onTouchStart={handleTouchStart} onTouchMove={handleTouchMove} onTouchEnd={handleTouchEnd}>
      {pullDistance > 0 && (
        <div style={{ textAlign: 'center', padding: 4, fontSize: 11, color: COLORS.textMuted, height: pullDistance, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          {refreshing ? 'Refreshing...' : '\u{2193} Pull to refresh'}
        </div>
      )}
      {refreshing && (
        <div style={{ textAlign: 'center', padding: 4, fontSize: 11, color: COLORS.accent }}>
          Refreshing data...
        </div>
      )}

      <div style={styles.sectionTitle}>Status Overview</div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 4 }}>
        <div style={styles.statCard}>
          <div style={styles.statLabel}>Health Index</div>
          <div style={{
            ...styles.statValue,
            color: healthIndex ? (healthIndex.overall >= 70 ? COLORS.riskNormal : healthIndex.overall >= 50 ? COLORS.riskElevated : COLORS.riskCritical) : COLORS.textMuted,
          }}>
            {healthIndex ? `${healthIndex.overall}` : '--'}
          </div>
          <div style={styles.statSub}>{healthIndex ? healthIndex.label : 'No data'}</div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statLabel}>Active Alerts</div>
          <div style={{ ...styles.statValue, color: filteredAlerts.length > 0 ? COLORS.riskElevated : COLORS.riskNormal }}>
            {filteredAlerts.length}
          </div>
          <div style={styles.statSub}>
            {filteredAlerts.filter(a => a.severity === 'critical').length} critical
          </div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statLabel}>Active Permits</div>
          <div style={{ ...styles.statValue, color: COLORS.accent }}>
            {activePermits.length}
          </div>
          <div style={styles.statSub}>
            {pendingPermits.length} pending approval
          </div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statLabel}>Risk Score</div>
          <div style={{ ...styles.statValue, color: getRiskColor(riskData?.risk_score || 0) }}>
            {riskData ? (riskData.risk_score * 100).toFixed(0) : '--'}
          </div>
          <div style={styles.statSub}>{riskData?.severity || 'No data'}</div>
        </div>
      </div>

      {pendingPermits.length > 0 && (
        <>
          <div style={styles.sectionTitle}>Permit Approvals</div>
          {pendingPermits.slice(0, 3).map((p, i) => (
            <div key={p.id || i} style={{ ...styles.permitAction, marginBottom: 6 }}>
              <div>
                <div style={{ fontSize: 12, fontWeight: 500 }}>{p.permit_type || 'Permit'}</div>
                <div style={{ fontSize: 10, color: COLORS.textDim }}>{p.zone_name} {'\u2022'} {p.contractor || 'N/A'}</div>
              </div>
              <button style={styles.approveBtn} onClick={() => handleApprovePermit(p.id)}>Approve</button>
            </div>
          ))}
        </>
      )}

      <div style={styles.sectionTitle}>Quick Emergency</div>
      <button style={styles.emergencyBtn} onClick={() => setShowEmergencyPicker(true)}>
        {'\u{1F6A8}'} TRIGGER EMERGENCY
      </button>

      <div style={{ height: 12 }} />
    </div>
  );

  const renderAlertsTab = () => (
    <div style={styles.content}>
      <div style={styles.sectionTitle}>Alerts & Notifications</div>
      <div style={styles.sectionSub}>Swipe to dismiss</div>
      {filteredAlerts.length === 0 && (
        <div style={{ textAlign: 'center', padding: 40, color: COLORS.textMuted }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>{'\u{2705}'}</div>
          <div style={{ fontSize: 14, fontWeight: 600 }}>No active alerts</div>
          <div style={{ fontSize: 11, marginTop: 4 }}>All safety parameters normal</div>
        </div>
      )}
      {filteredAlerts.map((alert, i) => (
        <AlertItem key={alert.id || alert.timestamp || i} alert={alert} onDismiss={dismissAlert} />
      ))}
      <div style={{ height: 12 }} />
    </div>
  );

  const renderPermitsTab = () => (
    <div style={styles.content}>
      <div style={styles.sectionTitle}>Active Permits ({activePermits.length})</div>
      {activePermits.length === 0 && (
        <div style={{ textAlign: 'center', padding: 40, color: COLORS.textMuted }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>{'\u{1F4CB}'}</div>
          <div style={{ fontSize: 14, fontWeight: 600 }}>No active permits</div>
        </div>
      )}
      {activePermits.map((p, i) => (
        <div key={p.id || i} style={{
          ...styles.permitAction, marginBottom: 6,
          background: p.status === 'pending_approval' ? COLORS.bgInfo : COLORS.bgCard,
          border: `1px solid ${p.status === 'pending_approval' ? COLORS.borderInfo : COLORS.border}`,
        }}>
          <div>
            <div style={{ fontSize: 12, fontWeight: 500 }}>{p.permit_type || 'Permit'}</div>
            <div style={{ fontSize: 10, color: COLORS.textDim }}>
              {p.zone_name} {'\u2022'} {p.contractor || ''}
              {p.status && ` \u2022 ${p.status.replace(/_/g, ' ')}`}
            </div>
            {p.valid_until && (
              <div style={{ fontSize: 9, color: COLORS.textMuted, marginTop: 2 }}>
                Valid until {new Date(p.valid_until).toLocaleDateString()}
              </div>
            )}
          </div>
          {p.status === 'pending_approval' && (
            <button style={styles.approveBtn} onClick={() => handleApprovePermit(p.id)}>Approve</button>
          )}
        </div>
      ))}
      <div style={{ height: 12 }} />
    </div>
  );

  const renderEmergencyTab = () => (
    <div style={styles.content}>
      <div style={styles.sectionTitle}>Emergency Response</div>

      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 11, color: COLORS.textMuted, marginBottom: 8 }}>Select emergency type:</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          {EMERGENCY_TYPES.map(et => (
            <button
              key={et.id}
              style={{
                ...styles.emergencyTypeBtn,
                borderColor: selectedEmergencyType === et.id ? et.color : COLORS.border,
                background: selectedEmergencyType === et.id ? `${et.color}1a` : COLORS.bgCard,
              }}
              onClick={() => setSelectedEmergencyType(et.id)}
            >
              <span style={{ fontSize: 24 }}>{et.icon}</span>
              <span>{et.label}</span>
            </button>
          ))}
        </div>
      </div>

      <button style={styles.emergencyBtn} onClick={handleEmergency}>
        {'\u{1F6A8}'} TRIGGER {EMERGENCY_TYPES.find(t => t.id === selectedEmergencyType)?.label.toUpperCase() || 'EMERGENCY'}
      </button>

      <div style={{ height: 12 }} />
    </div>
  );

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard': return renderDashboardTab();
      case 'alerts': return renderAlertsTab();
      case 'permits': return renderPermitsTab();
      case 'emergency': return renderEmergencyTab();
      default: return renderDashboardTab();
    }
  };

  return (
    <div style={styles.container}>
      {!connected && plantState && (
        <div style={styles.offlineBar}>
          {'\u{26A0}\uFE0F'} Offline — showing cached data
        </div>
      )}

      <div style={styles.header}>
        <div>
          <div style={styles.headerTitle}>ZeroHarm AI</div>
          <div style={styles.headerSub}>Field Safety</div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{ ...styles.statusDot, background: connected ? COLORS.riskNormal : COLORS.riskCritical }} />
          <span style={{ fontSize: 10, color: COLORS.textDim }}>{connected ? 'Live' : 'Offline'}</span>
        </div>
      </div>

      {showEmergencyPicker && (
        <div style={{
          position: 'fixed', inset: 0, background: COLORS.overlay, zIndex: 1000,
          display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20,
        }} onClick={() => setShowEmergencyPicker(false)}>
          <div style={{
            background: COLORS.bgCard, borderRadius: 12, padding: 20, width: '100%', maxWidth: 320,
            border: `1px solid ${COLORS.border}`,
          }} onClick={e => e.stopPropagation()}>
            <div style={{ fontSize: 15, fontWeight: 700, marginBottom: 12, textAlign: 'center' }}>
              Trigger Emergency
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 14 }}>
              {EMERGENCY_TYPES.map(et => (
                <button
                  key={et.id}
                  style={{
                    ...styles.emergencyTypeBtn,
                    borderColor: selectedEmergencyType === et.id ? et.color : COLORS.border,
                    background: selectedEmergencyType === et.id ? `${et.color}1a` : COLORS.bgCard,
                    padding: '10px 8px',
                  }}
                  onClick={() => setSelectedEmergencyType(et.id)}
                >
                  <span style={{ fontSize: 22 }}>{et.icon}</span>
                  <span>{et.label}</span>
                </button>
              ))}
            </div>
            <button style={{
              width: '100%', minHeight: 48, borderRadius: 10, border: 'none',
              background: COLORS.gradientCritical,
              color: COLORS.text, fontSize: 15, fontWeight: 700, cursor: 'pointer',
              WebkitTapHighlightColor: 'transparent', touchAction: 'manipulation',
            }} onClick={handleEmergency}>
              {'\u{1F6A8}'} CONFIRM EMERGENCY
            </button>
            <button style={{
              width: '100%', minHeight: 44, borderRadius: 8, border: `1px solid ${COLORS.border}`,
              background: 'transparent', color: COLORS.textMuted, fontSize: 12, cursor: 'pointer',
              marginTop: 8, WebkitTapHighlightColor: 'transparent', touchAction: 'manipulation',
            }} onClick={() => setShowEmergencyPicker(false)}>
              Cancel
            </button>
          </div>
        </div>
      )}

      {renderContent()}

      <div style={styles.bottomNav}>
        {NAV_TABS.map(tab => (
          <button
            key={tab.id}
            style={{
              ...styles.navItem,
              ...(activeTab === tab.id ? styles.navItemActive : {}),
              ...(tab.id === 'emergency' && activeTab !== 'emergency' ? { color: COLORS.textDim } : {}),
              ...(tab.id === 'emergency' && activeTab === 'emergency' ? { color: COLORS.riskCritical } : {}),
            }}
            onClick={() => setActiveTab(tab.id)}
          >
            <span style={styles.navIcon}>{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
