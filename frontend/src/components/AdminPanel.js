import React, { useState, useEffect, useCallback } from 'react';
import ws from '../store/websocketStore';
import { COLORS, FONT, SX, RADIUS } from '../store/theme';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

async function apiFetch(path, options = {}) {
  const token = localStorage.getItem('zeroharm_token') || '';
  const headers = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers };
  try {
    const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
    if (!res.ok) return { error: `HTTP ${res.status}` };
    return await res.json();
  } catch (e) {
    return { error: e.message };
  }
}

export default function AdminPanel() {
  const [users, setUsers] = useState([]);
  const [auditLog, setAuditLog] = useState([]);
  const [auditStats, setAuditStats] = useState(null);
  const [tab, setTab] = useState('users');
  const [newUser, setNewUser] = useState({ username: '', password: '', role: 'viewer', name: '' });
  const [resetPw, setResetPw] = useState({ username: '', new_password: '' });
  const [msg, setMsg] = useState(null);

  const loadUsers = useCallback(async () => {
    const data = await apiFetch('/admin/users');
    if (!data.error) setUsers(data.users || []);
  }, []);

  const loadAudit = useCallback(async () => {
    const data = await apiFetch('/audit/log?limit=200');
    if (!data.error) { setAuditLog(data.entries || []); setAuditStats(data.stats); }
  }, []);

  useEffect(() => { loadUsers(); }, [loadUsers]);
  useEffect(() => { if (tab === 'audit') loadAudit(); }, [tab, loadAudit]);

  const createUser = async () => {
    const data = await apiFetch('/auth/register', {
      method: 'POST', body: JSON.stringify(newUser),
    });
    setMsg(data.detail ? { type: 'success', text: data.detail } : { type: 'error', text: data.error || 'Failed' });
    if (data.detail) { loadUsers(); setNewUser({ username: '', password: '', role: 'viewer', name: '' }); }
  };

  const deleteUser = async (username) => {
    if (!window.confirm(`Delete user '${username}'?`)) return;
    const data = await apiFetch(`/admin/users/${username}`, { method: 'DELETE' });
    setMsg(data.detail ? { type: 'success', text: data.detail } : { type: 'error', text: data.error || 'Failed' });
    if (data.detail) loadUsers();
  };

  const changeRole = async (username, role) => {
    const data = await apiFetch(`/admin/users/${username}/role?role=${role}`, { method: 'PUT' });
    setMsg(data.detail ? { type: 'success', text: data.detail } : { type: 'error', text: data.error || 'Failed' });
    if (data.detail) loadUsers();
  };

  const resetPassword = async () => {
    const data = await apiFetch('/admin/users/reset-password', {
      method: 'POST', body: JSON.stringify(resetPw),
    });
    setMsg(data.detail ? { type: 'success', text: data.detail } : { type: 'error', text: data.error || 'Failed' });
    if (data.detail) setResetPw({ username: '', new_password: '' });
  };

  const inputStyle = { ...SX.input, marginBottom: 4, width: 'calc(100% - 16px)' };
  const selectStyle = { ...SX.select, marginBottom: 4, width: '100%' };
  const btnStyle = { padding: '6px 14px', border: 'none', borderRadius: RADIUS.sm, cursor: 'pointer', fontSize: FONT.sm, fontWeight: 600 };

  return (
    <div style={{ padding: 16 }}>
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {['users', 'audit'].map(t => (
          <div key={t} onClick={() => setTab(t)}
               style={{ ...btnStyle, background: tab === t ? COLORS.accent : COLORS.bgCard, color: tab === t ? '#000' : COLORS.text }}>
            {t === 'users' ? 'User Management' : 'Audit Log'}
          </div>
        ))}
      </div>
      {msg && <div style={{ padding: '6px 12px', marginBottom: 8, background: msg.type === 'success' ? COLORS.bgNormal : COLORS.bgCritical, border: `1px solid ${msg.type === 'success' ? COLORS.borderNormal : COLORS.borderCritical}`, borderRadius: RADIUS.sm, fontSize: FONT.sm, color: msg.type === 'success' ? COLORS.riskNormal : COLORS.riskCritical }}>{msg.text}</div>}
      {tab === 'users' && (
        <>
          <div style={{ ...SX.cardPadded, marginBottom: 16 }}>
            <div style={{ ...SX.sectionTitle, marginBottom: 8 }}>Create User</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              <input style={inputStyle} placeholder="Username" value={newUser.username} onChange={e => setNewUser({...newUser, username: e.target.value})} />
              <input style={inputStyle} type="password" placeholder="Password" value={newUser.password} onChange={e => setNewUser({...newUser, password: e.target.value})} />
              <select style={selectStyle} value={newUser.role} onChange={e => setNewUser({...newUser, role: e.target.value})}>
                <option value="viewer">Viewer</option><option value="operator">Operator</option><option value="safety_officer">Safety Officer</option><option value="admin">Admin</option>
              </select>
              <input style={inputStyle} placeholder="Display Name" value={newUser.name} onChange={e => setNewUser({...newUser, name: e.target.value})} />
            </div>
            <div style={{ marginTop: 8 }}><button style={{ ...btnStyle, background: COLORS.accent, color: '#000' }} onClick={createUser}>Create User</button></div>
          </div>
          <div style={{ ...SX.cardPadded, marginBottom: 16 }}>
            <div style={{ ...SX.sectionTitle, marginBottom: 8 }}>Reset Password</div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <input style={{ ...inputStyle, width: 200, margin: 0 }} placeholder="Username" value={resetPw.username} onChange={e => setResetPw({...resetPw, username: e.target.value})} />
              <input style={{ ...inputStyle, width: 200, margin: 0 }} type="password" placeholder="New password" value={resetPw.new_password} onChange={e => setResetPw({...resetPw, new_password: e.target.value})} />
              <button style={{ ...btnStyle, background: COLORS.riskHigh, color: '#fff' }} onClick={resetPassword}>Reset</button>
            </div>
          </div>
          <div style={{ ...SX.cardPadded }}>
            <div style={{ ...SX.sectionTitle, marginBottom: 8 }}>Users ({users.length})</div>
            {users.map(u => (
              <div key={u.username} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 8px', borderBottom: `1px solid ${COLORS.border}`, fontSize: FONT.base }}>
                <div><span style={{ fontWeight: 600 }}>{u.name}</span> <span style={{ color: COLORS.textMuted }}>@{u.username}</span></div>
                <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                  <select style={{ ...selectStyle, width: 130, margin: 0 }} value={u.role} onChange={e => changeRole(u.username, e.target.value)}>
                    <option value="viewer">Viewer</option><option value="operator">Operator</option><option value="safety_officer">Safety Officer</option><option value="admin">Admin</option>
                  </select>
                  {u.username !== 'admin' && <button style={{ ...btnStyle, background: COLORS.riskCritical, color: '#fff' }} onClick={() => deleteUser(u.username)}>Delete</button>}
                </div>
              </div>
            ))}
            {users.length === 0 && <div style={{ color: COLORS.textMuted, textAlign: 'center', padding: 16 }}>No users loaded</div>}
          </div>
        </>
      )}
      {tab === 'audit' && (
        <>
          {auditStats && <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
            <div style={{ ...SX.cardPadded, textAlign: 'center' }}><div style={{ fontSize: 22, fontWeight: 700, color: COLORS.accent }}>{auditStats.total}</div><div style={{ fontSize: FONT.xs, color: COLORS.textMuted }}>Total Events</div></div>
            {Object.entries(auditStats.actions || {}).sort((a,b) => b[1]-a[1]).slice(0,5).map(([a,c]) => (
              <div key={a} style={{ ...SX.cardPadded, textAlign: 'center' }}><div style={{ fontSize: 13, fontWeight: 600, color: COLORS.text }}>{c}</div><div style={{ fontSize: FONT.xs, color: COLORS.textMuted }}>{a}</div></div>
            ))}
          </div>}
          <div style={{ ...SX.cardPadded }}>
            <div style={{ ...SX.sectionTitle, marginBottom: 8 }}>Recent Events</div>
            <div style={{ maxHeight: 400, overflow: 'auto' }}>
              {auditLog.map((e, i) => (
                <div key={i} style={{ display: 'flex', gap: 8, padding: '4px 0', borderBottom: `1px solid ${COLORS.border}`, fontSize: FONT.xs, color: COLORS.textSecondary }}>
                  <span style={{ color: COLORS.textMuted, whiteSpace: 'nowrap' }}>{new Date(e.timestamp).toLocaleTimeString()}</span>
                  <span style={{ color: e.success ? COLORS.riskNormal : COLORS.riskCritical, fontWeight: 600 }}>{e.action}</span>
                  <span style={{ color: COLORS.textDim }}>{e.resource}</span>
                  <span style={{ color: COLORS.textMuted }}>by {e.username}</span>
                </div>
              ))}
              {auditLog.length === 0 && <div style={{ color: COLORS.textMuted, textAlign: 'center', padding: 16 }}>No audit events yet</div>}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
