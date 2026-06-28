"use client";

import { useState } from "react";
import Link from "next/link";
import { Menu, X, Brain } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const navLinks = [
  { href: "/", label: "Home" },
  { href: "#about", label: "About" },
  { href: "#how-it-works", label: "How It Works" },
  { href: "#features", label: "Features" },
];

export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass-card-strong border-t-0 border-x-0 rounded-none">
      <div className="container-wide flex items-center justify-between px-4 py-4">
        <Link href="/" className="flex items-center gap-2 group">
          <Brain className="w-7 h-7 text-accent-purple group-hover:animate-glow" />
          <span className="font-heading text-xl font-bold">
            <span className="text-gradient">SheCodes</span>
            <span className="text-text-primary"> Cities</span>
          </span>
        </Link>

        <div className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-text-secondary hover:text-accent-purple transition-colors text-sm font-medium"
            >
              {link.label}
            </Link>
          ))}
          <Link href="/login" className="btn-primary text-sm py-2 px-5">
            Get Started
          </Link>
        </div>

        <button
          className="md:hidden text-text-primary p-2"
          onClick={() => setMobileOpen(!mobileOpen)}
        >
          {mobileOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden border-t border-card-border"
          >
            <div className="flex flex-col gap-4 px-4 py-6">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className="text-text-secondary hover:text-accent-purple transition-colors"
                >
                  {link.label}
                </Link>
              ))}
              <Link
                href="/login"
                onClick={() => setMobileOpen(false)}
                className="btn-primary text-sm py-2 px-5 w-fit"
              >
                Get Started
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
