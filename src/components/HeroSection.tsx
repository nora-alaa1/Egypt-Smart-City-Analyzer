"use client";

import { motion } from "framer-motion";
import { ArrowRight, Play } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

export default function HeroSection() {
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouse = (e: MouseEvent) => {
      setMousePos({
        x: (e.clientX / window.innerWidth - 0.5) * 20,
        y: (e.clientY / window.innerHeight - 0.5) * 20,
      });
    };
    window.addEventListener("mousemove", handleMouse);
    return () => window.removeEventListener("mousemove", handleMouse);
  }, []);

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden hero-gradient">
      <div
        className="absolute inset-0 opacity-20"
        style={{
          backgroundImage:
            "linear-gradient(rgba(108, 59, 255, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(108, 59, 255, 0.1) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
          transform: `translate(${mousePos.x}px, ${mousePos.y}px)`,
          transition: "transform 0.2s ease-out",
        }}
      />

      <div className="absolute top-1/4 left-1/4 w-72 h-72 bg-accent-purple rounded-full opacity-[0.04] blur-[100px] animate-float" />
      <div
        className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent-purple rounded-full opacity-[0.03] blur-[120px] animate-float"
        style={{ animationDelay: "-3s" }}
      />

      <div className="relative z-10 text-center px-4 max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <div className="inline-flex items-center gap-2 glass-card px-4 py-2 mb-8 text-sm text-text-secondary">
            <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
            AI-Powered Urban Analytics
          </div>

          <h1 className="font-heading text-4xl md:text-6xl lg:text-7xl font-bold leading-tight mb-6">
            Smarter Decisions for{" "}
            <span className="text-gradient">Smarter Cities</span>
          </h1>

          <p className="text-text-secondary text-lg md:text-xl max-w-2xl mx-auto mb-10 leading-relaxed">
            Analyze urban data, discover opportunities, and choose the best
            locations for your business in Alexandria.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/login" className="btn-primary text-lg">
              Start Analyzing <ArrowRight size={20} />
            </Link>
            <Link href="#about" className="btn-secondary text-lg">
              <Play size={18} /> Learn More
            </Link>
          </div>
        </motion.div>
      </div>

      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
        <div className="w-6 h-10 border-2 border-accent-purple/30 rounded-full flex justify-center">
          <div className="w-1.5 h-3 bg-accent-purple/60 rounded-full mt-2 animate-pulse" />
        </div>
      </div>
    </section>
  );
}
