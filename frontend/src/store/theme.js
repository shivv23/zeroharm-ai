// ZeroHarm AI Theme — single source of truth for all visual constants

// -------- Colors --------
export const COLORS = {
  // Primary backgrounds
  bg: '#080c16',
  bgHeader: '#0d1520',
  bgCard: '#111827',
  bgElevated: '#0d1520',
  bgModal: '#0a0e17',

  // Text
  text: '#e0e5ec',
  textDim: '#4b5563',
  textMuted: '#6b7280',
  textSecondary: '#9ca3af',
  textAlt: '#d1d5db',

  // Accents
  accent: '#00e5ff',
  accentAlt: '#00bcd4',

  // Risk severity
  riskCritical: '#ff1744',
  riskHigh: '#ff6d00',
  riskElevated: '#ffa000',
  riskModerate: '#ffea00',
  riskNormal: '#00e676',

  // Severity backgrounds
  bgCritical: 'rgba(255,23,68,0.1)',
  bgCriticalLight: 'rgba(255,23,68,0.05)',
  bgCriticalStrong: 'rgba(255,23,68,0.15)',
  bgHigh: 'rgba(255,109,0,0.1)',
  bgWarning: 'rgba(255,160,0,0.1)',
  bgInfo: 'rgba(0,229,255,0.06)',
  bgNormal: 'rgba(0,230,118,0.1)',

  // Severity borders
  borderCritical: 'rgba(255,23,68,0.3)',
  borderHigh: 'rgba(255,109,0,0.3)',
  borderWarning: 'rgba(255,160,0,0.3)',
  borderInfo: 'rgba(0,229,255,0.3)',
  borderNormal: 'rgba(0,230,118,0.3)',

  // Borders
  border: '#1f2937',
  borderAlt: '#1a2332',
  borderTab: '#1a2332',

  // Status
  success: '#00e676',
  warning: '#ffa000',
  error: '#ff1744',
  offline: '#6b7280',

  // Health
  healthGood: '#00e676',
  healthWarn: '#ffa000',
  healthCrit: '#ff1744',

  // Overlay
  overlay: 'rgba(0,0,0,0.7)',

  // Accent backgrounds
  bgAccentHover: 'rgba(0,229,255,0.08)',
  bgAccentActive: 'rgba(0,229,255,0.15)',
  bgAccentStrong: 'rgba(0,229,255,0.1)',

  // Stronger severity backgrounds
  bgCriticalStronger: 'rgba(255,23,68,0.2)',
  bgHighStronger: 'rgba(255,109,0,0.2)',
  bgNormalStrong: 'rgba(0,230,118,0.15)',
  bgNormalMedium: 'rgba(0,230,118,0.2)',

  // Stronger borders
  borderCriticalStrong: 'rgba(255,23,68,0.4)',

  // Gradients
  gradientHeader: 'linear-gradient(135deg, #0d1520 0%, #111827 100%)',
  gradientTitle: 'linear-gradient(90deg, #00e5ff, #00bcd4)',
  gradientCritical: 'linear-gradient(135deg, #ff1744, #d50000)',
  gradientEmergency: 'linear-gradient(135deg, rgba(255,23,68,0.2), rgba(213,0,0,0.15))',
};

// -------- Font Sizes --------
export const FONT = {
  xs: 9,
  sm: 10,
  base: 11,
  md: 12,
  lg: 13,
  xl: 15,
  '2xl': 16,
  '3xl': 18,
  '4xl': 20,
  mono: "'SF Mono', 'Fira Code', monospace",
};

// -------- Spacing --------
export const SPACING = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  '2xl': 24,
};

// -------- Border Radii --------
export const RADIUS = {
  sm: 4,
  md: 6,
  lg: 8,
  xl: 10,
  pill: 12,
  round: '50%',
};

// -------- Shadows --------
export const SHADOWS = {
  card: 'none',
  glow: (color) => `0 0 8px ${color}33`,
  toast: '0 4px 20px rgba(0,0,0,0.4)',
};

// -------- Transitions --------
export const TRANSITION = 'all 0.2s';

// -------- Layout --------
export const LAYOUT = {
  narrowThreshold: 1100,
  sidebarNarrow: 240,
  sidebarWide: 340,
  headerHeight: 50,
  miniChartWidth: 80,
  miniChartHeight: 24,
};

// -------- Severity Config (unified across all components) --------
export const SEVERITY = {
  critical: {
    color: COLORS.riskCritical,
    bg: COLORS.bgCritical,
    border: COLORS.borderCritical,
    dot: COLORS.riskCritical,
    pulse: true,
  },
  high: {
    color: COLORS.riskHigh,
    bg: COLORS.bgHigh,
    border: COLORS.borderHigh,
    dot: COLORS.riskHigh,
    pulse: false,
  },
  warning: {
    color: COLORS.riskElevated,
    bg: COLORS.bgWarning,
    border: COLORS.borderWarning,
    dot: COLORS.riskElevated,
    pulse: false,
  },
  info: {
    color: COLORS.accent,
    bg: COLORS.bgInfo,
    border: COLORS.borderInfo,
    dot: COLORS.accent,
    pulse: false,
  },
  normal: {
    color: COLORS.riskNormal,
    bg: 'transparent',
    border: COLORS.borderNormal,
    dot: COLORS.riskNormal,
    pulse: false,
  },
};

// -------- Agent Colors --------
export const AGENT_COLORS = {
  'Sensor Monitor Agent': COLORS.accent,
  'Permit Activity Agent': COLORS.riskElevated,
  'Maintenance Status Agent': COLORS.riskNormal,
  'Compound Risk Detection Engine': COLORS.riskCritical,
  'Quality & Compliance Audit Agent': '#7c4dff',
  'Emergency Response Orchestrator': COLORS.riskHigh,
  'Risk Fusion Supervisor': COLORS.accentAlt,
  'ZeroHarm System': COLORS.textMuted,
};

// -------- Emergency Types --------
export const EMERGENCY_TYPES = [
  { id: 'gas_leak', label: 'Gas Leak', icon: '\u26A0\uFE0F', color: COLORS.riskHigh },
  { id: 'fire', label: 'Fire', icon: '\u1F525', color: COLORS.riskCritical },
  { id: 'confined_space_emergency', label: 'Confined Space Rescue', icon: '\u1F6AA', color: '#ff9100' },
  { id: 'explosion', label: 'Explosion', icon: '\u1F4A5', color: '#d50000' },
  { id: 'medical_emergency', label: 'Medical Emergency', icon: '\u1F3E5', color: COLORS.accent },
];

// -------- Compliance Category Labels --------
export const COMPLIANCE_CATEGORIES = {
  gas_detection: { title: 'Gas Detection Systems', standard: 'OISD-STD-116', icon: '\u1F4E1' },
  permit_to_work: { title: 'Permit-to-Work', standard: 'Factory Act / OISD-GDN-204', icon: '\u1F4CB' },
  maintenance_safety: { title: 'Maintenance Safety', standard: 'OISD-STD-201', icon: '\u1F527' },
  training_competency: { title: 'Training & Competency', standard: 'ISO 45001', icon: '\u1F393' },
  emergency_preparedness: { title: 'Emergency Preparedness', standard: 'OISD-STD-105', icon: '\u1F6A8' },
};

// -------- Tabs --------
export const APP_TABS = [
  { id: 'heatmap', label: 'Heatmap', icon: '\u{1F3E0}' },
  { id: 'alerts', label: 'Alerts', icon: '\u{26A0}\uFE0F' },
  { id: 'permits', label: 'Permits', icon: '\u{1F4CB}' },
  { id: 'compliance', label: 'Audit', icon: '\u{1F4DD}' },
  { id: 'safety', label: 'Safety Scores', icon: '\u{1F3C6}' },
  { id: 'forecast', label: 'Forecast', icon: '\u{1F4C8}' },
  { id: 'anomalies', label: 'Anomalies', icon: '\u{1F50D}' },
  { id: 'emergency', label: 'Emergency', icon: '\u{1F6A8}' },
  { id: 'scenarios', label: 'What-If', icon: '\u{1F9E9}' },
  { id: 'feed', label: 'Agents', icon: '\u{1F916}' },
  { id: 'patterns', label: 'Patterns', icon: '\u{1F50D}' },
  { id: 'investigations', label: 'Investigations', icon: '\u{1F50D}' },
  { id: '3dview', label: '3D Plant', icon: '\u{1F30D}' },
  { id: 'cost', label: 'Cost of Safety', icon: '\u{1F4B0}' },
  { id: 'rootcause', label: 'Root Cause', icon: '\u{1F50D}' },
  { id: 'twindash', label: 'Plant Pulse', icon: '\u{1F4CA}' },
  { id: 'reports', label: 'Reports', icon: '\u{1F4DD}' },
  { id: 'personnel', label: 'Personnel', icon: '\u{1F465}' },
  { id: 'triage', label: 'Alert Triage', icon: '\u{1F9D0}' },
  { id: 'eqhealth', label: 'Equip Health', icon: '\u{1F527}' },
  { id: 'observations', label: 'Observations', icon: '\u{1F4A1}' },
  { id: 'environmental', label: 'Environment', icon: '\u{1F30D}' },
];

// -------- Alert Duration Defaults --------
export const TOAST_DURATION = {
  default: 5000,
  success: 3000,
  warning: 5000,
  critical: 8000,
  emergency: 10000,
  scenario: 4000,
};

// -------- Alert Audio --------
export const ALERT_AUDIO = {
  frequency: 880,
  gain: 0.1,
  durationS: 0.5,
};

// -------- Risk Thresholds --------
export const RISK_THRESHOLDS = {
  critical: 0.8,
  high: 0.6,
  elevated: 0.4,
  moderate: 0.2,
};

export const HEALTH_THRESHOLDS = {
  excellent: 85,
  good: 70,
  fair: 50,
};

export const SENSOR_TYPES = ['O2','CO','H2S','LEL','Temperature','Pressure','VOC','NO2'];

// -------- Common Styles (for inline use via spread) --------
export const SX = {
  section: { marginBottom: SPACING.md, paddingBottom: SPACING.sm, borderBottom: `1px solid ${COLORS.borderAlt}` },
  sectionTitle: { fontSize: FONT.xs, fontWeight: 600, color: COLORS.accent, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 6 },
  card: { background: COLORS.bgCard, borderRadius: RADIUS.lg, border: `1px solid ${COLORS.border}` },
  cardPadded: { background: COLORS.bgCard, borderRadius: RADIUS.lg, border: `1px solid ${COLORS.border}`, padding: SPACING.md },
  input: {
    width: '100%', padding: '6px 8px', background: COLORS.bgElevated, color: COLORS.text,
    border: `1px solid ${COLORS.border}`, borderRadius: RADIUS.sm, fontSize: FONT.base, outline: 'none',
  },
  select: {
    width: '100%', padding: '6px 8px', background: COLORS.bgElevated, color: COLORS.text,
    border: `1px solid ${COLORS.border}`, borderRadius: RADIUS.sm, fontSize: FONT.base, outline: 'none',
  },
  emptyState: { textAlign: 'center', padding: 40, color: COLORS.textMuted },
  emptyIcon: { fontSize: 32, marginBottom: 8 },
  emptyTitle: { fontSize: 14, fontWeight: 600 },
  emptyDesc: { fontSize: 11, marginTop: 4 },
};
