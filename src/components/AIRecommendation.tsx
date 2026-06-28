"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import {
  Brain, Lightbulb, TrendingUp, Users, Banknote, Store,
  AlertTriangle, BarChart3, DollarSign, Clock, Target,
  CheckCircle2, XCircle, HelpCircle,
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, ResponsiveContainer,
  PieChart, Pie, Cell, Tooltip,
} from "recharts";

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

export interface AIRecommendationData {
  area_name: string;
  category: string;
  suitability_score: number;
  tier: string;
  population: number;
  estimated_rent: number;
  competitors_500m: number;
  recommended: boolean;
  rent_per_sqm?: number;
  traffic_score?: number;
  accessibility_score?: number;
  reason?: string;
  profit_analysis?: ProfitAnalysis;
}

interface AIRecommendationProps {
  data?: AIRecommendationData | null;
  loading?: boolean;
}

const PIE_COLORS = ["#6C3BFF", "#F59E0B", "#22C55E", "#94A3B8"];

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass-card-strong px-3 py-2 text-xs">
        <p style={{ color: payload[0].color }} className="font-semibold">
          {payload[0].name}: {payload[0].value?.toLocaleString()} EGP
        </p>
      </div>
    );
  }
  return null;
};

function FactorBar({ label, value, max, good, icon: Icon, color }: {
  label: string; value: number; max: number; good: "high" | "low" | "mid";
  icon: any; color: string;
}) {
  const pct = Math.min((value / max) * 100, 100);
  const isGood = good === "high" ? value >= max * 0.6
    : good === "low" ? value <= max * 0.4
    : value >= max * 0.4 && value <= max * 0.6;
  return (
    <div className="flex items-center gap-2">
      <Icon size={12} className="shrink-0" style={{ color }} />
      <div className="flex-1 min-w-0">
        <div className="flex justify-between text-[10px] mb-0.5">
          <span className="text-text-secondary truncate">{label}</span>
          <span className="font-medium">{value.toLocaleString()}</span>
        </div>
        <div className="h-1.5 rounded-full bg-deep-blue/50 overflow-hidden">
          <div className="h-full rounded-full transition-all duration-500"
            style={{ width: `${pct}%`, backgroundColor: color, opacity: isGood ? 0.8 : 0.4 }} />
        </div>
      </div>
      {isGood ? <CheckCircle2 size={10} className="text-success shrink-0" /> : <HelpCircle size={10} className="text-text-secondary shrink-0" />}
    </div>
  );
}

export default function AIRecommendation({ data, loading }: AIRecommendationProps) {
  const isLoading = loading || !data;

  const getScoreColor = (score: number) => {
    if (score >= 7.5) return "text-success";
    if (score >= 5.0) return "text-warning";
    return "text-danger";
  };

  const getScoreHex = (score: number) => {
    if (score >= 7.5) return "#22C55E";
    if (score >= 5.0) return "#F59E0B";
    return "#EF4444";
  };

  const profit = data?.profit_analysis;
  const traffic = data?.traffic_score ?? 5;
  const access = data?.accessibility_score ?? 5;

  const costPieData = useMemo(() => {
    if (!profit) return [];
    return [
      { name: "Rent", value: profit.monthly_rent, color: "#6C3BFF" },
      { name: "Labor", value: profit.monthly_labor, color: "#F59E0B" },
      { name: "Utilities", value: profit.monthly_utilities, color: "#22C55E" },
      { name: "Marketing", value: profit.monthly_marketing, color: "#94A3B8" },
    ];
  }, [profit]);

  const revCostData = useMemo(() => {
    if (!profit) return [];
    return [
      { name: "Revenue", value: profit.estimated_monthly_revenue, fill: "#22C55E" },
      { name: "Costs", value: profit.total_monthly_costs, fill: "#EF4444" },
      { name: "Profit", value: profit.estimated_monthly_profit, fill: "#6C3BFF" },
    ];
  }, [profit]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.6 }}
      className="glass-card p-5 relative overflow-hidden"
    >
      <div className="absolute top-0 right-0 w-32 h-32 bg-accent-purple opacity-[0.04] blur-[60px] rounded-full" />

      <div className="relative z-10">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-10 h-10 rounded-xl bg-accent-purple/20 border border-accent-purple/30 flex items-center justify-center">
            <Brain className="w-5 h-5 text-accent-purple" />
          </div>
          <div>
            <h3 className="font-heading text-lg font-semibold flex items-center gap-2">
              AI Recommendation
              <Lightbulb className="w-4 h-4 text-warning animate-pulse" />
            </h3>
            <p className="text-text-secondary text-xs">
              {isLoading ? "Run analysis to see results" : "AI model + real data analysis"}
            </p>
          </div>
        </div>

        {isLoading ? (
          <div className="glass-card bg-accent-purple/5 border-accent-purple/10 p-5 mb-4">
            <div className="animate-pulse space-y-3">
              <div className="h-6 bg-accent-purple/10 rounded w-3/4" />
              <div className="h-4 bg-accent-purple/5 rounded w-full" />
              <div className="grid grid-cols-3 gap-3 mt-4">
                {[1,2,3].map(i => <div key={i} className="h-16 bg-accent-purple/5 rounded-xl" />)}
              </div>
            </div>
          </div>
        ) : (
          <>
            {/* HEADER */}
            <div className="glass-card bg-accent-purple/5 border-accent-purple/10 p-4 mb-3">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-heading text-lg font-bold text-gradient">
                  {data.recommended ? "Best area to open" : "Analysis for"} {data.area_name}
                </h4>
                <div className={`flex items-center gap-1 ${getScoreColor(data.suitability_score)}`}>
                  <TrendingUp size={16} />
                  <span className="font-heading font-bold text-base">{data.suitability_score.toFixed(1)}</span>
                </div>
              </div>
              <p className="text-text-secondary text-xs leading-relaxed">
                {data.reason || `${data.category} — ${data.tier} tier.`}
              </p>
            </div>

            {/* AI SUMMARY */}
            <div className="glass-card bg-accent-purple/5 border-accent-purple/10 p-3 mb-3">
              <p className="text-[11px] text-text-secondary leading-relaxed">
                <span className="text-accent-purple font-semibold">Why {data.area_name}?</span>{" "}
                {data.reason ? (
                  data.reason.split(", ").map((part: string, i: number, arr: string[]) => (
                    <span key={i}>
                      {part.charAt(0).toUpperCase() + part.slice(1)}
                      {i < arr.length - 1 ? ", " : "."}
                    </span>
                  ))
                ) : (
                  <>
                    The AI recommends {data.area_name} for your {data.category.toLowerCase()} business
                    based on {data.suitability_score >= 7 ? "excellent" : data.suitability_score >= 5 ? "good" : "moderate"}
                    suitability scores ({data.suitability_score.toFixed(1)}/10, {data.tier} tier).
                  </>
                )}{" "}
                {data.population > 0 && `With ${(data.population / 1000).toFixed(0)}K residents${data.estimated_rent > 0 ? ` and estimated rent at ${data.estimated_rent.toLocaleString()} EGP` : ""}, `}
                {data.competitors_500m > 0 ? `there are ${data.competitors_500m} competitors within 500m.` : "competition is minimal."}{" "}
                {profit && `Projected profit is ${profit.estimated_monthly_profit.toLocaleString()} EGP/mo (${profit.profit_margin_pct}% margin) with ~${profit.estimated_payback_months}mo payback.`}
              </p>
            </div>

            {/* FACTOR BREAKDOWN */}
            <div className="glass-card bg-deep-blue/30 p-4 mb-3 space-y-2.5">
              <h5 className="font-heading text-xs font-semibold text-text-secondary uppercase tracking-wider flex items-center gap-1.5">
                <Target size={10} /> Factor Breakdown
              </h5>
              <FactorBar label="Population" value={data.population} max={50000} good="high" icon={Users} color="#8B5CF6" />
              <FactorBar label="Rent (EGP/m²)" value={data.estimated_rent} max={500} good="low" icon={Banknote} color="#F59E0B" />
              <FactorBar label="Competitors (500m)" value={data.competitors_500m} max={12} good="low" icon={Store} color="#EF4444" />
              <FactorBar label="Traffic Flow" value={Math.round(traffic * 10)} max={100} good="high" icon={BarChart3} color="#22C55E" />
              <FactorBar label="Accessibility" value={Math.round(access * 10)} max={100} good="high" icon={Target} color="#6C3BFF" />
            </div>

            {/* PROFIT PROJECTION */}
            {profit && (
              <div className="glass-card bg-deep-blue/30 p-4 mb-3">
                <h5 className="font-heading text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3 flex items-center gap-1.5">
                  <DollarSign size={10} /> Financial Projection
                </h5>

                {/* Revenue vs Costs vs Profit bar */}
                <div className="h-24 mb-3">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={revCostData} layout="vertical">
                      <XAxis type="number" hide />
                      <YAxis type="category" dataKey="name" tick={{ fill: "#94A3B8", fontSize: 10 }} width={55} />
                      <Tooltip content={<CustomTooltip />} />
                      <Bar dataKey="value" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Cost breakdown donut */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="h-20">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={costPieData} cx="50%" cy="50%" innerRadius={18} outerRadius={32} paddingAngle={2} dataKey="value">
                          {costPieData.map((entry, i) => (
                            <Cell key={i} fill={entry.color} stroke="rgba(255,255,255,0.05)" />
                          ))}
                        </Pie>
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="flex flex-col justify-center gap-0.5">
                    {costPieData.map(e => (
                      <div key={e.name} className="flex items-center gap-1.5 text-[9px]">
                        <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: e.color }} />
                        <span className="text-text-secondary">{e.name}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Key metrics grid */}
                <div className="grid grid-cols-2 gap-2 mt-3">
                  <div className="glass-card bg-deep-blue/50 p-2 text-center">
                    <div className="font-heading text-xs font-bold text-accent-purple">{profit.estimated_monthly_revenue.toLocaleString()}</div>
                    <div className="text-[8px] text-text-secondary">Mo. Revenue (EGP)</div>
                  </div>
                  <div className="glass-card bg-deep-blue/50 p-2 text-center">
                    <div className="font-heading text-xs font-bold" style={{ color: profit.profit_margin_pct > 20 ? "#22C55E" : "#F59E0B" }}>
                      {profit.profit_margin_pct}%
                    </div>
                    <div className="text-[8px] text-text-secondary">Profit Margin</div>
                  </div>
                  <div className="glass-card bg-deep-blue/50 p-2 text-center">
                    <div className="font-heading text-xs font-bold text-accent-purple">{profit.estimated_monthly_profit.toLocaleString()}</div>
                    <div className="text-[8px] text-text-secondary">Mo. Profit (EGP)</div>
                  </div>
                  <div className="glass-card bg-deep-blue/50 p-2 text-center">
                    <div className="font-heading text-xs font-bold" style={{ color: profit.estimated_payback_months < 18 ? "#22C55E" : "#F59E0B" }}>
                      {profit.estimated_payback_months}m
                    </div>
                    <div className="text-[8px] text-text-secondary">Payback Period</div>
                  </div>
                </div>
              </div>
            )}

            {/* TIP */}
            <div className={`flex items-start gap-2 p-3 rounded-xl ${
              data.recommended ? "bg-success/5 border border-success/10" : "bg-warning/5 border border-warning/10"
            }`}>
              {data.recommended ? (
                <Lightbulb className="w-4 h-4 text-success shrink-0 mt-0.5" />
              ) : (
                <AlertTriangle className="w-4 h-4 text-warning shrink-0 mt-0.5" />
              )}
              <p className="text-text-secondary text-[11px] leading-relaxed">
                {data.recommended ? (
                  <><strong className="text-success">Pro Tip:</strong> With {profit?.estimated_monthly_profit?.toLocaleString() || "strong"} EGP projected monthly profit and ~{profit?.estimated_payback_months || "—"}m payback, {data.area_name} is a solid choice for your {data.category.toLowerCase()} business.</>
                ) : (
                  <><strong className="text-warning">Review Needed:</strong> This area scores below the threshold. Consider adjusting budget or exploring other districts.</>
                )}
              </p>
            </div>
          </>
        )}
      </div>
    </motion.div>
  );
}
