import React, { useState, useEffect, useCallback } from 'react';

const C = {
  bg: '#080c16', card: '#111827', border: '#1f2937', text: '#e0e5ec',
  muted: '#6b7280', accent: '#00e5ff', critical: '#ff1744', high: '#ff6d00',
  warning: '#ffa000', ok: '#00e676',
};

function Gauge({ value, max, label, color, unit = '' }) {
  const pct = Math.min(value / max * 100, 100);
  return (
    <div style={{ textAlign: 'center', padding: '10px 6px' }}>
      <div style={{
        position: 'relative', width: 70, height: 70, margin: '0 auto 6px',
        borderRadius: '50%', background: `conic-gradient(${color} ${pct}%, #1a2332 ${pct}%)`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <div style={{
          width: 54, height: 54, borderRadius: '50%', background: C.card,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexDirection: 'column',
        }}>
          <span style={{ fontSize: 14, fontWeight: 700, color }}>{value}</span>
          {unit && <span style={{ fontSize: 7, color: C.muted }}>{unit}</span>}
        </div>
      </div>
      <div style={{ fontSize: 9, color: C.muted }}>{label}</div>
    </div>
  );
}

function MiniSparkline({ data, color }) {
  if (!data || data.length < 2) return null;
  const max = Math.max(...data, 1);
  const min = Math.min(...data, 0);
  const range = max - min || 1;
  const w = 80, h = 24;
  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * w;
    const y = h - ((v - min) / range) * h;
    return `${x},${y}`;
  }).join(' ');
  return (
    <svg width={w} height={h}>
      <polyline points={points} fill="none" stroke={color} strokeWidth={1.5} />
    </svg>
  );
}

export default function DigitalTwinDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/digital-twin');
      if (!res.ok) throw new Error('Failed');
      const json = await res.json();
      setData(json.data || json);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => { const id = setInterval(fetchData, 5000); return () => clearInterval(id); }, [fetchData]);

  if (loading) return <div style={{ padding: 40, textAlign: 'center', color: C.muted }}>Loading plant pulse...</div>;
  if (!data) return <div style={{ padding: 40, textAlign: 'center', color: C.critical }}>Failed to load</div>;

  const { kpi, sensors, permits, alerts, health_index, risk_score, severity, compliance_score, status_summary, zone_metrics } = data;

  return (
    <div style={{ padding: 16 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: C.accent }}>{'\u{1F4CA}'} Digital Twin Dashboard</div>
          <div style={{ fontSize: 9, color: C.muted }}>{data.plant_name} | {data.timestamp ? new Date(data.timestamp).toLocaleTimeString() : ''}</div>
        </div>
        <div style={{
          padding: '4px 12px', borderRadius: 12, fontSize: 10, fontWeight: 700,
          background: severity === 'critical' ? 'rgba(255,23,68,0.2)' : severity === 'high' ? 'rgba(255,109,0,0.2)' : 'rgba(0,230,118,0.15)',
          border: `1px solid ${severity === 'critical' ? C.critical : severity === 'high' ? C.high : C.ok}`,
          color: severity === 'critical' ? C.critical : severity === 'high' ? C.high : C.ok,
        }}>
          {severity.toUpperCase()} {data.trend_direction === 'increasing' ? '\u2191' : data.trend_direction === 'decreasing' ? '\u2193' : '\u2192'}
        </div>
      </div>

      {/* KPI Gauges */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(90px, 1fr))', gap: 8, marginBottom: 16 }}>
        <div style={{ background: C.card, borderRadius: 8, border: `1px solid ${C.border}` }}>
          <Gauge value={health_index?.overall ?? 0} max={100} label="Plant Health" color={C.accent} unit="%" />
        </div>
        <div style={{ background: C.card, borderRadius: 8, border: `1px solid ${C.border}` }}>
          <Gauge value={Math.round((risk_score ?? 0) * 100)} max={100} label="Risk Score" color={risk_score > 0.6 ? C.critical : risk_score > 0.3 ? C.high : C.ok} />
        </div>
        <div style={{ background: C.card, borderRadius: 8, border: `1px solid ${C.border}` }}>
          <Gauge value={sensors?.online ?? 0} max={sensors?.total ?? 1} label={`Sensors (${sensors?.total ?? 0})`} color={C.accent} />
        </div>
        <div style={{ background: C.card, borderRadius: 8, border: `1px solid ${C.border}` }}>
          <Gauge value={compliance_score ?? 0} max={100} label="Compliance" color={C.ok} unit="%" />
        </div>
        <div style={{ background: C.card, borderRadius: 8, border: `1px solid ${C.border}` }}>
          <Gauge value={kpi?.critical_zones ?? 0} max={kpi?.zone_count ?? 1} label="Critical Zones" color={C.critical} />
        </div>
        <div style={{ background: C.card, borderRadius: 8, border: `1px solid ${C.border}` }}>
          <Gauge value={alerts?.critical ?? 0} max={Math.max(alerts?.total ?? 1, 1)} label="Critical Alerts" color={C.critical} />
        </div>
      </div>

      {/* Status summary */}
      {status_summary?.lines && (
        <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
          {status_summary.lines.map((l, i) => (
            <div key={i} style={{
              padding: '6px 12px', borderRadius: 6, fontSize: 10, fontWeight: 600,
              background: l.level === 'critical' ? 'rgba(255,23,68,0.1)' : l.level === 'warning' ? 'rgba(255,109,0,0.1)' : l.level === 'ok' ? 'rgba(0,230,118,0.1)' : 'rgba(0,229,255,0.06)',
              border: `1px solid ${l.level === 'critical' ? C.critical : l.level === 'warning' ? C.high : l.level === 'ok' ? C.ok : C.accent}`,
              color: l.level === 'critical' ? C.critical : l.level === 'warning' ? C.high : l.level === 'ok' ? C.ok : C.accent,
            }}>{l.text}</div>
          ))}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {/* Zone risk breakdown */}
        <div style={{ background: C.card, borderRadius: 8, border: `1px solid ${C.border}`, padding: 14 }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: C.accent, marginBottom: 8 }}>Zone Risk Breakdown</div>
          {(zone_metrics || []).slice(0, 10).map(z => {
            const color = z.score > 0.6 ? C.critical : z.score > 0.3 ? C.high : z.score > 0.1 ? C.warning : C.ok;
            return (
              <div key={z.id} style={{ marginBottom: 6 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: C.muted, marginBottom: 2 }}>
                  <span>{z.id} - {z.name}</span>
                  <span style={{ color, fontWeight: 600 }}>{(z.score * 100).toFixed(0)}</span>
                </div>
                <div style={{ height: 4, background: '#1a2332', borderRadius: 2 }}>
                  <div style={{ width: `${Math.min(z.score * 100, 100)}%`, height: '100%', borderRadius: 2, background: color }} />
                </div>
              </div>
            );
          })}
        </div>

        {/* Sensor health + alert summary */}
        <div>
          <div style={{ background: C.card, borderRadius: 8, border: `1px solid ${C.border}`, padding: 14, marginBottom: 16 }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: C.accent, marginBottom: 8 }}>Sensor Health</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, fontSize: 11 }}>
              <div><span style={{ color: C.muted }}>Online:</span> <span style={{ color: C.ok }}>{sensors?.online ?? 0}</span></div>
              <div><span style={{ color: C.muted }}>Warning:</span> <span style={{ color: C.warning }}>{sensors?.warning ?? 0}</span></div>
              <div><span style={{ color: C.muted }}>Critical:</span> <span style={{ color: C.critical }}>{sensors?.critical ?? 0}</span></div>
              <div><span style={{ color: C.muted }}>Offline:</span> <span style={{ color: C.muted }}>{sensors?.offline ?? 0}</span></div>
            </div>
          </div>

          <div style={{ background: C.card, borderRadius: 8, border: `1px solid ${C.border}`, padding: 14 }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: C.accent, marginBottom: 8 }}>Permit Risk</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, fontSize: 11 }}>
              <div><span style={{ color: C.muted }}>Critical:</span> <span style={{ color: C.critical }}>{permits?.critical ?? 0}</span></div>
              <div><span style={{ color: C.muted }}>High:</span> <span style={{ color: C.high }}>{permits?.high ?? 0}</span></div>
              <div><span style={{ color: C.muted }}>Medium:</span> <span style={{ color: C.warning }}>{permits?.medium ?? 0}</span></div>
              <div><span style={{ color: C.muted }}>Low:</span> <span style={{ color: C.ok }}>{permits?.low ?? 0}</span></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
