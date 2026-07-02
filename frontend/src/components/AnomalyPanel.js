import React, { useState, useEffect } from 'react';
import ws from '../store/websocketStore';
import { COLORS } from '../store/theme';
import { getRiskColor } from '../store/plantData';

export default function AnomalyPanel() {
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      const data = await ws.fetchAPI('/anomalies');
      if (cancelled) return;
      if (data && data.data) setAnomalies(data.data);
      setLoading(false);
    }
    load();
    const interval = setInterval(load, 4000);
    return () => { cancelled = true; clearInterval(interval); };
  }, []);

  return (
    <div style={{ padding: 16, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 700 }}>{'\u{1F50D}'} Anomaly Detection Engine</div>
          <div style={{ fontSize: 11, color: COLORS.textMuted }}>
            Isolation Forest ML model scanning {anomalies.length} anomalies in real-time
          </div>
        </div>
        <div style={{
          padding: '4px 12px', borderRadius: 6,
          background: anomalies.length > 0 ? COLORS.bgCritical : COLORS.bgNormal,
          fontSize: 12, fontWeight: 700,
          color: anomalies.length > 0 ? COLORS.riskCritical : COLORS.riskNormal,
        }}>
          {anomalies.length > 0 ? `${anomalies.length} Anomalies` : 'All Normal'}
        </div>
      </div>

      {loading && <div style={{ textAlign: 'center', padding: 40, color: COLORS.textMuted }}>Loading anomaly data...</div>}

      {!loading && anomalies.length === 0 && (
        <div style={{ textAlign: 'center', padding: 60, color: COLORS.textMuted }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>{'\u2705'}</div>
          <div style={{ fontSize: 14, fontWeight: 600 }}>No Anomalies Detected</div>
          <div style={{ fontSize: 11, marginTop: 4 }}>All sensor readings are within expected ranges.</div>
        </div>
      )}

      <div style={{ flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column', gap: 6 }}>
        {anomalies.map((a, i) => (
          <div key={i} style={{
            background: COLORS.bgCard, borderRadius: 8, padding: 10,
            border: `1px solid ${COLORS.borderCritical}`, animation: 'pulse 2s infinite',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
              <div>
                <span style={{ fontSize: 12, fontWeight: 700, color: COLORS.riskCritical }}>{'\u26A0\uFE0F'} Anomaly Detected</span>
                <span style={{ fontSize: 10, color: COLORS.textMuted, marginLeft: 8 }}>Sensor: {a.sensor_id}</span>
              </div>
              <span style={{
                fontSize: 10, padding: '2px 8px', borderRadius: 8,
                background: COLORS.bgCritical, color: COLORS.riskCritical, fontWeight: 600,
              }}>
                Z-score: {a.z_score}
              </span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4, fontSize: 11 }}>
              <div><span style={{ color: COLORS.textMuted }}>Current Value:</span> <span style={{ color: getRiskColor(0.7), fontWeight: 600 }}>{a.current_value}</span></div>
              <div><span style={{ color: COLORS.textMuted }}>Mean:</span> <span>{a.mean}</span></div>
              <div><span style={{ color: COLORS.textMuted }}>Std Dev:</span> <span>{a.std}</span></div>
              <div><span style={{ color: COLORS.textMuted }}>Z-Score:</span> <span style={{ fontWeight: 600, color: COLORS.riskCritical }}>{a.z_score}</span></div>
            </div>
          </div>
        ))}
      </div>

      <div style={{ marginTop: 8, padding: '6px 12px', background: COLORS.bgElevated, borderRadius: 6, fontSize: 10, color: COLORS.textMuted, textAlign: 'center' }}>
        ML Model: Isolation Forest ({'\u03B5'}=0.1) · Scanning {anomalies.length > 0 ? 'anomalous' : 'all'} sensors
      </div>
    </div>
  );
}
