import React, { useState, useEffect, useCallback } from 'react';

const C = {
  bg: '#080c16', card: '#111827', border: '#1f2937', text: '#e0e5ec',
  muted: '#6b7280', accent: '#00e5ff', critical: '#ff1744', high: '#ff6d00',
  warning: '#ffa000', ok: '#00e676',
};

const SEVERITY_OPTIONS = [
  { id: 'low', color: C.ok }, { id: 'medium', color: C.warning },
  { id: 'high', color: C.high }, { id: 'critical', color: C.critical },
];

export default function SafetyObservations() {
  const [observations, setObservations] = useState([]);
  const [trends, setTrends] = useState(null);
  const [types, setTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ observation_type: 'unsafe_condition', zone_id: 'Z01', description: '', severity: 'medium', submitted_by: '', location_detail: '' });
  const [submitStatus, setSubmitStatus] = useState('');

  const fetchAll = useCallback(async () => {
    try {
      const [obsRes, trendRes, typeRes] = await Promise.all([
        fetch('/api/safety/observations').then(r => r.json()),
        fetch('/api/safety/observations/trends').then(r => r.json()),
        fetch('/api/safety/observations/types').then(r => r.json()),
      ]);
      setObservations((obsRes.data || obsRes).observations || []);
      setTrends(trendRes.data || trendRes);
      setTypes((typeRes.data || typeRes).types || []);
    } catch { /* silent */ }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const submit = useCallback(async () => {
    if (!form.description.trim()) return;
    setSubmitStatus('Submitting...');
    try {
      const res = await fetch('/api/safety/observations/submit', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      if (!res.ok) throw new Error('Failed');
      setSubmitStatus('\u2705 Observation submitted');
      setShowForm(false);
      setForm({ ...form, description: '', submitted_by: '', location_detail: '' });
      fetchAll();
    } catch {
      setSubmitStatus('\u274C Submission failed');
    }
  }, [form]);

  if (loading) return <div style={{ padding: 40, textAlign: 'center', color: C.muted }}>Loading observations...</div>;

  return (
    <div style={{ padding: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: C.accent }}>
          {'\u{1F4A1}'} Safety Observations & Near Miss Reporting
        </div>
        <button onClick={() => setShowForm(!showForm)} style={{
          padding: '7px 16px', background: C.accent, color: '#000',
          border: 'none', borderRadius: 6, fontSize: 11, fontWeight: 600, cursor: 'pointer',
        }}>{showForm ? 'Cancel' : '+ Report Observation'}</button>
      </div>

      {/* Submit form */}
      {showForm && (
        <div style={{ background: C.card, borderRadius: 8, border: `1px solid ${C.border}`, padding: 14, marginBottom: 16 }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: C.accent, marginBottom: 10 }}>Submit New Observation</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 10 }}>
            <select value={form.observation_type} onChange={e => setForm({...form, observation_type: e.target.value})}
              style={{ padding: '6px 8px', background: C.bg, color: C.text, border: `1px solid ${C.border}`, borderRadius: 4, fontSize: 11 }}>
              {types.map(t => <option key={t.id} value={t.id}>{t.label}</option>)}
            </select>
            <select value={form.zone_id} onChange={e => setForm({...form, zone_id: e.target.value})}
              style={{ padding: '6px 8px', background: C.bg, color: C.text, border: `1px solid ${C.border}`, borderRadius: 4, fontSize: 11 }}>
              {['Z01','Z02','Z03','Z04','Z05','Z06','Z07','Z08','Z09','Z10'].map(z =>
                <option key={z} value={z}>{z}</option>
              )}
            </select>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 10 }}>
            <input value={form.submitted_by} onChange={e => setForm({...form, submitted_by: e.target.value})}
              placeholder="Your name (optional)" style={{ padding: '6px 8px', background: C.bg, color: C.text, border: `1px solid ${C.border}`, borderRadius: 4, fontSize: 11 }} />
            <input value={form.location_detail} onChange={e => setForm({...form, location_detail: e.target.value})}
              placeholder="Location detail (optional)" style={{ padding: '6px 8px', background: C.bg, color: C.text, border: `1px solid ${C.border}`, borderRadius: 4, fontSize: 11 }} />
          </div>
          <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
            {SEVERITY_OPTIONS.map(s => (
              <div key={s.id} onClick={() => setForm({...form, severity: s.id})} style={{
                padding: '4px 12px', borderRadius: 12, cursor: 'pointer', fontSize: 10, fontWeight: 600,
                background: form.severity === s.id ? s.color : 'transparent',
                color: form.severity === s.id ? '#000' : s.color,
                border: `1px solid ${s.color}`,
              }}>{s.id.toUpperCase()}</div>
            ))}
          </div>
          <textarea value={form.description} onChange={e => setForm({...form, description: e.target.value})}
            placeholder="Describe the observation, hazard, or near miss..."
            rows={3} style={{ width: '100%', padding: '8px', background: C.bg, color: C.text, border: `1px solid ${C.border}`, borderRadius: 4, fontSize: 11, resize: 'vertical' }} />
          <div style={{ display: 'flex', gap: 8, marginTop: 10, alignItems: 'center' }}>
            <button onClick={submit} disabled={!form.description.trim()} style={{
              padding: '7px 18px', background: C.accent, color: '#000',
              border: 'none', borderRadius: 6, fontSize: 11, fontWeight: 600, cursor: 'pointer',
            }}>Submit</button>
            {submitStatus && <span style={{ fontSize: 10, color: submitStatus.includes('\u2705') ? C.ok : C.critical }}>{submitStatus}</span>}
          </div>
        </div>
      )}

      {/* Trends summary */}
      {trends && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: 8, marginBottom: 16 }}>
          <div style={{ background: C.card, borderRadius: 6, border: `1px solid ${C.border}`, padding: 10, textAlign: 'center' }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: C.text }}>{trends.total}</div>
            <div style={{ fontSize: 9, color: C.muted }}>Total</div>
          </div>
          <div style={{ background: C.card, borderRadius: 6, border: `1px solid ${C.border}`, padding: 10, textAlign: 'center' }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: C.high }}>{trends.by_severity?.high || 0}</div>
            <div style={{ fontSize: 9, color: C.muted }}>High Severity</div>
          </div>
          <div style={{ background: C.card, borderRadius: 6, border: `1px solid ${C.border}`, padding: 10, textAlign: 'center' }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: C.critical }}>{trends.by_severity?.critical || 0}</div>
            <div style={{ fontSize: 9, color: C.muted }}>Critical</div>
          </div>
          <div style={{ background: C.card, borderRadius: 6, border: `1px solid ${C.border}`, padding: 10, textAlign: 'center' }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: C.ok }}>{trends.open_count}</div>
            <div style={{ fontSize: 9, color: C.muted }}>Open Items</div>
          </div>
          <div style={{ background: C.card, borderRadius: 6, border: `1px solid ${C.border}`, padding: 10, textAlign: 'center' }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: C.accent }}>{Object.keys(trends.monthly || {}).length}</div>
            <div style={{ fontSize: 9, color: C.muted }}>Months Active</div>
          </div>
        </div>
      )}

      {/* Observations list */}
      <div style={{ fontSize: 11, fontWeight: 600, color: C.accent, marginBottom: 8 }}>Recent Observations</div>
      <div style={{ display: 'grid', gap: 8 }}>
        {observations.slice(0, 50).map((obs, i) => {
          const sevColor = SEVERITY_OPTIONS.find(s => s.id === obs.severity)?.color || C.muted;
          return (
            <div key={i} style={{
              background: C.card, borderRadius: 6, border: `1px solid ${C.border}`, padding: '8px 12px',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                  <span style={{ fontSize: 9, fontWeight: 600, color: sevColor, padding: '1px 6px', borderRadius: 4, border: `1px solid ${sevColor}` }}>
                    {obs.severity?.toUpperCase()}
                  </span>
                  <span style={{ fontSize: 10, color: C.text }}>{obs.type?.replace(/_/g, ' ')}</span>
                  <span style={{ fontSize: 9, color: C.muted }}>{obs.zone_id}</span>
                </div>
                <span style={{ fontSize: 9, color: obs.status === 'open' ? C.high : C.ok, fontWeight: 600 }}>
                  {obs.status?.toUpperCase()}
                </span>
              </div>
              <div style={{ fontSize: 10, color: C.muted, marginBottom: 2 }}>{obs.description}</div>
              <div style={{ fontSize: 8, color: C.muted }}>
                {obs.submitted_by} · {obs.submitted_at ? new Date(obs.submitted_at).toLocaleDateString() : ''}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
