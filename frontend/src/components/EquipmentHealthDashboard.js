import React, { useState, useEffect, useCallback } from 'react';

const C = {
  bg: '#080c16', card: '#111827', border: '#1f2937', text: '#e0e5ec',
  muted: '#6b7280', accent: '#00e5ff', critical: '#ff1744', high: '#ff6d00',
  warning: '#ffa000', ok: '#00e676',
};

function healthColor(score) {
  if (score >= 80) return C.ok;
  if (score >= 60) return C.warning;
  if (score >= 40) return C.high;
  return C.critical;
}

export default function EquipmentHealthDashboard() {
  const [equipment, setEquipment] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch('/api/maintenance/equipment-health');
      if (!res.ok) throw new Error('Failed');
      const json = await res.json();
      const d = json.data || json;
      setEquipment(d.equipment || []);
      setSummary(d.summary || null);
    } catch {
      setEquipment([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (loading) return <div style={{ padding: 40, textAlign: 'center', color: C.muted }}>Analyzing equipment health...</div>;

  return (
    <div style={{ padding: 16 }}>
      <div style={{ fontSize: 13, fontWeight: 700, color: C.accent, marginBottom: 16 }}>
        {'\u{1F527}'} Equipment Health & Predictive Maintenance
      </div>

      {/* Summary cards */}
      {summary && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: 10, marginBottom: 16 }}>
          <div style={{ background: C.card, borderRadius: 8, border: `1px solid ${C.border}`, padding: 12, textAlign: 'center' }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: C.text }}>{summary.total}</div>
            <div style={{ fontSize: 9, color: C.muted }}>Total Equipment</div>
          </div>
          <div style={{ background: C.card, borderRadius: 8, border: `1px solid ${C.border}`, padding: 12, textAlign: 'center' }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: C.ok }}>{summary.healthy}</div>
            <div style={{ fontSize: 9, color: C.muted }}>Healthy</div>
          </div>
          <div style={{ background: C.card, borderRadius: 8, border: `1px solid ${C.border}`, padding: 12, textAlign: 'center' }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: C.warning }}>{summary.warning}</div>
            <div style={{ fontSize: 9, color: C.muted }}>Needs Attention</div>
          </div>
          <div style={{ background: C.card, borderRadius: 8, border: `1px solid ${C.border}`, padding: 12, textAlign: 'center' }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: C.critical }}>{summary.critical}</div>
            <div style={{ fontSize: 9, color: C.muted }}>Critical</div>
          </div>
          <div style={{ background: C.card, borderRadius: 8, border: `1px solid ${C.border}`, padding: 12, textAlign: 'center' }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: C.accent }}>{summary.average_health}</div>
            <div style={{ fontSize: 9, color: C.muted }}>Avg Health Score</div>
          </div>
          <div style={{ background: C.card, borderRadius: 8, border: `1px solid ${C.border}`, padding: 12, textAlign: 'center' }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: C.high }}>{summary.high_risk_count}</div>
            <div style={{ fontSize: 9, color: C.muted }}>High Failure Risk</div>
          </div>
        </div>
      )}

      {/* Equipment list */}
      <div style={{ display: 'grid', gap: 10 }}>
        {equipment.map((eq, i) => {
          const color = healthColor(eq.health_score);
          return (
            <div key={i} style={{
              background: C.card, borderRadius: 8, border: `1px solid ${C.border}`, padding: 14,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <div>
                  <span style={{ fontSize: 12, fontWeight: 600, color: C.text }}>{eq.name}</span>
                  <span style={{ fontSize: 9, color: C.muted, marginLeft: 6 }}>{eq.id} | Zone {eq.zone_id}</span>
                  {eq.critical && <span style={{ fontSize: 8, color: C.critical, marginLeft: 6 }}>CRITICAL</span>}
                </div>
                <span style={{ fontSize: 14, fontWeight: 700, color }}>{eq.health_score}</span>
              </div>
              <div style={{ height: 6, background: '#1a2332', borderRadius: 3, marginBottom: 8 }}>
                <div style={{ width: `${eq.health_score}%`, height: '100%', borderRadius: 3, background: color }} />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 8, fontSize: 10, color: C.muted }}>
                <div>
                  <span style={{ color: C.muted }}>Failure Risk:</span>
                  <span style={{ color: eq.failure_risk > 0.5 ? C.critical : C.ok, fontWeight: 600, marginLeft: 4 }}>
                    {(eq.failure_risk * 100).toFixed(0)}%
                  </span>
                </div>
                <div>
                  <span style={{ color: C.muted }}>RUL:</span>
                  <span style={{ color: C.text, marginLeft: 4 }}>{eq.remaining_useful_life_days}d</span>
                </div>
                <div>
                  <span style={{ color: C.muted }}>Priority:</span>
                  <span style={{
                    color: eq.maintenance_priority === 'critical' ? C.critical : eq.maintenance_priority === 'high' ? C.high : eq.maintenance_priority === 'medium' ? C.warning : C.ok,
                    fontWeight: 600, marginLeft: 4,
                  }}>{eq.maintenance_priority.toUpperCase()}</span>
                </div>
                <div>
                  <span style={{ color: C.muted }}>Sensors:</span>
                  <span style={{ color: C.text, marginLeft: 4 }}>{eq.sensor_count}</span>
                </div>
              </div>
              <div style={{ marginTop: 8, padding: '6px 10px', background: eq.health_score < 40 ? 'rgba(255,23,68,0.08)' : eq.health_score < 60 ? 'rgba(255,109,0,0.06)' : 'rgba(0,229,255,0.04)', borderRadius: 4, fontSize: 10, color: eq.health_score < 60 ? C.high : C.muted }}>
                {'\u{1F4A1}'} {eq.recommended_action}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
