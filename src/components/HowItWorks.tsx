"use client";

import { motion } from "framer-motion";
import { Grid, Database, Brain, LayoutDashboard } from "lucide-react";

const steps = [
  {
    icon: Grid,
    title: "Smart Grids",
    description:
      "Alexandria divided into 500m x 500m analysis grids for precise urban data mapping.",
    step: "01",
  },
  {
    icon: Database,
    title: "Data Collection",
    description:
      "Aggregating data from OpenStreetMap, population datasets, real estate platforms, and traffic sensors.",
    step: "02",
  },
  {
    icon: Brain,
    title: "AI Scoring",
    description:
      "Proprietary AI engine processes and scores each grid across multiple business dimensions.",
    step: "03",
  },
  {
    icon: LayoutDashboard,
    title: "Results Dashboard",
    description:
      "Interactive dashboard visualizes scores, comparisons, and AI-powered recommendations.",
    step: "04",
  },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="section-padding relative">
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
            How It{" "}
            <span className="text-gradient">Works</span>
          </h2>
          <p className="text-text-secondary text-lg max-w-2xl mx-auto">
            From raw data to smart decisions in four simple steps
          </p>
        </motion.div>

        <div className="relative">
          <div className="hidden lg:block absolute top-1/2 left-[15%] right-[15%] h-0.5 bg-gradient-to-r from-accent-purple/20 via-accent-purple/50 to-accent-purple/20 -translate-y-1/2" />

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {steps.map((step, i) => (
              <motion.div
                key={step.step}
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.15 }}
                className="glass-card p-6 md:p-8 relative group hover:glow-purple-hover transition-all duration-300"
              >
                <div className="absolute -top-3 -right-3 w-10 h-10 rounded-full bg-accent-purple flex items-center justify-center text-xs font-bold font-heading shadow-lg shadow-accent-purple/30">
                  {step.step}
                </div>
                <step.icon className="w-10 h-10 text-accent-purple mb-4 group-hover:scale-110 transition-transform duration-300" />
                <h3 className="font-heading text-lg font-semibold mb-2">
                  {step.title}
                </h3>
                <p className="text-text-secondary text-sm leading-relaxed">
                  {step.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
