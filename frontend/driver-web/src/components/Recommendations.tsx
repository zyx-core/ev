import { useState, useEffect } from 'react';
import { api } from '../api';
import type { ChargingStation, RankedStation } from '../api';
import { Sparkles, MapPin, Zap, Battery } from 'lucide-react';

export default function Recommendations({ onSelect }: { onSelect: (station: ChargingStation) => void }) {
  const [recommendations, setRecommendations] = useState<RankedStation[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Prefs
  const [batterySoc, setBatterySoc] = useState(40);
  const [maxDistance, setMaxDistance] = useState(25);

  const loadRecs = async () => {
    try {
      setLoading(true);
      const data = await api.getRecommendations({
        user_location: { latitude: 12.9716, longitude: 77.5946 },
        battery_soc: batterySoc,
        max_distance_km: maxDistance
      });
      setRecommendations(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRecs();
  }, [batterySoc, maxDistance]);

  return (
    <div style={{ padding: '16px' }}>
      {/* AI Preferences Panel */}
      <div className="card bg-gradient-primary" style={{ position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'relative', zIndex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Sparkles size={20} color="white" />
            <span style={{ fontWeight: 700, fontSize: '1.1rem', color: 'white' }}>AI Routing Engine</span>
          </div>
          
          <div style={{ marginBottom: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: 'rgba(255,255,255,0.8)' }}>
              <span>Battery Level</span>
              <span style={{ fontWeight: 600 }}>{batterySoc}%</span>
            </div>
            <div className="slider-container" style={{ marginTop: '8px' }}>
              <input type="range" min="5" max="100" value={batterySoc} onChange={e => setBatterySoc(Number(e.target.value))} />
            </div>
          </div>
          
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: 'rgba(255,255,255,0.8)' }}>
              <span>Max Range</span>
              <span style={{ fontWeight: 600 }}>{maxDistance} km</span>
            </div>
            <div className="slider-container" style={{ marginTop: '8px' }}>
              <input type="range" min="1" max="100" value={maxDistance} onChange={e => setMaxDistance(Number(e.target.value))} />
            </div>
          </div>
        </div>
        {/* Decorative background element */}
        <div style={{ position: 'absolute', right: '-20px', bottom: '-20px', opacity: 0.1 }}>
          <Zap size={140} color="white" />
        </div>
      </div>

      <h2 style={{ fontSize: '1.1rem', fontWeight: 600, margin: '24px 0 16px 0' }}>Top Matches</h2>

      {loading ? (
        <div className="loader"></div>
      ) : recommendations.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>No matches found in range.</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {recommendations.map((rec, i) => {
            const rankColors = [
              'linear-gradient(135deg, #FFD700 0%, #FFA500 100%)', // Gold
              'linear-gradient(135deg, #E2E8F0 0%, #94A3B8 100%)', // Silver
              'linear-gradient(135deg, #FDBA74 0%, #C2410C 100%)', // Bronze
            ];
            const rankBg = i < 3 ? rankColors[i] : 'var(--bg-hover)';
            const scorePct = Math.round(rec.score * 100);

            return (
              <div key={rec.station.id} className={`card animate-slide-up delay-${(i % 3) + 1}`} onClick={() => onSelect(rec.station)}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div style={{ 
                    width: '40px', height: '40px', borderRadius: '12px', background: rankBg,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontWeight: 'bold', color: i < 3 ? '#000' : 'var(--text-secondary)'
                  }}>
                    #{i + 1}
                  </div>
                  
                  <div style={{ flex: 1 }}>
                    <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>{rec.station.name}</h3>
                    
                    <div style={{ display: 'flex', gap: '12px', fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><MapPin size={12}/> {rec.distance_km.toFixed(1)} km</span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Zap size={12}/> {Math.max(...rec.station.connectors.map(c => c.power_kw))} kW</span>
                    </div>

                    <div style={{ marginTop: '10px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{ flex: 1, height: '6px', background: 'var(--bg-hover)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ 
                          height: '100%', width: `${scorePct}%`, 
                          background: `interpolate(var(--accent-danger), var(--accent-success), ${rec.score})`, // fallback to green
                          backgroundColor: rec.score > 0.7 ? 'var(--accent-success)' : rec.score > 0.4 ? 'var(--accent-warning)' : 'var(--accent-danger)'
                        }}></div>
                      </div>
                      <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>{scorePct}%</span>
                    </div>
                  </div>

                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>₹{rec.station.pricing.effective_rate.toFixed(1)}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>/kWh</div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
