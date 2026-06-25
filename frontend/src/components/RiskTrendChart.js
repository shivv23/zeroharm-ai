import React from 'react';
import { getRiskColor } from '../store/plantData';

export default function RiskTrendChart({ data = [], width = 300, height = 80, mini = false }) {
  if (data.length < 2) {
    return (
      <div style={{
        width, height, display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: '#4b5563', fontSize: 10,
      }}>
        Collecting data...
      </div>
    );
  }

  const padding = mini ? 2 : 8;
  const chartW = width - padding * 2;
  const chartH = height - padding * 2;
  const scores = data.map(d => d.score ?? 0);
  const maxScore = Math.max(...scores, 0.1);
  const minScore = Math.min(...scores, 0);
  const range = maxScore - minScore || 0.1;

  const points = scores.map((s, i) => {
    const x = padding + (i / Math.max(scores.length - 1, 1)) * chartW;
    const y = padding + chartH - ((s - minScore) / range) * chartH;
    return `${x},${y}`;
  }).join(' ');

  const currentScore = scores[scores.length - 1];
  const trend = scores.length > 5
    ? (scores[scores.length - 1] - scores[scores.length - 5]) / 0.2
    : 0;

  const color = getRiskColor(currentScore);

  if (mini) {
    return (
      <svg width={width} height={height}>
        <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  }

  return (
    <div style={{ padding: '8px 0' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 600 }}>{'\u{1F4C8}'} Risk Score Trend</div>
          <div style={{ fontSize: 10, color: '#6b7280' }}>Last {data.length} readings · 2s intervals</div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 20, fontWeight: 700, color }}>{(currentScore * 100).toFixed(0)}</div>
          <div style={{ fontSize: 10, color: trend > 0.05 ? '#ff1744' : trend < -0.05 ? '#00e676' : '#6b7280' }}>
            {trend > 0.05 ? `\u{2191} Rising` : trend < -0.05 ? `\u{2193} Falling` : '\u{2192} Stable'}
          </div>
        </div>
      </div>
      <svg width={width} height={height} style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 8 }}>
        <defs>
          <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.25" />
            <stop offset="100%" stopColor={color} stopOpacity="0.01" />
          </linearGradient>
        </defs>
        <polyline points={points} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <polygon points={`${points} ${padding + chartW},${padding + chartH} ${padding},${padding + chartH}`} fill="url(#riskGradient)" />
        <circle cx={scores.length > 1 ? padding + ((scores.length - 1) / Math.max(scores.length - 1, 1)) * chartW : padding}
                cy={padding + chartH - ((currentScore - minScore) / range) * chartH}
                r="3" fill={color} stroke="#0a0e17" strokeWidth="1.5" />
        <text x={padding} y={padding - 2} fontSize="9" fill="#4b5563">{(maxScore * 100).toFixed(0)}</text>
        <text x={padding} y={padding + chartH + 10} fontSize="9" fill="#4b5563">{(minScore * 100).toFixed(0)}</text>
      </svg>
    </div>
  );
}
