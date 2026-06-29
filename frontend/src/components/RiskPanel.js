import React from 'react';
import { getRiskColor } from '../store/plantData';
import RiskTrendChart from './RiskTrendChart';
import { COLORS, SX, AGENT_COLORS } from '../store/theme';

export default function RiskPanel({ riskData = null, zoneRisks = {}, selectedZone = null, plantState = null, onEmergency = () => {}, riskTrend = [], compliance = null }) {
  const riskScore = riskData?.risk_score ?? 0;
  const severity = riskData?.severity ?? 'normal';
  const alerts = riskData?.alerts ?? [];
  const compoundRisks = riskData?.compound_risks ?? [];

  const severityColor = { critical: COLORS.riskCritical, high: COLORS.riskHigh, warning: COLORS.riskElevated, info: COLORS.accent, normal: COLORS.riskNormal };
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
            border: `4px solid ${severityColor[severity] || COLORS.riskNormal}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexDirection: 'column', background: COLORS.bgModal,
            boxShadow: `0 0 20px ${severityColor[severity] || COLORS.riskNormal}33`,
          }}>
            <div style={{ fontSize: 20, fontWeight: 700, color: severityColor[severity] || COLORS.riskNormal }}>
              {(riskScore * 100).toFixed(0)}
            </div>
            <div style={{ fontSize: 8, color: COLORS.textMuted }}>/ 100</div>
          </div>
          <div style={{
            marginTop: 6, fontSize: 12, fontWeight: 700,
            color: severityColor[severity] || COLORS.riskNormal,
            textTransform: 'uppercase', letterSpacing: 1,
          }}>{severity}</div>
          <div style={{ fontSize: 9, color: COLORS.textMuted, marginTop: 2 }}>{riskData?.summary || 'All systems nominal'}</div>
        </div>
      </div>

      {/* Health Index */}
      {complianceScore !== null && (
        <div style={sx.section}>
          <div style={sx.sectionTitle}>{'\u{1F3AF}'} Plant Health</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '4px 0' }}>
            <div style={{
              width: 44, height: 44, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
              border: `3px solid ${complianceScore >= 80 ? COLORS.riskNormal : complianceScore >= 60 ? COLORS.riskElevated : COLORS.riskCritical}`,
              fontSize: 16, fontWeight: 700,
              color: complianceScore >= 80 ? COLORS.riskNormal : complianceScore >= 60 ? COLORS.riskElevated : COLORS.riskCritical,
            }}>{complianceScore.toFixed(0)}</div>
            <div>
              <div style={{ fontSize: 12, color: COLORS.text }}>
                {complianceScore >= 80 ? 'Excellent' : complianceScore >= 60 ? 'Needs Review' : 'Critical'}
              </div>
              <div style={{ fontSize: 9, color: COLORS.textMuted }}>Compliance Score</div>
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
          <div style={{ flex: 1, textAlign: 'center', padding: '6px 4px', background: COLORS.bgCritical, borderRadius: 6, border: `1px solid ${COLORS.borderCritical}` }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: COLORS.riskCritical }}>{criticalAlerts}</div>
            <div style={{ fontSize: 9, color: COLORS.textMuted }}>Critical</div>
          </div>
          <div style={{ flex: 1, textAlign: 'center', padding: '6px 4px', background: COLORS.bgHigh, borderRadius: 6, border: `1px solid ${COLORS.borderHigh}` }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: COLORS.riskHigh }}>{highAlerts}</div>
            <div style={{ fontSize: 9, color: COLORS.textMuted }}>High</div>
          </div>
          <div style={{ flex: 1, textAlign: 'center', padding: '6px 4px', background: COLORS.bgWarning, borderRadius: 6, border: `1px solid ${COLORS.borderWarning}` }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: COLORS.riskElevated }}>{alerts.length - criticalAlerts - highAlerts}</div>
            <div style={{ fontSize: 9, color: COLORS.textMuted }}>Other</div>
          </div>
        </div>
      </div>

      {/* Compound Risks */}
      {compoundRisks && compoundRisks.length > 0 && (
        <div style={sx.section}>
          <div style={{ ...sx.sectionTitle, color: COLORS.riskCritical }}>{'\u{1F525}'} Compound Risk</div>
          {compoundRisks.slice(0, 2).map((cr, i) => (
            <div key={i} style={{ padding: '6px 8px', background: COLORS.bgCriticalLight, borderRadius: 6, marginBottom: 4, borderLeft: `3px solid ${COLORS.riskCritical}` }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: COLORS.riskCritical }}>{cr.zone_name} · {cr.permit_type}</div>
              {(cr.risks || []).slice(0, 1).map((r, j) => (
                <div key={j} style={{ fontSize: 9, color: COLORS.textSecondary, marginTop: 1 }}>{'\u{2022}'} {r}</div>
              ))}
              <div style={{ fontSize: 9, color: COLORS.riskHigh, marginTop: 2, fontWeight: 600 }}>Score: {(cr.compound_risk_score * 100).toFixed(0)}%</div>
            </div>
          ))}
        </div>
      )}

      {/* Zone Scores */}
      <div style={sx.section}>
        <div style={sx.sectionTitle}>{'\u{1F3E0}'} Zone Risks</div>
        {Object.entries(zoneRisks || {}).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([zid, score]) => (
          <div key={zid} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '2px 0' }}>
            <div style={{ flex: 1, fontSize: 10, color: selectedZone?.id === zid ? COLORS.accent : COLORS.textSecondary }}>{zid}</div>
            <div style={{ width: 70, height: 5, background: COLORS.border, borderRadius: 3 }}>
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
          { name: 'Sensor Monitor', status: 'Active', color: AGENT_COLORS['Sensor Monitor Agent'] },
          { name: 'Permit Activity', status: 'Active', color: AGENT_COLORS['Permit Activity Agent'] },
          { name: 'Maintenance', status: 'Active', color: AGENT_COLORS['Maintenance Status Agent'] },
          { name: 'Compound Risk', status: compoundRisks?.length > 0 ? 'Alert' : 'Active', color: compoundRisks?.length > 0 ? AGENT_COLORS['Compound Risk Detection Engine'] : AGENT_COLORS['Quality & Compliance Audit Agent'] },
          { name: 'Compliance Audit', status: 'Active', color: AGENT_COLORS['Quality & Compliance Audit Agent'] },
        ].map((agent, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '2px 0', fontSize: 10 }}>
            <span style={{ color: COLORS.textSecondary }}>{agent.name}</span>
            <span style={{ color: agent.color, fontWeight: 600 }}>{'\u{25CF}'} {agent.status}</span>
          </div>
        ))}
      </div>

      {/* Emergency Trigger */}
      <div style={{ padding: '8px 14px', background: COLORS.gradientEmergency,
                    borderRadius: 8, border: `1px solid ${COLORS.borderCritical}`, cursor: 'pointer', textAlign: 'center' }}
           onClick={onEmergency}>
        <div style={{ fontSize: 18 }}>{'\u{1F6A8}'}</div>
        <div style={{ fontSize: 11, fontWeight: 700, color: COLORS.riskCritical, marginTop: 2 }}>EMERGENCY RESPONSE</div>
        <div style={{ fontSize: 9, color: COLORS.textMuted, marginTop: 1 }}>Triggers full orchestration protocol</div>
      </div>
    </div>
  );
}

const sx = SX;
