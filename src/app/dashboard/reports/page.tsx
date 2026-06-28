"use client";

import { useState, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import {
  FileText,
  Download,
  Loader2,
  TrendingUp,
  MapPin,
  Users,
  Banknote,
  Store,
  BarChart3,
  Trophy,
  Sparkles,
  Printer,
} from "lucide-react";
import Sidebar from "@/components/Sidebar";
import AnalysisFilters, { type FilterValues } from "@/components/AnalysisFilters";
import { modelApi, type AnalysisResult } from "@/lib/modelApi";

export default function ReportsPage() {
  const reportRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentCategory, setCurrentCategory] = useState<string>("");

  const handleAnalyze = useCallback(async (filters: FilterValues) => {
    setLoading(true);
    setError(null);
    setCurrentCategory(filters.category);
    try {
      const data = await modelApi.analyze({
        area_id: filters.area_id,
        category: filters.category,
        rent_budget: filters.rent_budget,
        area_sqm: filters.area_sqm,
        min_population: filters.min_population,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const downloadPDF = async () => {
    if (!reportRef.current) return;
    setPdfLoading(true);
    try {
      const html2canvas = (await import("html2canvas")).default;
      const { default: jsPDF } = await import("jspdf");

      const canvas = await html2canvas(reportRef.current, {
        scale: 2,
        backgroundColor: "#FFFFFF",
        useCORS: true,
        logging: false,
      });

      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF("p", "mm", "a4");
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (canvas.height * pdfWidth) / canvas.width;

      let heightLeft = pdfHeight;
      let position = 0;
      const pageHeight = pdf.internal.pageSize.getHeight();

      pdf.addImage(imgData, "PNG", 0, position, pdfWidth, pdfHeight);
      heightLeft -= pageHeight;

      while (heightLeft > 0) {
        position = heightLeft - pdfHeight;
        pdf.addPage();
        pdf.addImage(imgData, "PNG", 0, position, pdfWidth, pdfHeight);
        heightLeft -= pageHeight;
      }

      pdf.save("SheCodes_Cities_Report.pdf");
    } catch (err) {
      console.error("PDF generation failed:", err);
    } finally {
      setPdfLoading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const getScoreColor = (score: number) => {
    if (score >= 7.5) return "#22C55E";
    if (score >= 5.0) return "#F59E0B";
    return "#EF4444";
  };

  const renderReportContent = () => {
    if (!result) return null;
    const current = result.current_area;
    const rankings = result.rankings || [];
    const best = result.best;
    const profit = current?.profit_analysis;
    const score10 = (s: number) => `${(s * 10).toFixed(0)}/100`;
    const fmt = (n: number) => n?.toLocaleString() ?? "—";

    return (
      <div ref={reportRef} style={{ background: "#FFFFFF", color: "#1E293B", padding: "32px 40px", fontFamily: "Inter, sans-serif" }}>
        {/* Header */}
        <div style={{ borderBottom: "3px solid #6C3BFF", paddingBottom: 20, marginBottom: 24, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h1 style={{ fontFamily: "'Space Grotesk',sans-serif", fontSize: 24, fontWeight: 700, color: "#0A0F2C", margin: 0 }}>
              SheCodes Cities
            </h1>
            <p style={{ color: "#64748B", fontSize: 13, margin: "4px 0 0" }}>AI-Powered Location Intelligence Report</p>
          </div>
          <div style={{ textAlign: "right", fontSize: 11, color: "#94A3B8" }}>
            <div>Generated {new Date().toLocaleDateString()}</div>
            <div>Alexandria, Egypt</div>
          </div>
        </div>

        {/* Summary */}
        <div style={{ background: "#F8FAFC", borderRadius: 12, padding: 20, marginBottom: 24, border: "1px solid #E2E8F0" }}>
          <h2 style={{ fontFamily: "'Space Grotesk',sans-serif", fontSize: 18, fontWeight: 700, color: "#0A0F2C", margin: "0 0 12px" }}>
            Analysis Summary
          </h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
            {[
              { label: "Total Areas", value: rankings.length, color: "#6C3BFF" },
              { label: "Top Area", value: best?.area_name || "N/A", color: "#22C55E" },
              { label: "Top Score", value: best ? score10(best.suitability_score) : "N/A", color: "#22C55E" },
              { label: "Category", value: currentCategory || "—", color: "#F59E0B" },
            ].map((s) => (
              <div key={s.label} style={{ background: "#FFFFFF", borderRadius: 8, padding: "12px 16px", border: "1px solid #E2E8F0" }}>
                <div style={{ fontSize: 11, color: "#94A3B8", marginBottom: 4 }}>{s.label}</div>
                <div style={{ fontSize: 16, fontWeight: 700, color: s.color }}>{s.value}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Current Area */}
        {current && (
          <div style={{ background: "#F8FAFC", borderRadius: 12, padding: 20, marginBottom: 24, border: "1px solid #E2E8F0" }}>
            <h2 style={{ fontFamily: "'Space Grotesk',sans-serif", fontSize: 18, fontWeight: 700, color: "#0A0F2C", margin: "0 0 12px" }}>
              Current Area: {current.area_name}
            </h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
              <div><span style={{ fontSize: 11, color: "#94A3B8" }}>Score</span><div style={{ fontSize: 20, fontWeight: 700, color: getScoreColor(current.suitability_score) }}>{score10(current.suitability_score)}</div></div>
              <div><span style={{ fontSize: 11, color: "#94A3B8" }}>Tier</span><div style={{ fontSize: 16, fontWeight: 600 }}>{current.tier}</div></div>
              <div><span style={{ fontSize: 11, color: "#94A3B8" }}>Status</span><div style={{ fontSize: 16, fontWeight: 600, color: current.recommended ? "#22C55E" : "#EF4444" }}>{current.recommended ? "Recommended" : "Not Recommended"}</div></div>
              <div><span style={{ fontSize: 11, color: "#94A3B8" }}>Population</span><div style={{ fontSize: 16, fontWeight: 600 }}>{(current.population / 1000).toFixed(0)}K</div></div>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginTop: 12 }}>
              <div><span style={{ fontSize: 11, color: "#94A3B8" }}>Rent/m²</span><div style={{ fontSize: 14, fontWeight: 600 }}>{current.rent_per_sqm?.toFixed(0)} EGP</div></div>
              <div><span style={{ fontSize: 11, color: "#94A3B8" }}>Affordability</span><div style={{ fontSize: 14, fontWeight: 600 }}>{current.affordability?.toFixed(2)}</div></div>
              <div><span style={{ fontSize: 11, color: "#94A3B8" }}>Comp 500m</span><div style={{ fontSize: 14, fontWeight: 600 }}>{current.competitors_500m}</div></div>
              <div><span style={{ fontSize: 11, color: "#94A3B8" }}>Comp 1km</span><div style={{ fontSize: 14, fontWeight: 600 }}>{current.competitors_1km}</div></div>
            </div>
            {profit && (
              <div style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid #E2E8F0" }}>
                <h3 style={{ fontFamily: "'Space Grotesk',sans-serif", fontSize: 14, fontWeight: 700, color: "#0A0F2C", margin: "0 0 10px" }}>Profit Analysis — {current.area_name}</h3>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10 }}>
                  <div><span style={{ fontSize: 10, color: "#94A3B8" }}>Revenue/mo</span><div style={{ fontSize: 14, fontWeight: 700, color: "#22C55E" }}>{fmt(profit.estimated_monthly_revenue)} EGP</div></div>
                  <div><span style={{ fontSize: 10, color: "#94A3B8" }}>Profit/mo</span><div style={{ fontSize: 14, fontWeight: 700, color: "#6C3BFF" }}>{fmt(profit.estimated_monthly_profit)} EGP</div></div>
                  <div><span style={{ fontSize: 10, color: "#94A3B8" }}>Margin</span><div style={{ fontSize: 14, fontWeight: 600 }}>{profit.profit_margin_pct}%</div></div>
                  <div><span style={{ fontSize: 10, color: "#94A3B8" }}>Payback</span><div style={{ fontSize: 14, fontWeight: 600 }}>{profit.estimated_payback_months} mo</div></div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Rankings Table */}
        <div style={{ background: "#F8FAFC", borderRadius: 12, padding: 20, border: "1px solid #E2E8F0" }}>
          <h2 style={{ fontFamily: "'Space Grotesk',sans-serif", fontSize: 18, fontWeight: 700, color: "#0A0F2C", margin: "0 0 12px" }}>
            Area Rankings
          </h2>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
            <thead>
              <tr style={{ borderBottom: "2px solid #E2E8F0" }}>
                <th style={{ textAlign: "left", padding: "8px 12px", color: "#64748B", fontWeight: 600 }}>#</th>
                <th style={{ textAlign: "left", padding: "8px 12px", color: "#64748B", fontWeight: 600 }}>Area</th>
                <th style={{ textAlign: "right", padding: "8px 12px", color: "#64748B", fontWeight: 600 }}>Score</th>
                <th style={{ textAlign: "right", padding: "8px 12px", color: "#64748B", fontWeight: 600 }}>Population</th>
                <th style={{ textAlign: "right", padding: "8px 12px", color: "#64748B", fontWeight: 600 }}>Est. Rent</th>
                <th style={{ textAlign: "right", padding: "8px 12px", color: "#64748B", fontWeight: 600 }}>Comp 500m</th>
                <th style={{ textAlign: "right", padding: "8px 12px", color: "#64748B", fontWeight: 600 }}>Tier</th>
              </tr>
            </thead>
            <tbody>
              {rankings.slice(0, 20).map((area, i) => (
                <tr key={area.area_id} style={{ borderBottom: "1px solid #E2E8F0" }}>
                  <td style={{ padding: "8px 12px", fontWeight: area.area_id === best?.area_id ? 700 : 400 }}>{i + 1}</td>
                  <td style={{ padding: "8px 12px", fontWeight: area.area_id === best?.area_id ? 700 : 400 }}>
                    {area.area_name}
                    {area.area_id === best?.area_id && <span style={{ color: "#6C3BFF", marginLeft: 6, fontSize: 10 }}>★ BEST</span>}
                  </td>
                  <td style={{ padding: "8px 12px", textAlign: "right", color: getScoreColor(area.suitability_score), fontWeight: 600 }}>{area.suitability_score.toFixed(1)}</td>
                  <td style={{ padding: "8px 12px", textAlign: "right" }}>{fmt(area.population)}</td>
                  <td style={{ padding: "8px 12px", textAlign: "right" }}>{area.estimated_rent != null ? `${fmt(area.estimated_rent)} EGP` : "—"}</td>
                  <td style={{ padding: "8px 12px", textAlign: "right" }}>{area.competitors_500m ?? "—"}</td>
                  <td style={{ padding: "8px 12px", textAlign: "right" }}>{area.tier || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div style={{ marginTop: 24, paddingTop: 16, borderTop: "1px solid #E2E8F0", fontSize: 10, color: "#94A3B8", textAlign: "center" }}>
          SheCodes Cities — AI-Powered Urban Analytics for Alexandria
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-deep-blue">
      <Sidebar />
      <main className="pl-64 transition-all duration-300 print:pl-0">
        <div className="p-6">
          <div className="mb-6">
            <h1 className="font-heading text-2xl md:text-3xl font-bold mb-1 flex items-center gap-2">
              <FileText className="w-7 h-7 text-accent-purple" />
              Reports
            </h1>
            <p className="text-text-secondary text-sm">
              Run analysis and generate PDF reports
            </p>
          </div>

          <AnalysisFilters onAnalyze={handleAnalyze} loading={loading} />

          {error && (
            <div className="glass-card p-4 mb-6 border border-danger/20 bg-danger/5">
              <p className="text-danger text-sm">{error}</p>
            </div>
          )}

          {result && (
            <div className="flex items-center gap-3 mb-6 print:hidden">
              <button
                onClick={downloadPDF}
                disabled={pdfLoading}
                className="btn-primary text-sm py-2 px-5 disabled:opacity-60"
              >
                {pdfLoading ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  <Download size={16} />
                )}
                Download PDF Report
              </button>
              <button
                onClick={handlePrint}
                className="btn-secondary text-sm py-2 px-5"
              >
                <Printer size={16} />
                Print
              </button>
            </div>
          )}

          <div className="print:block">
            {result ? (
              renderReportContent()
            ) : (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-card p-10 text-center"
              >
                <FileText className="w-16 h-16 text-accent-purple/30 mx-auto mb-4" />
                <h3 className="font-heading text-xl font-semibold mb-2">No Report Yet</h3>
                <p className="text-text-secondary text-sm max-w-md mx-auto">
                  Select your parameters above and run an analysis. Then download a
                  professional PDF report with full rankings and metrics.
                </p>
              </motion.div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
