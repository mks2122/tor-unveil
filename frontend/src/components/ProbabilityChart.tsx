import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from 'recharts';
import { GuardNode } from '../services/api';

interface ProbabilityChartProps {
  guards: GuardNode[];
}

const ProbabilityChart: React.FC<ProbabilityChartProps> = ({ guards }) => {
  const chartData = guards.map((guard, index) => ({
    name: guard.nickname,
    confidence: parseFloat(guard.confidence_score.toFixed(2)),
    similarity: parseFloat((guard.similarity_score * 100).toFixed(2)),
    rank: index + 1
  }));

  const COLORS = [
    '#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8',
    '#82CA9D', '#FFC658', '#8DD1E1', '#D084D0', '#A4DE6C'
  ];

  return (
    <div className="probability-chart-container">
      <h2>Probability Distribution</h2>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
          <YAxis label={{ value: 'Score (%)', angle: -90, position: 'insideLeft' }} />
          <Tooltip />
          <Legend />
          <Bar dataKey="confidence" name="Confidence Score" fill="#8884d8">
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Bar>
          <Bar dataKey="similarity" name="Similarity Score" fill="#82ca9d" />
        </BarChart>
      </ResponsiveContainer>
      
      <div className="chart-explanation">
        <p>
          <strong>Confidence Score:</strong> Combined probability based on traffic correlation 
          similarity, relay bandwidth, uptime, and consensus weight.
        </p>
        <p>
          <strong>Similarity Score:</strong> Pure traffic pattern correlation using Dynamic 
          Time Warping (DTW) between entry and exit patterns.
        </p>
      </div>
    </div>
  );
};

export default ProbabilityChart;
