import React, { useState, useEffect, useCallback } from 'react';
import ws from '../store/websocketStore';
import { COLORS, FONT, SX } from '../store/theme';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const STATUS_COLORS = {
  open: COLORS.riskHigh,
  in_progress: COLORS.riskElevated,
  completed: COLORS.accent,
  verified: '#7c4dff',
  closed: COLORS.riskNormal,
};

const inputStyle = {
  width: '100%', padding: '6px 8px', background: COLORS.bgElevated, color: COLORS.text,
  border: `1px solid ${COLORS.border}`, borderRadius: 4, fontSize: FONT.base, outline: 'none',
  boxSizing: 'border-box',
};

const selectStyle = { ...inputStyle };

const btnStyle = (bg, color = COLORS.text) => ({
  padding: '6px 14px', background: bg, color, border: 'none', borderRadius: 4,
  fontSize: FONT.base, fontWeight: 600, cursor: 'pointer',
});

export default function IncidentInvestigation() {
  const [investigations, setInvestigations] = useState([]);
  const [selectedInv, setSelectedInv] = useState(null);
  const [view, setView] = useState('list');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [stats, setStats] = useState(null);
  const [openCapas, setOpenCapas] = useState([]);
  const [showStats, setShowStats] = useState(false);

  const [newFinding, setNewFinding] = useState({ category: '', description: '' });
  const [newCapa, setNewCapa] = useState({ action_type: 'corrective', description: '', owner: '', deadline: '' });
  const [whyAnswers, setWhyAnswers] = useState({});
  const [rootCause, setRootCause] = useState('');

  const apiFetch = useCallback(async (url, options = {}) => {
    try {
      const token = localStorage.getItem('zeroharm_token') || '';
      const headers = { 'Content-Type': 'application/json', ...(token ? { 'Authorization': `Bearer ${token}` } : {}), ...options.headers };
      const res = await fetch(`${API}${url}`, { ...options, headers });
      return await res.json();
    } catch { return null; }
  }, []);

  const loadStats = useCallback(async () => {
    const res = await apiFetch('/api/capa/statistics');
    if (res) setStats(res);
  }, [apiFetch]);

  const loadOpenCapas = useCallback(async () => {
    const res = await apiFetch('/api/capa/open');
    if (res?.open_capas) setOpenCapas(res.open_capas);
  }, [apiFetch]);

  const loadInvestigation = useCallback(async (id) => {
    const res = await apiFetch(`/api/investigation/${id}`);
    if (res && res.id) {
      setSelectedInv(res);
      if (res.five_why) {
        const answers = {};
        for (let i = 1; i <= 5; i++) {
          const key = `why_${i}`;
          if (res.five_why[key]) answers[key] = res.five_why[key].answer || '';
        }
        setWhyAnswers(answers);
        setRootCause(res.five_why.root_cause || '');
      }
      setView('detail');
    }
  }, [apiFetch]);

  useEffect(() => { loadStats(); loadOpenCapas(); }, [loadStats, loadOpenCapas]);

  const handleCreateInvestigation = async () => {
    const res = await apiFetch('/api/investigation/create', {
      method: 'POST',
      body: JSON.stringify({ incident_data: { description: `Manual investigation ${new Date().toISOString()}` } }),
    });
    if (res && res.id) {
      setInvestigations(prev => [res, ...prev]);
      setSelectedInv(res);
      setView('detail');
    }
  };

  const handleAddFinding = async () => {
    if (!selectedInv || !newFinding.description) return;
    const res = await apiFetch(`/api/investigation/${selectedInv.id}/finding`, {
      method: 'POST',
      body: JSON.stringify({ finding: newFinding }),
    });
    if (res && res.id) loadInvestigation(selectedInv.id);
    setNewFinding({ category: '', description: '' });
  };

  const handleCreateCapa = async () => {
    if (!selectedInv || !newCapa.description) return;
    const res = await apiFetch(`/api/investigation/${selectedInv.id}/capa`, {
      method: 'POST',
      body: JSON.stringify({
        finding: { description: newCapa.description },
        action_type: newCapa.action_type,
        description: newCapa.description,
        owner: newCapa.owner,
        deadline: newCapa.deadline,
      }),
    });
    if (res && res.id) {
      loadInvestigation(selectedInv.id);
      loadOpenCapas();
    }
    setNewCapa({ action_type: 'corrective', description: '', owner: '', deadline: '' });
  };

  const handleUpdateCapaStatus = async (capaId, status) => {
    const res = await apiFetch(`/api/capa/${capaId}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status }),
    });
    if (res && res.id) {
      if (selectedInv) loadInvestigation(selectedInv.id);
      loadOpenCapas();
      loadStats();
    }
  };

  const handleUpdateWhy = async (level, answer) => {
    setWhyAnswers(prev => ({ ...prev, [level]: answer }));
  };

  const handleReport = async () => {
    if (!selectedInv) return;
    const res = await apiFetch(`/api/investigation/${selectedInv.id}/report`);
    if (res) {
      const w = window.open();
      if (w) { var pre = w.document.createElement('pre'); pre.textContent = JSON.stringify(res, null, 2); w.document.body.appendChild(pre); }
    }
  };

  const filteredInvestigations = investigations.filter(inv => {
    if (filterStatus !== 'all' && inv.status !== filterStatus) return false;
    if (searchTerm && !inv.description?.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    return true;
  });

  if (view === 'detail' && selectedInv) {
    const inv = selectedInv;
    return (
      <div style={{ padding: 16, height: '100%', display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
          <div style={{ cursor: 'pointer', color: COLORS.accent, fontSize: FONT.md }} onClick={() => setView('list')}>
            {'\u2190'} Back
          </div>
          <div style={{ fontSize: 16, fontWeight: 700 }}>Investigation {inv.id}</div>
          <div style={{ fontSize: 10, padding: '2px 8px', borderRadius: 8,
            background: STATUS_COLORS[inv.status] + '22',
            color: STATUS_COLORS[inv.status] || COLORS.textMuted,
            border: `1px solid ${STATUS_COLORS[inv.status] || COLORS.border}`,
            fontWeight: 600 }}>{inv.status}</div>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
            <button style={btnStyle(COLORS.bgAccentActive, COLORS.accent)} onClick={handleReport}>
              {'\u{1F4C4}'} Report
            </button>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 16, flex: 1, overflow: 'hidden' }}>
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 12, overflow: 'auto' }}>
            <div style={SX.cardPadded}>
              <div style={SX.sectionTitle}>Incident Details</div>
              <div style={{ fontSize: FONT.base, color: COLORS.textSecondary }}>{inv.description}</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 8, fontSize: FONT.sm }}>
                <div><span style={{ color: COLORS.textMuted }}>Created:</span> {new Date(inv.created_at).toLocaleString()}</div>
                <div><span style={{ color: COLORS.textMuted }}>Updated:</span> {new Date(inv.updated_at).toLocaleString()}</div>
              </div>
            </div>

            <div style={SX.cardPadded}>
              <div style={SX.sectionTitle}>5-Why Analysis</div>
              {inv.five_why && [1,2,3,4,5].map(i => {
                const key = `why_${i}`;
                const q = inv.five_why[key]?.question || `Why #${i}`;
                return (
                  <div key={key} style={{ marginBottom: 8 }}>
                    <div style={{ fontSize: FONT.sm, color: COLORS.accent, fontWeight: 600, marginBottom: 2 }}>{q}</div>
                    <input style={inputStyle} placeholder="Enter analysis..."
                      value={whyAnswers[key] || ''}
                      onChange={e => handleUpdateWhy(key, e.target.value)} />
                  </div>
                );
              })}
              <div style={{ marginBottom: 8 }}>
                <div style={{ fontSize: FONT.sm, color: COLORS.riskElevated, fontWeight: 600, marginBottom: 2 }}>Root Cause</div>
                <input style={inputStyle} placeholder="Identify systemic root cause..."
                  value={rootCause} onChange={e => setRootCause(e.target.value)} />
              </div>
            </div>

            <div style={SX.cardPadded}>
              <div style={SX.sectionTitle}>Fishbone Categories</div>
              {inv.fishbone?.categories && Object.entries(inv.fishbone.categories).map(([cat, data]) => (
                <div key={cat} style={{ display: 'flex', gap: 8, marginBottom: 4, fontSize: FONT.sm, alignItems: 'center' }}>
                  <span style={{ color: COLORS.accent, fontWeight: 600, minWidth: 100 }}>{cat}</span>
                  <span style={{ color: COLORS.textMuted }}>{data.factors?.join(', ') || 'No factors identified'}</span>
                </div>
              ))}
            </div>

            <div style={SX.cardPadded}>
              <div style={SX.sectionTitle}>Findings ({inv.findings?.length || 0})</div>
              {(inv.findings || []).map(f => (
                <div key={f.id} style={{ padding: '6px 8px', marginBottom: 4, background: COLORS.bgInfo, borderRadius: 4, fontSize: FONT.sm }}>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <span style={{ color: COLORS.accent, fontWeight: 600 }}>{f.id}</span>
                    <span style={{ color: f.category ? COLORS.riskElevated : COLORS.textMuted }}>{f.category || 'N/A'}</span>
                  </div>
                  <div style={{ color: COLORS.textSecondary, marginTop: 2 }}>{f.description}</div>
                </div>
              ))}
              <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
                <input style={{ ...inputStyle, width: 120 }} placeholder="Category"
                  value={newFinding.category} onChange={e => setNewFinding(prev => ({ ...prev, category: e.target.value }))} />
                <input style={{ ...inputStyle, flex: 1 }} placeholder="Finding description..."
                  value={newFinding.description} onChange={e => setNewFinding(prev => ({ ...prev, description: e.target.value }))} />
                <button style={btnStyle(COLORS.bgAccentActive, COLORS.accent)} onClick={handleAddFinding}>Add</button>
              </div>
            </div>
          </div>

          <div style={{ width: 320, display: 'flex', flexDirection: 'column', gap: 12, overflow: 'auto' }}>
            <div style={SX.cardPadded}>
              <div style={SX.sectionTitle}>CAPA Items ({inv.capas?.length || 0})</div>
              {(inv.capas || []).map(c => (
                <div key={c.id} style={{ padding: '8px', marginBottom: 6, background: COLORS.bgElevated, borderRadius: 4, border: `1px solid ${COLORS.border}` }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <span style={{ fontSize: FONT.xs, color: COLORS.textMuted }}>{c.id}</span>
                    <span style={{ fontSize: FONT.xs, padding: '1px 6px', borderRadius: 8,
                      background: STATUS_COLORS[c.status] + '22', color: STATUS_COLORS[c.status] || COLORS.textMuted,
                      fontWeight: 600 }}>{c.status}</span>
                  </div>
                  <div style={{ fontSize: FONT.sm, color: COLORS.text, marginBottom: 4 }}>{c.description}</div>
                  <div style={{ fontSize: FONT.xs, color: COLORS.textMuted, display: 'flex', gap: 8 }}>
                    <span>Owner: {c.owner || 'Unassigned'}</span>
                    <span>Deadline: {c.deadline || 'N/A'}</span>
                  </div>
                  <div style={{ fontSize: FONT.xs, color: COLORS.textMuted, marginTop: 4 }}>
                    Type: {c.action_type}
                  </div>
                  <div style={{ display: 'flex', gap: 4, marginTop: 6, flexWrap: 'wrap' }}>
                    {['in_progress', 'completed', 'verified', 'closed'].filter(s => {
                      const flow = ['open', 'in_progress', 'completed', 'verified', 'closed'];
                      const idx = flow.indexOf(c.status);
                      return flow.indexOf(s) > idx;
                    }).map(s => (
                      <div key={s} style={{ fontSize: FONT.xs, padding: '2px 6px', borderRadius: 4,
                        background: STATUS_COLORS[s] + '22', color: STATUS_COLORS[s], cursor: 'pointer', fontWeight: 600 }}
                        onClick={() => handleUpdateCapaStatus(c.id, s)}>
                        {s}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div style={SX.cardPadded}>
              <div style={SX.sectionTitle}>New CAPA</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <select style={selectStyle} value={newCapa.action_type}
                  onChange={e => setNewCapa(prev => ({ ...prev, action_type: e.target.value }))}>
                  <option value="corrective">Corrective</option>
                  <option value="preventive">Preventive</option>
                  <option value="training">Training</option>
                  <option value="engineering_control">Engineering Control</option>
                  <option value="admin_control">Admin Control</option>
                  <option value="disciplinary">Disciplinary</option>
                  <option value="ppe_control">PPE Control</option>
                </select>
                <input style={inputStyle} placeholder="Description..." value={newCapa.description}
                  onChange={e => setNewCapa(prev => ({ ...prev, description: e.target.value }))} />
                <input style={inputStyle} placeholder="Owner" value={newCapa.owner}
                  onChange={e => setNewCapa(prev => ({ ...prev, owner: e.target.value }))} />
                <input style={inputStyle} type="date" value={newCapa.deadline}
                  onChange={e => setNewCapa(prev => ({ ...prev, deadline: e.target.value }))} />
                <button style={btnStyle(COLORS.bgAccentActive, COLORS.accent)} onClick={handleCreateCapa}>
                  Create CAPA
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (showStats) {
    return (
      <div style={{ padding: 16, height: '100%', overflow: 'auto' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
          <div style={{ cursor: 'pointer', color: COLORS.accent, fontSize: FONT.md }} onClick={() => setShowStats(false)}>
            {'\u2190'} Back
          </div>
          <div style={{ fontSize: 16, fontWeight: 700 }}>CAPA Statistics</div>
        </div>
        {stats ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 12 }}>
            {Object.entries(stats).map(([key, val]) => (
              <div key={key} style={SX.cardPadded}>
                <div style={{ fontSize: FONT.xs, color: COLORS.textMuted, textTransform: 'uppercase', letterSpacing: 0.5 }}>{key.replace(/_/g, ' ')}</div>
                <div style={{ fontSize: 24, fontWeight: 700, color: COLORS.accent, marginTop: 4 }}>
                  {typeof val === 'number' && key === 'completion_rate' ? `${val}%` : val}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={SX.emptyState}>No statistics available</div>
        )}
      </div>
    );
  }

  return (
    <div style={{ padding: 16, height: '100%', display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 700 }}>{'\u{1F50D}'} Incident Investigations</div>
          <div style={{ fontSize: 10, color: COLORS.textMuted }}>Root cause analysis with CAPA tracking</div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button style={btnStyle(COLORS.bgAccentActive, COLORS.accent)} onClick={() => { loadStats(); setShowStats(true); }}>
            {'\u{1F4CA}'} Statistics
          </button>
          <button style={btnStyle(COLORS.accent, '#000')} onClick={() => { loadOpenCapas(); setView('capa_list'); }}>
            Open CAPAs ({openCapas.length})
          </button>
          <button style={btnStyle(COLORS.bgNormalStrong, COLORS.riskNormal)} onClick={handleCreateInvestigation}>
            + New Investigation
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
        <input style={{ ...inputStyle, maxWidth: 300 }} placeholder="Search investigations..."
          value={searchTerm} onChange={e => setSearchTerm(e.target.value)} />
        <select style={{ ...selectStyle, maxWidth: 140 }} value={filterStatus}
          onChange={e => setFilterStatus(e.target.value)}>
          <option value="all">All Status</option>
          <option value="open">Open</option>
          <option value="closed">Closed</option>
        </select>
      </div>

      {filteredInvestigations.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 40, color: COLORS.textMuted }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>{'\u{1F50D}'}</div>
          <div style={{ fontSize: 14, fontWeight: 600 }}>Create an investigation to get started</div>
          <div style={{ fontSize: 11, marginTop: 4 }}>Create a new investigation or trigger an emergency to auto-generate one.</div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {filteredInvestigations.map(inv => (
            <div key={inv.id} style={{
              ...SX.cardPadded, cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }} onClick={() => loadInvestigation(inv.id)}>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <span style={{ fontSize: FONT.md, fontWeight: 700, color: COLORS.text }}>{inv.description}</span>
                  <span style={{ fontSize: FONT.xs, padding: '1px 6px', borderRadius: 8,
                    background: STATUS_COLORS[inv.status] + '22', color: STATUS_COLORS[inv.status] || COLORS.textMuted,
                    fontWeight: 600 }}>{inv.status}</span>
                </div>
                <div style={{ fontSize: FONT.sm, color: COLORS.textMuted }}>
                  {inv.id} | {new Date(inv.created_at).toLocaleDateString()} | {inv.findings?.length || 0} findings | {inv.capas?.length || 0} CAPAs
                </div>
              </div>
              <div style={{ fontSize: FONT.lg, color: COLORS.textMuted }}>{'\u203A'}</div>
            </div>
          ))}
        </div>
      )}

      {view === 'capa_list' && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: COLORS.overlay, zIndex: 1000,
          display: 'flex', alignItems: 'center', justifyContent: 'center' }} onClick={() => setView('list')}>
          <div style={{ background: COLORS.bg, border: `1px solid ${COLORS.border}`, borderRadius: 10, padding: 20,
            maxWidth: 600, width: '90%', maxHeight: '80vh', overflow: 'auto' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <div style={{ fontSize: 16, fontWeight: 700 }}>Open CAPA Items ({openCapas.length})</div>
              <div style={{ cursor: 'pointer', color: COLORS.textMuted }} onClick={() => setView('list')}>{'\u2715'}</div>
            </div>
            {openCapas.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 20, color: COLORS.textMuted }}>No open CAPA items</div>
            ) : (
              openCapas.map(c => (
                <div key={c.id} style={{ padding: '8px', marginBottom: 6, background: COLORS.bgElevated, borderRadius: 4, border: `1px solid ${COLORS.border}` }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: FONT.xs, marginBottom: 4 }}>
                    <span style={{ color: COLORS.accent, fontWeight: 600 }}>{c.id}</span>
                    <span style={{ color: STATUS_COLORS[c.status], fontWeight: 600 }}>{c.status}</span>
                  </div>
                  <div style={{ fontSize: FONT.sm, color: COLORS.text }}>{c.description}</div>
                  <div style={{ fontSize: FONT.xs, color: COLORS.textMuted, marginTop: 2 }}>
                    Investigation: {c.investigation_id} | Owner: {c.owner || 'Unassigned'} | Deadline: {c.deadline || 'N/A'}
                  </div>
                  <div style={{ display: 'flex', gap: 4, marginTop: 4, flexWrap: 'wrap' }}>
                    {['in_progress', 'completed', 'verified', 'closed'].filter(s => {
                      const flow = ['open', 'in_progress', 'completed', 'verified', 'closed'];
                      const idx = flow.indexOf(c.status);
                      return flow.indexOf(s) > idx;
                    }).map(s => (
                      <div key={s} style={{ fontSize: FONT.xs, padding: '2px 6px', borderRadius: 4,
                        background: STATUS_COLORS[s] + '22', color: STATUS_COLORS[s], cursor: 'pointer', fontWeight: 600 }}
                        onClick={() => { handleUpdateCapaStatus(c.id, s); }}>
                        {s}
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
