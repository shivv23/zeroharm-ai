import React, { useState, useEffect, useCallback } from 'react';

const C = {
  bg: '#080c16', card: '#111827', border: '#1f2937', text: '#e0e5ec',
  muted: '#6b7280', accent: '#00e5ff', critical: '#ff1744', high: '#ff6d00',
  warning: '#ffa000', ok: '#00e676',
};

export default function PersonnelTracker() {
  const [locations, setLocations] = useState([]);
  const [occupancy, setOccupancy] = useState([]);
  const [mustering, setMustering] = useState(null);
  const [hazardExposure, setHazardExposure] = useState(null);
  const [activeTab, setActiveTab] = useState('locations');

  const fetchLocations = useCallback(async () => {
    try {
      const [locRes, occRes, hazRes] = await Promise.all([
        fetch('/api/personnel/locations').then(r => r.json()),
        fetch('/api/personnel/occupancy').then(r => r.json()),
        fetch('/api/personnel/hazard-exposure').then(r => r.json()),
      ]);
      setLocations((locRes.data || locRes).personnel || []);
      setOccupancy((occRes.data || occRes).zones || []);
      setHazardExposure(hazRes.data || hazRes);
    } catch { /* silent */ }
  }, []);

  useEffect(() => { fetchLocations(); }, [fetchLocations]);

  const triggerMustering = useCallback(async () => {
    try {
      const res = await fetch('/api/personnel/mustering/trigger?emergency_zone=Z01', { method: 'POST' });
      const json = await res.json();
      setMustering(json.data || json);
    } catch { /* silent */ }
  }, []);

  const musteringColor = mustering
    ? (mustering.mustering_pct >= 90 ? C.ok : mustering.mustering_pct >= 70 ? C.warning : C.critical)
    : C.muted;

  const tabStyle = (tab) => ({
    padding: '7px 14px', cursor: 'pointer', fontSize: 11, fontWeight: 600,
    borderBottom: `2px solid ${activeTab === tab ? C.accent : 'transparent'}`,
    color: activeTab === tab ? C.accent : C.muted,
    transition: 'all 0.2s',
  });

  return (
    <div style={{ padding: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: C.accent }}>
          {'\u{1F465}'} Personnel Safety Tracking
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', fontSize: 10, color: C.muted }}>
          <span>{locations.length} personnel</span>
          <button onClick={triggerMustering} style={{
            padding: '6px 14px', background: C.accent, color: '#000',
            border: 'none', borderRadius: 6, fontSize: 10, fontWeight: 600, cursor: 'pointer',
          }}>{'\u{1F6A8}'} Mustering Drill</button>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 0, borderBottom: `1px solid ${C.border}`, marginBottom: 12 }}>
        <div style={tabStyle('locations')} onClick={() => setActiveTab('locations')}>Locations</div>
        <div style={tabStyle('occupancy')} onClick={() => setActiveTab('occupancy')}>Zone Occupancy</div>
        <div style={tabStyle('mustering')} onClick={() => setActiveTab('mustering')}>
          Mustering {mustering ? `(${mustering.mustering_pct}%)` : ''}
        </div>
        <div style={tabStyle('hazard')} onClick={() => setActiveTab('hazard')}>
          Hazard Exposure {hazardExposure ? `(${hazardExposure.workers_with_exposure})` : ''}
        </div>
      </div>

      {activeTab === 'locations' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 8 }}>
          {locations.map((p, i) => {
            const mustered = p.mustered;
            return (
              <div key={i} style={{
                background: C.card, borderRadius: 6, border: `1px solid ${C.border}`,
                padding: '8px 12px', display: 'flex', justifyContent: 'space-between',
              }}>
                <div>
                  <div style={{ fontSize: 11, fontWeight: 600, color: C.text }}>{p.name}</div>
                  <div style={{ fontSize: 9, color: C.muted }}>{p.zone_name} ({p.zone_id})</div>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 2 }}>
                  <div style={{
                    width: 8, height: 8, borderRadius: '50%',
                    background: p.status === 'active' ? C.ok : C.muted,
                  }} />
                  <span style={{ fontSize: 8, color: mustered ? C.ok : C.critical }}>
                    {mustered ? 'Mustered' : 'Pending'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {activeTab === 'occupancy' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: 8 }}>
          {occupancy.map((z, i) => {
            const density = z.count / Math.max(locations.length, 1);
            return (
              <div key={i} style={{
                background: C.card, borderRadius: 6, border: `1px solid ${C.border}`, padding: 12,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: C.text }}>{z.zone_name}</span>
                  <span style={{ fontSize: 13, fontWeight: 700, color: C.accent }}>{z.count}</span>
                </div>
                <div style={{ height: 4, background: '#1a2332', borderRadius: 2 }}>
                  <div style={{
                    width: `${density * 100}%`, height: '100%', borderRadius: 2,
                    background: density > 0.2 ? C.critical : density > 0.1 ? C.high : C.accent,
                  }} />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {activeTab === 'mustering' && (
        <div>
          {mustering ? (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 16 }}>
                <div style={{ background: C.card, borderRadius: 8, border: `1px solid ${C.border}`, padding: 14, textAlign: 'center' }}>
                  <div style={{ fontSize: 22, fontWeight: 700, color: musteringColor }}>{mustering.mustering_pct}%</div>
                  <div style={{ fontSize: 10, color: C.muted }}>Mustered</div>
                </div>
                <div style={{ background: C.card, borderRadius: 8, border: `1px solid ${C.border}`, padding: 14, textAlign: 'center' }}>
                  <div style={{ fontSize: 22, fontWeight: 700, color: C.ok }}>{mustering.mustered}</div>
                  <div style={{ fontSize: 10, color: C.muted }}>Accounted For</div>
                </div>
                <div style={{ background: C.card, borderRadius: 8, border: `1px solid ${C.border}`, padding: 14, textAlign: 'center' }}>
                  <div style={{ fontSize: 22, fontWeight: 700, color: mustering.missing > 0 ? C.critical : C.ok }}>{mustering.missing}</div>
                  <div style={{ fontSize: 10, color: C.muted }}>Missing</div>
                </div>
              </div>
              {mustering.in_danger_zone?.length > 0 && (
                <div style={{ background: C.card, borderRadius: 8, border: `1px solid ${C.critical}`, padding: 14 }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: C.critical, marginBottom: 6 }}>
                    {'\u{26A0}\uFE0F'} Personnel in Danger Zone
                  </div>
                  {mustering.in_danger_zone.map((p, i) => (
                    <div key={i} style={{ fontSize: 10, color: C.muted, padding: '2px 0' }}>
                      {p.name} - {p.zone_name}
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div style={{ textAlign: 'center', padding: 30, color: C.muted, fontSize: 11 }}>
              Click "Mustering Drill" to simulate an emergency mustering scenario
            </div>
          )}
        </div>
      )}

      {activeTab === 'hazard' && hazardExposure && (
        <div>
          <div style={{ background: C.card, borderRadius: 8, border: `1px solid ${C.border}`, padding: 14, marginBottom: 12 }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: C.accent, marginBottom: 4 }}>
              Workers with High Hazard Exposure: {hazardExposure.workers_with_exposure}
            </div>
            <div style={{ fontSize: 10, color: C.muted }}>
              Personnel who have been in Extreme or High hazard zones during this shift
            </div>
          </div>
          <div style={{ display: 'grid', gap: 8 }}>
            {Object.entries(hazardExposure.details || {}).slice(0, 15).map(([name, info]) => (
              <div key={name} style={{
                background: C.card, borderRadius: 6, border: `1px solid ${C.border}`, padding: '8px 12px',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontSize: 11, fontWeight: 600, color: C.text }}>{name}</span>
                  <span style={{ fontSize: 10, color: info.high_hazard_exposures > 2 ? C.critical : C.high }}>
                    {info.high_hazard_exposures} high hazard exposure(s)
                  </span>
                </div>
                <div style={{ fontSize: 9, color: C.muted }}>
                  Total: {info.total_exposures} zone entries
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
