"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Sector, LineChart, Line,
} from "recharts";

const defaultCompetitorData = [
  { area: "Smouha", cafes: 12, gyms: 5, pharmacies: 8 },
  { area: "Sidi Gaber", cafes: 8, gyms: 3, pharmacies: 6 },
  { area: "Stanley", cafes: 15, gyms: 7, pharmacies: 4 },
  { area: "Louran", cafes: 6, gyms: 2, pharmacies: 5 },
  { area: "Cleopatra", cafes: 10, gyms: 4, pharmacies: 7 },
  { area: "Sports City", cafes: 4, gyms: 8, pharmacies: 3 },
];

const defaultVisitorsData = [
  { name: "Smouha", value: 1200 },
  { name: "Sidi Gaber", value: 980 },
  { name: "Stanley", value: 650 },
  { name: "Louran", value: 820 },
  { name: "Cleopatra", value: 750 },
  { name: "Sports City", value: 540 },
  { name: "Rushdy", value: 680 },
  { name: "Shatby", value: 430 },
];

const defaultRentalData = [
  { area: "Smouha", commercial: 320, residential: 180 },
  { area: "Sidi Gaber", commercial: 280, residential: 160 },
  { area: "Stanley", commercial: 450, residential: 250 },
  { area: "Louran", commercial: 350, residential: 200 },
  { area: "Cleopatra", commercial: 260, residential: 150 },
  { area: "Sports City", commercial: 190, residential: 120 },
  { area: "Rushdy", commercial: 300, residential: 170 },
  { area: "Shatby", commercial: 220, residential: 140 },
];

const PIE_COLORS = [
  "#6C3BFF", "#8B5CF6", "#A78BFA", "#22C55E",
  "#86EFAC", "#F59E0B", "#EF4444", "#F97316",
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass-card-strong px-4 py-3 text-sm">
        <p className="font-semibold mb-1">{label}</p>
        {payload.map((entry: any, i: number) => (
          <p key={i} style={{ color: entry.color }} className="text-xs">
            {entry.name}: {entry.value.toLocaleString()}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

const renderActiveShape = (props: any) => {
  const { cx, cy, innerRadius, outerRadius, startAngle, endAngle, fill, payload, percent } = props;
  return (
    <g>
      <text x={cx} y={cy - 8} textAnchor="middle" fill="#F8FAFC" fontSize={14} fontWeight={700}
        fontFamily="'Space Grotesk',sans-serif">{payload.name}</text>
      <text x={cx} y={cy + 12} textAnchor="middle" fill="#94A3B8" fontSize={11}>
        {payload.value.toLocaleString()} /day
      </text>
      <text x={cx} y={cy + 28} textAnchor="middle" fill={fill} fontSize={10}>
        {(percent * 100).toFixed(1)}%
      </text>
      <Sector cx={cx} cy={cy} innerRadius={innerRadius - 2} outerRadius={outerRadius + 6}
        startAngle={startAngle} endAngle={endAngle} fill={fill} opacity={0.3} />
      <Sector cx={cx} cy={cy} innerRadius={innerRadius} outerRadius={outerRadius}
        startAngle={startAngle} endAngle={endAngle} fill={fill} />
    </g>
  );
};

interface ChartsProps {
  analysisResult?: {
    rankings?: {
      area_id: number;
      area_name: string;
      suitability_score: number;
      population: number;
      competitors_500m: number;
      estimated_rent: number;
      profit_analysis?: {
        estimated_monthly_customers: number;
        estimated_monthly_revenue: number;
        estimated_monthly_profit: number;
        profit_margin_pct: number;
      };
    }[];
  } | null;
}

export default function Charts({ analysisResult }: ChartsProps) {
  const [activeIndex, setActiveIndex] = useState<number>(-1);

  const { scoreData, visitorsData, rentData } = useMemo(() => {
    if (!analysisResult?.rankings || analysisResult.rankings.length === 0) {
      return {
        scoreData: defaultCompetitorData,
        visitorsData: defaultVisitorsData,
        rentData: defaultRentalData,
      };
    }

    const rankings = analysisResult.rankings;
    const topAreas = rankings.slice(0, 8);

    const scores = topAreas.map((r) => ({
      area: r.area_name,
      score: Math.round(r.suitability_score * 10),
    }));

    const visitors = topAreas.map((r) => {
      const monthly = r.profit_analysis?.estimated_monthly_customers ?? r.population * 0.03;
      const daily = Math.round(monthly / 30);
      return { name: r.area_name, value: daily };
    });

    const rents = topAreas.map((r) => ({
      area: r.area_name,
      estimated: Math.round(r.estimated_rent / 100),
    }));

    return { scoreData: scores, visitorsData: visitors, rentData: rents };
  }, [analysisResult]);

  const onPieEnter = (_: any, index: number) => setActiveIndex(index);
  const onPieLeave = () => setActiveIndex(-1);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="glass-card p-5"
        >
          <h3 className="font-heading text-lg font-semibold mb-4">
            {analysisResult ? "Area Scores (0-100)" : "Competitor Density"}
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={scoreData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="area" tick={{ fill: "#94A3B8", fontSize: 11 }}
                axisLine={{ stroke: "rgba(255,255,255,0.1)" }} tickLine={false} />
              <YAxis tick={{ fill: "#94A3B8", fontSize: 11 }}
                axisLine={{ stroke: "rgba(255,255,255,0.1)" }} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey={analysisResult ? "score" : "cafes"} fill="#6C3BFF" radius={[4, 4, 0, 0]} />
              {!analysisResult && (
                <>
                  <Bar dataKey="gyms" fill="#22C55E" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="pharmacies" fill="#F59E0B" radius={[4, 4, 0, 0]} />
                </>
              )}
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="glass-card p-5"
        >
          <h3 className="font-heading text-lg font-semibold mb-4">
            {analysisResult ? "Predicted Visitors / Day" : "Population Distribution (%)"}
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={visitorsData}
                cx="50%" cy="50%"
                innerRadius={60} outerRadius={90}
                paddingAngle={3}
                dataKey="value"
                activeIndex={activeIndex >= 0 ? activeIndex : undefined}
                activeShape={renderActiveShape}
                onMouseEnter={onPieEnter}
                onMouseLeave={onPieLeave}
                animationBegin={0}
                animationDuration={800}
              >
                {visitorsData.map((_, i) => (
                  <Cell key={`cell-${i}`} fill={PIE_COLORS[i % PIE_COLORS.length]}
                    stroke="rgba(255,255,255,0.05)" />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap justify-center gap-3 mt-2">
            {visitorsData.map((item, i) => (
              <div key={item.name} className="flex items-center gap-1.5 cursor-pointer"
                onMouseEnter={() => setActiveIndex(i)}
                onMouseLeave={() => setActiveIndex(-1)}>
                <div className="w-2.5 h-2.5 rounded-full"
                  style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }} />
                <span className="text-[10px] text-text-secondary">{item.name}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.5 }}
        className="glass-card p-5"
      >
        <h3 className="font-heading text-lg font-semibold mb-4">
          {analysisResult ? "Estimated Rent per Area (EGP ÷ 100)" : "Rental Prices per Area (EGP/m²)"}
        </h3>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={rentData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="area" tick={{ fill: "#94A3B8", fontSize: 11 }}
              axisLine={{ stroke: "rgba(255,255,255,0.1)" }} tickLine={false} />
            <YAxis tick={{ fill: "#94A3B8", fontSize: 11 }}
              axisLine={{ stroke: "rgba(255,255,255,0.1)" }} tickLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Line type="monotone" dataKey={analysisResult ? "estimated" : "commercial"}
              stroke="#6C3BFF" strokeWidth={2} dot={{ fill: "#6C3BFF", r: 4 }} />
            {!analysisResult && (
              <Line type="monotone" dataKey="residential" stroke="#22C55E"
                strokeWidth={2} dot={{ fill: "#22C55E", r: 4 }} />
            )}
          </LineChart>
        </ResponsiveContainer>
      </motion.div>
    </div>
  );
}
