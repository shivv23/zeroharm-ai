import React, { useRef, useEffect } from 'react';
import { AGENT_COLORS, SEVERITY, COLORS, FONT } from '../store/theme';

export default function ActivityFeed({ entries = [] }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = 0;
    }
  }, [entries]);

  if (entries.length === 0) {
    return (
      <div style={{ padding: 40, textAlign: 'center', color: COLORS.textMuted }}>
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
          <div style={{ fontSize: 10, color: COLORS.textMuted }}>Real-time multi-agent system trace</div>
        </div>
        <div style={{ fontSize: 10, color: COLORS.textDim }}>{entries.length} events</div>
      </div>

      <div ref={containerRef} style={{ flex: 1, overflow: 'auto', fontFamily: FONT.mono, fontSize: 11 }}>
        {entries.map((entry, i) => {
          const sevStyle = SEVERITY[entry.severity] || SEVERITY.info;
          const agentColor = AGENT_COLORS[entry.agent] || COLORS.textMuted;
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
                <div style={{ width: 1, flex: 1, background: COLORS.border, marginTop: 2 }} />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                  <span style={{ color: agentColor, fontWeight: 600, fontSize: 10 }}>{entry.agent}</span>
                  <span style={{ color: COLORS.textDim, fontSize: 9 }}>{entry.time_display}</span>
                  <span style={{
                    fontSize: 8, padding: '1px 4px', borderRadius: 3, textTransform: 'uppercase',
                    background: sevStyle.pulse ? COLORS.bgCriticalStrong : 'rgba(255,255,255,0.05)',
                    color: entry.severity === 'critical' ? COLORS.riskCritical : COLORS.textMuted,
                  }}>{entry.severity}</span>
                </div>
                <div style={{ color: COLORS.textAlt, marginTop: 1, fontSize: 11 }}>{entry.action}</div>
                <div style={{ color: COLORS.textMuted, fontSize: 10, marginTop: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
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
