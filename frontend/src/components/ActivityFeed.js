import React, { useRef, useEffect } from 'react';

const AGENT_COLORS = {
  'Sensor Monitor Agent': '#00e5ff',
  'Permit Activity Agent': '#ffa000',
  'Maintenance Status Agent': '#00e676',
  'Compound Risk Detection Engine': '#ff1744',
  'Quality & Compliance Audit Agent': '#7c4dff',
  'Emergency Response Orchestrator': '#ff6d00',
  'Risk Fusion Supervisor': '#00bcd4',
  'ZeroHarm System': '#6b7280',
};

const SEVERITY_STYLES = {
  critical: { bg: 'rgba(255,23,68,0.12)', dot: '#ff1744', pulse: true },
  high: { bg: 'rgba(255,109,0,0.1)', dot: '#ff6d00', pulse: false },
  warning: { bg: 'rgba(255,160,0,0.08)', dot: '#ffa000', pulse: false },
  info: { bg: 'rgba(0,229,255,0.06)', dot: '#00e5ff', pulse: false },
  normal: { bg: 'transparent', dot: '#00e676', pulse: false },
};

export default function ActivityFeed({ entries = [] }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = 0;
    }
  }, [entries]);

  if (entries.length === 0) {
    return (
      <div style={{ padding: 40, textAlign: 'center', color: '#6b7280' }}>
        <div style={{ fontSize: 32, marginBottom: 8 }}>{'\u{1F916}'}</div>
        <div style={{ fontSize: 14, fontWeight: 600 }}>Agent Activity Feed</div>
        <div style={{ fontSize: 11, marginTop: 4 }}>Waiting for agent activity data...</div>
      </div>
    );
  }

  return (
    <div style={{ padding: 12, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: 10, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: 15, fontWeight: 700 }}>{'\u{1F916}'} Agent Activity Feed</div>
          <div style={{ fontSize: 10, color: '#6b7280' }}>Real-time multi-agent system trace</div>
        </div>
        <div style={{ fontSize: 10, color: '#4b5563' }}>{entries.length} events</div>
      </div>

      <div ref={containerRef} style={{ flex: 1, overflow: 'auto', fontFamily: "'SF Mono', 'Fira Code', monospace", fontSize: 11 }}>
        {entries.map((entry, i) => {
          const sevStyle = SEVERITY_STYLES[entry.severity] || SEVERITY_STYLES.info;
          const agentColor = AGENT_COLORS[entry.agent] || '#6b7280';
          const isLast = i === entries.length - 1;
          return (
            <div key={entry.id || i} style={{
              display: 'flex', gap: 8, padding: '5px 8px',
              background: sevStyle.bg,
              borderLeft: `2px solid ${sevStyle.dot}`,
              borderRadius: '0 4px 4px 0',
              marginBottom: 3,
              animation: isLast && sevStyle.pulse ? 'pulse 1.5s infinite' : 'none',
              transition: 'all 0.2s',
            }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 8, flexShrink: 0 }}>
                <div style={{ width: 6, height: 6, borderRadius: '50%', background: sevStyle.dot,
                              boxShadow: sevStyle.pulse ? `0 0 6px ${sevStyle.dot}` : 'none' }} />
                <div style={{ width: 1, flex: 1, background: '#1f2937', marginTop: 2 }} />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                  <span style={{ color: agentColor, fontWeight: 600, fontSize: 10 }}>{entry.agent}</span>
                  <span style={{ color: '#4b5563', fontSize: 9 }}>{entry.time_display}</span>
                  <span style={{
                    fontSize: 8, padding: '1px 4px', borderRadius: 3, textTransform: 'uppercase',
                    background: sevStyle.pulse ? 'rgba(255,23,68,0.2)' : 'rgba(255,255,255,0.05)',
                    color: entry.severity === 'critical' ? '#ff1744' : '#6b7280',
                  }}>{entry.severity}</span>
                </div>
                <div style={{ color: '#d1d5db', marginTop: 1, fontSize: 11 }}>{entry.action}</div>
                <div style={{ color: '#6b7280', fontSize: 10, marginTop: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {entry.detail}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
