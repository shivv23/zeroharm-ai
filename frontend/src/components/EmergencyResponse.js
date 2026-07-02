import React, { useState, useEffect, useRef, useCallback } from 'react';
import ws from '../store/websocketStore';
import { EMERGENCY_TYPES, COLORS } from '../store/theme';
import GasDispersionOverlay from './GasDispersionOverlay';

function speak(text) {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    window.speechSynthesis.speak(utterance);
  }
}

export default function EmergencyResponse({ triggerEmergency = () => {}, resolveEmergency = () => {}, showModal, setShowModal = () => {}, plantState = null }) {
  const [selectedType, setSelectedType] = useState('gas_leak');
  const [activeEmergencies, setActiveEmergencies] = useState([]);
  const [log, setLog] = useState([]);

  const addLog = useCallback((msg) => {
    setLog(prev => [...prev.slice(-19), { time: new Date().toLocaleTimeString(), text: msg }]);
  }, []);

  useEffect(() => {
    const unsub = ws.on('emergency_triggered', (d) => {
      setActiveEmergencies(prev => [...prev, d.data]);
      addLog(`EMERGENCY TRIGGERED: ${d.data.label} in ${d.data.zone_name}`);
      speak(`Emergency: ${d.data.label} in ${d.data.zone_name}. Evacuate area immediately.`);
    });
    const unsub2 = ws.on('emergency_resolved', (d) => {
      if (d.data) {
        setActiveEmergencies(prev => prev.filter(e => e.id !== d.data.id));
        addLog(`EMERGENCY RESOLVED: ${d.data.id}`);
        speak(`All clear. Emergency ${d.data.id} has been resolved.`);
      }
    });
    return () => { unsub(); unsub2(); };
  }, [addLog]);

  const handleTrigger = () => {
    const zoneId = plantState?.active_permits?.[0]?.zone_id || 'Z01';
    const context = {
      zone_id: zoneId,
      zone_name: plantState?.active_permits?.[0]?.zone_name || 'Unknown',
      sensor_snapshot: plantState?.sensors || {},
      permit_snapshot: plantState?.active_permits || [],
      personnel_in_zone: [],
    };
    triggerEmergency(selectedType, context);
    addLog(`Triggering ${selectedType} in ${context.zone_name}...`);
    speak(`Warning: ${selectedType.replace(/_/g, ' ')} reported in ${context.zone_name}. Take immediate action.`);
  };

  const handleResolve = (id) => {
    resolveEmergency(id, 'All clear. Incident contained.');
    addLog(`Resolving ${id}...`);
  };

  const formatTime = (iso) => {
    if (!iso) return '';
    return new Date(iso).toLocaleTimeString();
  };

  return (
    <div style={{ padding: 16, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 16, fontWeight: 700 }}>{'\u{1F6A8}'} Emergency Response Orchestrator</div>
        <div style={{ fontSize: 11, color: COLORS.textMuted }}>Autonomous emergency protocol with multi-channel dispatch</div>
      </div>

      <div style={{ display: 'flex', gap: 12, flex: 1, overflow: 'hidden' }}>
        {/* Left: Controls */}
        <div style={{ width: 280, display: 'flex', flexDirection: 'column', gap: 12 }}>
          {/* Emergency Type Selection */}
          <div style={{ background: COLORS.bgCard, borderRadius: 8, padding: 10, border: '1px solid ' + COLORS.border }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: COLORS.textMuted, marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 }}>
              Emergency Type
            </div>
            {EMERGENCY_TYPES.map(et => (
              <div key={et.id} style={{
                padding: '6px 8px', cursor: 'pointer', borderRadius: 4, marginBottom: 3,
                background: selectedType === et.id ? COLORS.bgAccentStrong : 'transparent',
                border: `1px solid ${selectedType === et.id ? COLORS.borderInfo : 'transparent'}`,
                display: 'flex', alignItems: 'center', gap: 6, fontSize: 12,
              }} onClick={() => setSelectedType(et.id)}>
                <span>{et.icon}</span>
                <span style={{ color: et.color }}>{et.label}</span>
              </div>
            ))}
          </div>

          {/* Trigger Button */}
          <div style={{
            padding: 12, background: COLORS.bgCriticalStrong, borderRadius: 8,
            border: '1px solid ' + COLORS.borderCritical, cursor: 'pointer',
            textAlign: 'center', transition: 'all 0.2s',
          }} onClick={handleTrigger}>
            <div style={{ fontSize: 28 }}>{'\u{1F6A8}'}</div>
            <div style={{ fontSize: 14, fontWeight: 700, color: COLORS.riskCritical, marginTop: 4 }}>
              TRIGGER EMERGENCY
            </div>
            <div style={{ fontSize: 10, color: COLORS.textMuted, marginTop: 2 }}>
              Dispatches alerts across all channels
            </div>
          </div>
        </div>

        {/* Right: Status / Timeline */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 12, overflow: 'hidden' }}>
          {/* Active Emergencies */}
          <div style={{ flex: 1, overflow: 'auto' }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: COLORS.riskCritical, marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 }}>
              Active Emergencies {activeEmergencies.length > 0 ? `(${activeEmergencies.length})` : ''}
            </div>
            {activeEmergencies.length === 0 && (
              <div style={{ textAlign: 'center', padding: 30, color: COLORS.textMuted, fontSize: 11 }}>
                No active emergencies. System is in normal operation.
              </div>
            )}
            {activeEmergencies.map((em, i) => (
              <div key={em.id || i} style={{
                background: COLORS.bgCard, borderRadius: 8, border: '1px solid ' + COLORS.borderCritical, marginBottom: 8, overflow: 'hidden',
              }}>
                {/* Header */}
                <div style={{ padding: '8px 12px', background: COLORS.bgCritical, borderBottom: '1px solid ' + COLORS.bgCriticalStronger, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <span style={{ fontSize: 12, fontWeight: 700, color: COLORS.riskCritical }}>{'\u{1F6A8}'} {em.label}</span>
                    <span style={{ fontSize: 10, color: COLORS.textMuted, marginLeft: 8 }}>{em.id}</span>
                  </div>
                  <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                    <span style={{ fontSize: 10, color: COLORS.riskCritical, fontWeight: 600, textTransform: 'uppercase' }}>{em.status}</span>
                    <div style={{ fontSize: 10, color: COLORS.accent, cursor: 'pointer' }} onClick={() => handleResolve(em.id)}>
                      Resolve
                    </div>
                  </div>
                </div>

                {/* Details */}
                <div style={{ padding: '8px 12px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, fontSize: 11 }}>
                  <div><span style={{ color: COLORS.textMuted }}>Zone:</span> <span style={{ color: COLORS.text }}>{em.zone_name}</span></div>
                  <div><span style={{ color: COLORS.textMuted }}>Evacuation:</span> <span style={{ color: em.evacuation_status === 'in_progress' ? COLORS.riskElevated : COLORS.text }}>{em.evacuation_radius_m > 0 ? `${em.evacuation_radius_m}m - ${em.evacuation_status}` : 'N/A'}</span></div>
                  <div><span style={{ color: COLORS.textMuted }}>Shutdown:</span> <span style={{ color: em.shutdown_initiated ? COLORS.riskCritical : COLORS.text }}>{em.shutdown_initiated ? 'Initiated' : 'Not required'}</span></div>
                  <div><span style={{ color: COLORS.textMuted }}>Rescue Team:</span> <span style={{ color: em.rescue_team_dispatched ? COLORS.riskElevated : COLORS.text }}>{em.rescue_team_dispatched ? 'Dispatched' : 'Standing by'}</span></div>
                </div>

                {/* Alerts dispatched */}
                <div style={{ padding: '0 12px 8px' }}>
                  <div style={{ fontSize: 10, fontWeight: 600, color: COLORS.riskNormal, marginBottom: 4 }}>Alerts Dispatched:</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                    {em.alerts_dispatched?.map((a, j) => (
                      <span key={j} style={{ fontSize: 9, padding: '1px 6px', background: COLORS.bgNormal, borderRadius: 8, color: COLORS.riskNormal }}>
                        {'\u{2705}'} {a.channel}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Timeline */}
                <div style={{ padding: '0 12px 8px', maxHeight: 120, overflow: 'auto' }}>
                  <div style={{ fontSize: 10, fontWeight: 600, color: COLORS.accent, marginBottom: 4 }}>Response Timeline:</div>
                  {(em.timeline || []).slice(-5).map((t, j) => (
                    <div key={j} style={{ display: 'flex', gap: 6, fontSize: 9, color: COLORS.textMuted, padding: '1px 0' }}>
                      <span style={{ color: COLORS.accent, flexShrink: 0 }}>{formatTime(t.time)}</span>
                      <span>{t.event}</span>
                    </div>
                  ))}
                </div>

                {/* Incident Report */}
                {em.incident_report && (
                  <div style={{ padding: '0 12px 8px' }}>
                    <div style={{ fontSize: 10, fontWeight: 600, color: COLORS.riskElevated, marginBottom: 2 }}>Incident Report Generated:</div>
                    <div style={{ fontSize: 9, color: COLORS.textMuted }}>Report ID: {em.incident_report.report_id} · {em.incident_report.status}</div>
                    <div style={{ fontSize: 9, color: COLORS.textMuted }}>Classification: {em.incident_report.classification}</div>
                    <div style={{ fontSize: 9, color: COLORS.riskElevated, marginTop: 4 }}>Regulatory References: {em.incident_report.details?.regulatory_references?.join(', ')}</div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Gas Dispersion Overlay */}
          {activeEmergencies.some(e => e.type === 'gas_leak' || e.type === 'explosion') && (
            <div style={{ position: 'relative', height: 200, background: '#080c16', borderRadius: 6, border: '1px solid #1f2937', overflow: 'hidden' }}>
              <GasDispersionOverlay emergency={activeEmergencies.find(e => e.type === 'gas_leak' || e.type === 'explosion')}
                zoneRisks={{}} plantState={plantState} />
            </div>
          )}

          {/* Log */}
          <div style={{ maxHeight: 100, overflow: 'auto', background: COLORS.bgElevated, borderRadius: 6, padding: 8, border: '1px solid ' + COLORS.border }}>
            <div style={{ fontSize: 9, fontWeight: 600, color: COLORS.textMuted, marginBottom: 4 }}>EVENT LOG</div>
            {log.map((entry, i) => (
              <div key={i} style={{ fontSize: 9, color: COLORS.textMuted, padding: '1px 0', fontFamily: 'monospace' }}>
                [{entry.time}] {entry.msg}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
