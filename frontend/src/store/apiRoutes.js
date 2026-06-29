// ZeroHarm AI API Routes — single source of truth for all endpoint paths

export const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';
export const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const API = {
  // Health
  health: '/health',

  // Plant
  plantLayout: '/plant/layout',
  plantState: '/plant/state',

  // Risk
  riskCurrent: '/risk/current',
  riskAlerts: '/risk/alerts',
  riskTrend: '/risk-trend',

  // Sensors
  sensors: '/sensors',
  sensorsByZone: (zoneId) => `/sensors/zone/${zoneId}`,

  // Permits
  permits: '/permits',

  // Compliance
  complianceAudit: '/compliance/audit',
  complianceTrend: '/compliance/trend',
  exportCompliance: '/export/compliance',

  // RAG
  ragPermitCompliance: '/rag/permit-compliance',
  ragSearch: '/rag/search',

  // Emergency
  emergencyTrigger: '/emergency/trigger',
  emergencyActive: '/emergency/active',
  emergencyResolve: (id) => `/emergency/resolve/${id}`,

  // Incident Patterns
  incidentPatterns: '/incident-patterns',
  incidentPatternsZone: (zoneId) => `/incident-patterns/zone/${zoneId}`,
  incidentPatternsRecs: '/incident-patterns/recommendations',

  // What-If
  whatIfScenarios: '/what-if/scenarios',
  whatIfApply: '/what-if/apply',
  whatIfCustom: '/what-if/custom',
  whatIfReset: '/what-if/reset',

  // Knowledge Graph
  kgQuery: '/kg/query',
  kgRegulatory: (hazardType) => `/kg/regulatory/${hazardType}`,
  knowledgeGraph: '/knowledge-graph',

  // Activity Feed
  activityFeed: '/activity-feed',

  // Regulatory Standards
  regulatoryStandards: '/regulatory-standards',

  // Health Index
  healthIndex: '/health-index',
};

export default API;
