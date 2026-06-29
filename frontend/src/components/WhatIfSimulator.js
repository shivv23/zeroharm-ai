import React, { useState, useEffect, useRef } from 'react';
import ws from '../store/websocketStore';

const WHAT_IF_TIMEOUT = 5000;

const SCENARIO_ICONS = {
  vizag_replay: '\u{1F4A5}',
  confined_space_near_miss: '\u{26B0}\uFE0F',
  gas_leak_cascade: '\u{1F4A8}',
  fire_scenario: '\u{1F525}',
  maintenance_mishap: '\u{1F527}',
};
import { PLANT_ZONES } from '../store/plantData';
import { COLORS, SENSOR_TYPES } from '../store/theme';

const ZONE_OPTIONS = PLANT_ZONES.map(z => z.id);
const SENSOR_OPTIONS = SENSOR_TYPES;

export default function WhatIfSimulator({ plantState }) {
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState(null);
  const [applied, setApplied] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showCustom, setShowCustom] = useState(false);
  const [customZone, setCustomZone] = useState('Z01');
  const [customSensor, setCustomSensor] = useState('CO');
  const [customLow, setCustomLow] = useState(50);
  const [customHigh, setCustomHigh] = useState(200);
  const [customPermit, setCustomPermit] = useState('Hot Work');
  const [customPermitRisk, setCustomPermitRisk] = useState('Critical');
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  useEffect(() => {
    ws.fetchAPI('/what-if/scenarios').then(data => {
      if (data?.scenarios) setScenarios(data.scenarios);
    });
  }, []);

  const handleApply = async (scenarioId) => {
    setLoading(true);
    setApplied(false);
    setShowCustom(false);
    setSelectedScenario(scenarioId);
    ws.send({ action: 'what_if_apply', scenario_id: scenarioId });
    const unsub = ws.on('what_if_applied', (d) => {
      if (!mountedRef.current) return;
      setResult(d.risk);
      setApplied(true);
      setLoading(false);
      unsub();
    });
    setTimeout(() => {
      if (!mountedRef.current) return;
      setLoading(false);
      unsub();
    }, WHAT_IF_TIMEOUT);
  };

  const handleCustomApply = async () => {
    setLoading(true);
    setApplied(false);
    setSelectedScenario(null);
    const changes = { [customZone]: { [customSensor]: [customLow, customHigh] } };
    const permits = [{ type: customPermit, zone_id: customZone, risk_level: customPermitRisk }];
    const data = await ws.fetchAPI('/what-if/custom', {
      method: 'POST',
      body: { name: `Custom: ${customSensor} in ${customZone}`, changes, permits_to_add: permits },
    });
    if (data && mountedRef.current) {
      setResult(data.risk);
      setApplied(true);
    }
    if (mountedRef.current) setLoading(false);
  };

  const handleReset = () => {
    setLoading(true);
    ws.send({ action: 'what_if_reset' });
    const unsub = ws.on('what_if_reset', (d) => {
      if (!mountedRef.current) return;
      setResult(null);
      setApplied(false);
      setSelectedScenario(null);
      setLoading(false);
      unsub();
    });
    setTimeout(() => {
      if (!mountedRef.current) return;
      setLoading(false);
      unsub();
    }, WHAT_IF_TIMEOUT);
  };

  const scenario = scenarios.find(s => s.id === selectedScenario);

  return (
    <div style={{ padding: 16, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 15, fontWeight: 700 }}>{'\u{1F9E9}'} What-If Scenario Simulator</div>
        <div style={{ fontSize: 10, color: COLORS.textMuted }}>Simulate safety-critical scenarios and observe AI response in real-time</div>
      </div>

      <div style={{ display: 'flex', gap: 12, flex: 1, overflow: 'hidden' }}>
        <div style={{ width: 260, display: 'flex', flexDirection: 'column', gap: 8, overflow: 'auto' }}>
          {scenarios.map(sc => {
            const isActive = selectedScenario === sc.id;
            const isApplied = applied && isActive;
            return (
              <div key={sc.id} style={{
                padding: '10px 12px', cursor: 'pointer', borderRadius: 8,
                background: isActive ? COLORS.bgAccentHover : COLORS.bgCard,
                border: `1px solid ${isApplied ? COLORS.borderCriticalStrong : isActive ? COLORS.borderInfo : COLORS.border}`,
                transition: 'all 0.2s',
              }} onClick={() => !loading && handleApply(sc.id)}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                  <span style={{ fontSize: 18 }}>{SCENARIO_ICONS[sc.id] || '\u{1F9E9}'}</span>
                  <span style={{ fontSize: 12, fontWeight: 600, color: isApplied ? COLORS.riskCritical : COLORS.text }}>{sc.name}</span>
                  {isApplied && <span style={{ fontSize: 9, color: COLORS.riskCritical, fontWeight: 700 }}>ACTIVE</span>}
                </div>
                <div style={{ fontSize: 10, color: COLORS.textMuted, lineHeight: 1.4 }}>{sc.description}</div>
                {sc.expected_alert && (
                  <div style={{ fontSize: 9, color: COLORS.riskElevated, marginTop: 4, fontStyle: 'italic' }}>
                    {'\u{1F4A1}'} {sc.expected_alert}
                  </div>
                )}
              </div>
            );
          })}
          <div style={{ padding: '10px 12px', cursor: 'pointer', borderRadius: 8,
                        background: showCustom ? COLORS.bgAccentHover : COLORS.bgCard,
                        border: `1px solid ${showCustom ? COLORS.borderInfo : COLORS.border}`,
                        transition: 'all 0.2s' }}
               onClick={() => { setShowCustom(!showCustom); setSelectedScenario(null); }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontSize: 18 }}>{'\u{1F3ED}'}</span>
              <span style={{ fontSize: 12, fontWeight: 600 }}>{'\u{002B}'} Custom Scenario</span>
            </div>
            <div style={{ fontSize: 10, color: COLORS.textMuted, marginTop: 4 }}>Build your own scenario with custom sensor values and permits</div>
          </div>
        </div>

        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 12 }}>
          {!scenario && !applied && !showCustom && (
            <div style={{ textAlign: 'center', padding: 40, color: COLORS.textMuted }}>
              <div style={{ fontSize: 40, marginBottom: 8 }}>{'\u{1F9E9}'}</div>
              <div style={{ fontSize: 13, fontWeight: 600 }}>Select a scenario</div>
              <div style={{ fontSize: 11, marginTop: 4 }}>Choose from the left or build a custom scenario</div>
            </div>
          )}

          {loading && (
            <div style={{ textAlign: 'center', padding: 30 }}>
              <div style={{ fontSize: 12, color: COLORS.accent, animation: 'pulse 1s infinite' }}>
                {applied ? 'Resetting...' : 'Applying...'}
              </div>
            </div>
          )}

          {showCustom && !applied && (
            <div style={{ background: COLORS.bgCard, borderRadius: 8, border: `1px solid ${COLORS.border}`, padding: 12 }}>
              <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>{'\u{1F3ED}'} Custom Scenario Builder</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div>
                  <div style={{ fontSize: 10, color: COLORS.textMuted, marginBottom: 3 }}>Zone</div>
                  <select value={customZone} onChange={e => setCustomZone(e.target.value)}
                          style={selectStyle}>
                    {ZONE_OPTIONS.map(z => <option key={z} value={z}>{z}</option>)}
                  </select>
                </div>
                <div>
                  <div style={{ fontSize: 10, color: COLORS.textMuted, marginBottom: 3 }}>Sensor Type</div>
                  <select value={customSensor} onChange={e => setCustomSensor(e.target.value)}
                          style={selectStyle}>
                    {SENSOR_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div>
                  <div style={{ fontSize: 10, color: COLORS.textMuted, marginBottom: 3 }}>Low Value</div>
                  <input type="number" value={customLow} onChange={e => setCustomLow(Number(e.target.value))}
                         style={inputStyle} />
                </div>
                <div>
                  <div style={{ fontSize: 10, color: COLORS.textMuted, marginBottom: 3 }}>High Value</div>
                  <input type="number" value={customHigh} onChange={e => setCustomHigh(Number(e.target.value))}
                         style={inputStyle} />
                </div>
                <div>
                  <div style={{ fontSize: 10, color: COLORS.textMuted, marginBottom: 3 }}>Permit Type</div>
                  <select value={customPermit} onChange={e => setCustomPermit(e.target.value)}
                          style={selectStyle}>
                    {['Hot Work','Confined Space Entry','Height Work','Electrical','Lockout-Tagout'].map(p => <option key={p} value={p}>{p}</option>)}
                  </select>
                </div>
                <div>
                  <div style={{ fontSize: 10, color: COLORS.textMuted, marginBottom: 3 }}>Permit Risk</div>
                  <select value={customPermitRisk} onChange={e => setCustomPermitRisk(e.target.value)}
                          style={selectStyle}>
                    {['Low','Medium','High','Critical'].map(r => <option key={r} value={r}>{r}</option>)}
                  </select>
                </div>
              </div>
              <div style={{ marginTop: 10 }}>
                <div onClick={handleCustomApply} style={{
                  padding: '8px 16px', background: COLORS.bgAccentActive,
                  border: `1px solid ${COLORS.borderInfo}`, borderRadius: 6,
                  cursor: 'pointer', textAlign: 'center',
                  fontSize: 12, fontWeight: 600, color: COLORS.accent,
                }}>
                  {'\u{25B6}'} Apply Custom Scenario
                </div>
              </div>
            </div>
          )}

          {scenario && applied && result && (
            <div style={{ background: COLORS.bgCard, borderRadius: 8, border: `1px solid ${COLORS.border}`, padding: 12 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: COLORS.riskCritical, marginBottom: 8 }}>
                {'\u{26A0}\uFE0F'} Scenario Active: {scenario.name}
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, marginBottom: 8 }}>
                <div style={{ textAlign: 'center', padding: 8, background: COLORS.bgCritical, borderRadius: 6 }}>
                  <div style={{ fontSize: 18, fontWeight: 700, color: COLORS.riskCritical }}>{(result.risk_score * 100).toFixed(0)}</div>
                  <div style={{ fontSize: 9, color: COLORS.textMuted }}>Risk Score</div>
                </div>
                <div style={{ textAlign: 'center', padding: 8, background: COLORS.bgHigh, borderRadius: 6 }}>
                  <div style={{ fontSize: 18, fontWeight: 700, color: COLORS.riskHigh, textTransform: 'uppercase' }}>{result.severity}</div>
                  <div style={{ fontSize: 9, color: COLORS.textMuted }}>Severity</div>
                </div>
                <div style={{ textAlign: 'center', padding: 8, background: COLORS.bgAccentStrong, borderRadius: 6 }}>
                  <div style={{ fontSize: 18, fontWeight: 700, color: COLORS.accent }}>{result.alerts?.length || 0}</div>
                  <div style={{ fontSize: 9, color: COLORS.textMuted }}>Alerts Fired</div>
                </div>
              </div>

              {result.alerts?.length > 0 && (
                <div>
                  <div style={{ fontSize: 11, fontWeight: 600, color: COLORS.textSecondary, marginBottom: 4 }}>Alerts Generated:</div>
                  {result.alerts.slice(0, 5).map((a, i) => (
                    <div key={i} style={{
                      padding: '6px 8px', background: COLORS.bgCriticalLight, borderRadius: 4, marginBottom: 3,
                      borderLeft: `3px solid ${COLORS.riskCritical}`, fontSize: 10, color: COLORS.textAlt,
                    }}>
                      <span style={{ color: COLORS.riskCritical, fontWeight: 600 }}>[{a.type}]</span> {a.message}
                    </div>
                  ))}
                </div>
              )}

              {result.compound_risks?.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: COLORS.riskCritical, marginBottom: 4 }}>
                    {'\u{1F525}'} Compound Risks Detected:
                  </div>
                  {result.compound_risks.map((cr, i) => (
                    <div key={i} style={{ fontSize: 10, color: COLORS.riskElevated, marginBottom: 2 }}>
                      {'\u{2022}'} {cr.recommendation?.substring(0, 100)}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {applied && (
            <div style={{ padding: '10px 16px', background: COLORS.bgNormal, borderRadius: 8,
                          border: `1px solid ${COLORS.borderNormal}`, cursor: 'pointer', textAlign: 'center' }}
                 onClick={handleReset}>
              <div style={{ fontSize: 12, fontWeight: 700, color: COLORS.riskNormal }}>{'\u{1F504}'} Reset to Normal Operations</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const selectStyle = {
  width: '100%', padding: '6px 8px', background: COLORS.bgElevated, color: COLORS.text,
  border: `1px solid ${COLORS.border}`, borderRadius: 4, fontSize: 11, outline: 'none',
};
const inputStyle = {
  width: '100%', padding: '6px 8px', background: COLORS.bgElevated, color: COLORS.text,
  border: `1px solid ${COLORS.border}`, borderRadius: 4, fontSize: 11, outline: 'none', boxSizing: 'border-box',
};
