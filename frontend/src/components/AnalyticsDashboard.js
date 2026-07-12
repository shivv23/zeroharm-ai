import React, { useState, useEffect } from 'react';
import ws from '../store/websocketStore';
import RiskTrendChart from './RiskTrendChart';
import { COLORS, FONT, SX, RADIUS } from '../store/theme';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

async function apiFetch(path) {
  const token = localStorage.getItem('zeroharm_token') || '';
  const headers = { ...(token ? { Authorization: `Bearer ${token}` } : {}) };
  try { const res = await fetch(`${API_BASE}${path}`, { headers }); return res.ok ? await res.json() : null; } catch (e) { return null; }
}

function MiniBar({ value, max, color, height = 6 }) {
  const pct = Math.min(100, (value / max) * 100);
  return <div style={{ width: '100%', height, background: COLORS.bgElevated, borderRadius: 3, overflow: 'hidden' }}>
    <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 3 }} />
  </div>;
}

export default function AnalyticsDashboard({ riskTrend }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch('/analytics/dashboard').then(d => { setData(d); setLoading(false); });
  }, []);

  if (loading) return <div style={{ padding: 40, textAlign: 'center', color: COLORS.textMuted }}>Loading analytics...</div>;
  if (!data) return <div style={{ padding: 40, textAlign: 'center', color: COLORS.textMuted }}>No data available</div>;

  const { sensor_summary, permit_summary, zone_risks, current_risk, current_severity, compliance_score, health_index } = data;
  const maxZoneRisk = Math.max(...(zone_risks || []).map(z => z.score), 1);

  return (
    <div style={{ padding: 16 }}>
      <div style={{ ...SX.sectionTitle, fontSize: FONT.md, marginBottom: 12 }}>Plant Analytics Dashboard</div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 10, marginBottom: 16 }}>
        {[
          { label: 'Risk Score', value: (current_risk * 100).toFixed(0), unit: '%', color: current_risk > 0.6 ? COLORS.riskCritical : current_risk > 0.3 ? COLORS.riskElevated : COLORS.riskNormal, sub: current_severity.toUpperCase() },
          { label: 'Compliance', value: compliance_score, unit: '%', color: compliance_score >= 70 ? COLORS.riskNormal : compliance_score >= 50 ? COLORS.riskElevated : COLORS.riskCritical, sub: health_index?.label || '' },
          { label: 'Sensors', value: sensor_summary?.total || 0, unit: 'total', color: COLORS.accent, sub: `${sensor_summary?.critical || 0} critical, ${sensor_summary?.warning || 0} warning` },
          { label: 'Permits', value: permit_summary?.total || 0, unit: 'active', color: COLORS.accentAlt, sub: `${permit_summary?.high_risk || 0} high risk` },
        ].map((card, i) => (
          <div key={i} style={{ ...SX.cardPadded, textAlign: 'center' }}>
            <div style={{ fontSize: FONT.xs, color: COLORS.textMuted, marginBottom: 4 }}>{card.label}</div>
            <div style={{ fontSize: 24, fontWeight: 700, color: card.color }}>{card.value}<span style={{ fontSize: FONT.sm, fontWeight: 400, color: COLORS.textMuted }}>/{card.unit}</span></div>
            <div style={{ fontSize: FONT.xs, color: COLORS.textDim, marginTop: 2 }}>{card.sub}</div>
          </div>
        ))}
      </div>

      {zone_risks && zone_risks.length > 0 && (
        <div style={{ ...SX.cardPadded, marginBottom: 16 }}>
          <div style={{ ...SX.sectionTitle }}>Zone Risk Scores</div>
          {zone_risks.slice(0, 10).map(z => {
            const color = z.score > 0.6 ? COLORS.riskCritical : z.score > 0.3 ? COLORS.riskElevated : COLORS.riskNormal;
            return <div key={z.zone_id} style={{ marginBottom: 6 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: FONT.xs, marginBottom: 2 }}>
                <span style={{ fontWeight: 600, color: COLORS.text }}>{z.zone_id}</span>
                <span style={{ color }}>{(z.score * 100).toFixed(0)}%</span>
              </div>
              <MiniBar value={z.score} max={maxZoneRisk} color={color} />
            </div>;
          })}
        </div>
      )}

      {riskTrend && riskTrend.length > 1 && (
        <div style={{ ...SX.cardPadded, marginBottom: 16 }}>
          <div style={{ ...SX.sectionTitle }}>Risk Score Trend</div>
          <RiskTrendChart data={riskTrend} width={600} height={120} />
        </div>
      )}

      {sensor_summary?.severity_breakdown && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 8 }}>
          {Object.entries(sensor_summary.severity_breakdown).sort().map(([sev, count]) => {
            const sevColors = { critical: COLORS.riskCritical, warning: COLORS.riskElevated, high: COLORS.riskHigh, normal: COLORS.riskNormal, info: COLORS.accent };
            return <div key={sev} style={{ ...SX.cardPadded, textAlign: 'center' }}>
              <div style={{ fontSize: 18, fontWeight: 700, color: sevColors[sev] || COLORS.text }}>{count}</div>
              <div style={{ fontSize: FONT.xs, color: COLORS.textMuted, textTransform: 'capitalize' }}>{sev}</div>
            </div>;
          })}
        </div>
      )}
    </div>
  );
}
