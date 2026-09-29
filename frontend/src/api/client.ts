import axios from "axios";
import type {
  Alert,
  Customer,
  CreditDecisionResult,
  DecisionResult,
  ExpectedLossResponse,
  FairnessRow,
  ModelMetricsResponse,
  ModelMonitoringResponse,
  PortfolioSummary,
  PredictRiskRequest,
  RiskHistoryPoint,
  StressTestRequest,
  StressTestResponse,
  DatasetProvenance,
  RealDatasetSummary,
  RealDatasetMetrics,
  RealFairness,
  RealAlert,
} from "./types";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const client = axios.create({ baseURL: API_BASE_URL, timeout: 30000 });

export async function getPortfolioSummary() {
  return (await client.get<PortfolioSummary>("/portfolio/summary")).data;
}

export async function getAlerts(params: { risk_level?: string; resolved?: boolean; limit?: number } = {}) {
  return (await client.get<Alert[]>("/alerts", { params })).data;
}

export async function getCustomer(id: number) {
  return (await client.get<Customer>(`/customer/${id}`)).data;
}

export async function getCustomerHistory(id: number) {
  return (await client.get<RiskHistoryPoint[]>(`/customer/${id}/risk-history`)).data;
}

export async function postCreditDecision(customerId: number, requestedAmount: number) {
  return (
    await client.post<CreditDecisionResult>("/credit-decision", {
      customer_id: customerId,
      requested_amount: requestedAmount,
    })
  ).data;
}

export async function postPredictRisk(payload: PredictRiskRequest) {
  return (await client.post<DecisionResult>("/predict-risk", payload)).data;
}

export async function getModelMetrics() {
  return (await client.get<ModelMetricsResponse>("/model/metrics")).data;
}

export async function getModelMonitoring() {
  return (await client.get<ModelMonitoringResponse>("/model/monitoring")).data;
}

export async function getExpectedLoss() {
  return (await client.get<ExpectedLossResponse>("/portfolio/expected-loss")).data;
}

export async function getFairness() {
  return (await client.get<FairnessRow[]>("/portfolio/fairness")).data;
}

export async function postStressTest(payload: StressTestRequest) {
  return (await client.post<StressTestResponse>("/portfolio/stress-test", payload)).data;
}

// --- Real dataset (UCI) ---

export async function getRealProvenance() {
  return (await client.get<DatasetProvenance>("/real-dataset/provenance")).data;
}

export async function getRealSummary() {
  return (await client.get<RealDatasetSummary>("/real-dataset/summary")).data;
}

export async function getRealMetrics() {
  return (await client.get<RealDatasetMetrics>("/real-dataset/metrics")).data;
}

export async function getRealFairness() {
  return (await client.get<RealFairness>("/real-dataset/fairness")).data;
}

export async function getRealAlerts(limit = 25) {
  return (await client.get<RealAlert[]>("/real-dataset/alerts", { params: { limit } })).data;
}
