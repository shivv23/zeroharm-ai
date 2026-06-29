import React, { useState, useEffect } from 'react';
import ws from '../store/websocketStore';
import { COLORS } from '../store/theme';

const SEVERITY_COLORS = {
  CRITICAL: COLORS.riskCritical,
  HIGH: COLORS.riskHigh,
  MEDIUM: COLORS.riskElevated,
  LOW: COLORS.riskModerate,
  INFO: COLORS.accent,
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
          <div style={{ fontSize: 11, color: COLORS.textMuted }}>RAG-powered cross-reference of incident data and regulatory guidance</div>
        </div>
        <div style={{ fontSize: 10, color: COLORS.accent, cursor: 'pointer' }} onClick={loadData}>{'\u{1F504}'} Refresh</div>
      </div>

      <div style={{ display: 'flex', gap: 12, flex: 1, overflow: 'hidden' }}>
        {/* Left: Statistics */}
        <div style={{ width: 240, display: 'flex', flexDirection: 'column', gap: 10 }}>
          {stats && (
            <div style={{ background: COLORS.bgCard, borderRadius: 8, padding: 10, border: `1px solid ${COLORS.border}` }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: COLORS.textMuted, marginBottom: 6, textTransform: 'uppercase' }}>Statistics</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: COLORS.text }}>{stats.total_incidents}</div>
              <div style={{ fontSize: 10, color: COLORS.textMuted }}>Total incidents analyzed</div>
              <div style={{ marginTop: 8 }}>
                {Object.entries(stats.by_severity || {}).map(([sev, count]) => (
                  <div key={sev} style={{ display: 'flex', justifyContent: 'space-between', padding: '2px 0', fontSize: 11 }}>
                    <span style={{ color: SEVERITY_COLORS[sev.toUpperCase()] || COLORS.textMuted }}>{sev}</span>
                    <span style={{ color: COLORS.text, fontWeight: 600 }}>{count}</span>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 8, borderTop: `1px solid ${COLORS.border}`, paddingTop: 6 }}>
                <div style={{ fontSize: 10, fontWeight: 600, color: COLORS.textMuted, marginBottom: 4 }}>By Type</div>
                {Object.entries(stats.by_type || {}).map(([type, count]) => (
                  <div key={type} style={{ display: 'flex', justifyContent: 'space-between', padding: '1px 0', fontSize: 10, color: COLORS.textSecondary }}>
                    <span>{type.replace(/_/g, ' ')}</span>
                    <span>{count}</span>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 8, borderTop: `1px solid ${COLORS.border}`, paddingTop: 6 }}>
                <div style={{ fontSize: 10, fontWeight: 600, color: COLORS.textMuted, marginBottom: 4 }}>By Zone</div>
                {Object.entries(stats.by_zone || {}).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([zone, count]) => (
                  <div key={zone} style={{ display: 'flex', justifyContent: 'space-between', padding: '1px 0', fontSize: 10, color: COLORS.textSecondary }}>
                    <span>{zone}</span>
                    <span>{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Top Contributing Factors */}
          {stats?.top_contributing_factors && (
            <div style={{ background: COLORS.bgCard, borderRadius: 8, padding: 10, border: `1px solid ${COLORS.border}` }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: COLORS.textMuted, marginBottom: 6, textTransform: 'uppercase' }}>Top Factors</div>
              {stats.top_contributing_factors.slice(0, 5).map((f, i) => (
                <div key={i} style={{ padding: '3px 0', borderBottom: `1px solid ${COLORS.border}`, fontSize: 10, color: COLORS.textSecondary }}>
                  <div>{f.factor}</div>
                  <div style={{ fontSize: 9, color: COLORS.riskElevated }}>Mentioned in {f.count} incident(s)</div>
                </div>
              ))}
            </div>
          )}

          {/* Filter */}
          <div style={{ background: COLORS.bgCard, borderRadius: 8, padding: 10, border: `1px solid ${COLORS.border}` }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: COLORS.textMuted, marginBottom: 6, textTransform: 'uppercase' }}>Filter</div>
            {['all', 'RECURRING_ZONE', 'RECURRING_CAUSE', 'TYPE_ZONE_PATTERN'].map(f => (
              <div key={f} style={{
                padding: '4px 8px', cursor: 'pointer', borderRadius: 4, marginBottom: 2, fontSize: 11,
                background: activeFilter === f ? COLORS.bgAccentStrong : 'transparent',
                color: activeFilter === f ? COLORS.accent : COLORS.textMuted,
              }} onClick={() => setActiveFilter(f)}>
                {f.replace(/_/g, ' ')}
              </div>
            ))}
          </div>
        </div>

        {/* Right: Patterns List */}
        <div style={{ flex: 1, overflow: 'auto' }}>
          {filteredPatterns.length === 0 && (
            <div style={{ textAlign: 'center', padding: 40, color: COLORS.textMuted, fontSize: 11 }}>
              No patterns match the selected filter
            </div>
          )}
          {filteredPatterns.map((p, i) => (
            <div key={i} style={{
              padding: '10px 12px', background: COLORS.bgCard, borderRadius: 8, marginBottom: 6,
              border: `1px solid ${SEVERITY_COLORS[p.severity] || COLORS.border}33`,
              borderLeft: `3px solid ${SEVERITY_COLORS[p.severity] || COLORS.border}`,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ fontSize: 10, fontWeight: 700, color: SEVERITY_COLORS[p.severity] || COLORS.textMuted, textTransform: 'uppercase' }}>
                    {p.type?.replace(/_/g, ' ')}
                  </span>
                  <span style={{ fontSize: 9, color: COLORS.textMuted }}>
                    {p.incident_count} incident(s)
                  </span>
                </div>
                <span style={{
                  fontSize: 9, fontWeight: 700, padding: '1px 6px', borderRadius: 8,
                  background: `${SEVERITY_COLORS[p.severity] || COLORS.textMuted}22`,
                  color: SEVERITY_COLORS[p.severity] || COLORS.textMuted,
                }}>{p.severity}</span>
              </div>
              <div style={{ fontSize: 12, color: COLORS.text }}>{p.description}</div>
              {p.zone && <div style={{ fontSize: 10, color: COLORS.textMuted, marginTop: 2 }}>{'\u{1F3E0}'} {p.zone}</div>}
              {p.cause && <div style={{ fontSize: 10, color: COLORS.riskElevated, marginTop: 2 }}>Cause: {p.cause}</div>}
              <div style={{ fontSize: 11, color: COLORS.accent, marginTop: 4, fontStyle: 'italic' }}>
                {'\u{1F4A1}'} {p.recommendation}
              </div>
              {p.incidents && (
                <div style={{ marginTop: 4, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                  {p.incidents.map((incId, j) => (
                    <span key={j} style={{ fontSize: 9, padding: '1px 6px', background: COLORS.bgAccentStrong, borderRadius: 8, color: COLORS.accent }}>
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
