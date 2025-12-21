import React, { useState, useEffect } from 'react';
import GuardNodeTable from './GuardNodeTable';
import ProbabilityChart from './ProbabilityChart';
import PathDiagram from './PathDiagram';
import TimelineView from './TimelineView';
import { runAnalysis, getRelayStats, refreshRelays, getRealtimeAnalyses, AnalysisResult, RelayStats, RealtimeAnalysis } from '../services/api';

const Dashboard: React.FC = () => {
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [relayStats, setRelayStats] = useState<RelayStats | null>(null);
  const [realtimeAnalyses, setRealtimeAnalyses] = useState<RealtimeAnalysis[]>([]);
  const [selectedRealtime, setSelectedRealtime] = useState<RealtimeAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'simulated' | 'realtime'>('simulated');
  const [config, setConfig] = useState({
    simulation_count: 100,
    top_n: 10,
    random_seed: 42,
    guard_location: 'United States',
  });

  useEffect(() => {
    loadRelayStats();
    loadRealtimeAnalyses();
    
    // Auto-refresh realtime analyses every 10 seconds
    const interval = setInterval(() => {
      loadRealtimeAnalyses();
    }, 10000);
    
    return () => clearInterval(interval);
  }, []);

  const loadRelayStats = async () => {
    try {
      const stats = await getRelayStats();
      setRelayStats(stats);
    } catch (err) {
      console.error('Failed to load relay stats:', err);
    }
  };

  const loadRealtimeAnalyses = async () => {
    try {
      const data = await getRealtimeAnalyses(10);
      setRealtimeAnalyses(data.analyses);
    } catch (err) {
      console.error('Failed to load realtime analyses:', err);
    }
  };

  const handleRefreshRelays = async () => {
    try {
      setLoading(true);
      setError(null);
      await refreshRelays();
      await loadRelayStats();
      setError(null);
    } catch (err: any) {
      setError(`Failed to refresh relays: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRunAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await runAnalysis(config);
      console.log('Dashboard: Analysis result:', result);
      console.log('Dashboard: analysis_db_id:', result.analysis_db_id);
      setAnalysisResult(result);
    } catch (err: any) {
      setError(`Analysis failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleConfigChange = (key: string, value: number) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>🧅 TOR - Unveil: Peel the Onion</h1>
        <p className="subtitle">
          Analytical tool for Tor relay metadata and traffic pattern correlation
        </p>
        <div className="disclaimer">
          ⚠️ <strong>Research Tool Only</strong> - Uses synthetic traffic and public metadata. 
          No real traffic capture or user deanonymization.
        </div>
      </header>

      <div className="controls-panel">
        <div className="stats-section">
          <h3>Relay Statistics</h3>
          {relayStats && (
            <div className="stats-grid">
              <div className="stat-item">
                <div className="stat-value">{relayStats.total}</div>
                <div className="stat-label">Total Relays</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">{relayStats.guard}</div>
                <div className="stat-label">Guard Nodes</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">{relayStats.exit}</div>
                <div className="stat-label">Exit Nodes</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">{relayStats.middle}</div>
                <div className="stat-label">Middle Nodes</div>
              </div>
            </div>
          )}
          <button
            className="btn btn-secondary"
            onClick={handleRefreshRelays}
            disabled={loading}
          >
            Refresh Relay Data
          </button>
        </div>

        <div className="config-section">
          <h3>Analysis Configuration</h3>
          <div className="config-grid">
            <div className="config-item">
              <label>Simulation Count:</label>
              <input
                type="number"
                value={config.simulation_count}
                onChange={(e) => handleConfigChange('simulation_count', parseInt(e.target.value))}
                min="10"
                max="1000"
              />
            </div>
            <div className="config-item">
              <label>Top N Results:</label>
              <input
                type="number"
                value={config.top_n}
                onChange={(e) => handleConfigChange('top_n', parseInt(e.target.value))}
                min="1"
                max="50"
              />
            </div>
            <div className="config-item">
              <label>Random Seed:</label>
              <input
                type="number"
                value={config.random_seed}
                onChange={(e) => handleConfigChange('random_seed', parseInt(e.target.value))}
              />
            </div>
            <div className="config-item">
              <label>Simulated Guard Node Country:</label>
              <select
                value={config.guard_location}
                onChange={(e) => setConfig({...config, guard_location: e.target.value})}
                style={{ padding: '8px', borderRadius: '4px', border: '1px solid #444' }}
              >
                <option value="United States">🇺🇸 United States</option>
                <option value="Germany">🇩🇪 Germany</option>
                <option value="France">🇫🇷 France</option>
                <option value="Netherlands">🇳🇱 Netherlands</option>
                <option value="United Kingdom">🇬🇧 United Kingdom</option>
                <option value="Canada">🇨🇦 Canada</option>
                <option value="Sweden">🇸🇪 Sweden</option>
                <option value="Switzerland">🇨🇭 Switzerland</option>
                <option value="Austria">🇦🇹 Austria</option>
                <option value="Finland">🇫🇮 Finland</option>
                <option value="Norway">🇳🇴 Norway</option>
                <option value="Denmark">🇩🇰 Denmark</option>
                <option value="Belgium">🇧🇪 Belgium</option>
                <option value="Poland">🇵🇱 Poland</option>
                <option value="Czech Republic">🇨🇿 Czech Republic</option>
                <option value="Romania">🇷🇴 Romania</option>
                <option value="Russia">🇷🇺 Russia</option>
                <option value="Ukraine">🇺🇦 Ukraine</option>
                <option value="Japan">🇯🇵 Japan</option>
                <option value="South Korea">🇰🇷 South Korea</option>
                <option value="Singapore">🇸🇬 Singapore</option>
                <option value="Australia">🇦🇺 Australia</option>
                <option value="New Zealand">🇳🇿 New Zealand</option>
                <option value="India">🇮🇳 India</option>
                <option value="Brazil">🇧🇷 Brazil</option>
                <option value="Argentina">🇦🇷 Argentina</option>
                <option value="Mexico">🇲🇽 Mexico</option>
                <option value="South Africa">🇿🇦 South Africa</option>
                <option value="Israel">🇮🇱 Israel</option>
                <option value="Turkey">🇹🇷 Turkey</option>
              </select>
            </div>
          </div>
          <button
            className="btn btn-primary"
            onClick={handleRunAnalysis}
            disabled={loading || !relayStats || relayStats.guard === 0}
          >
            {loading ? 'Running Analysis...' : '▶ Run Analysis'}
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {analysisResult && (
        <div className="results-container">
          <div className="results-header">
            <h2>Analysis Results</h2>
            <div className="results-meta">
              <span>Analysis ID: {analysisResult.analysis_id.substring(0, 8)}...</span>
              <span>Execution Time: {analysisResult.execution_time.toFixed(2)}s</span>
              <span>
                Guards Analyzed: {analysisResult.configuration.total_guards_analyzed}
              </span>
            </div>
            <div className="export-buttons">
              <button 
                className="btn btn-export"
                onClick={() => window.open(`http://localhost:8000/api/export/json/${analysisResult.analysis_db_id || 'latest'}`, '_blank')}
              >
                📄 Export JSON
              </button>
              <button 
                className="btn btn-export"
                onClick={() => window.open(`http://localhost:8000/api/export/csv/${analysisResult.analysis_db_id || 'latest'}`, '_blank')}
              >
                📊 Export CSV
              </button>
              <button 
                className="btn btn-export"
                onClick={() => window.open(`http://localhost:8000/api/export/pdf/${analysisResult.analysis_db_id || 'latest'}`, '_blank')}
              >
                📑 Export Forensic Report (PDF)
              </button>
            </div>
          </div>

          <GuardNodeTable guards={analysisResult.ranked_guards} />
          <ProbabilityChart guards={analysisResult.ranked_guards} />
          
          <PathDiagram 
            entryNode={analysisResult.ranked_guards[0]?.fingerprint}
            exitNode="EXIT_NODE"
            entryCountry={analysisResult.ranked_guards[0]?.country}
            entryCountryName={analysisResult.ranked_guards[0]?.country_name}
          />

          <TimelineView analysisId={analysisResult.analysis_db_id ?? null} />

          <div className="statistics-summary">
            <h3>Statistical Summary</h3>
            <div className="stats-grid">
              <div className="stat-item">
                <div className="stat-value">
                  {analysisResult.statistics.avg_confidence.toFixed(2)}%
                </div>
                <div className="stat-label">Average Confidence</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">
                  {analysisResult.statistics.max_confidence.toFixed(2)}%
                </div>
                <div className="stat-label">Max Confidence</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">
                  {analysisResult.statistics.median_confidence.toFixed(2)}%
                </div>
                <div className="stat-label">Median Confidence</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {!analysisResult && !loading && relayStats && relayStats.guard > 0 && (
        <div className="welcome-message">
          <h2>Ready to Begin Analysis</h2>
          <p>
            Configure your analysis parameters above and click "Run Analysis" to identify 
            probable guard nodes based on synthetic traffic pattern correlation.
          </p>
          <PathDiagram />
        </div>
      )}

      {!analysisResult && !loading && relayStats && relayStats.total === 0 && (
        <div className="welcome-message">
          <h2>⚠️ No Relay Data Available</h2>
          <p>
            Click the <strong>"Refresh Relay Data"</strong> button above to load relay metadata.
          </p>
          <p>
            The application will load sample data or fetch live data from the Tor network 
            based on your DATA_SOURCE configuration.
          </p>
          <div className="info-box">
            <strong>Configuration:</strong> Check your .env file DATA_SOURCE setting
            <ul>
              <li><code>DATA_SOURCE=sample</code> - Use offline sample data</li>
              <li><code>DATA_SOURCE=live</code> - Fetch from Tor Onionoo API</li>
              <li><code>DATA_SOURCE=both</code> - Try live, fallback to sample</li>
            </ul>
          </div>
        </div>
      )}

      {/* Real-Time Analysis Section */}
      <div className="realtime-section">
        <h2>🔴 Real-Time Tor Traffic Analysis</h2>
        <p className="realtime-description">
          Live analysis results from honeypot captures. Access the honeypot via Tor Browser 
          through the ngrok URL to generate real traffic data.
        </p>
        
        <button 
          className="btn btn-secondary" 
          onClick={loadRealtimeAnalyses}
          style={{ marginBottom: '1rem' }}
        >
          🔄 Refresh Real-Time Results
        </button>

        {realtimeAnalyses.length === 0 ? (
          <div className="info-box">
            <strong>No real-time analyses yet.</strong>
            <p>To capture real Tor traffic:</p>
            <ol>
              <li>Start the honeypot: <code>python backend/honeypot_server.py</code></li>
              <li>Expose with ngrok: <code>ngrok http 5000</code></li>
              <li>Access the ngrok URL via <strong>Tor Browser</strong></li>
              <li>Click the page buttons to generate traffic</li>
            </ol>
          </div>
        ) : (
          <div className="realtime-results">
            <table className="realtime-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Exit IP</th>
                  <th>Top Guard</th>
                  <th>Probability</th>
                  <th>Country</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {realtimeAnalyses.map((analysis) => (
                  <tr key={analysis.analysis_id} className={selectedRealtime?.analysis_id === analysis.analysis_id ? 'selected' : ''}>
                    <td>{new Date(analysis.created_at).toLocaleTimeString()}</td>
                    <td><code>{analysis.exit_ip || 'N/A'}</code></td>
                    <td>
                      {analysis.ranked_guards?.[0]?.nickname || 'Unknown'}
                    </td>
                    <td>
                      <span className="probability-badge">
                        {((analysis.ranked_guards?.[0]?.probability || 0) * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td>{analysis.ranked_guards?.[0]?.country?.toUpperCase() || 'N/A'}</td>
                    <td>
                      <button 
                        className="btn btn-small"
                        onClick={() => setSelectedRealtime(analysis)}
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {selectedRealtime && (
              <div className="realtime-details">
                <h3>Analysis Details: {selectedRealtime.analysis_id.substring(0, 8)}...</h3>
                <div className="detail-grid">
                  <div><strong>Mode:</strong> {selectedRealtime.mode}</div>
                  <div><strong>Exit IP:</strong> {selectedRealtime.exit_ip || 'Unknown'}</div>
                  <div><strong>Exit Fingerprint:</strong> {selectedRealtime.exit_fingerprint?.substring(0, 16) || 'Unknown'}...</div>
                  <div><strong>Execution Time:</strong> {selectedRealtime.execution_time?.toFixed(2) || 0}s</div>
                </div>
                
                <h4>Top 5 Probable Guards:</h4>
                <table className="guards-mini-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Nickname</th>
                      <th>Fingerprint</th>
                      <th>Probability</th>
                      <th>Country</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedRealtime.ranked_guards?.slice(0, 5).map((guard: any, idx: number) => (
                      <tr key={guard.fingerprint}>
                        <td>{idx + 1}</td>
                        <td>{guard.nickname}</td>
                        <td><code>{guard.fingerprint?.substring(0, 12)}...</code></td>
                        <td>{(guard.probability * 100).toFixed(2)}%</td>
                        <td>{guard.country?.toUpperCase()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                
                <button 
                  className="btn btn-secondary"
                  onClick={() => setSelectedRealtime(null)}
                  style={{ marginTop: '1rem' }}
                >
                  Close Details
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
