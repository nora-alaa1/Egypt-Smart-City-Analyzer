"use client";

import { useState, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import { Info } from "lucide-react";

interface GridCell {
  id: string;
  score: number;
  label: string;
  area_id?: number;
}

const defaultGrid: GridCell[] = [
  { id: "A1", score: 92, label: "Smouha", area_id: 1 },
  { id: "A2", score: 85, label: "Sidi Gaber", area_id: 2 },
  { id: "A3", score: 72, label: "Stanley", area_id: 3 },
  { id: "A4", score: 88, label: "Louran", area_id: 4 },
  { id: "B1", score: 89, label: "Rushdy", area_id: 7 },
  { id: "B2", score: 68, label: "Cleopatra", area_id: 5 },
  { id: "B3", score: 78, label: "Ibrahimia", area_id: 9 },
  { id: "B4", score: 81, label: "Shatby", area_id: 8 },
  { id: "C1", score: 65, label: "Kafr Abdu", area_id: 11 },
  { id: "C2", score: 55, label: "Moharam Bek", area_id: 10 },
  { id: "C3", score: 42, label: "El-Attarin", area_id: 12 },
  { id: "C4", score: 95, label: "Sports City", area_id: 6 },
  { id: "D1", score: 62, label: "Miami" },
  { id: "D2", score: 58, label: "El Agamy" },
  { id: "D3", score: 48, label: "Abu Qir" },
  { id: "D4", score: 45, label: "Mansheya" },
];

interface InteractiveMapProps {
  rankings?: {
    area_id: number;
    area_name: string;
    suitability_score: number;
  }[] | null;
}

function getScoreColor(score: number): string {
  if (score >= 80) return "bg-[#22C55E]";
  if (score >= 60) return "bg-[#86EFAC]";
  if (score >= 40) return "bg-[#FDE047]";
  if (score >= 20) return "bg-[#F97316]";
  return "bg-[#EF4444]";
}

function getScoreGlow(score: number): string {
  if (score >= 80) return "shadow-[#22C55E]/30";
  if (score >= 60) return "shadow-[#86EFAC]/20";
  if (score >= 40) return "shadow-[#FDE047]/20";
  if (score >= 20) return "shadow-[#F97316]/20";
  return "shadow-[#EF4444]/20";
}

function getScoreBg(score: number): string {
  if (score >= 80) return "rgba(34,197,94,0.2)";
  if (score >= 60) return "rgba(134,239,172,0.15)";
  if (score >= 40) return "rgba(253,224,71,0.15)";
  if (score >= 20) return "rgba(249,115,22,0.2)";
  return "rgba(239,68,68,0.2)";
}

export default function InteractiveMap({ rankings }: InteractiveMapProps) {
  const [grid, setGrid] = useState<GridCell[]>(defaultGrid);
  const [animateKey, setAnimateKey] = useState(0);

  useEffect(() => {
    if (rankings && rankings.length > 0) {
      const idMap = new Map(
        rankings.map((r) => [r.area_id, r.suitability_score])
      );
      setGrid((prev) =>
        prev.map((cell) => {
          if (cell.area_id != null && idMap.has(cell.area_id)) {
            const score = Math.round(idMap.get(cell.area_id)! * 10);
            return { ...cell, score };
          }
          return cell;
        })
      );
      setAnimateKey((k) => k + 1);
    }
  }, [rankings]);

  const cells = useMemo(() => grid, [grid]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className="glass-card p-5"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-heading text-lg font-semibold">
          Grid Score Map — Alexandria
        </h3>
        <div className="flex items-center gap-2 text-text-secondary text-xs">
          <Info size={14} />
          <span>{rankings ? "Live scores" : "Default scores"}</span>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-2">
        {cells.map((cell, i) => (
          <motion.div
            key={`${cell.id}-${animateKey}`}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay: i * 0.03 }}
            className={`relative rounded-lg aspect-square flex flex-col items-center justify-center cursor-pointer transition-all duration-300 hover:scale-105 hover:shadow-lg ${getScoreGlow(cell.score)}`}
            style={{ background: getScoreBg(cell.score) }}
          >
            <div
              className={`w-2 h-2 rounded-full mb-1 ${getScoreColor(cell.score)}`}
            />
            <span className="text-[10px] font-bold font-heading">
              {cell.score}
            </span>
            <span className="text-[8px] text-text-secondary truncate max-w-full px-1">
              {cell.label}
            </span>
          </motion.div>
        ))}
      </div>

      <div className="flex items-center justify-center gap-4 mt-4">
        {[
          { label: "Optimal", color: "bg-[#22C55E]" },
          { label: "Good", color: "bg-[#86EFAC]" },
          { label: "Fair", color: "bg-[#FDE047]" },
          { label: "Low", color: "bg-[#F97316]" },
          { label: "Poor", color: "bg-[#EF4444]" },
        ].map((item) => (
          <div key={item.label} className="flex items-center gap-1.5">
            <div className={`w-2.5 h-2.5 rounded-full ${item.color}`} />
            <span className="text-[10px] text-text-secondary">
              {item.label}
            </span>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
