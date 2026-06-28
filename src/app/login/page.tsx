"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Brain, Eye, EyeOff, Loader2 } from "lucide-react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    // Simulate auth
    setTimeout(() => {
      setLoading(false);
      window.location.href = "/dashboard";
    }, 1500);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden hero-gradient">
      <div className="absolute top-1/3 left-1/4 w-96 h-96 bg-accent-purple rounded-full opacity-[0.05] blur-[120px] animate-float" />
      <div
        className="absolute bottom-1/3 right-1/4 w-80 h-80 bg-accent-purple rounded-full opacity-[0.03] blur-[100px] animate-float"
        style={{ animationDelay: "-4s" }}
      />

      <div
        className="absolute inset-0 opacity-10"
        style={{
          backgroundImage:
            "linear-gradient(rgba(108, 59, 255, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(108, 59, 255, 0.1) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="relative z-10 w-full max-w-md"
      >
        <Link
          href="/"
          className="flex items-center justify-center gap-2 mb-8 group"
        >
          <Brain className="w-8 h-8 text-accent-purple" />
          <span className="font-heading text-2xl font-bold">
            <span className="text-gradient">SheCodes</span>
            <span className="text-text-primary"> Cities</span>
          </span>
        </Link>

        <div className="glass-card-strong glow-purple p-8 md:p-10">
          <h2 className="font-heading text-2xl font-bold mb-2 text-center">
            Welcome Back
          </h2>
          <p className="text-text-secondary text-sm text-center mb-8">
            Sign in to access your dashboard
          </p>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm text-text-secondary mb-2">
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
                className="w-full bg-deep-blue/50 border border-card-border rounded-xl px-4 py-3 text-text-primary placeholder:text-text-secondary/40 focus:outline-none focus:border-accent-purple focus:ring-1 focus:ring-accent-purple/50 transition-all"
              />
            </div>

            <div>
              <label className="block text-sm text-text-secondary mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full bg-deep-blue/50 border border-card-border rounded-xl px-4 py-3 text-text-primary placeholder:text-text-secondary/40 focus:outline-none focus:border-accent-purple focus:ring-1 focus:ring-accent-purple/50 transition-all pr-12"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-text-secondary hover:text-text-primary transition-colors"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between text-sm">
              <label className="flex items-center gap-2 text-text-secondary cursor-pointer">
                <input
                  type="checkbox"
                  className="rounded border-card-border bg-deep-blue/50 accent-accent-purple"
                />
                Remember me
              </label>
              <button
                type="button"
                className="text-accent-purple hover:text-accent-glow transition-colors"
              >
                Forgot password?
              </button>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full justify-center text-base py-3 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading ? (
                <Loader2 size={20} className="animate-spin" />
              ) : (
                "Sign In"
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-text-secondary text-sm">
              Don&apos;t have an account?{" "}
              <button
                type="button"
                className="text-accent-purple hover:text-accent-glow transition-colors font-medium"
              >
                Create account
              </button>
            </p>
          </div>

          <div className="mt-6 pt-6 border-t border-card-border">
            <p className="text-text-secondary text-xs text-center mb-4">
              Or continue with
            </p>
            <button className="w-full flex items-center justify-center gap-3 border border-card-border rounded-xl px-4 py-3 text-text-secondary hover:bg-white/5 hover:border-accent-purple/30 transition-all text-sm">
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path
                  fill="currentColor"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                />
                <path
                  fill="currentColor"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="currentColor"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="currentColor"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              Continue with Google
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
