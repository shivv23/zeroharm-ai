import React, { useState, useEffect, useCallback } from 'react';

const C = {
  bg: '#080c16', card: '#111827', border: '#1f2937', text: '#e0e5ec',
  muted: '#6b7280', accent: '#00e5ff', critical: '#ff1744', high: '#ff6d00',
  warning: '#ffa000', ok: '#00e676',
};

function metricColor(status) {
  return status === 'critical' ? C.critical : status === 'warning' ? C.high : C.ok;
}

export default function EnvironmentalDashboard() {
  const [metrics, setMetrics] = useState(null);
  const [compliance, setCompliance] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [metRes, compRes] = await Promise.all([
        fetch('/api/environmental/metrics').then(r => r.json()),
        fetch('/api/environmental/compliance').then(r => r.json()),
      ]);
      setMetrics(metRes.data || metRes);
      setCompliance(compRes.data || compRes);
    } catch { /* silent */ }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (loading) return <div style={{ padding: 40, textAlign: 'center', color: C.muted }}>Loading environmental data...</div>;

  const overall = metrics?.overall_status || 'unknown';
  const metricList = metrics?.metrics || {};

  return (
    <div style={{ padding: 16 }}>
      <div style={{ fontSize: 13, fontWeight: 700, color: C.accent, marginBottom: 16 }}>
        {'\u{1F30D}'} Environmental Sustainability Dashboard
      </div>

      {/* Overall status */}
      <div style={{
        background: C.card, borderRadius: 8, border: `1px solid ${C.border}`,
        padding: 14, marginBottom: 16, textAlign: 'center',
      }}>
        <div style={{
          fontSize: 14, fontWeight: 700,
          color: overall === 'critical' ? C.critical : overall === 'warning' ? C.high : C.ok,
        }}>
          Overall Environmental Status: {overall.toUpperCase()}
        </div>
        <div style={{ display: 'flex', justifyContent: 'center', gap: 16, marginTop: 8, fontSize: 11 }}>
          <span><span style={{ color: C.ok }}>{'\u25CF'}</span> Normal: {metrics?.normal || 0}</span>
          <span><span style={{ color: C.high }}>{'\u25CF'}</span> Warning: {metrics?.warning || 0}</span>
          <span><span style={{ color: C.critical }}>{'\u25CF'}</span> Critical: {metrics?.critical || 0}</span>
        </div>
      </div>

      {/* Metrics grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 10, marginBottom: 16 }}>
        {Object.entries(metricList).map(([key, m]) => {
          const color = metricColor(m.status);
          const isLimit = m.limit !== undefined && m.limit !== null;
          const pct = isLimit ? Math.min((m.value / m.limit) * 100, 100) : null;
          return (
            <div key={key} style={{
              background: C.card, borderRadius: 8, border: `1px solid ${color}30`, padding: 12,
            }}>
              <div style={{ fontSize: 9, fontWeight: 600, color: C.muted, textTransform: 'uppercase', marginBottom: 2 }}>{m.label}</div>
              <div style={{ fontSize: 16, fontWeight: 700, color }}>{m.value} <span style={{ fontSize: 9, color: C.muted }}>{m.unit}</span></div>
              {pct !== null && (
                <div style={{ height: 3, background: '#1a2332', borderRadius: 2, marginTop: 6 }}>
                  <div style={{ width: `${pct}%`, height: '100%', borderRadius: 2, background: color }} />
                </div>
              )}
              {isLimit && <div style={{ fontSize: 8, color: C.muted, marginTop: 2 }}>Limit: {m.limit}{m.unit}</div>}
            </div>
          );
        })}
      </div>

      {/* Compliance table */}
      {compliance?.standards && (
        <div style={{ background: C.card, borderRadius: 8, border: `1px solid ${C.border}`, padding: 14 }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: C.accent, marginBottom: 8 }}>Regulatory Compliance Status</div>
          {compliance.standards.map((std, i) => (
            <div key={i} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '8px 10px', marginBottom: 4,
              background: std.compliant ? 'rgba(0,230,118,0.04)' : 'rgba(255,23,68,0.06)',
              border: `1px solid ${std.compliant ? 'rgba(0,230,118,0.15)' : 'rgba(255,23,68,0.2)'}`,
              borderRadius: 6,
            }}>
              <div>
                <span style={{ fontSize: 11, fontWeight: 600, color: C.text }}>{std.standard}</span>
                <span style={{ fontSize: 9, color: C.muted, marginLeft: 6 }}>
                  ({std.total_applicable} metrics, {std.non_compliant_count} non-compliant)
                </span>
              </div>
              <span style={{
                fontSize: 9, fontWeight: 700, padding: '2px 8px', borderRadius: 8,
                background: std.compliant ? 'rgba(0,230,118,0.15)' : 'rgba(255,23,68,0.15)',
                color: std.compliant ? C.ok : C.critical,
              }}>{std.compliant ? 'COMPLIANT' : 'NON-COMPLIANT'}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
