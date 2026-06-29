"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Search,
  MapPin,
  Briefcase,
  DollarSign,
  Users,
  Building2,
  Loader2,
  Sparkles,
} from "lucide-react";
import { type Area } from "@/lib/modelApi";

export interface FilterValues {
  area_id: number;
  category: string;
  rent_budget: number;
  area_sqm: number;
  min_population: number;
}

interface AnalysisFiltersProps {
  onAnalyze: (filters: FilterValues) => void;
  loading: boolean;
}

const BUSINESS_CATEGORIES = [
  "Food & Beverage",
  "Retail",
  "Healthcare",
  "Education",
  "Fitness",
  "Entertainment",
];

// 12 core districts (simple 1-12 IDs matching fallback model)
const CORE_AREAS: Area[] = [
  { area_id: 1,  area_name: "Smouha",     population: 45000 },
  { area_id: 2,  area_name: "Sidi Gaber",  population: 38000 },
  { area_id: 3,  area_name: "Stanley",     population: 25000 },
  { area_id: 4,  area_name: "Louran",      population: 32000 },
  { area_id: 5,  area_name: "Cleopatra",   population: 35000 },
  { area_id: 6,  area_name: "Sports City", population: 22000 },
  { area_id: 7,  area_name: "Rushdy",      population: 29000 },
  { area_id: 8,  area_name: "Shatby",      population: 18000 },
  { area_id: 9,  area_name: "Ibrahimia",   population: 26000 },
  { area_id: 10, area_name: "Moharam Bek", population: 31000 },
  { area_id: 11, area_name: "Kafr Abdu",   population: 27000 },
  { area_id: 12, area_name: "El-Attarin",  population: 15000 },
];

export default function AnalysisFilters({
  onAnalyze,
  loading,
}: AnalysisFiltersProps) {
  const [areas, setAreas] = useState<Area[]>(CORE_AREAS);
  const [filters, setFilters] = useState<FilterValues>({
    area_id: 1,
    category: "Food & Beverage",
    rent_budget: 50000,
    area_sqm: 120,
    min_population: 0,
  });

  const selectedArea = areas.find((a) => a.area_id === filters.area_id);



  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onAnalyze(filters);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="glass-card p-5 mb-6"
    >
      <form onSubmit={handleSubmit}>
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="w-5 h-5 text-accent-purple" />
          <h2 className="font-heading text-lg font-semibold">
            AI Analysis Panel
          </h2>
          <span className="text-text-secondary text-xs ml-auto">
            Run analysis on Alexandria urban data
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {/* Area */}
          <div>
            <label className="flex items-center gap-1.5 text-xs text-text-secondary mb-1.5">
              <MapPin size={12} className="text-accent-purple" />
              District
            </label>
            <select
              value={filters.area_id}
              onChange={(e) =>
                setFilters({ ...filters, area_id: Number(e.target.value) })
              }
              className="w-full bg-deep-blue/50 border border-card-border rounded-xl px-3 py-2.5 text-sm text-text-primary focus:outline-none focus:border-accent-purple focus:ring-1 focus:ring-accent-purple/50 transition-all appearance-none cursor-pointer"
            >
              {areas.map((a) => (
                <option key={a.area_id} value={a.area_id}>
                  {a.area_name}
                </option>
              ))}
            </select>
          </div>

          {/* Business Type */}
          <div>
            <label className="flex items-center gap-1.5 text-xs text-text-secondary mb-1.5">
              <Briefcase size={12} className="text-accent-purple" />
              Business Type
            </label>
            <select
              value={filters.category}
              onChange={(e) =>
                setFilters({ ...filters, category: e.target.value })
              }
              className="w-full bg-deep-blue/50 border border-card-border rounded-xl px-3 py-2.5 text-sm text-text-primary focus:outline-none focus:border-accent-purple focus:ring-1 focus:ring-accent-purple/50 transition-all appearance-none cursor-pointer"
            >
              {BUSINESS_CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          {/* Rent Budget */}
          <div>
            <label className="flex items-center gap-1.5 text-xs text-text-secondary mb-1.5">
              <DollarSign size={12} className="text-accent-purple" />
              Rent Budget (EGP)
            </label>
            <input
              type="number"
              value={filters.rent_budget}
              onChange={(e) =>
                setFilters({
                  ...filters,
                  rent_budget: Number(e.target.value),
                })
              }
              min={5000}
              max={500000}
              step={1000}
              className="w-full bg-deep-blue/50 border border-card-border rounded-xl px-3 py-2.5 text-sm text-text-primary focus:outline-none focus:border-accent-purple focus:ring-1 focus:ring-accent-purple/50 transition-all"
            />
          </div>

          {/* Area Size */}
          <div>
            <label className="flex items-center gap-1.5 text-xs text-text-secondary mb-1.5">
              <Building2 size={12} className="text-accent-purple" />
              Space (m²)
            </label>
            <input
              type="number"
              value={filters.area_sqm}
              onChange={(e) =>
                setFilters({ ...filters, area_sqm: Number(e.target.value) })
              }
              min={20}
              max={1000}
              step={10}
              className="w-full bg-deep-blue/50 border border-card-border rounded-xl px-3 py-2.5 text-sm text-text-primary focus:outline-none focus:border-accent-purple focus:ring-1 focus:ring-accent-purple/50 transition-all"
            />
          </div>

          {/* Min Population */}
          <div>
            <label className="flex items-center gap-1.5 text-xs text-text-secondary mb-1.5">
              <Users size={12} className="text-accent-purple" />
              Min Population
            </label>
            <select
              value={filters.min_population}
              onChange={(e) =>
                setFilters({
                  ...filters,
                  min_population: Number(e.target.value),
                })
              }
              className="w-full bg-deep-blue/50 border border-card-border rounded-xl px-3 py-2.5 text-sm text-text-primary focus:outline-none focus:border-accent-purple focus:ring-1 focus:ring-accent-purple/50 transition-all appearance-none cursor-pointer"
            >
              <option value={0}>Any</option>
              <option value={15000}>15,000+</option>
              <option value={20000}>20,000+</option>
              <option value={25000}>25,000+</option>
              <option value={30000}>30,000+</option>
              <option value={40000}>40,000+</option>
            </select>
          </div>
        </div>

        <div className="mt-4 flex items-center justify-between">
          <div className="text-xs text-text-secondary">
            {selectedArea?.area_name || "Selected"}
            {selectedArea && ` — ${(selectedArea.population / 1000).toFixed(0)}K residents`}
          </div>
          <button
            type="submit"
            disabled={loading}
            className="btn-primary text-sm py-2 px-6 disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Search size={16} />
                Run Analysis
              </>
            )}
          </button>
        </div>
      </form>
    </motion.div>
  );
}
