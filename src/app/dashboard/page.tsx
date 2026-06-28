"use client";

import { useState, useCallback } from "react";
import Sidebar from "@/components/Sidebar";
import OverviewCards from "@/components/OverviewCards";
import InteractiveMap from "@/components/InteractiveMap";
import AlexandriaMap from "@/components/AlexandriaMap";
import Charts from "@/components/Charts";
import AIRecommendation, { type AIRecommendationData } from "@/components/AIRecommendation";
import AnalysisFilters, { type FilterValues } from "@/components/AnalysisFilters";
import { modelApi, type AnalysisResult } from "@/lib/modelApi";
import { BarChart3, Download, Loader2, Sparkles } from "lucide-react";

export default function DashboardPage() {
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [recommendation, setRecommendation] = useState<AIRecommendationData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [powerBILoading, setPowerBILoading] = useState<string | null>(null);

  const handleAnalyze = useCallback(async (filters: FilterValues) => {
    setLoading(true);
    setError(null);
    try {
      const result = await modelApi.analyze({
        area_id: filters.area_id,
        category: filters.category,
        rent_budget: filters.rent_budget,
        area_sqm: filters.area_sqm,
        min_population: filters.min_population,
      });
      setAnalysisResult(result);
      if (result.best) {
        setRecommendation({
          area_name: result.best.area_name,
          category: filters.category,
          suitability_score: result.best.suitability_score,
          tier: result.best.tier,
          population: result.best.population,
          estimated_rent: result.best.estimated_rent,
          rent_per_sqm: result.best.rent_per_sqm,
          competitors_500m: result.best.competitors_500m,
          recommended: result.best.suitability_score >= 6.0,
          reason: result.best.reason,
          traffic_score: (result.best as any).traffic_score ?? 5,
          accessibility_score: (result.best as any).accessibility_score ?? 5,
          profit_analysis: (result.best as any).profit_analysis,
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
      setAnalysisResult(null);
      setRecommendation(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const downloadPowerBI = async (type: string, label: string) => {
    setPowerBILoading(label);
    try {
      const url = type === "areas"
        ? modelApi.getExportUrl("/export/areas")
        : modelApi.getExportUrl(`/export/area-scores?category=Food %26 Beverage`);
      const response = await fetch(url);
      const blob = await response.blob();
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = `smartcity_${type}.csv`;
      link.click();
    } catch (err) {
      console.error("Download failed:", err);
    } finally {
      setPowerBILoading(null);
    }
  };

  // Build rankings for the map
  const mapRankings = analysisResult?.rankings?.map((r) => ({
    area_id: r.area_id,
    area_name: r.area_name,
    suitability_score: r.suitability_score,
  })) ?? null;

  return (
    <div className="min-h-screen bg-deep-blue">
      <Sidebar />
      <main className="pl-64 transition-all duration-300">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Sparkles className="w-5 h-5 text-warning" />
                <span className="text-text-secondary text-sm">Welcome back, Explorer</span>
              </div>
              <h1 className="font-heading text-2xl md:text-3xl font-bold mb-1">Analyzer Dashboard</h1>
              <p className="text-text-secondary text-sm">
                AI-powered urban analysis for Alexandria, Egypt
              </p>
            </div>
            {/* Power BI Download Buttons */}
            <div className="hidden md:flex items-center gap-2">
              <button
                onClick={() => downloadPowerBI("areas", "Areas")}
                disabled={powerBILoading !== null}
                className="glass-card px-3 py-2 text-xs text-text-secondary hover:text-accent-purple hover:border-accent-purple/30 transition-all flex items-center gap-1.5 disabled:opacity-50"
              >
                {powerBILoading === "Areas" ? <Loader2 size={12} className="animate-spin" /> : <Download size={12} />}
                Areas CSV
              </button>
              <button
                onClick={() => downloadPowerBI("scores", "Scores")}
                disabled={powerBILoading !== null}
                className="glass-card px-3 py-2 text-xs text-text-secondary hover:text-accent-purple hover:border-accent-purple/30 transition-all flex items-center gap-1.5 disabled:opacity-50"
              >
                {powerBILoading === "Scores" ? <Loader2 size={12} className="animate-spin" /> : <BarChart3 size={12} />}
                Scores CSV
              </button>
            </div>
          </div>

          <AnalysisFilters onAnalyze={handleAnalyze} loading={loading} />

          {error && (
            <div className="glass-card p-4 mb-6 border border-danger/20 bg-danger/5">
              <p className="text-danger text-sm">{error}</p>
            </div>
          )}

          <OverviewCards analysisResult={analysisResult} />

          <div className="mt-6 grid grid-cols-1 lg:grid-cols-5 gap-6">
            <div className="lg:col-span-3">
              <InteractiveMap rankings={mapRankings} />
            </div>
            <div className="lg:col-span-2">
              <AIRecommendation data={recommendation} loading={loading} />
            </div>
          </div>

          {/* Alexandria Map Section */}
          <div id="map-section" className="mt-6">
            <AlexandriaMap rankings={mapRankings} />
          </div>

          <div className="mt-6">
            <Charts analysisResult={analysisResult} />
          </div>

          {/* Mobile Power BI buttons */}
          <div className="mt-6 md:hidden flex flex-wrap items-center gap-2">
            <span className="text-text-secondary text-xs">Power BI Export:</span>
            <button
              onClick={() => downloadPowerBI("areas", "Areas")}
              disabled={powerBILoading !== null}
              className="glass-card px-3 py-2 text-xs text-text-secondary hover:text-accent-purple transition-all flex items-center gap-1.5 disabled:opacity-50"
            >
              {powerBILoading === "Areas" ? <Loader2 size={12} className="animate-spin" /> : <Download size={12} />}
              Areas CSV
            </button>
            <button
              onClick={() => downloadPowerBI("scores", "Scores")}
              disabled={powerBILoading !== null}
              className="glass-card px-3 py-2 text-xs text-text-secondary hover:text-accent-purple transition-all flex items-center gap-1.5 disabled:opacity-50"
            >
              {powerBILoading === "Scores" ? <Loader2 size={12} className="animate-spin" /> : <BarChart3 size={12} />}
              Scores CSV
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
