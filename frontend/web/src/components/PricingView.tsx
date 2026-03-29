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
            const [ovData, stData, stratData] = await Promise.all([
                dashboardApi.getPricingOverview(),
                dashboardApi.getStationsStatus(),
                pricingApi.getCurrentStrategy()
            ]);
            setOverview(ovData);
            setStations(stData);
            setStrategy(stratData);
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

    return (
        <>
            <header className="page-header">
                <h1 className="page-title">Dynamic Pricing</h1>
                <p className="page-subtitle">Real-time MARL-based pricing optimization</p>
            </header>

            {/* Strategy Indicator */}
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
                            {strategy?.pricing_strategy || 'Loading...'}
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

            {/* Overview Cards */}
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
                                    <small style={{ color: 'var(--text-muted)' }}>{station.id}</small>
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
                                    <button className="btn-primary" style={{ padding: '6px 12px', fontSize: '12px' }}>Details</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </>
    );
}
