import React, { useState, useEffect, useMemo } from 'react';
import ws from '../store/websocketStore';
import { COLORS, LAYOUT } from '../store/theme';
import { getRiskColor } from '../store/plantData';

export default function PredictiveRiskPanel({ riskTrend = [] }) {
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      const data = await ws.fetchAPI('/predictive-risk');
      if (cancelled) return;
      if (data && data.data) setForecast(data.data);
      setLoading(false);
    }
    load();
    const interval = setInterval(load, 4000);
    return () => { cancelled = true; clearInterval(interval); };
  }, []);

  const chartWidth = 400;
  const chartHeight = 120;
  const padding = 16;

  const chartPoints = useMemo(() => {
    if (!forecast || !forecast.forecast || forecast.forecast.length === 0) return null;
    const all = [
      ...(forecast.current_risk != null ? [forecast.current_risk] : []),
      ...forecast.forecast
    ];
    return all.map((v, i) => ({
      x: padding + (i / Math.max(all.length - 1, 1)) * (chartWidth - padding * 2),
      y: padding + chartHeight - padding - v * (chartHeight - padding * 2),
      value: v,
      isForecast: i > 0,
    }));
  }, [forecast]);

  const trendIcon = forecast?.trend === 'rising' ? '\u2191' : forecast?.trend === 'falling' ? '\u2193' : '\u2192';
  const trendColor = forecast?.trend === 'rising' ? COLORS.riskCritical : forecast?.trend === 'falling' ? COLORS.riskNormal : COLORS.textMuted;

  return (
    <div style={{ padding: 16, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 700 }}>{'\u{1F4C8}'} Predictive Risk Forecast</div>
          <div style={{ fontSize: 11, color: COLORS.textMuted }}>ML-powered 5-step lookahead · updated every 4s</div>
        </div>
        {forecast && (
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: trendColor }}>
              {trendIcon} {forecast.trend.toUpperCase()}
            </div>
            <div style={{ fontSize: 10, color: COLORS.textMuted }}>
              Slope: {forecast.slope != null ? forecast.slope.toFixed(4) : 'N/A'}
            </div>
          </div>
        )}
      </div>

      {loading && <div style={{ textAlign: 'center', padding: 40, color: COLORS.textMuted }}>Loading forecast...</div>}

      {forecast && forecast.forecast && (
        <div style={{
          background: COLORS.bgCard, borderRadius: 8, border: `1px solid ${COLORS.border}`,
          padding: 12, marginBottom: 12,
        }}>
          <svg width={chartWidth} height={chartHeight}>
            <line x1={padding} y1={chartHeight - padding} x2={chartWidth - padding} y2={chartHeight - padding}
                  stroke={COLORS.border} strokeWidth="0.5" />
            {chartPoints && chartPoints.map((pt, i) => (
              <React.Fragment key={i}>
                {i > 0 && (
                  <line x1={chartPoints[i - 1].x} y1={chartPoints[i - 1].y}
                        x2={pt.x} y2={pt.y}
                        stroke={pt.isForecast ? COLORS.accent : getRiskColor(pt.value)}
                        strokeWidth={pt.isForecast ? 1.5 : 2}
                        strokeDasharray={pt.isForecast ? '3,2' : 'none'} />
                )}
                <circle cx={pt.x} cy={pt.y} r={3}
                        fill={pt.isForecast ? COLORS.accent : getRiskColor(pt.value)}
                        stroke={COLORS.bgCard} strokeWidth="1" />
              </React.Fragment>
            ))}
            <text x={padding} y={padding} fontSize="8" fill={COLORS.textDim}>1.0</text>
            <text x={padding} y={chartHeight - padding + 10} fontSize="8" fill={COLORS.textDim}>0.0</text>
            <text x={chartWidth - padding} y={chartHeight - padding + 10} fontSize="8" fill={COLORS.textDim}>+5 steps</text>
          </svg>
          <div style={{ display: 'flex', justifyContent: 'center', gap: 16, fontSize: 10, color: COLORS.textMuted, marginTop: 4 }}>
            <span><span style={{ color: COLORS.riskNormal }}>{'\u2500'}</span> Historical</span>
            <span><span style={{ color: COLORS.accent }}>{'- -'}</span> Predicted</span>
          </div>
        </div>
      )}

      {forecast && !forecast.forecast && (
        <div style={{ padding: 30, textAlign: 'center', color: COLORS.textMuted, fontSize: 12 }}>
          Collecting enough data for prediction... ({forecast.note || 'need 10+ readings'})
        </div>
      )}

      <div style={{ flex: 1, overflow: 'auto' }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: COLORS.textMuted, marginBottom: 8, textTransform: 'uppercase' }}>
          Recent Risk Trend
        </div>
        {riskTrend.length === 0 && (
          <div style={{ color: COLORS.textMuted, fontSize: 11 }}>No trend data yet.</div>
        )}
        {riskTrend.slice(-20).reverse().map((r, i) => {
          const color = getRiskColor(r.score || 0);
          return (
            <div key={i} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '4px 8px', background: i % 2 === 0 ? COLORS.bgElevated : 'transparent',
              borderRadius: 4, fontSize: 11, marginBottom: 2,
            }}>
              <span style={{ color: COLORS.textMuted }}>
                {r.timestamp ? new Date(r.timestamp).toLocaleTimeString() : ''}
              </span>
              <span style={{ fontWeight: 600, color }}>
                {(r.score * 100).toFixed(0)}%
              </span>
              <span style={{ color: COLORS.textMuted, fontSize: 10 }}>{r.severity}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
