import { useState } from 'react';
import { Map, Zap, Settings, Search, BatteryCharging, ChevronLeft } from 'lucide-react';
import StationList from './components/StationList';
import Recommendations from './components/Recommendations';
import StationDetail from './components/StationDetail';
import type { ChargingStation } from './api';

export type ViewState = 'list' | 'recommendations' | 'detail';

function App() {
  const [view, setView] = useState<ViewState>('list');
  const [selectedStation, setSelectedStation] = useState<ChargingStation | null>(null);

  const navigateTo = (newView: ViewState, station?: ChargingStation) => {
    if (station) setSelectedStation(station);
    setView(newView);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header">
        <div className="header-title">
          {view === 'detail' && (
            <button 
              className="icon-btn" 
              onClick={() => setView('list')}
              style={{ marginRight: '12px' }}
            >
              <ChevronLeft size={24} />
            </button>
          )}
          {view === 'list' && <span>⚡ IEVC<span className="text-gradient">eco</span> Driver</span>}
          {view === 'recommendations' && <span>Smart Suggestions</span>}
          {view === 'detail' && <span>Station Details</span>}
        </div>
        
        <div className="header-actions">
          {view === 'list' && (
            <button className="icon-btn" onClick={() => navigateTo('recommendations')}>
              <Zap size={20} color="var(--accent-primary)" />
            </button>
          )}
          <button className="icon-btn">
            <Settings size={20} />
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="main-content">
        {view === 'list' && <StationList onSelect={(s) => navigateTo('detail', s)} />}
        {view === 'recommendations' && <Recommendations onSelect={(s) => navigateTo('detail', s)} />}
        {view === 'detail' && selectedStation && (
          <StationDetail station={selectedStation} />
        )}
      </main>

      {/* Floating Action / Bottom Nav */}
      {view === 'list' && (
        <button 
          className="fab animate-slide-up delay-3"
          onClick={() => navigateTo('recommendations')}
        >
          <Zap size={20} />
          <span>Get Recommendations</span>
        </button>
      )}
    </div>
  );
}

export default App;
