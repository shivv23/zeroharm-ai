import React, { useMemo } from 'react';
import { getRiskColor } from '../store/plantData';
import { COLORS } from '../store/theme';

const ZONE_SIZE = 90;
const GAP = 6;
const COLS = 5;

function toIsometric(x, y) {
  const isoX = (x - y) * 0.866;
  const isoY = (x + y) * 0.5;
  return { x: isoX, y: isoY };
}

const PLANTS = [
  { label: 'Coke Oven Battery', zone: 'Z01', w: 2, h: 1 },
  { label: 'Blast Furnace', zone: 'Z02', w: 2, h: 2 },
  { label: 'BOS', zone: 'Z03', w: 1, h: 1 },
  { label: 'Continuous Casting', zone: 'Z04', w: 2, h: 1 },
  { label: 'Hot Rolling', zone: 'Z05', w: 2, h: 1 },
  { label: 'Raw Material Yard', zone: 'Z06', w: 2, h: 1 },
  { label: 'Gas Holder Area', zone: 'Z07', w: 2, h: 1 },
  { label: 'Central Control', zone: 'Z08', w: 1, h: 1 },
  { label: 'Workshop', zone: 'Z09', w: 1, h: 1 },
  { label: 'Cooling Tower', zone: 'Z10', w: 1, h: 1 },
];

function getHealthColor(riskScore) {
  const s = riskScore || 0;
  if (s > 0.6) return '#ff1744';
  if (s > 0.3) return '#ffa000';
  return '#00e676';
}

export default function IsometricPlantView({ zones, zoneRisks, selectedZone, onSelectZone }) {
  const gridSize = ZONE_SIZE + GAP;
  const structures = useMemo(() => {
    return PLANTS.map((p, i) => {
      const col = i % COLS;
      const row = Math.floor(i / COLS);
      const cx = col * (gridSize * 1.2) + (row % 2) * (gridSize * 0.6);
      const cy = row * (gridSize * 0.9);
      const iso = toIsometric(cx + ZONE_SIZE * 0.5, cy + ZONE_SIZE * 0.5);
      const risk = zoneRisks?.[p.zone] || 0;
      return { ...p, iso, risk, col, row, cx, cy };
    });
  }, [zoneRisks]);

  const svgW = 900;
  const svgH = 500;

  return (
    <div style={{
      background: '#080c16', borderRadius: 8, border: '1px solid #1f2937',
      padding: 16, overflow: 'auto',
    }}>
      <div style={{ fontSize: 13, fontWeight: 700, color: '#00e5ff', marginBottom: 12 }}>
        {'\u{1F30D}'} 3D Isometric Plant View
      </div>
      <svg viewBox={`-50 -50 ${svgW} ${svgH}`} style={{ width: '100%', height: 'auto', maxHeight: 460 }}>
        <defs>
          {structures.map(s => {
            const c = getHealthColor(s.risk);
            return (
              <linearGradient key={s.zone} id={`grad-${s.zone}`} x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor={c} stopOpacity={0.7} />
                <stop offset="100%" stopColor={c} stopOpacity={0.3} />
              </linearGradient>
            );
          })}
        </defs>
        {structures.map(s => {
          const iso = s.iso;
          const w = ZONE_SIZE * s.w * 0.7;
          const h = ZONE_SIZE * s.h * 0.45;
          const color = getHealthColor(s.risk);
          const isSelected = selectedZone === s.zone;
          const yOff = isSelected ? -8 : 0;

          return (
            <g key={s.zone} onClick={() => onSelectZone?.(isSelected ? null : s.zone)}
               style={{ cursor: 'pointer', transition: 'transform 0.3s' }}>
              {/* Floor tile */}
              <polygon
                points={`${iso.x},${iso.y + yOff} ${iso.x + w},${iso.y + h * 0.5 + yOff} ${iso.x},${iso.y + h + yOff} ${iso.x - w},${iso.y + h * 0.5 + yOff}`}
                fill={`url(#grad-${s.zone})`}
                stroke={isSelected ? '#00e5ff' : color}
                strokeWidth={isSelected ? 2 : 1}
                opacity={0.9}
              />
              {/* Front face */}
              <polygon
                points={`${iso.x - w},${iso.y + h * 0.5 + yOff} ${iso.x},${iso.y + h + yOff} ${iso.x},${iso.y + h - 15 + yOff} ${iso.x - w},${iso.y + h * 0.5 - 15 + yOff}`}
                fill={color} opacity={0.3} stroke={color} strokeWidth={0.5}
              />
              {/* Right face */}
              <polygon
                points={`${iso.x},${iso.y + h + yOff} ${iso.x + w},${iso.y + h * 0.5 + yOff} ${iso.x + w},${iso.y + h * 0.5 - 15 + yOff} ${iso.x},${iso.y + h - 15 + yOff}`}
                fill={color} opacity={0.2} stroke={color} strokeWidth={0.5}
              />
              {/* Label */}
              <text x={iso.x} y={iso.y + h * 0.5 + yOff} textAnchor="middle" dominantBaseline="middle"
                fill="#e0e5ec" fontSize={9} fontWeight={600}>{s.zone}</text>
              <text x={iso.x} y={iso.y + h * 0.5 + 12 + yOff} textAnchor="middle" dominantBaseline="middle"
                fill="#6b7280" fontSize={7}>{s.label}</text>
              {/* Risk badge */}
              <rect x={iso.x - 14} y={iso.y + h * 0.5 + 20 + yOff} width={28} height={14} rx={4}
                fill={color} opacity={0.8} />
              <text x={iso.x} y={iso.y + h * 0.5 + 27 + yOff} textAnchor="middle" dominantBaseline="middle"
                fill="#fff" fontSize={8} fontWeight={700}>{(s.risk * 100).toFixed(0)}</text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
