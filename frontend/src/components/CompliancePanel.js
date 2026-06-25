import React, { useState, useEffect } from 'react';
import ws from '../store/websocketStore';

const CATEGORY_LABELS = {
  gas_detection: { title: 'Gas Detection Systems', standard: 'OISD-STD-116', icon: '\u{1F4E1}' },
  permit_to_work: { title: 'Permit-to-Work', standard: 'Factory Act / OISD-GDN-204', icon: '\u{1F4CB}' },
  maintenance_safety: { title: 'Maintenance Safety', standard: 'OISD-STD-201', icon: '\u{1F527}' },
  training_competency: { title: 'Training & Competency', standard: 'ISO 45001', icon: '\u{1F393}' },
  emergency_preparedness: { title: 'Emergency Preparedness', standard: 'OISD-STD-105', icon: '\u{1F6A8}' },
};

export default function CompliancePanel({ compliance }) {
  const [data, setData] = useState(compliance);
  const [expandedCat, setExpandedCat] = useState(null);
  const [loading, setLoading] = useState(!compliance);
  const [trend, setTrend] = useState([]);
  const scoreHistory = React.useRef([]);

  useEffect(() => {
    if (compliance) {
      setData(compliance);
      setLoading(false);
      const s = compliance.overall_compliance_score || 0;
      scoreHistory.current = [...scoreHistory.current.slice(-40), { score: s, ts: Date.now() }];
      setTrend(scoreHistory.current);
    }
  }, [compliance]);

  useEffect(() => {
    if (!data) {
      ws.fetchAPI('/compliance/audit').then(r => { setData(r); setLoading(false); });
    }
  }, [data]);

  if (loading && !data) {
    return (
      <div style={{ padding: 40, textAlign: 'center', color: '#6b7280' }}>
        <div style={{ fontSize: 32, marginBottom: 8 }}>{'\u{1F4DD}'}</div>
        <div>Running compliance audit...</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div style={{ padding: 40, textAlign: 'center', color: '#6b7280' }}>
        <div style={{ fontSize: 32, marginBottom: 8 }}>{'\u{1F4DD}'}</div>
        <div>No compliance data available</div>
      </div>
    );
  }

  const score = data.overall_compliance_score || 0;
  const scoreColor = score >= 80 ? '#00e676' : score >= 60 ? '#ffa000' : '#ff1744';
  const violations = data.violations || [];
  const criticals = data.critical_findings || [];
  const categories = data.category_scores || {};

  return (
    <div style={{ padding: 16, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: 10, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: 15, fontWeight: 700 }}>{'\u{1F4DD}'} Quality & Compliance Audit</div>
          <div style={{ fontSize: 10, color: '#6b7280' }}>AI-powered regulatory compliance monitoring</div>
        </div>
      </div>

      {/* Overall Score */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
        <div style={{ flex: 1, background: '#111827', borderRadius: 10, border: '1px solid #1f2937', padding: 12, textAlign: 'center' }}>
          <div style={{ position: 'relative', width: 64, height: 64, margin: '0 auto' }}>
            <svg width="64" height="64" viewBox="0 0 64 64">
              <circle cx="32" cy="32" r="28" fill="none" stroke="#1f2937" strokeWidth="6" />
              <circle cx="32" cy="32" r="28" fill="none" stroke={scoreColor} strokeWidth="6"
                      strokeDasharray={`${(score / 100) * 176} 176`} transform="rotate(-90 32 32)" strokeLinecap="round" />
            </svg>
            <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', fontSize: 18, fontWeight: 700, color: scoreColor }}>
              {score.toFixed(0)}
            </div>
          </div>
          <div style={{ fontSize: 10, color: '#6b7280', marginTop: 4 }}>Compliance Score</div>
          <div style={{ fontSize: 11, fontWeight: 600, color: scoreColor }}>{score >= 80 ? 'PASS' : score >= 60 ? 'REVIEW' : 'FAIL'}</div>
        </div>

        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 6 }}>
          <div style={{ flex: 1, background: 'rgba(255,23,68,0.1)', borderRadius: 8, border: '1px solid rgba(255,23,68,0.3)', padding: '6px 10px', display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 18 }}>{'\u{1F525}'}</span>
            <div>
              <div style={{ fontSize: 16, fontWeight: 700, color: '#ff1744' }}>{criticals.length}</div>
              <div style={{ fontSize: 9, color: '#6b7280' }}>Critical</div>
            </div>
          </div>
          <div style={{ flex: 1, background: 'rgba(255,160,0,0.1)', borderRadius: 8, border: '1px solid rgba(255,160,0,0.3)', padding: '6px 10px', display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 18 }}>{'\u{26A0}\uFE0F'}</span>
            <div>
              <div style={{ fontSize: 16, fontWeight: 700, color: '#ffa000' }}>{violations.length}</div>
              <div style={{ fontSize: 9, color: '#6b7280' }}>Violations</div>
            </div>
          </div>
        </div>
      </div>

      {/* Compliance Trend */}
      {trend.length > 1 && (
        <div style={{ background: '#111827', borderRadius: 8, border: '1px solid #1f2937', padding: 8, marginBottom: 8 }}>
          <div style={{ fontSize: 10, color: '#6b7280', marginBottom: 4 }}>Compliance Score Trend</div>
          <svg width="100%" height="40" viewBox={`0 0 ${trend.length * 10} 40`} preserveAspectRatio="none">
            <defs>
              <linearGradient id="compGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#00e676" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#00e676" stopOpacity="0.0" />
              </linearGradient>
            </defs>
            <path d={trend.map((p, i) => `${i === 0 ? 'M' : 'L'}${i * 10} ${40 - (p.score / 100) * 36}`).join(' ')}
                  fill="none" stroke="#00e676" strokeWidth="1.5" strokeLinecap="round" />
            <path d={`${trend.map((p, i) => `${i === 0 ? 'M' : 'L'}${i * 10} ${40 - (p.score / 100) * 36}`).join(' ')} L${(trend.length - 1) * 10} 40 L0 40 Z`}
                  fill="url(#compGrad)" />
            <circle cx={(trend.length - 1) * 10} cy={40 - (trend[trend.length - 1].score / 100) * 36} r="2" fill="#00e676" />
          </svg>
        </div>
      )}

      {/* Category Scores */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {Object.entries(categories).map(([catId, cat]) => {
          const info = CATEGORY_LABELS[catId] || { title: catId, standard: '', icon: '\u{1F4CB}' };
          const catScore = (cat.score || 0) * 100;
          const catColor = catScore >= 80 ? '#00e676' : catScore >= 60 ? '#ffa000' : '#ff1744';
          const isExpanded = expandedCat === catId;
          const catViolations = (cat.checks || []).filter(c => !c.passed);
          return (
            <div key={catId} style={{
              background: '#111827', borderRadius: 8, border: '1px solid #1f2937', marginBottom: 6, overflow: 'hidden',
              borderLeft: `3px solid ${catColor}`,
            }}>
              <div style={{ padding: '8px 12px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}
                   onClick={() => setExpandedCat(isExpanded ? null : catId)}>
                <span style={{ fontSize: 16 }}>{info.icon}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 11, fontWeight: 600 }}>{info.title}</div>
                  <div style={{ fontSize: 9, color: '#4b5563' }}>{info.standard}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: catColor }}>{catScore.toFixed(0)}%</div>
                  <div style={{ fontSize: 9, color: catViolations.length > 0 ? '#ffa000' : '#00e676' }}>
                    {catViolations.length > 0 ? `${catViolations.length} issues` : 'Compliant'}
                  </div>
                </div>
              </div>

              {isExpanded && (cat.checks || []).map((check, i) => (
                <div key={i} style={{
                  padding: '5px 12px 5px 44px', fontSize: 10, borderTop: '1px solid #1a2332',
                  display: 'flex', alignItems: 'center', gap: 6,
                  background: check.passed ? 'transparent' : 'rgba(255,23,68,0.03)',
                }}>
                  <span>{check.passed ? '\u{2705}' : '\u{274C}'}</span>
                  <span style={{ color: check.passed ? '#9ca3af' : '#ffa000', flex: 1 }}>{check.description}</span>
                  {!check.passed && check.detail && (
                    <span style={{ color: '#6b7280', fontSize: 9, fontStyle: 'italic' }}>{check.detail}</span>
                  )}
                </div>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}
