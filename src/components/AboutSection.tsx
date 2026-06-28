"use client";

import { motion } from "framer-motion";
import { BarChart3, Lightbulb, Target, Users } from "lucide-react";

const stats = [
  { icon: BarChart3, value: "50K+", label: "Data Points" },
  { icon: Target, value: "12", label: "District Grids" },
  { icon: Users, value: "500+", label: "Business Types" },
  { icon: Lightbulb, value: "98%", label: "Accuracy Rate" },
];

export default function AboutSection() {
  return (
    <section id="about" className="section-padding relative">
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
            About the{" "}
            <span className="text-gradient">Project</span>
          </h2>
          <p className="text-text-secondary text-lg max-w-3xl mx-auto leading-relaxed">
            Egypt Smart City Analyzer transforms raw urban data into actionable
            business intelligence. By dividing Alexandria into smart grids and
            analyzing population density, rental prices, traffic patterns, and
            competitor presence, we help entrepreneurs and investors make
            data-driven location decisions — no guesswork, just insights.
          </p>
        </motion.div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
          {stats.map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
              className="glass-card p-6 text-center hover:glow-purple-hover transition-all duration-300"
            >
              <stat.icon className="w-8 h-8 text-accent-purple mx-auto mb-3" />
              <div className="font-heading text-2xl md:text-3xl font-bold text-gradient mb-1">
                {stat.value}
              </div>
              <div className="text-text-secondary text-sm">{stat.label}</div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
