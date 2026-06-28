"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { MapPin, Trophy, Banknote, Users } from "lucide-react";

interface OverviewCardsProps {
  analysisResult?: {
    rankings?: {
      area_name: string;
      suitability_score: number;
      population: number;
      estimated_rent: number;
    }[];
    best?: {
      area_name: string;
      suitability_score: number;
    } | null;
  } | null;
}

export default function OverviewCards({ analysisResult }: OverviewCardsProps) {
  const cards = useMemo(() => {
    const base = [
      {
        icon: MapPin,
        label: "Total Areas Analyzed",
        value: "48",
        change: "+12 this month",
        color: "#6C3BFF",
      },
      {
        icon: Trophy,
        label: "Best Area Score",
        value: "94.2",
        change: "Smouha District",
        color: "#22C55E",
      },
      {
        icon: Banknote,
        label: "Avg Rent (EGP/m²)",
        value: "285",
        change: "↓ 3.2% from last quarter",
        color: "#F59E0B",
      },
      {
        icon: Users,
        label: "Population Density",
        value: "1,842",
        change: "/km² avg across grids",
        color: "#8B5CF6",
      },
    ];

    if (analysisResult?.rankings && analysisResult.rankings.length > 0) {
      const r = analysisResult.rankings;
      const totalAreas = r.length;
      const best = analysisResult.best;
      const avgRent = Math.round(
        r.reduce((s, x) => s + x.estimated_rent, 0) / r.length
      );
      const avgPop = Math.round(
        r.reduce((s, x) => s + x.population, 0) / r.length
      );

      base[0] = {
        ...base[0],
        value: String(totalAreas),
        change: "areas evaluated in query",
      };
      if (best) {
        base[1] = {
          ...base[1],
          value: best.suitability_score.toFixed(1),
          change: `${best.area_name} District`,
        };
      }
      base[2] = {
        ...base[2],
        value: avgRent.toLocaleString(),
        change: "EGP avg estimated rent",
      };
      base[3] = {
        ...base[3],
        value: avgPop.toLocaleString(),
        change: "avg population across areas",
      };
    }

    return base;
  }, [analysisResult]);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, i) => (
        <motion.div
          key={card.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: i * 0.1 }}
          className="glass-card p-5 hover:glow-purple-hover transition-all duration-300"
        >
          <div
            className="w-10 h-10 rounded-lg flex items-center justify-center mb-3"
            style={{
              background: `${card.color}20`,
              border: `1px solid ${card.color}30`,
            }}
          >
            <card.icon className="w-5 h-5" style={{ color: card.color }} />
          </div>
          <div className="font-heading text-2xl font-bold mb-1">
            {card.value}
          </div>
          <div className="text-text-secondary text-xs mb-1">{card.label}</div>
          <div className="text-text-secondary/60 text-xs">{card.change}</div>
        </motion.div>
      ))}
    </div>
  );
}
