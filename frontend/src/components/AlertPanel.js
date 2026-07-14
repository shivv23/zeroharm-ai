import React from 'react';
import { SEVERITY, COLORS } from '../store/theme';

const SEVERITY_CONFIG = Object.entries(SEVERITY).reduce((acc, [key, val]) => {
  acc[key] = { ...val, icon: key === 'critical' ? '\u{1F525}' : key === 'high' ? '\u{26A0}\uFE0F' : key === 'warning' ? '\u{26A0}\uFE0F' : key === 'info' ? '\u{2139}\uFE0F' : '\u{2705}' };
  return acc;
}, {});

function AlertPanel({ alerts = [], riskData }) {
  const compoundRisks = riskData?.compound_risks ?? [];
  const allItems = [
    ...(compoundRisks.map(cr => ({
      type: 'COMPOUND_RISK',
      severity: 'critical',
      source: 'compound_risk_engine',
      message: cr.recommendation || 'Compound risk condition detected',
      zone_name: cr.zone_name,
      permit_type: cr.permit_type,
      risks: cr.risks,
      compound_risk_score: cr.compound_risk_score,
    }))),
    ...alerts,
  ].sort((a, b) => {
    const order = { critical: 0, high: 1, warning: 2, info: 3, normal: 4 };
    return (order[a.severity] ?? 5) - (order[b.severity] ?? 5);
  });

  const criticalCount = allItems.filter(a => a.severity === 'critical').length;
  const highCount = allItems.filter(a => a.severity === 'high').length;

  return (
    <div style={{ padding: 16, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 700 }}>{'\u{26A0}\uFE0F'} Alerts & Intelligence</div>
          <div style={{ fontSize: 11, color: COLORS.textMuted }}>Fused from all agent analyses</div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {criticalCount > 0 && (
            <div style={{ background: COLORS.bgCriticalStrong, color: COLORS.riskCritical, padding: '2px 8px', borderRadius: 12, fontSize: 11, fontWeight: 700 }}>
              {criticalCount} Critical
            </div>
          )}
          {highCount > 0 && (
            <div style={{ background: COLORS.bgHigh, color: COLORS.riskHigh, padding: '2px 8px', borderRadius: 12, fontSize: 11, fontWeight: 700 }}>
              {highCount} High
            </div>
          )}
        </div>
      </div>

      <div style={{ flex: 1, overflow: 'auto' }}>
        {allItems.length === 0 && (
          <div style={{ textAlign: 'center', padding: 40, color: COLORS.textMuted }}>
            <div style={{ fontSize: 40, marginBottom: 8 }}>{'\u{2705}'}</div>
            <div style={{ fontSize: 14, fontWeight: 600 }}>No active alerts</div>
            <div style={{ fontSize: 11 }}>All safety parameters are within normal range</div>
          </div>
        )}
        {allItems.map((item, i) => {
          const config = SEVERITY_CONFIG[item.severity] || SEVERITY_CONFIG.info;
          return (
            <div key={i} style={{
              padding: '10px 12px', background: config.bg, borderRadius: 8,
              border: `1px solid ${config.border}`, marginBottom: 6,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span>{config.icon}</span>
                  <span style={{ fontSize: 10, fontWeight: 700, color: config.color, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                    {item.type?.replace(/_/g, ' ') || item.severity}
                  </span>
                  <span style={{ fontSize: 9, color: COLORS.textMuted }}>{item.source?.replace(/_/g, ' ')}</span>
                </div>
                <span style={{ fontSize: 9, color: COLORS.textMuted }}>
                  {item.timestamp ? new Date(item.timestamp).toLocaleTimeString() : ''}
                </span>
              </div>
              <div style={{ fontSize: 12, color: COLORS.text }}>{item.message}</div>
              {item.zone_name && (
                <div style={{ fontSize: 10, color: COLORS.textMuted, marginTop: 2 }}>
                  {'\u{1F3E0}'} {item.zone_name} {item.permit_type ? `· ${item.permit_type}` : ''}
                </div>
              )}
              {item.risks && item.risks.length > 0 && (
                <div style={{ marginTop: 4 }}>
                  {item.risks.slice(0, 3).map((r, j) => (
                    <div key={j} style={{ fontSize: 10, color: COLORS.riskElevated, marginTop: 1 }}>{'\u{2022}'} {r}</div>
                  ))}
                </div>
              )}
              {item.compound_risk_score && (
                <div style={{ fontSize: 10, color: config.color, marginTop: 4, fontWeight: 600 }}>
                  Compound Risk Score: {(item.compound_risk_score * 100).toFixed(0)}%
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default React.memo(AlertPanel);
