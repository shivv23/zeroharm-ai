import React, { useState, useEffect } from 'react';
import ws from '../store/websocketStore';
import { COLORS, COMPLIANCE_CATEGORIES as CATEGORY_LABELS } from '../store/theme';

export default function CompliancePanel({ compliance }) {
  const uid = React.useId();
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
      <div style={{ padding: 40, textAlign: 'center', color: COLORS.textMuted }}>
        <div style={{ fontSize: 32, marginBottom: 8 }}>{'\u{1F4DD}'}</div>
        <div>Running compliance audit...</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div style={{ padding: 40, textAlign: 'center', color: COLORS.textMuted }}>
        <div style={{ fontSize: 32, marginBottom: 8 }}>{'\u{1F4DD}'}</div>
        <div>No compliance data available</div>
      </div>
    );
  }

  const score = data.overall_compliance_score || 0;
  const scoreColor = score >= 80 ? '#00e676' : score >= 60 ? COLORS.riskElevated : COLORS.riskCritical;
  const violations = data.violations || [];
  const criticals = data.critical_findings || [];
  const categories = data.category_scores || {};

  return (
    <div style={{ padding: 16, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: 10, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: 15, fontWeight: 700 }}>{'\u{1F4DD}'} Quality & Compliance Audit</div>
          <div style={{ fontSize: 10, color: COLORS.textMuted }}>AI-powered regulatory compliance monitoring</div>
        </div>
      </div>

      {/* Overall Score */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
        <div style={{ flex: 1, background: '#111827', borderRadius: 10, border: '1px solid ' + COLORS.border, padding: 12, textAlign: 'center' }}>
          <div style={{ position: 'relative', width: 64, height: 64, margin: '0 auto' }}>
            <svg width="64" height="64" viewBox="0 0 64 64">
              <circle cx="32" cy="32" r="28" fill="none" stroke={COLORS.border} strokeWidth="6" />
              <circle cx="32" cy="32" r="28" fill="none" stroke={scoreColor} strokeWidth="6"
                      strokeDasharray={`${(score / 100) * 176} 176`} transform="rotate(-90 32 32)" strokeLinecap="round" />
            </svg>
            <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', fontSize: 18, fontWeight: 700, color: scoreColor }}>
              {score.toFixed(0)}
            </div>
          </div>
          <div style={{ fontSize: 10, color: COLORS.textMuted, marginTop: 4 }}>Compliance Score</div>
          <div style={{ fontSize: 11, fontWeight: 600, color: scoreColor }}>{score >= 80 ? 'PASS' : score >= 60 ? 'REVIEW' : 'FAIL'}</div>
        </div>

        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 6 }}>
          <div style={{ flex: 1, background: COLORS.bgCritical, borderRadius: 8, border: '1px solid ' + COLORS.borderCritical, padding: '6px 10px', display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 18 }}>{'\u{1F525}'}</span>
            <div>
              <div style={{ fontSize: 16, fontWeight: 700, color: COLORS.riskCritical }}>{criticals.length}</div>
              <div style={{ fontSize: 9, color: COLORS.textMuted }}>Critical</div>
            </div>
          </div>
          <div style={{ flex: 1, background: COLORS.bgWarning, borderRadius: 8, border: '1px solid ' + COLORS.borderWarning, padding: '6px 10px', display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 18 }}>{'\u{26A0}\uFE0F'}</span>
            <div>
              <div style={{ fontSize: 16, fontWeight: 700, color: COLORS.riskElevated }}>{violations.length}</div>
              <div style={{ fontSize: 9, color: COLORS.textMuted }}>Violations</div>
            </div>
          </div>
        </div>
      </div>

      {/* Compliance Trend */}
      {trend.length > 1 && (
        <div style={{ background: '#111827', borderRadius: 8, border: '1px solid ' + COLORS.border, padding: 8, marginBottom: 8 }}>
          <div style={{ fontSize: 10, color: COLORS.textMuted, marginBottom: 4 }}>Compliance Score Trend</div>
          <svg width="100%" height="40" viewBox={`0 0 ${trend.length * 10} 40`} preserveAspectRatio="none">
            <defs>
              <linearGradient id={`compGrad-${uid}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#00e676" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#00e676" stopOpacity="0.0" />
              </linearGradient>
            </defs>
            <path d={trend.map((p, i) => `${i === 0 ? 'M' : 'L'}${i * 10} ${40 - (p.score / 100) * 36}`).join(' ')}
                  fill="none" stroke="#00e676" strokeWidth="1.5" strokeLinecap="round" />
            <path d={`${trend.map((p, i) => `${i === 0 ? 'M' : 'L'}${i * 10} ${40 - (p.score / 100) * 36}`).join(' ')} L${(trend.length - 1) * 10} 40 L0 40 Z`}
                  fill={`url(#compGrad-${uid})`} />
            <circle cx={(trend.length - 1) * 10} cy={40 - (trend[trend.length - 1].score / 100) * 36} r="2" fill="#00e676" />
          </svg>
        </div>
      )}

      {/* Category Scores */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {Object.entries(categories).map(([catId, cat]) => {
          const info = CATEGORY_LABELS[catId] || { title: catId, standard: '', icon: '\u{1F4CB}' };
          const catScore = (cat.score || 0) * 100;
          const catColor = catScore >= 80 ? '#00e676' : catScore >= 60 ? COLORS.riskElevated : COLORS.riskCritical;
          const isExpanded = expandedCat === catId;
          const catViolations = (cat.checks || []).filter(c => !c.passed);
          return (
            <div key={catId} style={{
              background: '#111827', borderRadius: 8, border: '1px solid ' + COLORS.border, marginBottom: 6, overflow: 'hidden',
              borderLeft: `3px solid ${catColor}`,
            }}>
              <div style={{ padding: '8px 12px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}
                   onClick={() => setExpandedCat(isExpanded ? null : catId)}>
                <span style={{ fontSize: 16 }}>{info.icon}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 11, fontWeight: 600 }}>{info.title}</div>
                  <div style={{ fontSize: 9, color: COLORS.textDim }}>{info.standard}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: catColor }}>{catScore.toFixed(0)}%</div>
                  <div style={{ fontSize: 9, color: catViolations.length > 0 ? COLORS.riskElevated : '#00e676' }}>
                    {catViolations.length > 0 ? `${catViolations.length} issues` : 'Compliant'}
                  </div>
                </div>
              </div>

              {isExpanded && (cat.checks || []).map((check, i) => (
                <div key={i} style={{
                  padding: '5px 12px 5px 44px', fontSize: 10, borderTop: '1px solid #1a2332',
                  display: 'flex', alignItems: 'center', gap: 6,
                  background: check.passed ? 'transparent' : COLORS.bgCriticalLight,
                }}>
                  <span>{check.passed ? '\u{2705}' : '\u{274C}'}</span>
                  <span style={{ color: check.passed ? '#9ca3af' : COLORS.riskElevated, flex: 1 }}>{check.description}</span>
                  {!check.passed && check.detail && (
                    <span style={{ color: COLORS.textMuted, fontSize: 9, fontStyle: 'italic' }}>{check.detail}</span>
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
