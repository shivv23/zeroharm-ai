import React, { useState, useEffect, useCallback } from 'react';
import { COLORS, SX } from '../store/theme';

const STYLE = {
  card: { background: '#111827', borderRadius: 8, border: '1px solid #1f2937', padding: 16 },
  value: { fontSize: 22, fontWeight: 700, color: '#e0e5ec' },
  label: { fontSize: 10, color: '#6b7280', marginTop: 2 },
  accent: { color: '#00e5ff' },
  green: { color: '#00e676' },
  red: { color: '#ff1744' },
  orange: { color: '#ffa000' },
};

export default function CostOfSafetyDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/cost-of-safety');
      if (!res.ok) throw new Error('Failed to load');
      const json = await res.json();
      setData(json.data || json);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (loading) return <div style={{ padding: 40, textAlign: 'center', color: '#6b7280' }}>Loading cost data...</div>;
  if (error) return <div style={{ padding: 40, textAlign: 'center', color: '#ff1744' }}>Error: {error}</div>;
  if (!data) return null;

  const maxZoneCost = Math.max(...Object.values(data.zone_costs || {}), 1);
  const maxYearCost = Math.max(...Object.values(data.yearly_costs || {}), 1);
  const severityOrder = ['catastrophic', 'critical', 'major', 'moderate', 'near_miss'];

  return (
    <div style={{ padding: 16 }}>
      <div style={{ ...SX.sectionTitle, fontSize: 13, marginBottom: 16 }}>
        {'\u{1F4B0}'} Cost of Safety Dashboard
      </div>

      {/* KPI cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(170px, 1fr))', gap: 12, marginBottom: 20 }}>
        <div style={STYLE.card}>
          <div style={STYLE.value}>{'\u{20B9}'}{(data.total_cost || 0).toLocaleString()}</div>
          <div style={STYLE.label}>Total Cost (all incidents)</div>
        </div>
        <div style={STYLE.card}>
          <div style={{ ...STYLE.value, ...STYLE.red }}>{'\u{20B9}'}{(data.total_fines || 0).toLocaleString()}</div>
          <div style={STYLE.label}>Regulatory Fines</div>
        </div>
        <div style={STYLE.card}>
          <div style={{ ...STYLE.value, ...STYLE.orange }}>{'\u{20B9}'}{((data.ongoing_risk_cost || 0)).toLocaleString()}</div>
          <div style={STYLE.label}>Current Risk Exposure (monthly)</div>
        </div>
        <div style={STYLE.card}>
          <div style={{ ...STYLE.value, ...STYLE.green }}>{'\u{20B9}'}{(data.prevention_savings_estimate || 0).toLocaleString()}</div>
          <div style={STYLE.label}>Estimated Prevention Savings (annual)</div>
        </div>
        <div style={STYLE.card}>
          <div style={STYLE.value}>{data.total_incidents || 0}</div>
          <div style={STYLE.label}>Total Incidents</div>
        </div>
        <div style={STYLE.card}>
          <div style={STYLE.value}>{'\u{20B9}'}{(data.cost_per_incident_avg || 0).toLocaleString()}</div>
          <div style={STYLE.label}>Avg Cost Per Incident</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {/* Severity breakdown */}
        <div style={STYLE.card}>
          <div style={{ fontSize: 11, fontWeight: 600, color: '#00e5ff', marginBottom: 12 }}>By Severity</div>
          {severityOrder.map(s => {
            const count = data.severity_breakdown?.[s] || 0;
            if (!count) return null;
            const cost = {
              catastrophic: 5000000, critical: 1000000, major: 500000,
              moderate: 100000, near_miss: 50000,
            }[s] || 0;
            return (
              <div key={s} style={{ marginBottom: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#9ca3af', marginBottom: 3 }}>
                  <span style={{ textTransform: 'capitalize' }}>{s.replace('_', ' ')}</span>
                  <span>{count} incidents ({'\u{20B9}'}{(cost * count).toLocaleString()})</span>
                </div>
                <div style={{ height: 6, background: '#1a2332', borderRadius: 3 }}>
                  <div style={{
                    width: `${(count / Math.max(...Object.values(data.severity_breakdown || {}), 1)) * 100}%`,
                    height: '100%', borderRadius: 3,
                    background: s === 'catastrophic' ? '#ff1744' : s === 'critical' ? '#ff6d00' : s === 'major' ? '#ffa000' : s === 'moderate' ? '#ffea00' : '#00e676',
                  }} />
                </div>
              </div>
            );
          })}
        </div>

        {/* Zone costs */}
        <div style={STYLE.card}>
          <div style={{ fontSize: 11, fontWeight: 600, color: '#00e5ff', marginBottom: 12 }}>Cost by Zone</div>
          {Object.entries(data.zone_costs || {}).sort((a, b) => b[1] - a[1]).map(([zone, cost]) => (
            <div key={zone} style={{ marginBottom: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#9ca3af', marginBottom: 3 }}>
                <span>{zone}</span>
                <span>{'\u{20B9}'}{cost.toLocaleString()}</span>
              </div>
              <div style={{ height: 6, background: '#1a2332', borderRadius: 3 }}>
                <div style={{
                  width: `${(cost / maxZoneCost) * 100}%`,
                  height: '100%', borderRadius: 3,
                  background: '#00e5ff',
                }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Yearly trend */}
      <div style={{ ...STYLE.card, marginTop: 16 }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: '#00e5ff', marginBottom: 12 }}>Yearly Cost Trend</div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end', height: 120 }}>
          {Object.entries(data.yearly_costs || {}).sort().map(([year, cost]) => (
            <div key={year} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <div style={{
                width: '80%', height: `${(cost / maxYearCost) * 100}%`,
                minHeight: 8, borderRadius: '4px 4px 0 0',
                background: 'linear-gradient(180deg, #00e5ff, #0055ff)',
                transition: 'height 0.5s',
              }} />
              <div style={{ fontSize: 9, color: '#6b7280', marginTop: 4 }}>{year}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
