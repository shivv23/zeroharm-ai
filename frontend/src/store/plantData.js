export const PLANT_ZONES = [
  { id: 'Z01', name: 'Coke Oven Battery', x: 5, y: 15, w: 25, h: 20, hazard: 'Extreme', baseRisk: 0.85,
    color: '#ff1744', description: 'CO/H2S/LEL sensors. Coke oven gas byproduct.' },
  { id: 'Z02', name: 'Blast Furnace Area', x: 40, y: 5, w: 22, h: 28, hazard: 'Extreme', baseRisk: 0.9,
    color: '#d50000', description: 'High temp, molten iron, CO gas. Critical zone.' },
  { id: 'Z03', name: 'Steelmaking (BOS)', x: 72, y: 12, w: 22, h: 24, hazard: 'High', baseRisk: 0.7,
    color: '#ff6d00', description: 'Basic Oxygen Steelmaking. High temp processes.' },
  { id: 'Z04', name: 'Continuous Casting', x: 5, y: 42, w: 28, h: 20, hazard: 'Medium', baseRisk: 0.4,
    color: '#ffa000', description: 'Molten steel casting. Moderate risk zone.' },
  { id: 'Z05', name: 'Hot Rolling Mill', x: 50, y: 48, w: 38, h: 20, hazard: 'High', baseRisk: 0.65,
    color: '#ff6d00', description: 'Rolling at high temp. Mechanical and thermal hazards.' },
  { id: 'Z06', name: 'Raw Material Yard', x: 3, y: 72, w: 25, h: 20, hazard: 'Medium', baseRisk: 0.35,
    color: '#ffa000', description: 'Material storage and handling.' },
  { id: 'Z07', name: 'Gas Holder Area', x: 68, y: 72, w: 25, h: 22, hazard: 'Extreme', baseRisk: 0.9,
    color: '#b71c1c', description: 'BFG/COG holders. Explosion risk zone.' },
  { id: 'Z08', name: 'Central Control Room', x: 38, y: 36, w: 14, h: 10, hazard: 'Low', baseRisk: 0.05,
    color: '#00c853', description: 'Plant control center. Safe zone.' },
  { id: 'Z09', name: 'Maintenance Workshop', x: 38, y: 72, w: 22, h: 14, hazard: 'Low', baseRisk: 0.15,
    color: '#00e676', description: 'Equipment maintenance area.' },
  { id: 'Z10', name: 'Cooling Tower Area', x: 5, y: 28, w: 16, h: 12, hazard: 'Low', baseRisk: 0.1,
    color: '#00e676', description: 'Water cooling systems.' },
];

export function getRiskColor(score) {
  if (score >= 0.8) return '#ff1744';
  if (score >= 0.6) return '#ff6d00';
  if (score >= 0.4) return '#ffa000';
  if (score >= 0.2) return '#ffea00';
  return '#00e676';
}

export function getRiskLabel(score) {
  if (score >= 0.8) return 'CRITICAL';
  if (score >= 0.6) return 'HIGH';
  if (score >= 0.4) return 'ELEVATED';
  if (score >= 0.2) return 'MODERATE';
  return 'NORMAL';
}
