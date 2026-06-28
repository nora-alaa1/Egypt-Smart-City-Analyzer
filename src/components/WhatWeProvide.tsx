"use client";

import { motion } from "framer-motion";
import {
  MapPin,
  Users,
  Banknote,
  Route,
  Store,
  Gauge,
} from "lucide-react";

const features = [
  {
    icon: MapPin,
    title: "Location Intelligence",
    description:
      "Deep analysis of each grid's characteristics, demographics, and growth potential.",
    color: "#6C3BFF",
  },
  {
    icon: Users,
    title: "Population Insights",
    description:
      "Density distribution, age groups, income levels, and foot traffic estimates.",
    color: "#8B5CF6",
  },
  {
    icon: Banknote,
    title: "Rental Price Analysis",
    description:
      "Commercial and residential rental trends across all districts of Alexandria.",
    color: "#22C55E",
  },
  {
    icon: Route,
    title: "Accessibility & Traffic",
    description:
      "Public transport access, road connectivity, and traffic congestion patterns.",
    color: "#F59E0B",
  },
  {
    icon: Store,
    title: "Competitor Mapping",
    description:
      "Identify existing businesses, saturation levels, and market gaps per grid.",
    color: "#EF4444",
  },
  {
    icon: Gauge,
    title: "Smart Scoring System",
    description:
      "AI-powered composite score ranking each grid by suitability for your business.",
    color: "#A78BFA",
  },
];

export default function WhatWeProvide() {
  return (
    <section id="features" className="section-padding relative">
      <div className="absolute inset-0 bg-gradient-to-b from-deep-blue via-accent-purple/[0.02] to-deep-blue pointer-events-none" />

      <div className="container-wide relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="font-heading text-3xl md:text-4xl font-bold mb-6">
            What We{" "}
            <span className="text-gradient">Provide</span>
          </h2>
          <p className="text-text-secondary text-lg max-w-2xl mx-auto">
            Everything you need to make confident location decisions
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, i) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.08 }}
              className="glass-card p-6 group hover:glow-purple-hover transition-all duration-300 cursor-default"
            >
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300"
                style={{
                  background: `${feature.color}20`,
                  border: `1px solid ${feature.color}30`,
                }}
              >
                <feature.icon
                  className="w-6 h-6"
                  style={{ color: feature.color }}
                />
              </div>
              <h3 className="font-heading text-lg font-semibold mb-2">
                {feature.title}
              </h3>
              <p className="text-text-secondary text-sm leading-relaxed">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
