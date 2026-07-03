import React, { useState, useCallback } from 'react';

const C = {
  bg: '#080c16', card: '#111827', border: '#1f2937', text: '#e0e5ec',
  muted: '#6b7280', accent: '#00e5ff', critical: '#ff1744', high: '#ff6d00',
  warning: '#ffa000', ok: '#00e676',
};

function PriorityBadge({ priority }) {
  const color = priority === 'immediate' ? C.critical : priority === 'high' ? C.high : priority === 'medium' ? C.warning : C.ok;
  return <span style={{ fontSize: 8, fontWeight: 700, color: '#000', background: color, padding: '1px 6px', borderRadius: 4 }}>{priority.toUpperCase()}</span>;
}

export default function AlertTriagePanel({ alerts }) {
  const [selected, setSelected] = useState(null);
  const [triage, setTriage] = useState(null);
  const [loading, setLoading] = useState(false);

  const triageAlert = useCallback(async (alert) => {
    setSelected(alert);
    setLoading(true);
    try {
      const res = await fetch(`/api/alerts/triage?alert_id=${alert.id || 'unknown'}&severity=${alert.severity}&zone=${alert.zone || 'plant'}`,
        { method: 'POST' });
      if (!res.ok) throw new Error('Failed');
      const json = await res.json();
      setTriage(json.data || json);
    } catch {
      setTriage(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const sortedAlerts = [...(alerts || [])].sort(
    (a, b) => ({ critical: 4, high: 3, warning: 2, info: 1 }[b.severity] || 0) -
                ({ critical: 4, high: 3, warning: 2, info: 1 }[a.severity] || 0)
  );

  return (
    <div style={{ padding: 16, display: 'flex', gap: 16, height: '100%' }}>
      {/* Alert list */}
      <div style={{ width: 280, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 6, overflow: 'auto' }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: C.accent, marginBottom: 4 }}>
          {'\u{1F9D0}'} Alert Triage ({sortedAlerts.length})
        </div>
        {sortedAlerts.length === 0 && (
          <div style={{ fontSize: 11, color: C.muted, padding: 20, textAlign: 'center' }}>No active alerts</div>
        )}
        {sortedAlerts.map((a, i) => {
          const color = a.severity === 'critical' ? C.critical : a.severity === 'high' ? C.high : a.severity === 'warning' ? C.warning : C.muted;
          return (
            <div key={i} onClick={() => triageAlert(a)} style={{
              padding: '8px 10px', cursor: 'pointer', borderRadius: 6,
              background: selected === a ? 'rgba(0,229,255,0.08)' : C.card,
              border: `1px solid ${selected === a ? C.accent : color}40`,
              transition: 'all 0.2s',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 10, fontWeight: 600, color }}>{a.severity.toUpperCase()}</span>
                <span style={{ fontSize: 9, color: C.muted }}>{a.zone || 'plant'}</span>
              </div>
              <div style={{ fontSize: 10, color: C.text, marginTop: 2, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                {a.message || a.type || 'Alert'}
              </div>
            </div>
          );
        })}
      </div>

      {/* Triage result */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {!selected && !loading && (
          <div style={{ textAlign: 'center', padding: 40, color: C.muted, fontSize: 11 }}>
            Select an alert to triage
          </div>
        )}
        {loading && <div style={{ textAlign: 'center', padding: 40, color: C.muted }}>Analyzing alert...</div>}
        {triage && (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
              <div style={{
                padding: '4px 12px', borderRadius: 12, fontSize: 11, fontWeight: 700,
                background: triage.urgency === 'critical' ? 'rgba(255,23,68,0.2)' : triage.urgency === 'high' ? 'rgba(255,109,0,0.2)' : 'rgba(0,229,255,0.1)',
                border: `1px solid ${triage.urgency === 'critical' ? C.critical : triage.urgency === 'high' ? C.high : C.accent}`,
                color: triage.urgency === 'critical' ? C.critical : triage.urgency === 'high' ? C.high : C.accent,
              }}>
                URGENCY: {triage.urgency.toUpperCase()}
              </div>
              {triage.requires_immediate_attention && (
                <span style={{ fontSize: 10, color: C.critical, fontWeight: 600 }}>{'\u{26A0}\uFE0F'} Requires immediate attention</span>
              )}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginBottom: 16 }}>
              <div style={{ background: C.card, borderRadius: 6, border: `1px solid ${C.border}`, padding: 10, textAlign: 'center' }}>
                <div style={{ fontSize: 10, color: C.muted }}>Zone Risk</div>
                <div style={{ fontSize: 16, fontWeight: 700, color: triage.zone_risk_score > 0.6 ? C.critical : C.accent }}>
                  {(triage.zone_risk_score * 100).toFixed(0)}
                </div>
              </div>
              <div style={{ background: C.card, borderRadius: 6, border: `1px solid ${C.border}`, padding: 10, textAlign: 'center' }}>
                <div style={{ fontSize: 10, color: C.muted }}>Related Incidents</div>
                <div style={{ fontSize: 16, fontWeight: 700, color: triage.related_incidents > 0 ? C.high : C.ok }}>
                  {triage.related_incidents}
                </div>
              </div>
              <div style={{ background: C.card, borderRadius: 6, border: `1px solid ${C.border}`, padding: 10, textAlign: 'center' }}>
                <div style={{ fontSize: 10, color: C.muted }}>Zone</div>
                <div style={{ fontSize: 14, fontWeight: 700, color: C.text }}>{triage.zone?.name || 'N/A'}</div>
              </div>
            </div>

            {/* Suggested actions */}
            <div style={{ background: C.card, borderRadius: 8, border: `1px solid ${C.border}`, padding: 14 }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: C.accent, marginBottom: 8 }}>Suggested Response Actions</div>
              {triage.suggested_actions?.map((action, i) => (
                <div key={i} style={{
                  display: 'flex', gap: 8, padding: '8px 10px', marginBottom: 6,
                  background: action.priority === 'immediate' ? 'rgba(255,23,68,0.06)' :
                    action.priority === 'high' ? 'rgba(255,109,0,0.06)' :
                    action.priority === 'medium' ? 'rgba(255,160,0,0.04)' : 'rgba(0,229,255,0.04)',
                  borderRadius: 6, border: `1px solid ${
                    action.priority === 'immediate' ? C.critical :
                    action.priority === 'high' ? C.high :
                    action.priority === 'medium' ? C.warning : C.accent
                  }30`,
                }}>
                  <div style={{ marginTop: 1 }}>
                    <PriorityBadge priority={action.priority} />
                  </div>
                  <div>
                    <div style={{ fontSize: 11, fontWeight: 600, color: C.text }}>{action.action}</div>
                    <div style={{ fontSize: 10, color: C.muted }}>{action.detail}</div>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
