import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface AnalysisRequest {
  simulation_count: number;
  top_n: number;
  random_seed: number;
}

export interface GuardNode {
  fingerprint: string;
  nickname: string;
  probability_score: number;
  confidence_score: number;
  similarity_score: number;
  bandwidth: number;
  uptime: number;
  country: string;
  country_name: string;
  consensus_weight: number;
  component_scores: any;
}

export interface AnalysisResult {
  analysis_id: string;
  ranked_guards: GuardNode[];
  statistics: any;
  configuration: any;
  execution_time: number;
}

export interface RelayStats {
  total: number;
  guard: number;
  exit: number;
  middle: number;
}

export const runAnalysis = async (request: AnalysisRequest): Promise<AnalysisResult> => {
  const response = await api.post('/api/analysis/run', request);
  return response.data;
};

export const getRelayStats = async (): Promise<RelayStats> => {
  const response = await api.get('/api/relays/stats');
  return response.data;
};

export const refreshRelays = async (): Promise<any> => {
  const response = await api.post('/api/relays/refresh');
  return response.data;
};

export const getRecentAnalyses = async (limit: number = 10): Promise<any[]> => {
  const response = await api.get(`/api/analysis/?limit=${limit}`);
  return response.data;
};

export default api;
