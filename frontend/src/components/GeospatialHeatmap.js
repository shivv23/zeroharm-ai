import React, { useMemo } from 'react';
import { getRiskColor, getRiskLabel } from '../store/plantData';
import { COLORS } from '../store/theme';

const SENSOR_DOT_SIZE = 6;

export default function GeospatialHeatmap({ zones, zoneRisks, selectedZone, onSelectZone, plantState }) {
  const sensors = plantState?.sensors ? Object.values(plantState.sensors) : [];
  const permits = plantState?.active_permits || [];

  const sensorPositions = useMemo(() => {
    return zones.flatMap(zone => {
      const zoneSensors = sensors.filter(s => s.zone_id === zone.id);
      return zoneSensors.map((s, i) => {
        const col = i % 3;
        const row = Math.floor(i / 3);
        return {
          ...s,
          x: zone.x + 10 + col * 8,
          y: zone.y + 8 + row * 7,
        };
      });
    });
  }, [zones, sensors]);

  const permitIndicators = useMemo(() => {
    const zonePermits = {};
    permits.forEach(p => {
      if (!zonePermits[p.zone_id]) zonePermits[p.zone_id] = [];
      zonePermits[p.zone_id].push(p);
    });
    return Object.entries(zonePermits).map(([zoneId, perms]) => {
      const zone = zones.find(z => z.id === zoneId);
      if (!zone) return null;
      return { zoneId, x: zone.x + zone.w - 8, y: zone.y + 4, count: perms.length,
               critical: perms.some(p => p.risk_level === 'Critical') };
    }).filter(Boolean);
  }, [zones, permits]);

  return (
    <div style={{ padding: 16, height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Title */}
      <div style={{ marginBottom: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 700, color: COLORS.text }}>{'\u{1F3E0}'} Geospatial Safety Heatmap</div>
          <div style={{ fontSize: 11, color: COLORS.textMuted }}>Visakhapatnam Steel Plant · Real-time risk overlay</div>
        </div>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div style={{ width: 12, height: 12, borderRadius: 2, background: COLORS.riskNormal }} />
            <span style={{ fontSize: 10, color: COLORS.textSecondary }}>Normal</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div style={{ width: 12, height: 12, borderRadius: 2, background: COLORS.riskElevated }} />
            <span style={{ fontSize: 10, color: COLORS.textSecondary }}>Elevated</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div style={{ width: 12, height: 12, borderRadius: 2, background: COLORS.riskHigh }} />
            <span style={{ fontSize: 10, color: COLORS.textSecondary }}>High</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div style={{ width: 12, height: 12, borderRadius: 2, background: COLORS.riskCritical }} />
            <span style={{ fontSize: 10, color: COLORS.textSecondary }}>Critical</span>
          </div>
        </div>
      </div>

      {/* Plant SVG */}
      <div style={{ flex: 1, position: 'relative', background: COLORS.bgElevated, borderRadius: 12, border: '1px solid ' + COLORS.border, overflow: 'hidden' }}>
        <svg viewBox="0 0 100 100" style={{ width: '100%', height: '100%' }}>
          {/* Zones */}
          {zones.map(zone => {
            const riskScore = zoneRisks?.[zone.id] ?? zone.baseRisk ?? 0;
            const isSelected = selectedZone?.id === zone.id;
            const color = getRiskColor(riskScore);
            const opacity = isSelected ? 0.9 : 0.6;
            return (
              <g key={zone.id} onClick={() => onSelectZone(zone)} style={{ cursor: 'pointer' }}>
                <rect x={zone.x} y={zone.y} width={zone.w} height={zone.h} rx={3}
                      fill={color} fillOpacity={opacity} stroke={isSelected ? '#fff' : 'transparent'}
                      strokeWidth={isSelected ? 0.8 : 0} />
                <text x={zone.x + zone.w / 2} y={zone.y + zone.h / 2 - 3}
                      textAnchor="middle" fontSize="3.5" fontWeight="700" fill="#fff" style={{ pointerEvents: 'none' }}>
                  {zone.name}
                </text>
                <text x={zone.x + zone.w / 2} y={zone.y + zone.h / 2 + 5}
                      textAnchor="middle" fontSize="2.8" fill="rgba(255,255,255,0.7)" style={{ pointerEvents: 'none' }}>
                  Risk: {(riskScore * 100).toFixed(0)}%
                </text>
                {/* Hazard class badge */}
                {zone.hazard === 'Extreme' && (
                  <text x={zone.x + zone.w / 2} y={zone.y + 8}
                        textAnchor="middle" fontSize="2.5" fill={COLORS.riskCritical} fontWeight="700">
                    {'\u26A0\uFE0F'} EXTREME
                  </text>
                )}
              </g>
            );
          })}

          {/* Sensor dots */}
          {sensorPositions.map((s, i) => {
            const color = s.status === 'critical' ? COLORS.riskCritical : s.status === 'warning' ? COLORS.riskElevated : COLORS.riskNormal;
            return (
              <g key={s.id || i}>
                <circle cx={s.x} cy={s.y} r={s.status === 'critical' ? 2 : 1.5}
                        fill={color} stroke="#fff" strokeWidth="0.3" />
                {s.status !== 'normal' && (
                  <text x={s.x} y={s.y - 2.5} textAnchor="middle" fontSize="2" fill={color} fontWeight="700">
                    {s.type} {s.value?.toFixed(1)}
                  </text>
                )}
              </g>
            );
          })}

          {/* Permit indicators */}
          {permitIndicators.map((p, i) => (
            <g key={`permit-${i}`}>
              <circle cx={p.x} cy={p.y} r={3} fill={p.critical ? COLORS.riskCritical : COLORS.riskElevated}
                      stroke="#fff" strokeWidth="0.5" />
              <text x={p.x} y={p.y + 1} textAnchor="middle" fontSize="2.2" fill="#fff" fontWeight="700">
                {p.count}
              </text>
            </g>
          ))}

          {/* Connections between related zones */}
          <line x1="30" y1="25" x2="40" y2="19" stroke={COLORS.riskCritical} strokeWidth="0.3" strokeOpacity="0.3" strokeDasharray="1,1" />
          <line x1="30" y1="25" x2="68" y2="18" stroke={COLORS.riskHigh} strokeWidth="0.3" strokeOpacity="0.3" strokeDasharray="1,1" />
          <line x1="62" y1="19" x2="68" y2="72" stroke={COLORS.riskCritical} strokeWidth="0.3" strokeOpacity="0.3" strokeDasharray="1,1" />

          {/* Legend overlay for zone names */}
          <rect x="1" y="93" width="40" height="6" rx="2" fill="rgba(0,0,0,0.5)" />
          <text x="3" y="97" fontSize="2.5" fill={COLORS.textSecondary}>
            {new Date().toLocaleTimeString()} · {sensors.length} sensors · {permits.length} active permits
          </text>
        </svg>

        {/* Overlay toolbar */}
        <div style={{
          position: 'absolute', top: 8, right: 8, display: 'flex', gap: 4,
          background: 'rgba(0,0,0,0.6)', padding: '4px 8px', borderRadius: 6,
        }}>
          <div style={overlayBtn}>All zones</div>
          <div style={{ ...overlayBtn, background: 'rgba(0,229,255,0.2)', color: COLORS.accent }}>Risk only</div>
          <div style={overlayBtn}>Sensors</div>
        </div>
      </div>

      {/* Selected Zone Detail */}
      {selectedZone && (
        <div style={{
          marginTop: 8, padding: '8px 12px', background: COLORS.bgCard, borderRadius: 8,
          border: '1px solid ' + COLORS.border, display: 'flex', alignItems: 'center', gap: 12,
        }}>
          <div style={{ width: 4, height: 32, borderRadius: 2, background: getRiskColor(zoneRisks?.[selectedZone.id] ?? 0) }} />
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 13, fontWeight: 600 }}>{selectedZone.name}</div>
            <div style={{ fontSize: 11, color: COLORS.textMuted }}>{selectedZone.description}</div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: getRiskColor(zoneRisks?.[selectedZone.id] ?? 0) }}>
              {(zoneRisks?.[selectedZone.id] ?? 0) > 0
                ? (zoneRisks[selectedZone.id] * 100).toFixed(0) + '%'
                : '--'}
            </div>
            <div style={{ fontSize: 10, color: COLORS.textMuted }}>
              {getRiskLabel(zoneRisks?.[selectedZone.id] ?? 0)}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const overlayBtn = {
  padding: '2px 8px', borderRadius: 4, fontSize: 10, color: COLORS.textSecondary,
  cursor: 'pointer', background: 'rgba(255,255,255,0.05)',
};
