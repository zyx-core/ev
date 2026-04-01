import { useState } from 'react';
import { api } from '../api';
import type { ChargingStation } from '../api';
import { Zap, ArrowRightLeft, CreditCard } from 'lucide-react';

export default function StationDetail({ station }: { station: ChargingStation }) {
  const [v2gEnabled, setV2gEnabled] = useState(false);
  const [soc, setSoc] = useState(82);
  const [loading, setLoading] = useState(false);
  const [reserved, setReserved] = useState(false);
  const [bookingTime, setBookingTime] = useState(() => {
    const d = new Date();
    d.setHours(d.getHours() + 1);
    return d.toISOString().slice(0, 16);
  });
  const [showReserveBox, setShowReserveBox] = useState(false);
  const [selectedConnectorIndex, setSelectedConnectorIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const selectedConnector = station.connectors[selectedConnectorIndex];

  const handleReserve = async () => {
    try {
      setLoading(true);
      setError(null);
      await api.createReservation({
        station_id: station.id,
        connector_type: selectedConnector?.connector_type,
        scheduled_start: new Date(bookingTime).toISOString()
      });
      setReserved(true);
      setShowReserveBox(false);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleV2gToggle = async () => {
    try {
      setLoading(true);
      // Mock session ID for demo
      if (!v2gEnabled) {
        await api.enableV2g('demo-session-id');
      }
      setV2gEnabled(!v2gEnabled);
    } catch (e) {
      console.error(e);
      // allow toggle locally anyway for demo continuity
      setV2gEnabled(!v2gEnabled);
    } finally {
      setLoading(false);
    }
  };

  const sellableKwh = Math.max(0, (soc - 20) * 0.7); // 70kWh battery assumption, keep 20%
  const earnings = sellableKwh * (station.pricing.base_rate * 1.5); // Sell premium

  return (
    <div style={{ padding: '0' }}>
      {/* Hero Header */}
      <div style={{ 
        background: 'linear-gradient(to bottom, var(--bg-hover) 0%, var(--bg-primary) 100%)',
        padding: '32px 20px 20px',
        textAlign: 'center'
      }}>
        <div style={{ 
          width: '64px', height: '64px', borderRadius: '20px', 
          background: 'var(--glass-bg)', border: '1px solid var(--border-color)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          margin: '0 auto 16px'
        }}>
          <Zap size={32} color="var(--accent-primary)" />
        </div>
        <h1 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '8px' }}>{station.name}</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          {station.location.latitude.toFixed(4)}, {station.location.longitude.toFixed(4)}
        </p>
      </div>

      <div style={{ padding: '20px' }}>
        {/* Pay / Rate Card */}
        <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'relative', overflow: 'visible' }}>
          <div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', textTransform: 'uppercase' }}>Current Rate</div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
              <span style={{ fontSize: '1.8rem', fontWeight: 800 }}>₹{station.pricing.effective_rate.toFixed(1)}</span>
              <span style={{ color: 'var(--text-muted)' }}>/kWh</span>
            </div>
            {station.pricing.dynamic_multiplier !== 1 && (
              <div style={{ fontSize: '0.75rem', color: station.pricing.dynamic_multiplier > 1 ? 'var(--accent-danger)' : 'var(--accent-success)' }}>
                {station.pricing.dynamic_multiplier}x Dynamic Multiplier
              </div>
            )}
          </div>
          {reserved ? (
            <div style={{ textAlign: 'right' }}>
              <div style={{ color: 'var(--accent-success)', fontWeight: 700, fontSize: '1rem' }}>✓ Reserved</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Escrow Locked</div>
            </div>
          ) : (
            <button 
              className="btn-primary" 
              style={{ width: 'auto', padding: '12px 24px' }}
              onClick={() => setShowReserveBox(!showReserveBox)}
              disabled={loading}
            >
              {showReserveBox ? 'Close' : 'Reserve'}
            </button>
          )}

        </div>
        {error && <div style={{ color: 'var(--accent-danger)', fontSize: '0.8rem', marginTop: '8px' }}>⚠ {error}</div>}

        {/* V2G Panel */}

        {/* V2G Panel */}
        <div className="card animate-slide-up delay-1" style={{ 
          border: v2gEnabled ? '1px solid var(--accent-success)' : '1px solid var(--border-color)',
          background: v2gEnabled ? 'rgba(16, 185, 129, 0.05)' : 'var(--bg-card)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ArrowRightLeft size={20} color={v2gEnabled ? 'var(--accent-success)' : 'var(--text-secondary)'} />
              <span style={{ fontWeight: 600, fontSize: '1.1rem' }}>V2G Energy Trading</span>
            </div>
            
            {/* Custom iOS-like Switch */}
            <div 
              style={{ 
                width: '50px', height: '28px', borderRadius: '14px',
                background: v2gEnabled ? 'var(--accent-success)' : 'var(--bg-hover)',
                position: 'relative', cursor: 'pointer', transition: '0.3s'
              }}
              onClick={handleV2gToggle}
            >
              <div style={{
                position: 'absolute', top: '2px', left: v2gEnabled ? '24px' : '2px',
                width: '24px', height: '24px', borderRadius: '50%', background: 'white',
                transition: '0.3s', boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
              }} />
            </div>
          </div>

          {v2gEnabled && (
            <div className="animate-slide-up" style={{ borderTop: '1px solid var(--border-color)', paddingTop: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '8px' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Current Battery (SoC)</span>
                <span style={{ fontWeight: 600, color: 'var(--accent-success)' }}>{soc}%</span>
              </div>
              
              <div className="slider-container" style={{ marginBottom: '24px' }}>
                <input type="range" min="20" max="100" value={soc} onChange={e => setSoc(Number(e.target.value))} />
              </div>

              <div style={{ background: 'rgba(0,0,0,0.2)', padding: '16px', borderRadius: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Available to sell:</span>
                  <span style={{ fontWeight: 600 }}>~{sellableKwh.toFixed(1)} kWh</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Estimated Earnings:</span>
                  <span style={{ fontWeight: 700, color: 'var(--accent-success)', fontSize: '1.1rem' }}>+₹{earnings.toFixed(0)}</span>
                </div>
              </div>
              
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '12px', textAlign: 'center' }}>
                You are helping stabilize the local electrical grid! 🌱
              </p>
            </div>
          )}
        </div>

        {/* Connectors List */}
        <h3 style={{ fontSize: '1rem', fontWeight: 600, margin: '24px 0 12px 0' }}>Connectors</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {station.connectors.map((c, i) => (
            <div key={i} className="card" style={{ margin: 0, padding: '12px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span className={`chip ${c.connector_type.toLowerCase()}`}>{c.connector_type}</span>
                <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{c.power_kw} kW</span>
              </div>
              <span style={{ 
                fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', padding: '4px 8px', borderRadius: '4px',
                background: c.status === 'available' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                color: c.status === 'available' ? 'var(--accent-success)' : 'var(--accent-warning)'
              }}>
                {c.status}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* New Centered Modal (Flex Centered) */}
      {showReserveBox && !reserved && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, 
          zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center',
          padding: '20px'
        }}>
          {/* Backdrop Overlay */}
          <div 
            style={{ 
              position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, 
              background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(10px)',
              animation: 'fadeIn 0.3s ease'
            }}
            onClick={() => setShowReserveBox(false)}
          />
          
          {/* Centered Modal Box */}
          <div className="animate-slide-up" style={{
            position: 'relative', zIndex: 10000, width: '100%', maxWidth: '380px',
            background: 'var(--bg-card)', border: '1px solid var(--border-color)', 
            borderRadius: '28px', padding: '28px', boxShadow: '0 40px 100px rgba(0,0,0,0.8)', 
            backdropFilter: 'blur(30px)', boxSizing: 'border-box'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <h4 style={{ margin: 0, fontSize: '1.3rem', fontWeight: 800, letterSpacing: '-0.02em' }}>Configure Reservation</h4>
              <button 
                onClick={() => setShowReserveBox(false)}
                style={{ 
                  background: 'var(--bg-hover)', border: 'none', color: 'var(--text-primary)', 
                  cursor: 'pointer', fontSize: '1.2rem', width: '32px', height: '32px', 
                  borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' 
                }}
              >
                &times;
              </button>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
              {/* Connector Selection */}
              <div>
                <label style={{ fontSize: '0.7rem', color: 'var(--accent-primary)', textTransform: 'uppercase', display: 'block', marginBottom: '8px', fontWeight: 700 }}>
                  Connector & Power
                </label>
                <select 
                  value={selectedConnectorIndex} 
                  onChange={(e) => setSelectedConnectorIndex(Number(e.target.value))}
                  style={{ 
                    width: '100%', padding: '14px', background: 'rgba(0,0,0,0.2)', 
                    border: '1px solid var(--border-color)', color: 'white', borderRadius: '14px',
                    fontSize: '1rem', appearance: 'none', cursor: 'pointer'
                  }}
                >
                  {station.connectors.map((c, i) => (
                    <option key={i} value={i}>
                      {c.connector_type} • {c.power_kw} kW • {c.status}
                    </option>
                  ))}
                </select>
              </div>

              {/* Booking Time */}
              <div>
                <label style={{ fontSize: '0.7rem', color: 'var(--accent-primary)', textTransform: 'uppercase', display: 'block', marginBottom: '8px', fontWeight: 700 }}>
                  Booking Time
                </label>
                <input 
                  type="datetime-local" 
                  value={bookingTime}
                  onChange={(e) => setBookingTime(e.target.value)}
                  style={{ 
                    width: '100%', padding: '14px', background: 'rgba(0,0,0,0.2)', 
                    border: '1px solid var(--border-color)', color: 'white', borderRadius: '14px',
                    fontSize: '1rem'
                  }}
                />
              </div>

              {/* Summary Visualization */}
              <div style={{ background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%)', padding: '20px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.05)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{ width: '42px', height: '42px', borderRadius: '12px', background: 'var(--glass-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Zap size={22} color="var(--accent-primary)" />
                  </div>
                  <div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Assigned Capacity</div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'white' }}>{selectedConnector?.power_kw} kW Fast Charge</div>
                  </div>
                </div>
              </div>

              <button 
                className="btn-primary" 
                style={{ width: '100%', padding: '16px', borderRadius: '16px', marginTop: '4px', fontSize: '1rem', fontWeight: 700 }}
                onClick={handleReserve}
                disabled={loading || selectedConnector?.status !== 'available'}
              >
                {loading ? 'Securing Slot...' : 'Confirm Reservation'}
              </button>
              
              {selectedConnector?.status !== 'available' && (
                <p style={{ color: 'var(--accent-danger)', fontSize: '0.8rem', margin: 0, textAlign: 'center', fontWeight: 500 }}>
                   Note: Selected connector is {selectedConnector?.status}
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
