import { useState, useEffect } from 'react';
import { api } from '../api';
import type { ChargingStation } from '../api';
import { MapPin, Zap, Filter, CheckCircle, Navigation } from 'lucide-react';

interface Props {
  onSelect: (station: ChargingStation) => void;
}

export default function StationList({ onSelect }: Props) {
  const [stations, setStations] = useState<ChargingStation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [typeFilter, setTypeFilter] = useState<string | null>(null);
  const [radius, setRadius] = useState<number>(50);

  const loadStations = async () => {
    try {
      if (stations.length === 0) setLoading(true);
      const data = await api.getStations({
        lat: 12.9716, // Default Bangalore
        lon: 77.5946,
        radius_km: radius,
        connector_type: typeFilter || undefined
      });
      setStations(data);
      setError(null);
    } catch (err) {
      setError('Failed to load stations');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStations();
    
    // Continuous live stream
    const source = new EventSource('http://localhost:8000/api/v1/dashboard/stream');
    
    source.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setStations(data);
    };

    return () => source.close();
  }, [typeFilter, radius]);

  const availableConnectors = stations.reduce((acc, s) => acc + s.connectors.filter(c => c.status === 'available').length, 0);

  return (
    <div style={{ padding: '16px' }}>
      {/* Stats Row */}
      <div className="stats-row" style={{ borderRadius: '16px', marginBottom: '24px' }}>
        <div className="stat-item">
          <div className="stat-icon-wrapper" style={{ background: 'rgba(59, 130, 246, 0.15)' }}>
            <MapPin size={24} color="var(--accent-primary)" />
          </div>
          <span className="stat-value">{stations.length}</span>
          <span className="stat-label">Stations</span>
        </div>
        <div className="stat-item">
          <div className="stat-icon-wrapper" style={{ background: 'rgba(16, 185, 129, 0.15)' }}>
            <CheckCircle size={24} color="var(--accent-success)" />
          </div>
          <span className="stat-value">{availableConnectors}</span>
          <span className="stat-label">Available</span>
        </div>
        <div className="stat-item">
          <div className="stat-icon-wrapper" style={{ background: 'rgba(245, 158, 11, 0.15)' }}>
            <Zap size={24} color="var(--accent-warning)" />
          </div>
          <span className="stat-value">{stations.length === 0 ? 0 : (stations.reduce((acc, s) => acc + s.connectors.length, 0) - availableConnectors)}</span>
          <span className="stat-label">In Use</span>
        </div>
      </div>

      {/* Filters Overlay Toggle */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h2 style={{ fontSize: '1.2rem', fontWeight: 600 }}>Nearby Chargers</h2>
        <button className="icon-btn" onClick={() => {
          // simple inline filter toggle
          const nextType = typeFilter === null ? 'CCS2' : typeFilter === 'CCS2' ? 'Type2' : null;
          setTypeFilter(nextType);
        }}>
          <Filter size={20} color={typeFilter ? 'var(--accent-primary)' : 'var(--text-secondary)'} />
        </button>
      </div>

      {typeFilter && (
        <div style={{ marginBottom: '16px', display: 'flex', gap: '8px' }}>
          <span className={`chip ${typeFilter.toLowerCase()}`}>{typeFilter} Filter Active</span>
          <button style={{ background: 'transparent', border: 'none', color: 'var(--accent-danger)', cursor: 'pointer', fontSize: '12px' }} onClick={() => setTypeFilter(null)}>Clear</button>
        </div>
      )}

      {loading ? (
        <div className="loader"></div>
      ) : error ? (
        <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--accent-danger)' }}>{error}</div>
      ) : stations.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-secondary)' }}>
          <MapPin size={48} style={{ opacity: 0.5, marginBottom: '16px' }} />
          <p>No stations found nearby.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {stations.map((station, i) => {
            const avail = station.connectors.filter(c => c.status === 'available').length;
            const total = station.connectors.length;
            const maxKw = Math.max(...station.connectors.map(c => c.power_kw));
            const types = Array.from(new Set(station.connectors.map(c => c.connector_type)));

            return (
              <div 
                key={station.id} 
                className={`card animate-slide-up delay-${(i % 3) + 1}`}
                onClick={() => onSelect(station)}
              >
                <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start' }}>
                  <div className="bg-gradient-primary" style={{ padding: '12px', borderRadius: '12px' }}>
                    <Zap size={24} color="white" />
                  </div>
                  <div style={{ flex: 1 }}>
                    <h3 style={{ fontSize: '1.05rem', fontWeight: 600, marginBottom: '4px' }}>{station.name}</h3>
                    
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
                      <span className={`status-dot ${avail > 0 ? 'available' : 'occupied'}`}></span>
                      <span style={{ fontSize: '0.85rem', color: avail > 0 ? 'var(--accent-success)' : 'var(--accent-warning)', fontWeight: 500 }}>
                        {avail}/{total} available
                      </span>
                    </div>

                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                      {types.map(t => (
                        <span key={t} className={`chip ${t.toLowerCase()}`}>{t}</span>
                      ))}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>₹{station.pricing.effective_rate.toFixed(1)}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>/kWh</div>
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '16px', paddingTop: '12px', borderTop: '1px solid var(--border-color)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Zap size={14} /> {maxKw} kW max
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Navigation size={14} /> {station.location.latitude.toFixed(3)}, {station.location.longitude.toFixed(3)}
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
