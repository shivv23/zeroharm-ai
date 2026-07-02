import React, { useState, useCallback } from 'react';

const C = {
  bg: '#080c16', card: '#111827', border: '#1f2937', text: '#e0e5ec',
  muted: '#6b7280', accent: '#00e5ff', critical: '#ff1744', ok: '#00e676',
};

const STANDARDS = [
  { id: 'oisd', label: 'OISD-STD', desc: 'Oil Industry Safety Directorate standards for industrial safety compliance' },
  { id: 'factory-act', label: 'Factory Act 1948', desc: 'Indian Factory Act compliance covering workplace safety, health, and welfare' },
  { id: 'iso45001', label: 'ISO 45001:2018', desc: 'International standard for occupational health and safety management systems' },
];

export default function RegulatoryReporter() {
  const [generating, setGenerating] = useState(null);
  const [status, setStatus] = useState('');

  const generate = useCallback(async (stdId) => {
    setGenerating(stdId);
    setStatus(`Generating ${stdId.toUpperCase()} report...`);
    try {
      const res = await fetch(`/api/reports/regulatory/${stdId}`);
      if (!res.ok) throw new Error('Failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `compliance_${stdId}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      setStatus(`\u2705 ${stdId.toUpperCase()} report downloaded`);
    } catch {
      setStatus(`\u274C Failed to generate ${stdId.toUpperCase()} report`);
    } finally {
      setGenerating(null);
    }
  }, []);

  return (
    <div style={{ padding: 16 }}>
      <div style={{ fontSize: 13, fontWeight: 700, color: C.accent, marginBottom: 16 }}>
        {'\u{1F4DD}'} Regulatory Compliance Reports
      </div>
      <div style={{ fontSize: 10, color: C.muted, marginBottom: 16 }}>
        Generate auto-compliant PDF reports for major industrial safety standards
      </div>

      <div style={{ display: 'grid', gap: 12 }}>
        {STANDARDS.map(s => (
          <div key={s.id} style={{
            background: C.card, borderRadius: 8, border: `1px solid ${C.border}`,
            padding: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>{s.label}</div>
              <div style={{ fontSize: 10, color: C.muted, marginTop: 2 }}>{s.desc}</div>
            </div>
            <button onClick={() => generate(s.id)} disabled={generating === s.id} style={{
              padding: '8px 18px', background: generating === s.id ? C.muted : C.accent,
              color: '#000', border: 'none', borderRadius: 6, fontSize: 12,
              fontWeight: 600, cursor: 'pointer', whiteSpace: 'nowrap', minWidth: 90,
            }}>
              {generating === s.id ? 'Generating...' : `\u{1F4E5} Download`}
            </button>
          </div>
        ))}
      </div>

      {status && (
        <div style={{
          marginTop: 16, padding: '10px 14px', borderRadius: 6, fontSize: 11,
          background: status.includes('\u2705') ? 'rgba(0,230,118,0.1)' : 'rgba(255,23,68,0.1)',
          border: `1px solid ${status.includes('\u2705') ? C.ok : C.critical}`,
          color: status.includes('\u2705') ? C.ok : C.critical,
        }}>{status}</div>
      )}

      <div style={{ marginTop: 20, background: C.card, borderRadius: 8, border: `1px solid ${C.border}`, padding: 14 }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: C.accent, marginBottom: 6 }}>About Auto-Compliance Reporting</div>
        <div style={{ fontSize: 10, color: C.muted, lineHeight: 1.5 }}>
          Reports are generated in real-time using the latest plant data, incident records, and compliance checklist.
          Each report includes: incident summary, compliance checklist status, and regulatory standards reference.
          Reports are formatted per the respective standard's documentation guidelines.
        </div>
      </div>
    </div>
  );
}
