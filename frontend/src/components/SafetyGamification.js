import React, { useState, useEffect } from 'react';
import ws from '../store/websocketStore';
import { COLORS } from '../store/theme';

function getScoreColor(score) {
  if (score >= 80) return COLORS.riskNormal;
  if (score >= 60) return COLORS.riskElevated;
  if (score >= 40) return COLORS.riskHigh;
  return COLORS.riskCritical;
}

function getHazardIcon(hazard) {
  if (hazard === 'Extreme') return '\u2622\uFE0F';
  if (hazard === 'High') return '\u26A0\uFE0F';
  if (hazard === 'Medium') return '\u26A0\uFE0F';
  return '\u2705';
}

export default function SafetyGamification() {
  const [scores, setScores] = useState([]);
  const [average, setAverage] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      const data = await ws.fetchAPI('/safety-scores');
      if (cancelled) return;
      if (data && data.zones) {
        setScores(data.zones || []);
        setAverage(data.plant_average || 0);
      }
      setLoading(false);
    }
    load();
    const interval = setInterval(load, 5000);
    return () => { cancelled = true; clearInterval(interval); };
  }, []);

  return (
    <div style={{ padding: 16, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 700 }}>{'\u{1F3C6}'} Safety Score Leaderboard</div>
          <div style={{ fontSize: 11, color: COLORS.textMuted }}>Per-zone safety performance · higher is better</div>
        </div>
        <div style={{
          padding: '6px 14px', borderRadius: 8, background: COLORS.bgCard,
          border: `1px solid ${getScoreColor(average)}`, textAlign: 'center',
        }}>
          <div style={{ fontSize: 20, fontWeight: 700, color: getScoreColor(average) }}>{average.toFixed(1)}</div>
          <div style={{ fontSize: 9, color: COLORS.textMuted }}>Plant Avg</div>
        </div>
      </div>

      {loading && <div style={{ textAlign: 'center', padding: 40, color: COLORS.textMuted }}>Loading scores...</div>}

      <div style={{ flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column', gap: 6 }}>
        {scores.map((zone, i) => {
          const color = getScoreColor(zone.safety_score);
          const barWidth = `${zone.safety_score}%`;
          const isTop3 = i >= scores.length - 3;
          const isBottom3 = i < 3;
          return (
            <div key={zone.zone_id} style={{
              background: COLORS.bgCard, borderRadius: 8, padding: '8px 12px',
              border: `1px solid ${COLORS.border}`,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  {isTop3 && <span style={{ fontSize: 14 }}>{'\u{1F947}'}</span>}
                  {isBottom3 && <span style={{ fontSize: 14 }}>{'\u{1F6A8}'}</span>}
                  <span style={{ fontSize: 13, fontWeight: 600 }}>{zone.name}</span>
                  <span style={{ fontSize: 9, color: COLORS.textMuted }}>({zone.zone_id})</span>
                  <span style={{ fontSize: 10 }}>{getHazardIcon(zone.hazard)} {zone.hazard}</span>
                </div>
                <div style={{ fontSize: 18, fontWeight: 700, color }}>{zone.safety_score}</div>
              </div>
              <div style={{
                height: 6, background: COLORS.bgElevated, borderRadius: 3, overflow: 'hidden',
              }}>
                <div style={{
                  width: barWidth, height: '100%', background: color, borderRadius: 3,
                  transition: 'width 0.5s ease',
                }} />
              </div>
              <div style={{ fontSize: 9, color: COLORS.textMuted, marginTop: 2, textAlign: 'right' }}>
                {zone.safety_score >= 80 ? 'Excellent' : zone.safety_score >= 60 ? 'Needs Improvement' : 'Critical Attention Required'}
              </div>
            </div>
          );
        })}
      </div>

      <div style={{ marginTop: 8, padding: '6px 12px', background: COLORS.bgElevated, borderRadius: 6, fontSize: 10, color: COLORS.textMuted, textAlign: 'center' }}>
        {'\u{1F3C6}'} Top 3 zones shown with trophies | {'\u{1F6A8}'} Bottom 3 zones flagged for attention
      </div>
    </div>
  );
}
