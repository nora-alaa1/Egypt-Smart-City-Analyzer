"use client";

import { motion } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";
import Link from "next/link";

export default function CTASection() {
  return (
    <section className="section-padding relative">
      <div className="absolute inset-0 hero-gradient" />

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        whileInView={{ opacity: 1, scale: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
        className="container-wide relative z-10"
      >
        <div className="glass-card-strong glow-purple p-10 md:p-16 text-center max-w-4xl mx-auto">
          <Sparkles className="w-12 h-12 text-accent-purple mx-auto mb-6 animate-pulse" />
          <h2 className="font-heading text-3xl md:text-4xl font-bold mb-4">
            Start Your Analysis Today
          </h2>
          <p className="text-text-secondary text-lg mb-8 max-w-lg mx-auto">
            Join hundreds of entrepreneurs who have found their perfect business
            location with AI-powered insights.
          </p>
          <Link href="/login" className="btn-primary text-lg inline-flex">
            Get Started Free <ArrowRight size={20} />
          </Link>
        </div>
      </motion.div>
    </section>
  );
}
