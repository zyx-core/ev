import React, { useState, useEffect, useCallback } from 'react';
import './GridStressView.css';

const API_BASE = 'http://localhost:8000/api/v1';

interface GridState {
  load_factor: number;
}

// Simulated transformer segments derived from a single grid load
function getTransformers(gridLoad: number) {
  return [
    { id: 'T-North', load: Math.min(1, gridLoad * 1.1 + Math.random() * 0.05) },
    { id: 'T-South', load: Math.min(1, gridLoad * 0.95 + Math.random() * 0.05) },
    { id: 'T-East',  load: Math.min(1, gridLoad * 1.05 + Math.random() * 0.05) },
    { id: 'T-West',  load: Math.min(1, gridLoad * 0.9  + Math.random() * 0.05) },
    { id: 'F-Grid1', load: Math.min(1, gridLoad * 1.15 + Math.random() * 0.05) },
    { id: 'F-Grid2', load: Math.min(1, gridLoad * 0.85 + Math.random() * 0.05) },
  ];
}

function getStatus(load: number): 'normal' | 'warn' | 'critical' {
  if (load > 0.85) return 'critical';
  if (load > 0.60) return 'warn';
  return 'normal';
}

export const GridStressView: React.FC = () => {
  const [gridState, setGridState] = useState<GridState>({ load_factor: 0.5 });
  const [transformers, setTransformers] = useState(getTransformers(0.5));
  const [lastUpdated, setLastUpdated] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  const fetchGridLoad = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/iot/grid/load`);
      if (!res.ok) throw new Error('Failed to fetch grid load');
      const data: GridState = await res.json();
      setGridState(data);
      setTransformers(getTransformers(data.load_factor));
      setLastUpdated(new Date().toLocaleTimeString());
      setError(null);
    } catch (e: any) {
      setError(e.message);
    }
  }, []);

  useEffect(() => {
    fetchGridLoad();
    const interval = setInterval(fetchGridLoad, 2000);
    return () => clearInterval(interval);
  }, [fetchGridLoad]);

  const globalLoad = gridState.load_factor;
  const globalStatus = getStatus(globalLoad);

  return (
    <div className="grid-stress-view">
      <div className="grid-header">
        <h2>⚡ Live Grid Stress Monitor</h2>
        <div className="grid-meta">
          {lastUpdated && <span>Last updated: {lastUpdated}</span>}
          {error && <span className="error-badge">⚠ {error}</span>}
        </div>
      </div>

      {/* Global gauge */}
      <div className={`global-gauge ${globalStatus}`}>
        <div className="gauge-label">Global Grid Load</div>
        <div className="gauge-bar-track">
          <div
            className={`gauge-bar-fill ${globalStatus}`}
            style={{ width: `${globalLoad * 100}%` }}
          />
        </div>
        <div className="gauge-value">{(globalLoad * 100).toFixed(1)}%</div>
        <div className={`status-pill ${globalStatus}`}>
          {globalStatus === 'normal' ? '🟢 Normal' : globalStatus === 'warn' ? '🟠 Warning' : '🔴 Critical'}
        </div>
      </div>

      {/* Transformer tiles */}
      <div className="transformer-grid">
        {transformers.map(t => {
          const status = getStatus(t.load);
          return (
            <div key={t.id} className={`transformer-tile ${status}`}>
              <div className="tile-label">{t.id}</div>
              <div className="tile-load-bar">
                <div
                  className={`tile-bar-fill ${status}`}
                  style={{ height: `${t.load * 100}%` }}
                />
              </div>
              <div className="tile-value">{(t.load * 100).toFixed(0)}%</div>
            </div>
          );
        })}
      </div>

      <div className="legend">
        <span className="legend-item normal">🟢 &lt;60% Normal</span>
        <span className="legend-item warn">🟠 60–85% Warning</span>
        <span className="legend-item critical">🔴 &gt;85% Critical</span>
      </div>
    </div>
  );
};

export default GridStressView;
