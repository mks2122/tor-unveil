import React from 'react';
import { GuardNode } from '../services/api';

interface GuardNodeTableProps {
  guards: GuardNode[];
}

const GuardNodeTable: React.FC<GuardNodeTableProps> = ({ guards }) => {
  return (
    <div className="guard-table-container">
      <h2>Top Probable Entry Nodes</h2>
      <div className="table-wrapper">
        <table className="guard-table">
          <thead>
            <tr>
              <th>Rank</th>
              <th>Nickname</th>
              <th>Fingerprint</th>
              <th>Confidence Score</th>
              <th>Similarity</th>
              <th>Country</th>
              <th>Bandwidth</th>
              <th>Uptime (days)</th>
            </tr>
          </thead>
          <tbody>
            {guards.map((guard, index) => (
              <tr key={guard.fingerprint}>
                <td className="rank">{index + 1}</td>
                <td className="nickname">{guard.nickname}</td>
                <td className="fingerprint" title={guard.fingerprint}>
                  {guard.fingerprint.substring(0, 16)}...
                </td>
                <td className="confidence">
                  <div className="confidence-bar-container">
                    <div
                      className="confidence-bar"
                      style={{ width: `${guard.confidence_score}%` }}
                    />
                    <span className="confidence-text">
                      {guard.confidence_score.toFixed(2)}%
                    </span>
                  </div>
                </td>
                <td className="similarity">
                  {(guard.similarity_score * 100).toFixed(2)}%
                </td>
                <td className="country">
                  {guard.country} {guard.country_name}
                </td>
                <td className="bandwidth">
                  {formatBandwidth(guard.bandwidth)}
                </td>
                <td className="uptime">
                  {Math.floor(guard.uptime / 86400)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const formatBandwidth = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
};

export default GuardNodeTable;
