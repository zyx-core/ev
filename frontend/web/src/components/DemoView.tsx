import { useState } from 'react';
import { demoApi } from '../services/api';
import './DemoView.css';

export default function DemoView() {
    const [activeDemo, setActiveDemo] = useState<string | null>(null);
    const [logs, setLogs] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);

    const demos = [
        { id: '1', title: 'Station Discovery', description: 'Show all available stations with real-time pricing' },
        { id: '2', title: 'Dynamic Pricing', description: 'Demonstrate MARL-based pricing adjustments based on grid load' },
        { id: '3', title: 'Load Simulation', description: 'Simulate 20 concurrent EVs requesting charging stations' },
        { id: '4', title: 'Reservation Flow', description: 'Full flow: Reserve -> Blockchain Escrow -> Charge -> Payment' },
        { id: '5', title: 'Grid Dashboard', description: 'Show aggregated grid statistics and revenue' },
    ];

    const runDemo = async (id: string) => {
        try {
            setLoading(true);
            setActiveDemo(id);
            setLogs(['Initializing demo scenario...', 'Waiting for backend response...']);

            const response = await demoApi.run(id);
            setLogs(response.logs);
        } catch (err) {
            setLogs(prev => [...prev, '[ERROR] Failed to run demo. Check backend connection.']);
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            <header className="page-header">
                <h1 className="page-title">Live Demo Control</h1>
                <p className="page-subtitle">Execute backend demo scenarios and visualize the output logic</p>
            </header>

            <div className="demo-container">
                <div className="demo-list">
                    <h3>Scenarios</h3>
                    <div className="demo-buttons">
                        {demos.map(demo => (
                            <button
                                key={demo.id}
                                className={`demo-btn ${activeDemo === demo.id ? 'active' : ''}`}
                                onClick={() => runDemo(demo.id)}
                                disabled={loading}
                            >
                                <div className="demo-btn-header">
                                    <span className="demo-id">#{demo.id}</span>
                                    <strong>{demo.title}</strong>
                                </div>
                                <p>{demo.description}</p>
                            </button>
                        ))}
                    </div>
                </div>

                <div className="demo-console">
                    <div className="console-header">
                        <span>Console Output</span>
                        {loading && <span className="console-loading">Running...</span>}
                    </div>
                    <div className="console-content">
                        {logs.length === 0 ? (
                            <div className="console-empty">
                                Select a scenario to see the output logic.
                            </div>
                        ) : (
                            logs.map((log, i) => (
                                <div key={i} className="log-line">
                                    {log || '\u00A0'}
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </>
    );
}
