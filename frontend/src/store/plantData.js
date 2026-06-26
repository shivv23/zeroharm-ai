const RISK_COLOR_CRITICAL = '#ff1744';
const RISK_COLOR_HIGH = '#ff6d00';
const RISK_COLOR_ELEVATED = '#ffa000';
const RISK_COLOR_MODERATE = '#ffea00';
const RISK_COLOR_NORMAL = '#00e676';

const RISK_THRESHOLD_CRITICAL = 0.8;
const RISK_THRESHOLD_HIGH = 0.6;
const RISK_THRESHOLD_ELEVATED = 0.4;
const RISK_THRESHOLD_MODERATE = 0.2;

export const PLANT_ZONES = [
  { id: 'Z01', name: 'Coke Oven Battery', x: 5, y: 15, w: 25, h: 20, hazard: 'Extreme', baseRisk: 0.85,
    color: RISK_COLOR_CRITICAL, description: 'CO/H2S/LEL sensors. Coke oven gas byproduct.' },
  { id: 'Z02', name: 'Blast Furnace Area', x: 40, y: 5, w: 22, h: 28, hazard: 'Extreme', baseRisk: 0.9,
    color: '#d50000', description: 'High temp, molten iron, CO gas. Critical zone.' },
  { id: 'Z03', name: 'Steelmaking (BOS)', x: 72, y: 12, w: 22, h: 24, hazard: 'High', baseRisk: 0.7,
    color: RISK_COLOR_HIGH, description: 'Basic Oxygen Steelmaking. High temp processes.' },
  { id: 'Z04', name: 'Continuous Casting', x: 5, y: 42, w: 28, h: 20, hazard: 'Medium', baseRisk: 0.4,
    color: RISK_COLOR_ELEVATED, description: 'Molten steel casting. Moderate risk zone.' },
  { id: 'Z05', name: 'Hot Rolling Mill', x: 50, y: 48, w: 38, h: 20, hazard: 'High', baseRisk: 0.65,
    color: RISK_COLOR_HIGH, description: 'Rolling at high temp. Mechanical and thermal hazards.' },
  { id: 'Z06', name: 'Raw Material Yard', x: 3, y: 72, w: 25, h: 20, hazard: 'Medium', baseRisk: 0.35,
    color: RISK_COLOR_ELEVATED, description: 'Material storage and handling.' },
  { id: 'Z07', name: 'Gas Holder Area', x: 68, y: 72, w: 25, h: 22, hazard: 'Extreme', baseRisk: 0.9,
    color: '#b71c1c', description: 'BFG/COG holders. Explosion risk zone.' },
  { id: 'Z08', name: 'Central Control Room', x: 38, y: 36, w: 14, h: 10, hazard: 'Low', baseRisk: 0.05,
    color: RISK_COLOR_NORMAL, description: 'Plant control center. Safe zone.' },
  { id: 'Z09', name: 'Maintenance Workshop', x: 38, y: 72, w: 22, h: 14, hazard: 'Low', baseRisk: 0.15,
    color: '#00e676', description: 'Equipment maintenance area.' },
  { id: 'Z10', name: 'Cooling Tower Area', x: 5, y: 28, w: 16, h: 12, hazard: 'Low', baseRisk: 0.1,
    color: '#00e676', description: 'Water cooling systems.' },
];

export function getRiskColor(score) {
  if (score >= RISK_THRESHOLD_CRITICAL) return RISK_COLOR_CRITICAL;
  if (score >= RISK_THRESHOLD_HIGH) return RISK_COLOR_HIGH;
  if (score >= RISK_THRESHOLD_ELEVATED) return RISK_COLOR_ELEVATED;
  if (score >= RISK_THRESHOLD_MODERATE) return RISK_COLOR_MODERATE;
  return RISK_COLOR_NORMAL;
}

export function getRiskLabel(score) {
  if (score >= RISK_THRESHOLD_CRITICAL) return 'CRITICAL';
  if (score >= RISK_THRESHOLD_HIGH) return 'HIGH';
  if (score >= RISK_THRESHOLD_ELEVATED) return 'ELEVATED';
  if (score >= RISK_THRESHOLD_MODERATE) return 'MODERATE';
  return 'NORMAL';
}
