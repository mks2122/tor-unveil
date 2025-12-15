import React, { useState, useEffect } from 'react';
import GuardNodeTable from './GuardNodeTable';
import ProbabilityChart from './ProbabilityChart';
import PathDiagram from './PathDiagram';
import { runAnalysis, getRelayStats, refreshRelays, AnalysisResult, RelayStats } from '../services/api';

const Dashboard: React.FC = () => {
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [relayStats, setRelayStats] = useState<RelayStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [config, setConfig] = useState({
    simulation_count: 100,
    top_n: 10,
    random_seed: 42,
  });

  useEffect(() => {
    loadRelayStats();
  }, []);

  const loadRelayStats = async () => {
    try {
      const stats = await getRelayStats();
      setRelayStats(stats);
      
      // Don't auto-refresh in sample mode to prevent infinite loops
      // User can manually click "Refresh Relay Data" button
    } catch (err) {
      console.error('Failed to load relay stats:', err);
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
          </div>

          <GuardNodeTable guards={analysisResult.ranked_guards} />
          <ProbabilityChart guards={analysisResult.ranked_guards} />
          <PathDiagram />

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
    </div>
  );
};

export default Dashboard;
