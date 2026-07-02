import React, { useState, useEffect, useCallback } from 'react';

const C = {
  bg: '#080c16', card: '#111827', border: '#1f2937', text: '#e0e5ec',
  muted: '#6b7280', accent: '#00e5ff', critical: '#ff1744', high: '#ff6d00',
  warning: '#ffa000', ok: '#00e676',
};

function SeverityBadge({ confidence }) {
  const color = confidence > 0.6 ? C.critical : confidence > 0.3 ? C.warning : C.muted;
  return <span style={{ fontSize: 9, color, fontWeight: 600 }}>({(confidence * 100).toFixed(0)}%)</span>;
}

export default function RootCauseAnalysis() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [incidentType, setIncidentType] = useState('');

  const fetchAnalysis = useCallback(async () => {
    setLoading(true);
    try {
      const url = incidentType ? `/api/incident/root-cause?incident_type=${incidentType}` : '/api/incident/root-cause';
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed');
      const json = await res.json();
      setData(json.data || json);
    } catch (e) {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [incidentType]);

  useEffect(() => { fetchAnalysis(); }, [fetchAnalysis]);

  return (
    <div style={{ padding: 16 }}>
      <div style={{ fontSize: 13, fontWeight: 700, color: C.accent, marginBottom: 16 }}>
        {'\u{1F50D}'} Root Cause Analysis Engine
      </div>

      {/* Controls */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16, alignItems: 'center' }}>
        <select value={incidentType} onChange={e => setIncidentType(e.target.value)}
          style={{
            padding: '6px 10px', background: C.card, color: C.text,
            border: `1px solid ${C.border}`, borderRadius: 6, fontSize: 12,
          }}>
          <option value="">Latest incident</option>
          <option value="gas_leak">Gas Leak</option>
          <option value="fire">Fire</option>
          <option value="explosion">Explosion</option>
          <option value="confined_space_emergency">Confined Space</option>
        </select>
        <button onClick={fetchAnalysis} style={{
          padding: '6px 14px', background: C.accent, color: '#000',
          border: 'none', borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: 'pointer',
        }}>Analyze</button>
      </div>

      {loading && <div style={{ textAlign: 'center', padding: 40, color: C.muted }}>Analyzing causal chains...</div>}

      {data && data.incident && (
        <>
          {/* Incident summary */}
          <div style={{ background: C.card, borderRadius: 8, border: `1px solid ${C.border}`, padding: 14, marginBottom: 16 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: C.critical, marginBottom: 8 }}>
              {data.incident.description || data.incident.type.toUpperCase()}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, fontSize: 11 }}>
              <div><span style={{ color: C.muted }}>Zone:</span> {data.incident.zone} ({data.incident.zone_name})</div>
              <div><span style={{ color: C.muted }}>Severity:</span> {data.incident.severity}</div>
              <div><span style={{ color: C.muted }}>Hazard Class:</span> {data.incident.hazard_class}</div>
              <div><span style={{ color: C.muted }}>Date:</span> {data.incident.date || 'N/A'}</div>
              <div><span style={{ color: C.muted }}>Confidence:</span> {(data.overall_confidence * 100).toFixed(0)}%</div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            {/* Root causes */}
            <div style={{ background: C.card, borderRadius: 8, border: `1px solid ${C.border}`, padding: 14 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: C.accent, marginBottom: 8 }}>Root Causes</div>
              {data.root_causes.length === 0 && (
                <div style={{ fontSize: 11, color: C.muted }}>No primary root causes identified</div>
              )}
              {data.root_causes.map((c, i) => (
                <div key={i} style={{
                  padding: '8px 10px', marginBottom: 6,
                  background: 'rgba(255,23,68,0.08)', borderRadius: 6,
                  border: '1px solid rgba(255,23,68,0.2)',
                }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: C.critical }}>
                    {c.type.replace(/_/g, ' ').toUpperCase()} <SeverityBadge confidence={c.confidence} />
                  </div>
                  <div style={{ fontSize: 10, color: C.muted, marginTop: 2 }}>{c.description}</div>
                </div>
              ))}
            </div>

            {/* Contributing factors */}
            <div style={{ background: C.card, borderRadius: 8, border: `1px solid ${C.border}`, padding: 14 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: C.high, marginBottom: 8 }}>Contributing Factors</div>
              {data.contributing_factors.length === 0 && (
                <div style={{ fontSize: 11, color: C.muted }}>No contributing factors identified</div>
              )}
              {data.contributing_factors.map((c, i) => (
                <div key={i} style={{
                  padding: '8px 10px', marginBottom: 6,
                  background: 'rgba(255,109,0,0.06)', borderRadius: 6,
                  border: '1px solid rgba(255,109,0,0.15)',
                }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: C.high }}>
                    {c.type.replace(/_/g, ' ')} <SeverityBadge confidence={c.confidence} />
                  </div>
                  <div style={{ fontSize: 10, color: C.muted, marginTop: 2 }}>{c.description}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Causal chain */}
          <div style={{ background: C.card, borderRadius: 8, border: `1px solid ${C.border}`, padding: 14, marginTop: 16 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: C.accent, marginBottom: 8 }}>Causal Chain</div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {data.causal_chain.map((c, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', gap: 6,
                  background: c.confidence > 0.6 ? 'rgba(255,23,68,0.08)' : 'rgba(255,109,0,0.06)',
                  border: `1px solid ${c.confidence > 0.6 ? 'rgba(255,23,68,0.2)' : 'rgba(255,109,0,0.15)'}`,
                  borderRadius: 6, padding: '6px 10px', fontSize: 10, color: C.text,
                }}>
                  <span>{c.type.replace(/_/g, ' ')}</span>
                  <SeverityBadge confidence={c.confidence} />
                  {i < data.causal_chain.length - 1 && (
                    <span style={{ color: C.muted }}>{'\u2192'}</span>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Recommendations */}
          <div style={{ background: C.card, borderRadius: 8, border: `1px solid ${C.border}`, padding: 14, marginTop: 16 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: C.accent, marginBottom: 8 }}>Recommendations</div>
            <div style={{ display: 'grid', gap: 6 }}>
              {data.recommendations.map((r, i) => (
                <div key={i} style={{
                  display: 'flex', gap: 8, padding: '8px 10px',
                  background: r.priority === 'critical' ? 'rgba(255,23,68,0.06)' : r.priority === 'high' ? 'rgba(255,109,0,0.06)' : 'rgba(0,229,255,0.04)',
                  border: `1px solid ${r.priority === 'critical' ? 'rgba(255,23,68,0.2)' : r.priority === 'high' ? 'rgba(255,109,0,0.15)' : 'rgba(0,229,255,0.1)'}`,
                  borderRadius: 6,
                }}>
                  <span style={{
                    fontSize: 9, fontWeight: 700, padding: '2px 6px', borderRadius: 4,
                    background: r.priority === 'critical' ? C.critical : r.priority === 'high' ? C.high : C.accent,
                    color: '#000', height: 'fit-content',
                  }}>{r.priority.toUpperCase()}</span>
                  <div>
                    <div style={{ fontSize: 11, fontWeight: 600, color: C.text }}>{r.action}</div>
                    <div style={{ fontSize: 10, color: C.muted }}>{r.detail}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
