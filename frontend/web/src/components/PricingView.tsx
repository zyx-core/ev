import { useState, useEffect, useCallback } from 'react';
import { dashboardApi, pricingApi } from '../services/api';

export default function PricingView() {
    const [overview, setOverview] = useState<any>(null);
    const [stations, setStations] = useState<any[]>([]);
    const [strategy, setStrategy] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    const fetchData = useCallback(async () => {
        try {
            setLoading(true);
            const ovTask = dashboardApi.getPricingOverview();
            const stTask = dashboardApi.getStationsStatus();
            const stratTask = pricingApi.getCurrentStrategy();

            const [ovRes, stRes, stratRes] = await Promise.allSettled([ovTask, stTask, stratTask]);

            if (ovRes.status === 'fulfilled') setOverview(ovRes.value);
            if (stRes.status === 'fulfilled') setStations(stRes.value);
            if (stratRes.status === 'fulfilled') setStrategy(stratRes.value);
        } catch (err) {
            console.error("Failed to fetch pricing data", err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 30000); // Refresh every 30s
        return () => clearInterval(interval);
    }, [fetchData]);

    const [selectedStation, setSelectedStation] = useState<any>(null);

    return (
        <>
            <header className="page-header">
                <h1 className="page-title">Dynamic Pricing</h1>
                <p className="page-subtitle">Real-time MARL-based pricing optimization</p>
            </header>
            
            {/* ... Strategy Banner as is ... */}
            <div className="strategy-banner" style={{
                background: 'var(--bg-card)',
                padding: '16px 24px',
                borderRadius: 'var(--radius-lg)',
                marginBottom: '24px',
                border: '1px solid rgba(139, 92, 246, 0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
            }}>
                <div>
                    <h3 style={{ fontSize: '16px', marginBottom: '4px' }}>Current Strategy</h3>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                        <span style={{ fontSize: '24px' }}>🤖</span>
                        <span style={{ fontSize: '20px', fontWeight: 'bold', color: 'var(--accent-secondary)' }}>
                            {strategy?.pricing_strategy || 'Balanced Load Optimization'}
                        </span>
                    </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Grid Status</div>
                    <div className={`status-badge ${strategy?.grid_status === 'critical' ? 'faulted' : strategy?.grid_status === 'high' ? 'occupied' : 'available'}`}>
                        {strategy?.grid_status?.toUpperCase() || 'NORMAL'}
                    </div>
                </div>
            </div>

            {/* Overview Cards ... as is ... */}
            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-card-header">
                        <div className="stat-card-icon blue">₹</div>
                    </div>
                    <div className="stat-value">₹{overview?.avg_effective_rate || '0.00'}</div>
                    <div className="stat-label">Avg Effective Rate</div>
                </div>

                <div className="stat-card">
                    <div className="stat-card-header">
                        <div className="stat-card-icon purple">📈</div>
                    </div>
                    <div className="stat-value">{overview?.avg_multiplier || '1.0'}x</div>
                    <div className="stat-label">Avg Multiplier</div>
                </div>

                <div className="stat-card">
                    <div className="stat-card-header">
                        <div className="stat-card-icon orange">⚡</div>
                    </div>
                    <div className="stat-value">₹{overview?.max_rate || '0.00'}</div>
                    <div className="stat-label">Max Rate</div>
                </div>

                <div className="stat-card">
                    <div className="stat-card-header">
                        <div className="stat-card-icon green">📉</div>
                    </div>
                    <div className="stat-value">₹{overview?.min_rate || '0.00'}</div>
                    <div className="stat-label">Min Rate</div>
                </div>
            </div>

            {/* Stations Pricing Table */}
            <div className="data-table-container">
                <div className="table-header">
                    <h2 className="table-title">Station Pricing</h2>
                    <button className="refresh-btn" onClick={fetchData} disabled={loading}>
                        {loading ? '↻...' : '↻ Refresh'}
                    </button>
                </div>

                <table className="data-table">
                    <thead>
                        <tr>
                            <th>Station</th>
                            <th>Base Rate</th>
                            <th>Multiplier</th>
                            <th>Effective Rate</th>
                            <th>Status</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {stations.map(station => (
                            <tr key={station.id}>
                                <td>
                                    <strong>{station.name}</strong><br />
                                    <small style={{ color: 'var(--text-muted)' }}>{station.id.substring(0, 8)}...</small>
                                </td>
                                <td>₹{station.current_rate ? (station.current_rate / station.price_multiplier).toFixed(2) : '-'}</td>
                                <td>
                                    <span className={`price-multiplier ${station.price_multiplier > 1 ? 'high' : station.price_multiplier < 1 ? 'low' : ''}`} style={{ fontWeight: 'bold', fontSize: '14px' }}>
                                        {station.price_multiplier}x
                                    </span>
                                </td>
                                <td>
                                    <strong style={{ fontSize: '16px' }}>₹{station.current_rate}</strong>
                                </td>
                                <td>
                                    <div className="connector-chips">
                                        <span className="connector-chip" style={{ background: 'rgba(255,255,255,0.05)' }}>
                                            {station.utilization}% Utilized
                                        </span>
                                    </div>
                                </td>
                                <td>
                                    <button 
                                        className="btn-primary" 
                                        style={{ padding: '6px 12px', fontSize: '12px' }}
                                        onClick={() => setSelectedStation(station)}
                                    >
                                        Details
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Reasoning Modal */}
            {selectedStation && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    zIndex: 1000
                }} onClick={() => setSelectedStation(null)}>
                    <div style={{
                        background: 'var(--bg-card)', padding: '32px', borderRadius: 'var(--radius-lg)',
                        width: '450px', border: '1px solid rgba(139, 92, 246, 0.4)',
                        position: 'relative'
                    }} onClick={e => e.stopPropagation()}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
                            <span style={{ fontSize: '32px' }}>🧠</span>
                            <div>
                                <h3 style={{ fontSize: '20px', color: 'var(--accent-secondary)' }}>AI Pricing Reasoning</h3>
                                <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{selectedStation.name}</p>
                            </div>
                        </div>

                        <div className="card" style={{ background: 'rgba(255,255,255,0.03)', marginBottom: '16px' }}>
                            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Logic Engine</div>
                            <div style={{ fontSize: '15px', fontWeight: 600 }}>{selectedStation.reasoning}</div>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                            <div className="card" style={{ background: 'rgba(255,255,255,0.03)' }}>
                                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Occupancy</div>
                                <div style={{ fontSize: '18px', fontWeight: 700 }}>{selectedStation.utilization}%</div>
                            </div>
                            <div className="card" style={{ background: 'rgba(255,255,255,0.03)' }}>
                                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Multiplier</div>
                                <div style={{ fontSize: '18px', fontWeight: 700 }}>{selectedStation.price_multiplier}x</div>
                            </div>
                        </div>

                        <button 
                            className="btn-primary" 
                            style={{ marginTop: '24px', width: '100%', background: 'rgba(139, 92, 246, 0.2)' }}
                            onClick={() => setSelectedStation(null)}
                        >
                            Close
                        </button>
                    </div>
                </div>
            )}
        </>
    );
}
