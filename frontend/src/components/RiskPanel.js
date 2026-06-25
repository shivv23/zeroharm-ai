import React from 'react';
import { getRiskColor, getRiskLabel } from '../store/plantData';
import RiskTrendChart from './RiskTrendChart';

export default function RiskPanel({ riskData, zoneRisks, selectedZone, plantState, onEmergency, riskTrend, compliance }) {
  const riskScore = riskData?.risk_score ?? 0;
  const severity = riskData?.severity ?? 'normal';
  const alerts = riskData?.alerts ?? [];
  const compoundRisks = riskData?.compound_risks ?? [];
  const sensorAnalysis = riskData?.sensor_analysis ?? {};
  const permitAnalysis = riskData?.permit_analysis ?? {};

  const severityColor = { critical: '#ff1744', high: '#ff6d00', warning: '#ffa000', info: '#00e5ff', normal: '#00e676' };
  const criticalAlerts = alerts.filter(a => a.severity === 'critical').length;
  const highAlerts = alerts.filter(a => a.severity === 'high').length;
  const complianceScore = compliance?.overall_compliance_score ?? null;

  return (
    <div style={{ padding: 14, fontSize: 12 }}>
      {/* Overall Risk Score */}
      <div style={sx.section}>
        <div style={sx.sectionTitle}>{'\u{1F4CA}'} Risk Score</div>
        <div style={{ textAlign: 'center', padding: '8px 0' }}>
          <div style={{
            width: 72, height: 72, borderRadius: '50%', margin: '0 auto',
            border: `4px solid ${severityColor[severity] || '#00e676'}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexDirection: 'column', background: 'rgba(0,0,0,0.3)',
            boxShadow: `0 0 20px ${severityColor[severity] || '#00e676'}33`,
          }}>
            <div style={{ fontSize: 20, fontWeight: 700, color: severityColor[severity] || '#00e676' }}>
              {(riskScore * 100).toFixed(0)}
            </div>
            <div style={{ fontSize: 8, color: '#6b7280' }}>/ 100</div>
          </div>
          <div style={{
            marginTop: 6, fontSize: 12, fontWeight: 700,
            color: severityColor[severity] || '#00e676',
            textTransform: 'uppercase', letterSpacing: 1,
          }}>{severity}</div>
          <div style={{ fontSize: 9, color: '#6b7280', marginTop: 2 }}>{riskData?.summary || 'All systems nominal'}</div>
        </div>
      </div>

      {/* Health Index */}
      {complianceScore !== null && (
        <div style={sx.section}>
          <div style={sx.sectionTitle}>{'\u{1F3AF}'} Plant Health</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '4px 0' }}>
            <div style={{
              width: 44, height: 44, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
              border: `3px solid ${complianceScore >= 80 ? '#00e676' : complianceScore >= 60 ? '#ffa000' : '#ff1744'}`,
              fontSize: 16, fontWeight: 700,
              color: complianceScore >= 80 ? '#00e676' : complianceScore >= 60 ? '#ffa000' : '#ff1744',
            }}>{complianceScore.toFixed(0)}</div>
            <div>
              <div style={{ fontSize: 12, color: '#e0e5ec' }}>
                {complianceScore >= 80 ? 'Excellent' : complianceScore >= 60 ? 'Needs Review' : 'Critical'}
              </div>
              <div style={{ fontSize: 9, color: '#6b7280' }}>Compliance Score</div>
            </div>
          </div>
        </div>
      )}

      {/* Risk Trend Chart */}
      {riskTrend && riskTrend.length > 1 && (
        <div style={sx.section}>
          <RiskTrendChart data={riskTrend} width={280} height={60} />
        </div>
      )}

      {/* Alert Summary */}
      <div style={sx.section}>
        <div style={sx.sectionTitle}>{'\u{26A0}\uFE0F'} Alerts</div>
        <div style={{ display: 'flex', gap: 6, marginTop: 6 }}>
          <div style={{ flex: 1, textAlign: 'center', padding: '6px 4px', background: 'rgba(255,23,68,0.1)', borderRadius: 6, border: '1px solid rgba(255,23,68,0.3)' }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: '#ff1744' }}>{criticalAlerts}</div>
            <div style={{ fontSize: 9, color: '#6b7280' }}>Critical</div>
          </div>
          <div style={{ flex: 1, textAlign: 'center', padding: '6px 4px', background: 'rgba(255,109,0,0.1)', borderRadius: 6, border: '1px solid rgba(255,109,0,0.3)' }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: '#ff6d00' }}>{highAlerts}</div>
            <div style={{ fontSize: 9, color: '#6b7280' }}>High</div>
          </div>
          <div style={{ flex: 1, textAlign: 'center', padding: '6px 4px', background: 'rgba(255,160,0,0.1)', borderRadius: 6, border: '1px solid rgba(255,160,0,0.3)' }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: '#ffa000' }}>{alerts.length - criticalAlerts - highAlerts}</div>
            <div style={{ fontSize: 9, color: '#6b7280' }}>Other</div>
          </div>
        </div>
      </div>

      {/* Compound Risks */}
      {compoundRisks && compoundRisks.length > 0 && (
        <div style={sx.section}>
          <div style={{ ...sx.sectionTitle, color: '#ff1744' }}>{'\u{1F525}'} Compound Risk</div>
          {compoundRisks.slice(0, 2).map((cr, i) => (
            <div key={i} style={{ padding: '6px 8px', background: 'rgba(255,23,68,0.08)', borderRadius: 6, marginBottom: 4, borderLeft: '3px solid #ff1744' }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: '#ff1744' }}>{cr.zone_name} · {cr.permit_type}</div>
              {(cr.risks || []).slice(0, 1).map((r, j) => (
                <div key={j} style={{ fontSize: 9, color: '#9ca3af', marginTop: 1 }}>{'\u{2022}'} {r}</div>
              ))}
              <div style={{ fontSize: 9, color: '#ff6d00', marginTop: 2, fontWeight: 600 }}>Score: {(cr.compound_risk_score * 100).toFixed(0)}%</div>
            </div>
          ))}
        </div>
      )}

      {/* Zone Scores */}
      <div style={sx.section}>
        <div style={sx.sectionTitle}>{'\u{1F3E0}'} Zone Risks</div>
        {Object.entries(zoneRisks || {}).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([zid, score]) => (
          <div key={zid} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '2px 0' }}>
            <div style={{ flex: 1, fontSize: 10, color: selectedZone?.id === zid ? '#00e5ff' : '#9ca3af' }}>{zid}</div>
            <div style={{ width: 70, height: 5, background: '#1f2937', borderRadius: 3 }}>
              <div style={{ width: `${score * 100}%`, height: '100%', background: getRiskColor(score), borderRadius: 3, transition: 'width 0.5s' }} />
            </div>
            <div style={{ fontSize: 10, fontWeight: 600, color: getRiskColor(score), width: 26, textAlign: 'right' }}>{(score * 100).toFixed(0)}</div>
          </div>
        ))}
      </div>

      {/* Agent Status */}
      <div style={sx.section}>
        <div style={sx.sectionTitle}>{'\u{1F916}'} Agents</div>
        {[
          { name: 'Sensor Monitor', status: 'Active', color: '#00e5ff' },
          { name: 'Permit Activity', status: 'Active', color: '#ffa000' },
          { name: 'Maintenance', status: 'Active', color: '#00e676' },
          { name: 'Compound Risk', status: compoundRisks?.length > 0 ? 'Alert' : 'Active', color: compoundRisks?.length > 0 ? '#ff1744' : '#7c4dff' },
          { name: 'Compliance Audit', status: 'Active', color: '#7c4dff' },
        ].map((agent, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '2px 0', fontSize: 10 }}>
            <span style={{ color: '#9ca3af' }}>{agent.name}</span>
            <span style={{ color: agent.color, fontWeight: 600 }}>{'\u{25CF}'} {agent.status}</span>
          </div>
        ))}
      </div>

      {/* Emergency Trigger */}
      <div style={{ padding: '8px 14px', background: 'linear-gradient(135deg, rgba(255,23,68,0.2), rgba(213,0,0,0.15))',
                    borderRadius: 8, border: '1px solid rgba(255,23,68,0.3)', cursor: 'pointer', textAlign: 'center' }}
           onClick={onEmergency}>
        <div style={{ fontSize: 18 }}>{'\u{1F6A8}'}</div>
        <div style={{ fontSize: 11, fontWeight: 700, color: '#ff1744', marginTop: 2 }}>EMERGENCY RESPONSE</div>
        <div style={{ fontSize: 9, color: '#6b7280', marginTop: 1 }}>Triggers full orchestration protocol</div>
      </div>
    </div>
  );
}

const sx = {
  section: { marginBottom: 12, paddingBottom: 10, borderBottom: '1px solid #1a2332' },
  sectionTitle: { fontSize: 10, fontWeight: 600, color: '#00e5ff', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 6 },
};
