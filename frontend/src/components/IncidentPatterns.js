import React, { useState, useEffect } from 'react';
import ws from '../store/websocketStore';

const SEVERITY_COLORS = {
  CRITICAL: '#ff1744',
  HIGH: '#ff6d00',
  MEDIUM: '#ffa000',
  LOW: '#ffea00',
  INFO: '#00e5ff',
};

export default function IncidentPatterns() {
  const [patterns, setPatterns] = useState([]);
  const [stats, setStats] = useState(null);
  const [activeFilter, setActiveFilter] = useState('all');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    const data = await ws.fetchAPI('/incident-patterns');
    if (data) {
      setPatterns(data.patterns || []);
      setStats(data.statistics || null);
    }
  };

  const filteredPatterns = activeFilter === 'all'
    ? patterns
    : patterns.filter(p => p.type === activeFilter);

  return (
    <div style={{ padding: 16, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 700 }}>{'\u{1F50D}'} Incident Pattern Intelligence</div>
          <div style={{ fontSize: 11, color: '#6b7280' }}>RAG-powered cross-reference of incident data and regulatory guidance</div>
        </div>
        <div style={{ fontSize: 10, color: '#00e5ff', cursor: 'pointer' }} onClick={loadData}>{'\u{1F504}'} Refresh</div>
      </div>

      <div style={{ display: 'flex', gap: 12, flex: 1, overflow: 'hidden' }}>
        {/* Left: Statistics */}
        <div style={{ width: 240, display: 'flex', flexDirection: 'column', gap: 10 }}>
          {stats && (
            <div style={{ background: '#111827', borderRadius: 8, padding: 10, border: '1px solid #1f2937' }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: '#6b7280', marginBottom: 6, textTransform: 'uppercase' }}>Statistics</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#e0e5ec' }}>{stats.total_incidents}</div>
              <div style={{ fontSize: 10, color: '#6b7280' }}>Total incidents analyzed</div>
              <div style={{ marginTop: 8 }}>
                {Object.entries(stats.by_severity || {}).map(([sev, count]) => (
                  <div key={sev} style={{ display: 'flex', justifyContent: 'space-between', padding: '2px 0', fontSize: 11 }}>
                    <span style={{ color: SEVERITY_COLORS[sev.toUpperCase()] || '#6b7280' }}>{sev}</span>
                    <span style={{ color: '#e0e5ec', fontWeight: 600 }}>{count}</span>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 8, borderTop: '1px solid #1f2937', paddingTop: 6 }}>
                <div style={{ fontSize: 10, fontWeight: 600, color: '#6b7280', marginBottom: 4 }}>By Type</div>
                {Object.entries(stats.by_type || {}).map(([type, count]) => (
                  <div key={type} style={{ display: 'flex', justifyContent: 'space-between', padding: '1px 0', fontSize: 10, color: '#9ca3af' }}>
                    <span>{type.replace(/_/g, ' ')}</span>
                    <span>{count}</span>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 8, borderTop: '1px solid #1f2937', paddingTop: 6 }}>
                <div style={{ fontSize: 10, fontWeight: 600, color: '#6b7280', marginBottom: 4 }}>By Zone</div>
                {Object.entries(stats.by_zone || {}).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([zone, count]) => (
                  <div key={zone} style={{ display: 'flex', justifyContent: 'space-between', padding: '1px 0', fontSize: 10, color: '#9ca3af' }}>
                    <span>{zone}</span>
                    <span>{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Top Contributing Factors */}
          {stats?.top_contributing_factors && (
            <div style={{ background: '#111827', borderRadius: 8, padding: 10, border: '1px solid #1f2937' }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: '#6b7280', marginBottom: 6, textTransform: 'uppercase' }}>Top Factors</div>
              {stats.top_contributing_factors.slice(0, 5).map((f, i) => (
                <div key={i} style={{ padding: '3px 0', borderBottom: '1px solid #1f2937', fontSize: 10, color: '#9ca3af' }}>
                  <div>{f.factor}</div>
                  <div style={{ fontSize: 9, color: '#ffa000' }}>Mentioned in {f.count} incident(s)</div>
                </div>
              ))}
            </div>
          )}

          {/* Filter */}
          <div style={{ background: '#111827', borderRadius: 8, padding: 10, border: '1px solid #1f2937' }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: '#6b7280', marginBottom: 6, textTransform: 'uppercase' }}>Filter</div>
            {['all', 'RECURRING_ZONE', 'RECURRING_CAUSE', 'TYPE_ZONE_PATTERN'].map(f => (
              <div key={f} style={{
                padding: '4px 8px', cursor: 'pointer', borderRadius: 4, marginBottom: 2, fontSize: 11,
                background: activeFilter === f ? 'rgba(0,229,255,0.1)' : 'transparent',
                color: activeFilter === f ? '#00e5ff' : '#6b7280',
              }} onClick={() => setActiveFilter(f)}>
                {f.replace(/_/g, ' ')}
              </div>
            ))}
          </div>
        </div>

        {/* Right: Patterns List */}
        <div style={{ flex: 1, overflow: 'auto' }}>
          {filteredPatterns.length === 0 && (
            <div style={{ textAlign: 'center', padding: 40, color: '#6b7280', fontSize: 11 }}>
              No patterns match the selected filter
            </div>
          )}
          {filteredPatterns.map((p, i) => (
            <div key={i} style={{
              padding: '10px 12px', background: '#111827', borderRadius: 8, marginBottom: 6,
              border: `1px solid ${SEVERITY_COLORS[p.severity] || '#1f2937'}33`,
              borderLeft: `3px solid ${SEVERITY_COLORS[p.severity] || '#1f2937'}`,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ fontSize: 10, fontWeight: 700, color: SEVERITY_COLORS[p.severity] || '#6b7280', textTransform: 'uppercase' }}>
                    {p.type?.replace(/_/g, ' ')}
                  </span>
                  <span style={{ fontSize: 9, color: '#6b7280' }}>
                    {p.incident_count} incident(s)
                  </span>
                </div>
                <span style={{
                  fontSize: 9, fontWeight: 700, padding: '1px 6px', borderRadius: 8,
                  background: `${SEVERITY_COLORS[p.severity] || '#6b7280'}22`,
                  color: SEVERITY_COLORS[p.severity] || '#6b7280',
                }}>{p.severity}</span>
              </div>
              <div style={{ fontSize: 12, color: '#e0e5ec' }}>{p.description}</div>
              {p.zone && <div style={{ fontSize: 10, color: '#6b7280', marginTop: 2 }}>{'\u{1F3E0}'} {p.zone}</div>}
              {p.cause && <div style={{ fontSize: 10, color: '#ffa000', marginTop: 2 }}>Cause: {p.cause}</div>}
              <div style={{ fontSize: 11, color: '#00e5ff', marginTop: 4, fontStyle: 'italic' }}>
                {'\u{1F4A1}'} {p.recommendation}
              </div>
              {p.incidents && (
                <div style={{ marginTop: 4, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                  {p.incidents.map((incId, j) => (
                    <span key={j} style={{ fontSize: 9, padding: '1px 6px', background: 'rgba(0,229,255,0.1)', borderRadius: 8, color: '#00e5ff' }}>
                      {incId}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
