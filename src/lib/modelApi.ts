const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Area = {
  area_id: number;
  area_name: string;
  population: number;
};

export type Prediction = {
  area_sqm: number;
  rent_egp: number;
  rent_per_sqm: number;
  category: string;
  area_name: string;
  population: number;
  competitors_500m: number;
  competitors_1km: number;
  suitability_score: number;
  tier: string;
  recommended: boolean;
};

export type Recommendation = {
  area_id: number;
  area_name: string;
  population: number;
  suitability_score: number;
  tier: string;
  estimated_rent: number;
  avg_rent_per_sqm: number;
  competitors_500m: number;
  competitors_1km: number;
  recommended: boolean;
};

export type RecommendResult = {
  query: { category: string; max_rent: number; area_sqm: number };
  total_areas_evaluated: number;
  recommendations: Recommendation[];
  best: Recommendation | null;
};

export interface ProfitAnalysis {
  estimated_monthly_customers: number;
  avg_transaction_egp: number;
  estimated_monthly_revenue: number;
  monthly_rent: number;
  monthly_labor: number;
  monthly_utilities: number;
  monthly_marketing: number;
  total_monthly_costs: number;
  estimated_monthly_profit: number;
  profit_margin_pct: number;
  initial_investment_egp: number;
  estimated_payback_months: number;
  penetration_rate_pct: number;
}

export type AnalysisResult = {
  current_area: {
    area_id: number;
    area_name: string;
    population: number;
    suitability_score: number;
    tier: string;
    recommended: boolean;
    rent_per_sqm: number;
    affordability: number;
    competitors_500m: number;
    competitors_1km: number;
    traffic_score?: number;
    accessibility_score?: number;
    reason?: string;
    profit_analysis?: ProfitAnalysis;
  };
  rankings: {
    area_id: number;
    area_name: string;
    population: number;
    suitability_score: number;
    tier: string;
    estimated_rent: number;
    competitors_500m: number;
    competitors_1km?: number;
    traffic_score?: number;
    accessibility_score?: number;
    reason?: string;
    profit_analysis?: ProfitAnalysis;
  }[];
  best: {
    area_id: number;
    area_name: string;
    population: number;
    suitability_score: number;
    tier: string;
    estimated_rent: number;
    rent_per_sqm?: number;
    competitors_500m: number;
    competitors_1km?: number;
    traffic_score?: number;
    accessibility_score?: number;
    reason?: string;
    profit_analysis?: ProfitAnalysis;
  } | null;
};

async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error: ${res.status}`);
  }
  return res.json();
}

export const modelApi = {
  getAreas: () => fetchApi<{ areas: Area[]; count: number }>("/areas"),

  getCategories: () =>
    fetchApi<{ categories: string[]; count: number }>("/categories"),

  predict: (data: {
    area_sqm: number;
    rent_egp: number;
    category: string;
    area_id?: number;
    comp_500m?: number;
    comp_1km?: number;
  }) =>
    fetchApi<Prediction>("/predict", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  recommend: (data: {
    category: string;
    max_rent: number;
    area_sqm: number;
    top_n?: number;
  }) =>
    fetchApi<RecommendResult>("/recommend", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  analyze: (data: {
    area_id: number;
    category: string;
    rent_budget: number;
    area_sqm: number;
    min_population?: number;
  }) =>
    fetchApi<AnalysisResult>("/analyze", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  health: () => fetchApi<{ status: string }>("/health"),

  getExportUrl: (endpoint: string) => `${API_BASE}${endpoint}`,
};
