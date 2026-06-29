import React, { useState } from 'react';
import ws from '../store/websocketStore';
import { COLORS } from '../store/theme';

export default function PermitIntelligence({ permits, plantState }) {
  const [complianceCheck, setComplianceCheck] = useState(null);
  const [checkingPermit, setCheckingPermit] = useState(null);
  const [showAllPermits, setShowAllPermits] = useState(false);

  const displayedPermits = showAllPermits ? permits : permits.slice(0, 10);
  const criticalPermits = permits.filter(p => p.risk_level === 'Critical');
  const highPermits = permits.filter(p => p.risk_level === 'High');
  const permitTypes = {};
  permits.forEach(p => { permitTypes[p.type] = (permitTypes[p.type] || 0) + 1; });

  const zonePermitCount = {};
  permits.forEach(p => {
    if (!zonePermitCount[p.zone_id]) zonePermitCount[p.zone_id] = { count: 0, critical: 0, name: p.zone_name };
    zonePermitCount[p.zone_id].count++;
    if (p.risk_level === 'Critical') zonePermitCount[p.zone_id].critical++;
  });

  const overlapping = Object.entries(zonePermitCount).filter(([_, z]) => z.count > 1);

  const handleCheckCompliance = async (permit) => {
    setCheckingPermit(permit.id);
    try {
      const zoneSensors = plantState?.sensors
        ? Object.values(plantState.sensors).filter(s => s.zone_id === permit.zone_id)
        : [];
      const sensorReadings = {};
      zoneSensors.forEach(s => { sensorReadings[s.type] = s.value; });
      const result = await ws.fetchAPI('/rag/permit-compliance', {
        method: 'POST',
        body: { permit_type: permit.type, zone_hazard_class: 'High', sensor_readings: sensorReadings },
      });
      if (result) setComplianceCheck(result);
    } catch (e) {
      console.error('Compliance check error:', e);
    }
    setCheckingPermit(null);
  };

  return (
    <div style={{ padding: 16, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 16, fontWeight: 700 }}>{'\u{1F4CB}'} Digital Permit Intelligence Agent</div>
        <div style={{ fontSize: 11, color: COLORS.textMuted }}>AI-powered permit analysis against real-time plant conditions</div>
      </div>

      <div style={{ display: 'flex', gap: 12, flex: 1, overflow: 'hidden' }}>
        {/* Left: Permit List */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Summary Cards */}
          <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
            <div style={{ flex: 1, textAlign: 'center', padding: '6px 8px', background: COLORS.bgCard, borderRadius: 8, border: `1px solid ${COLORS.border}` }}>
              <div style={{ fontSize: 18, fontWeight: 700, color: COLORS.accent }}>{permits.length}</div>
              <div style={{ fontSize: 10, color: COLORS.textMuted }}>Active Permits</div>
            </div>
            <div style={{ flex: 1, textAlign: 'center', padding: '6px 8px', background: COLORS.bgCritical, borderRadius: 8, border: `1px solid ${COLORS.borderCritical}` }}>
              <div style={{ fontSize: 18, fontWeight: 700, color: COLORS.riskCritical }}>{criticalPermits.length}</div>
              <div style={{ fontSize: 10, color: COLORS.textMuted }}>Critical</div>
            </div>
            <div style={{ flex: 1, textAlign: 'center', padding: '6px 8px', background: COLORS.bgHigh, borderRadius: 8, border: `1px solid ${COLORS.borderHigh}` }}>
              <div style={{ fontSize: 18, fontWeight: 700, color: COLORS.riskHigh }}>{highPermits.length}</div>
              <div style={{ fontSize: 10, color: COLORS.textMuted }}>High Risk</div>
            </div>
          </div>

          {/* Overlap warnings */}
          {overlapping.length > 0 && (
            <div style={{ marginBottom: 8 }}>
              {overlapping.slice(0, 3).map(([zid, z]) => (
                <div key={zid} style={{ padding: '6px 10px', background: COLORS.bgWarning, borderRadius: 6, marginBottom: 4, border: `1px solid ${COLORS.borderWarning}`, fontSize: 11, color: COLORS.riskElevated }}>
                  {'\u{26A0}\uFE0F'} {z.count} permits active in {z.name} {z.critical > 0 ? `(${z.critical} critical)` : ''}
                </div>
              ))}
            </div>
          )}

          {/* Permit List */}
          <div style={{ flex: 1, overflow: 'auto' }}>
            {displayedPermits.map((p, i) => (
              <div key={p.id || i} style={{
                padding: '8px 10px', background: COLORS.bgCard, borderRadius: 6, marginBottom: 4,
                border: `1px solid ${p.risk_level === 'Critical' ? COLORS.borderCritical : p.risk_level === 'High' ? COLORS.borderHigh : COLORS.border}`,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <span style={{ fontSize: 11, fontWeight: 600, color: COLORS.text }}>{p.type}</span>
                    <span style={{ fontSize: 10, color: COLORS.textMuted, marginLeft: 8 }}>{p.id}</span>
                  </div>
                  <span style={{
                    fontSize: 9, fontWeight: 700, padding: '1px 6px', borderRadius: 8,
                    background: p.risk_level === 'Critical' ? COLORS.bgCriticalStronger : p.risk_level === 'High' ? COLORS.bgHighStronger : COLORS.bgNormal,
                    color: p.risk_level === 'Critical' ? COLORS.riskCritical : p.risk_level === 'High' ? COLORS.riskHigh : COLORS.riskNormal,
                  }}>{p.risk_level}</span>
                </div>
                <div style={{ fontSize: 10, color: COLORS.textMuted, marginTop: 2 }}>{p.zone_name} · {p.workers?.slice(0, 3).join(', ')}</div>
                <div style={{ marginTop: 4, display: 'flex', gap: 4 }}>
                  <div style={{ fontSize: 9, color: COLORS.accent, cursor: 'pointer' }}
                       onClick={() => handleCheckCompliance(p)}>
                    {'\u{1F50D}'} Check compliance
                  </div>
                </div>
              </div>
            ))}
            {permits.length > 10 && (
              <div style={{ textAlign: 'center', padding: 8, cursor: 'pointer', color: COLORS.accent, fontSize: 11 }}
                   onClick={() => setShowAllPermits(!showAllPermits)}>
                {showAllPermits ? 'Show less' : `Show all ${permits.length} permits`}
              </div>
            )}
          </div>
        </div>

        {/* Right: Compliance Check Result */}
        <div style={{ width: 320, overflow: 'auto' }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: COLORS.accent, marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 }}>
            Compliance Check
          </div>
          {!complianceCheck && (
            <div style={{ textAlign: 'center', padding: 30, color: COLORS.textMuted, fontSize: 11 }}>
              Click "Check compliance" on any permit to analyze against real-time conditions
            </div>
          )}
          {complianceCheck && (
            <div>
              <div style={{
                padding: '8px 12px', borderRadius: 6, marginBottom: 8,
                background: complianceCheck.compliant ? COLORS.bgNormal : COLORS.bgCritical,
                border: `1px solid ${complianceCheck.compliant ? COLORS.borderNormal : COLORS.borderCritical}`,
              }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: complianceCheck.compliant ? COLORS.riskNormal : COLORS.riskCritical }}>
                  {complianceCheck.compliant ? '\u{2705} COMPLIANT' : '\u{26A0}\uFE0F NON-COMPLIANT'}
                </div>
                <div style={{ fontSize: 10, color: COLORS.textSecondary, marginTop: 2 }}>{complianceCheck.permit_type}</div>
              </div>

              {complianceCheck.violations?.map((v, i) => (
                <div key={i} style={{ padding: '6px 10px', background: COLORS.bgCriticalLight, borderRadius: 4, marginBottom: 4, border: `1px solid ${COLORS.bgCriticalStrong}` }}>
                  <div style={{ fontSize: 10, color: COLORS.riskCritical }}>{'\u{2716}'} {v}</div>
                </div>
              ))}

              {complianceCheck.recommendations?.map((r, i) => (
                <div key={i} style={{ padding: '6px 10px', background: COLORS.bgInfo, borderRadius: 4, marginBottom: 4, border: `1px solid ${COLORS.bgAccentActive}` }}>
                  <div style={{ fontSize: 10, color: COLORS.accent }}>{'\u{1F4A1}'} {r}</div>
                </div>
              ))}

              {complianceCheck.applicable_regulations?.map((reg, i) => (
                <div key={i} style={{ padding: '6px 10px', background: COLORS.bgCard, borderRadius: 4, marginBottom: 4, border: `1px solid ${COLORS.border}` }}>
                  <div style={{ fontSize: 10, fontWeight: 600, color: COLORS.text }}>{reg.title}</div>
                  <div style={{ fontSize: 9, color: COLORS.textMuted, marginTop: 2 }}>{reg.content?.substring(0, 100)}...</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
