import { useState, useEffect, useCallback } from 'react';
import { dashboardApi, reservationsApi, stationsApi } from '../services/api';
import type { Station } from '../services/api';

export default function ReservationsView() {
    const [sessions, setSessions] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);

    // Modal Form State
    const [stations, setStations] = useState<Station[]>([]);
    const [formData, setFormData] = useState({
        station_id: '',
        user_email: 'test@example.com',
        user_name: 'Test User'
    });
    const [submitting, setSubmitting] = useState(false);

    const fetchData = useCallback(async () => {
        try {
            setLoading(true);
            const data = await dashboardApi.getRecentSessions(20);
            setSessions(data);
        } catch (err) {
            console.error("Failed to fetch sessions", err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    // Load stations when modal opens
    useEffect(() => {
        if (showModal && stations.length === 0) {
            stationsApi.getAll().then(setStations);
        }
    }, [showModal, stations.length]);

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.station_id) return;

        try {
            setSubmitting(true);
            await reservationsApi.create(formData);
            setShowModal(false);
            fetchData(); // Refresh list
            alert("Reservation created successfully!");
        } catch (err) {
            alert("Failed to create reservation");
            console.error(err);
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <>
            <header className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h1 className="page-title">Reservations & Sessions</h1>
                    <p className="page-subtitle">Manage charging bookings and active sessions</p>
                </div>
                <button className="btn-primary" onClick={() => setShowModal(true)}>
                    + New Reservation
                </button>
            </header>

            <div className="data-table-container">
                <div className="table-header">
                    <h2 className="table-title">Recent Activity</h2>
                    <button className="refresh-btn" onClick={fetchData} disabled={loading}>
                        {loading ? '↻' : '↻ Refresh'}
                    </button>
                </div>

                <table className="data-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Station</th>
                            <th>Status</th>
                            <th>Time</th>
                            <th>Energy</th>
                            <th>Cost</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sessions.length === 0 ? (
                            <tr><td colSpan={6} style={{ textAlign: 'center', padding: '40px' }}>No recent sessions found.</td></tr>
                        ) : (
                            sessions.map(s => (
                                <tr key={s.id}>
                                    <td style={{ fontFamily: 'monospace', color: 'var(--text-muted)' }}>
                                        {s.id.substring(0, 8)}...
                                    </td>
                                    <td>{s.station_id}</td>
                                    <td>
                                        <span className={`status-badge ${s.status === 'completed' ? 'available' :
                                            s.status === 'active' ? 'occupied' :
                                                s.status === 'reserved' ? 'reserved' : 'faulted'
                                            }`}>
                                            {s.status.toUpperCase()}
                                        </span>
                                    </td>
                                    <td>
                                        <div>{new Date(s.created_at).toLocaleDateString()}</div>
                                        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                                            {new Date(s.created_at).toLocaleTimeString()}
                                        </div>
                                    </td>
                                    <td>{s.energy_kwh} kWh</td>
                                    <td>₹{s.cost?.toFixed(2)}</td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Simple Modal */}
            {showModal && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    zIndex: 1000
                }}>
                    <div style={{
                        background: 'var(--bg-card)', padding: '24px', borderRadius: 'var(--radius-lg)',
                        width: '400px', border: '1px solid rgba(255,255,255,0.1)'
                    }}>
                        <h3 style={{ marginBottom: '16px' }}>Create Reservation</h3>
                        <form onSubmit={handleCreate} className="sim-form">
                            <div className="form-group">
                                <label>Select Station</label>
                                <select
                                    className="form-control"
                                    value={formData.station_id}
                                    onChange={e => setFormData({ ...formData, station_id: e.target.value })}
                                    required
                                >
                                    <option value="">-- Select Station --</option>
                                    {stations.map(s => (
                                        <option key={s.id} value={s.id}>{s.name} ({s.id})</option>
                                    ))}
                                </select>
                            </div>
                            <div className="form-group">
                                <label>User Email</label>
                                <input
                                    type="email" className="form-control"
                                    value={formData.user_email}
                                    onChange={e => setFormData({ ...formData, user_email: e.target.value })}
                                    required
                                />
                            </div>
                            <div style={{ display: 'flex', gap: '8px', marginTop: '16px' }}>
                                <button type="button" className="btn-primary" style={{ background: 'var(--bg-card-hover)' }} onClick={() => setShowModal(false)}>Cancel</button>
                                <button type="submit" className="btn-primary" disabled={submitting}>
                                    {submitting ? 'Creating...' : 'Confirm'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </>
    );
}
