export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type Decision = "APPROVE" | "MANUAL_REVIEW" | "REJECT";

export interface RiskDriver {
  /** Model feature name. The dashboard renders the label per locale. */
  code: string;
  contribution: number;
}

export interface PortfolioSummary {
  total_customers: number;
  avg_probability_of_default: number;
  active_alerts: number;
  risk_level_distribution: Record<string, number>;
}

export interface Signal {
  code: string;
  params: Record<string, number>;
}

export interface Alert {
  id: number;
  customer_id: number;
  previous_risk_level: RiskLevel;
  current_risk_level: RiskLevel;
  previous_pd: number;
  current_pd: number;
  signals: Signal[];
  recommended_action: string;
  resolved: boolean;
  created_at: string;
}

export interface Customer {
  customer_id: number;
  age: number;
  occupation: string;
  income: number;
  employment_years: number;
  credit_history_years: number;
  num_existing_loans: number;
  total_debt: number;
  credit_utilization: number;
  account_balance: number;
  latest_risk_score: number | null;
  latest_pd: number | null;
  latest_risk_level: RiskLevel | null;
}

export interface RiskHistoryPoint {
  month_index: number;
  credit_utilization: number;
  account_balance: number;
}

export interface PredictRiskRequest {
  age: number;
  occupation: string;
  income: number;
  employment_years: number;
  credit_history_years: number;
  num_existing_loans: number;
  num_credit_inquiries_6m: number;
  total_debt: number;
  monthly_payment: number;
  credit_utilization: number;
  num_late_payments: number;
  account_balance: number;
  transaction_intensity: number;
  loan_amount: number;
}

export interface DecisionResult {
  risk_score: number;
  probability_of_default: number;
  risk_level: RiskLevel;
  decision: Decision;
  suggested_interest_rate: number | null;
  approved_amount: number | null;
  key_risk_drivers: RiskDriver[];
  reason_codes: string[];
}

export interface CreditDecisionResult extends DecisionResult {
  customer_id: number;
}

export interface CalibrationCurve {
  mean_predicted: number[];
  fraction_positive: number[];
}

export interface ModelMetricEntry {
  roc_auc: number;
  pr_auc: number;
  gini: number;
  ks_statistic: number;
  brier_score: number;
  precision: number;
  recall: number;
  f1: number;
  decision_threshold: number;
  default_rate_actual: number;
  default_rate_predicted: number;
  calibration_curve: CalibrationCurve;
}

export interface ModelMetricsResponse {
  champion_model: string;
  model_version: string | null;
  trained_at: string | null;
  comparison: Record<string, ModelMetricEntry>;
  n_train: number;
  n_test: number;
}

export interface FeatureDriftEntry {
  psi: number;
  severity: "LOW" | "MEDIUM" | "HIGH";
}

export interface ModelMonitoringResponse {
  population_psi: number;
  feature_drift: Record<string, FeatureDriftEntry>;
  sample_size: number;
  risk_level_distribution: Record<string, number>;
}

export interface ExpectedLossResponse {
  lgd_assumption: number;
  total_exposure: number;
  total_expected_loss: number;
  expected_loss_ratio: number;
  expected_loss_by_risk_level: Record<string, number>;
  n_accounts: number;
}

export interface FairnessRow {
  occupation: string;
  n: number;
  avg_pd: number;
  approval_rate: number;
  adverse_impact_ratio: number;
  flagged: boolean;
}

export interface StressTestRequest {
  unemployment_shock_pp: number;
  rate_shock_pp: number;
  sample_size: number;
}

export interface StressTestResponse {
  baseline_avg_pd: number;
  stressed_avg_pd: number;
  avg_pd_delta_pp: number;
  baseline_risk_distribution: Record<string, number>;
  stressed_risk_distribution: Record<string, number>;
  baseline_expected_loss: ExpectedLossResponse;
  stressed_expected_loss: ExpectedLossResponse;
  sample_size: number;
}

// --- Real dataset (UCI) ---

export interface DatasetProvenance {
  name: string;
  source: string;
  url: string;
  citation: string;
  origin: string;
  n_customers: number;
  history_months: number;
  target: string;
  excluded_from_model: string[];
  excluded_reason: string;
}

export interface RealDatasetSummary {
  total_customers: number;
  avg_probability_of_default: number;
  actual_default_rate: number;
  risk_level_distribution: Record<string, number>;
  decision_distribution: Record<string, number>;
  expected_loss: ExpectedLossResponse;
  alert_count: number;
  early_warning_lookback_months: number;
}

export interface FairnessGroupRow {
  n: number;
  avg_pd: number;
  approval_rate: number;
  adverse_impact_ratio: number;
  insufficient_sample: boolean;
  flagged: boolean;
  [attribute: string]: string | number | boolean;
}

export type RealFairness = Record<string, FairnessGroupRow[]>;

export interface RealDatasetMetrics {
  real: ModelMetricsResponse & { dataset: string; base_default_rate: number };
  synthetic?: ModelMetricsResponse & { dataset?: string; base_default_rate?: number };
}

export interface RealAlert {
  customer_id: number;
  previous_risk_level: RiskLevel;
  current_risk_level: RiskLevel;
  previous_pd: number;
  current_pd: number;
  signals: Signal[];
  recommended_action: string;
}
