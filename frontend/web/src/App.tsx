import { useState, useEffect, useCallback } from 'react';
import { stationsApi, simulationApi } from './services/api';
import type { Station, SimulationResult, SimulationConfig } from './services/api';
import PricingView from './components/PricingView';
import ReservationsView from './components/ReservationsView';
import DemoView from './components/DemoView';
import GridStressView from './components/GridStressView';
import './App.css';

function App() {
  const [view, setView] = useState<'dashboard' | 'simulation' | 'pricing' | 'reservations' | 'demo' | 'grid'>('dashboard');
  const [stations, setStations] = useState<Station[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchStations = useCallback(async () => {
    try {
      if (stations.length === 0) setLoading(true);
      setError(null);
      const data = await stationsApi.getAll();
      setStations(data);
      setLastUpdated(new Date());
    } catch (err) {
      setError('Failed to fetch stations. Make sure the backend is running on port 8000.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStations();
    
    // Continuous SSE Stream for live demo
    const source = new EventSource('http://localhost:8000/api/v1/dashboard/stream');
    
    source.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setStations(data);
      setLastUpdated(new Date());
    };
    
    source.onerror = (err) => {
      console.warn("SSE Stream disconnected, falling back to polling.", err);
      source.close();
    };

    return () => source.close();
  }, [fetchStations]);

  const navItems = [
    { id: 'dashboard', icon: '📊', label: 'Monitoring' },
    { id: 'reservations', icon: '📅', label: 'Reservations' },
    { id: 'pricing', icon: '💰', label: 'Pricing' },
    { id: 'simulation', icon: '🎮', label: 'Simulation' },
    { id: 'grid', icon: '⚡', label: 'Grid Monitor' },
    { id: 'demo', icon: '🚀', label: 'Demo Control' },
  ];

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">⚡</div>
          <div>
            <h1>IEVC-eco</h1>
            <span>CPO Dashboard</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          {navItems.map(item => (
            <button
              key={item.id}
              onClick={() => setView(item.id as any)}
              className={`nav-item ${view === item.id ? 'active' : ''}`}
              style={{ width: '100%', border: 'none', textAlign: 'left', cursor: 'pointer', background: view === item.id ? 'var(--gradient-primary)' : 'transparent' }}
            >
              <span className="nav-icon">{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
      </aside>

      <main className="main-content">
        {view === 'dashboard' ? (
          <DashboardView
            stations={stations}
            loading={loading}
            error={error}
            lastUpdated={lastUpdated}
            onRefresh={fetchStations}
          />
        ) : view === 'pricing' ? (
          <PricingView />
        ) : view === 'reservations' ? (
          <ReservationsView />
        ) : view === 'demo' ? (
          <DemoView />
        ) : view === 'grid' ? (
          <GridStressView />
        ) : (
          <SimulationView />
        )}
      </main>
    </div>
  );
}

function DashboardView({ stations, loading, error, lastUpdated, onRefresh }: any) {
  const availableConnectors = stations?.reduce(
    (acc: any, s: any) => acc + (s.connectors?.filter((c: any) => c.status === 'available').length || 0),
    0
  ) || 0;

  const occupiedConnectors = stations?.reduce(
    (acc: any, s: any) => acc + (s.connectors?.filter((c: any) => c.status === 'occupied').length || 0),
    0
  ) || 0;

  const avgPrice = stations?.length > 0
    ? (stations.reduce((acc: any, s: any) => acc + (s.pricing?.effective_rate || 0), 0) / stations.length).toFixed(2)
    : '0.00';

  const getConnectorStatusSummary = (station: Station) => {
    const available = station.connectors?.filter(c => c.status === 'available').length || 0;
    const total = station.connectors?.length || 0;
    return `${available}/${total}`;
  };

  const getStationStatus = (station: Station) => {
    const available = station.connectors?.filter(c => c.status === 'available').length || 0;
    const total = station.connectors?.length || 0;
    if (total > 0 && available === total) return 'available';
    if (available === 0) return 'occupied';
    return 'available';
  };

  return (
    <>
      <header className="page-header">
        <h1 className="page-title">Station Monitoring</h1>
        <p className="page-subtitle">
          Real-time status of all charging stations • Last updated: {lastUpdated.toLocaleTimeString()}
        </p>
      </header>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-card-header">
            <div className="stat-card-icon blue">🔌</div>
            <span className="stat-change positive">+2 today</span>
          </div>
          <div className="stat-value">{stations.length}</div>
          <div className="stat-label">Total Stations</div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <div className="stat-card-icon green">✓</div>
          </div>
          <div className="stat-value">{availableConnectors}</div>
          <div className="stat-label">Available Connectors</div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <div className="stat-card-icon orange">⚡</div>
          </div>
          <div className="stat-value">{occupiedConnectors}</div>
          <div className="stat-label">In Use</div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <div className="stat-card-icon purple">₹</div>
          </div>
          <div className="stat-value">₹{avgPrice}</div>
          <div className="stat-label">Avg. Rate/kWh</div>
        </div>
      </div>

      <div className="data-table-container">
        <div className="table-header">
          <h2 className="table-title">All Charging Stations</h2>
          <button className="refresh-btn" onClick={onRefresh} disabled={loading}>
            {loading ? '↻ Refreshing...' : '↻ Refresh'}
          </button>
        </div>

        {error && <div className="error-message"><span>⚠️</span>{error}</div>}

        {loading && stations.length === 0 ? (
          <div className="loading-spinner"><div className="spinner"></div></div>
        ) : stations.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">🔌</div>
            <p>No stations found.</p>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Station Name</th>
                <th>Status</th>
                <th>Connectors</th>
                <th>Available</th>
                <th>Price</th>
                <th>Max Power</th>
              </tr>
            </thead>
            <tbody>
              {stations.map((station: any) => (
                <tr key={station.id}>
                  <td>
                    <strong>{station.name}</strong><br />
                    <small style={{ color: 'var(--text-muted)' }}>
                      {station.location?.latitude?.toFixed(4) || '0.0'}, {station.location?.longitude?.toFixed(4) || '0.0'}
                    </small>
                  </td>
                  <td>
                    <span className={`status-badge ${getStationStatus(station)}`}>
                      <span className={`status-dot ${getStationStatus(station)}`}></span>
                      {getStationStatus(station) === 'available' ? 'Online' : 'Busy'}
                    </span>
                  </td>
                  <td>
                    <div className="connector-chips">
                      {station.connectors?.map((c: any, i: number) => (
                        <span key={i} className={`connector-chip ${c.connector_type}`}>{c.connector_type}</span>
                      ))}
                    </div>
                  </td>
                  <td><strong>{getConnectorStatusSummary(station)}</strong></td>
                  <td>
                    <div className="price-cell">
                      <span className="price-value">₹{station.pricing?.effective_rate?.toFixed(2) || '0.00'}</span>
                      <span className={`price-multiplier ${station.pricing?.dynamic_multiplier > 1 ? 'high' : station.pricing?.dynamic_multiplier < 1 ? 'low' : ''}`}>
                        {station.pricing?.dynamic_multiplier !== 1 ? `${station.pricing?.dynamic_multiplier.toFixed(2)}x multiplier` : 'Standard rate'}
                      </span>
                    </div>
                  </td>
                  <td>
                    <strong>
                      {station.connectors?.length > 0 
                        ? Math.max(...station.connectors.map((c: any) => parseFloat(c.power_kw) || 0)) 
                        : 0} kW
                    </strong>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}

function SimulationView() {
  const [config, setConfig] = useState<SimulationConfig>({
    evs: 500,
    stations: 20,
    cpos: 5,
    steps: 144, // 12 hours
  });
  const [history, setHistory] = useState<SimulationResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeSim, setActiveSim] = useState<SimulationResult | null>(null);

  const fetchHistory = useCallback(async () => {
    try {
      const data = await simulationApi.getHistory();
      setHistory(data);

      // If there's a running simulation in history, poll it
      const running = data.find(s => s.status === 'running' || s.status === 'pending');
      if (running) {
        setActiveSim(running);
      }
    } catch (err) {
      console.error('Failed to fetch simulation history', err);
    }
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  // Polling for active simulation
  useEffect(() => {
    let interval: any;
    if (activeSim && (activeSim.status === 'running' || activeSim.status === 'pending')) {
      interval = setInterval(async () => {
        const status = await simulationApi.getStatus(activeSim.id);
        setActiveSim(status);
        if (status.status === 'completed' || status.status === 'failed') {
          fetchHistory();
          clearInterval(interval);
        }
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [activeSim, fetchHistory]);

  const handleRun = async () => {
    try {
      setLoading(true);
      const res = await simulationApi.run(config);
      const status = await simulationApi.getStatus(res.id);
      setActiveSim(status);
      fetchHistory();
    } catch (err) {
      alert('Failed to start simulation');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <header className="page-header">
        <h1 className="page-title">Simulation Control Center</h1>
        <p className="page-subtitle">Configure and run MARL stress tests with thousands of virtual EVs</p>
      </header>

      <div className="simulation-grid">
        <div className="sim-config-card">
          <h3>Simulation Parameters</h3>
          <div className="sim-form" style={{ marginTop: '20px' }}>
            <div className="form-group">
              <label>Number of EVs</label>
              <input
                type="range" min="100" max="5000" step="100"
                value={config.evs}
                onChange={e => setConfig({ ...config, evs: parseInt(e.target.value) })}
              />
              <div className="range-values"><span>100</span><strong>{config.evs} EVs</strong><span>5000</span></div>
            </div>

            <div className="form-group">
              <label>Stations</label>
              <input
                type="range" min="5" max="100" step="5"
                value={config.stations}
                onChange={e => setConfig({ ...config, stations: parseInt(e.target.value) })}
              />
              <div className="range-values"><span>5</span><strong>{config.stations} Stations</strong><span>100</span></div>
            </div>

            <div className="form-group">
              <label>Simulation Steps (5 min each)</label>
              <input
                type="range" min="12" max="576" step="12"
                value={config.steps}
                onChange={e => setConfig({ ...config, steps: parseInt(e.target.value) })}
              />
              <div className="range-values"><span>1h</span><strong>{Math.round(config.steps * 5 / 60)} Hours</strong><span>48h</span></div>
            </div>

            <button
              className="btn-primary"
              onClick={handleRun}
              disabled={loading || (activeSim?.status === 'running' || activeSim?.status === 'pending')}
            >
              {loading ? 'Initializing...' : activeSim?.status === 'running' ? 'Simulation Running...' : '🚀 Start Simulation'}
            </button>
          </div>

          {activeSim && activeSim.status === 'completed' && activeSim.results && (
            <div className="results-display">
              <h4 style={{ marginBottom: '16px' }}>Last Run Results</h4>
              <div className="results-grid">
                <div className="res-item">
                  <span className="res-label">Avg Price</span>
                  <span className="res-value">₹{activeSim.results.pricing.avg_price.toFixed(2)}</span>
                </div>
                <div className="res-item">
                  <span className="res-label">Grid Load</span>
                  <span className="res-value">{(activeSim.results.grid.avg_load * 100).toFixed(1)}%</span>
                </div>
                <div className="res-item">
                  <span className="res-label">Revenue</span>
                  <span className="res-value">₹{activeSim.results.revenue.total.toFixed(0)}</span>
                </div>
                <div className="res-item">
                  <span className="res-label">Wait Time</span>
                  <span className="res-value">{activeSim.results.utilization.avg_wait_time_minutes.toFixed(1)}m</span>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="sim-history-card">
          <h3 style={{ marginBottom: '20px' }}>Recent History</h3>
          {history.length === 0 ? (
            <p style={{ color: 'var(--text-secondary)' }}>No simulation history found.</p>
          ) : (
            <div className="sim-list">
              {history.map(sim => (
                <div key={sim.id} className="sim-item">
                  <div className="sim-info">
                    <h4>{sim.config.evs} EVs • {sim.config.stations} Stations</h4>
                    <p>{new Date(sim.created_at).toLocaleString()} • {Math.round(sim.config.steps * 5 / 60)}h Duration</p>
                  </div>
                  <div className="sim-actions">
                    <span className={`sim-status ${sim.status}`}>{sim.status}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

export default App;

