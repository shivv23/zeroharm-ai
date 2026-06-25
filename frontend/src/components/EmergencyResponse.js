import React, { useState, useEffect } from 'react';
import ws from '../store/websocketStore';

const EMERGENCY_TYPES = [
  { id: 'gas_leak', label: 'Gas Leak', icon: '\u{26A0}\uFE0F', color: '#ff6d00' },
  { id: 'fire', label: 'Fire', icon: '\u{1F525}', color: '#ff1744' },
  { id: 'confined_space_emergency', label: 'Confined Space Rescue', icon: '\u{1F6AA}', color: '#ff9100' },
  { id: 'explosion', label: 'Explosion', icon: '\u{1F4A5}', color: '#d50000' },
  { id: 'medical_emergency', label: 'Medical Emergency', icon: '\u{1F3E5}', color: '#00e5ff' },
];

export default function EmergencyResponse({ triggerEmergency, resolveEmergency, showModal, setShowModal, plantState }) {
  const [selectedType, setSelectedType] = useState('gas_leak');
  const [emergencyStatus, setEmergencyStatus] = useState(null);
  const [activeEmergencies, setActiveEmergencies] = useState([]);
  const [log, setLog] = useState([]);

  useEffect(() => {
    const unsub = ws.on('emergency_triggered', (d) => {
      setEmergencyStatus(d.data);
      setActiveEmergencies(prev => [...prev, d.data]);
      addLog(`EMERGENCY TRIGGERED: ${d.data.label} in ${d.data.zone_name}`);
    });
    const unsub2 = ws.on('emergency_resolved', (d) => {
      if (d.data) {
        setActiveEmergencies(prev => prev.filter(e => e.id !== d.data.id));
        addLog(`EMERGENCY RESOLVED: ${d.data.id}`);
      }
    });
    return () => { unsub(); unsub2(); };
  }, []);

  useEffect(() => {
    if (showModal) {
      setSelectedType('gas_leak');
      setShowModal(false);
    }
  }, [showModal, setShowModal]);

  const addLog = (msg) => {
    setLog(prev => [{ time: new Date().toLocaleTimeString(), msg }, ...prev].slice(0, 20));
  };

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
        <div style={{ fontSize: 11, color: '#6b7280' }}>Autonomous emergency protocol with multi-channel dispatch</div>
      </div>

      <div style={{ display: 'flex', gap: 12, flex: 1, overflow: 'hidden' }}>
        {/* Left: Controls */}
        <div style={{ width: 280, display: 'flex', flexDirection: 'column', gap: 12 }}>
          {/* Emergency Type Selection */}
          <div style={{ background: '#111827', borderRadius: 8, padding: 10, border: '1px solid #1f2937' }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: '#6b7280', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 }}>
              Emergency Type
            </div>
            {EMERGENCY_TYPES.map(et => (
              <div key={et.id} style={{
                padding: '6px 8px', cursor: 'pointer', borderRadius: 4, marginBottom: 3,
                background: selectedType === et.id ? 'rgba(0,229,255,0.1)' : 'transparent',
                border: `1px solid ${selectedType === et.id ? 'rgba(0,229,255,0.3)' : 'transparent'}`,
                display: 'flex', alignItems: 'center', gap: 6, fontSize: 12,
              }} onClick={() => setSelectedType(et.id)}>
                <span>{et.icon}</span>
                <span style={{ color: et.color }}>{et.label}</span>
              </div>
            ))}
          </div>

          {/* Trigger Button */}
          <div style={{
            padding: 12, background: 'rgba(255,23,68,0.15)', borderRadius: 8,
            border: '1px solid rgba(255,23,68,0.3)', cursor: 'pointer',
            textAlign: 'center', transition: 'all 0.2s',
          }} onClick={handleTrigger}>
            <div style={{ fontSize: 28 }}>{'\u{1F6A8}'}</div>
            <div style={{ fontSize: 14, fontWeight: 700, color: '#ff1744', marginTop: 4 }}>
              TRIGGER EMERGENCY
            </div>
            <div style={{ fontSize: 10, color: '#6b7280', marginTop: 2 }}>
              Dispatches alerts across all channels
            </div>
          </div>
        </div>

        {/* Right: Status / Timeline */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 12, overflow: 'hidden' }}>
          {/* Active Emergencies */}
          <div style={{ flex: 1, overflow: 'auto' }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: '#ff1744', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 }}>
              Active Emergencies {activeEmergencies.length > 0 ? `(${activeEmergencies.length})` : ''}
            </div>
            {activeEmergencies.length === 0 && (
              <div style={{ textAlign: 'center', padding: 30, color: '#6b7280', fontSize: 11 }}>
                No active emergencies. System is in normal operation.
              </div>
            )}
            {activeEmergencies.map((em, i) => (
              <div key={em.id || i} style={{
                background: '#111827', borderRadius: 8, border: '1px solid rgba(255,23,68,0.3)', marginBottom: 8, overflow: 'hidden',
              }}>
                {/* Header */}
                <div style={{ padding: '8px 12px', background: 'rgba(255,23,68,0.1)', borderBottom: '1px solid rgba(255,23,68,0.2)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <span style={{ fontSize: 12, fontWeight: 700, color: '#ff1744' }}>{'\u{1F6A8}'} {em.label}</span>
                    <span style={{ fontSize: 10, color: '#6b7280', marginLeft: 8 }}>{em.id}</span>
                  </div>
                  <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                    <span style={{ fontSize: 10, color: '#ff1744', fontWeight: 600, textTransform: 'uppercase' }}>{em.status}</span>
                    <div style={{ fontSize: 10, color: '#00e5ff', cursor: 'pointer' }} onClick={() => handleResolve(em.id)}>
                      Resolve
                    </div>
                  </div>
                </div>

                {/* Details */}
                <div style={{ padding: '8px 12px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, fontSize: 11 }}>
                  <div><span style={{ color: '#6b7280' }}>Zone:</span> <span style={{ color: '#e0e5ec' }}>{em.zone_name}</span></div>
                  <div><span style={{ color: '#6b7280' }}>Evacuation:</span> <span style={{ color: em.evacuation_status === 'in_progress' ? '#ffa000' : '#e0e5ec' }}>{em.evacuation_radius_m > 0 ? `${em.evacuation_radius_m}m - ${em.evacuation_status}` : 'N/A'}</span></div>
                  <div><span style={{ color: '#6b7280' }}>Shutdown:</span> <span style={{ color: em.shutdown_initiated ? '#ff1744' : '#e0e5ec' }}>{em.shutdown_initiated ? 'Initiated' : 'Not required'}</span></div>
                  <div><span style={{ color: '#6b7280' }}>Rescue Team:</span> <span style={{ color: em.rescue_team_dispatched ? '#ffa000' : '#e0e5ec' }}>{em.rescue_team_dispatched ? 'Dispatched' : 'Standing by'}</span></div>
                </div>

                {/* Alerts dispatched */}
                <div style={{ padding: '0 12px 8px' }}>
                  <div style={{ fontSize: 10, fontWeight: 600, color: '#00e676', marginBottom: 4 }}>Alerts Dispatched:</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                    {em.alerts_dispatched?.map((a, j) => (
                      <span key={j} style={{ fontSize: 9, padding: '1px 6px', background: 'rgba(0,230,118,0.1)', borderRadius: 8, color: '#00e676' }}>
                        {'\u{2705}'} {a.channel}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Timeline */}
                <div style={{ padding: '0 12px 8px', maxHeight: 120, overflow: 'auto' }}>
                  <div style={{ fontSize: 10, fontWeight: 600, color: '#00e5ff', marginBottom: 4 }}>Response Timeline:</div>
                  {(em.timeline || []).slice(-5).map((t, j) => (
                    <div key={j} style={{ display: 'flex', gap: 6, fontSize: 9, color: '#6b7280', padding: '1px 0' }}>
                      <span style={{ color: '#00e5ff', flexShrink: 0 }}>{formatTime(t.time)}</span>
                      <span>{t.event}</span>
                    </div>
                  ))}
                </div>

                {/* Incident Report */}
                {em.incident_report && (
                  <div style={{ padding: '0 12px 8px' }}>
                    <div style={{ fontSize: 10, fontWeight: 600, color: '#ffa000', marginBottom: 2 }}>Incident Report Generated:</div>
                    <div style={{ fontSize: 9, color: '#6b7280' }}>Report ID: {em.incident_report.report_id} · {em.incident_report.status}</div>
                    <div style={{ fontSize: 9, color: '#6b7280' }}>Classification: {em.incident_report.classification}</div>
                    <div style={{ fontSize: 9, color: '#ffa000', marginTop: 4 }}>Regulatory References: {em.incident_report.details?.regulatory_references?.join(', ')}</div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Log */}
          <div style={{ maxHeight: 100, overflow: 'auto', background: '#0d1520', borderRadius: 6, padding: 8, border: '1px solid #1f2937' }}>
            <div style={{ fontSize: 9, fontWeight: 600, color: '#6b7280', marginBottom: 4 }}>EVENT LOG</div>
            {log.map((entry, i) => (
              <div key={i} style={{ fontSize: 9, color: '#6b7280', padding: '1px 0', fontFamily: 'monospace' }}>
                [{entry.time}] {entry.msg}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
