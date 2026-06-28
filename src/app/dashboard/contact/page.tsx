"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  MessageSquare, Send, Mail, MapPin, Phone, Clock,
  Loader2, CheckCircle2, Sparkles,
} from "lucide-react";
import Sidebar from "@/components/Sidebar";

export default function ContactPage() {
  const [form, setForm] = useState({ name: "", email: "", subject: "", message: "" });
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSending(true);
    // Simulate send
    await new Promise((r) => setTimeout(r, 1500));
    setSending(false);
    setSent(true);
    setForm({ name: "", email: "", subject: "", message: "" });
    setTimeout(() => setSent(false), 4000);
  };

  return (
    <div className="min-h-screen bg-deep-blue relative overflow-hidden">
      {/* Aura decorations */}
      <div className="fixed top-1/4 left-1/3 w-96 h-96 bg-accent-purple rounded-full opacity-[0.03] blur-[120px] animate-float pointer-events-none" />
      <div className="fixed bottom-1/4 right-1/3 w-80 h-80 bg-accent-purple rounded-full opacity-[0.02] blur-[100px]" style={{ animation: "float 7s ease-in-out infinite", animationDelay: "-3s" }} />

      <Sidebar />
      <main className="pl-64 transition-all duration-300 relative z-10">
        <div className="p-6">
          <div className="mb-6">
            <h1 className="font-heading text-2xl md:text-3xl font-bold mb-1 flex items-center gap-2">
              <MessageSquare className="w-7 h-7 text-accent-purple" />
              Contact Us
            </h1>
            <p className="text-text-secondary text-sm">
              Have a question or feedback? We&apos;d love to hear from you.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Form */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="lg:col-span-2 glass-card p-6 md:p-8"
            >
              <div className="flex items-center gap-2 mb-6">
                <Sparkles className="w-4 h-4 text-accent-purple" />
                <h2 className="font-heading text-lg font-semibold">Send us a message</h2>
              </div>

              {sent ? (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="flex flex-col items-center justify-center py-12"
                >
                  <div className="w-16 h-16 rounded-full bg-success/20 border border-success/30 flex items-center justify-center mb-4">
                    <CheckCircle2 className="w-8 h-8 text-success" />
                  </div>
                  <h3 className="font-heading text-lg font-semibold mb-1">Message Sent!</h3>
                  <p className="text-text-secondary text-sm">We&apos;ll get back to you within 24 hours.</p>
                </motion.div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs text-text-secondary mb-1.5">Your Name</label>
                      <input
                        type="text" required value={form.name}
                        onChange={(e) => setForm({ ...form, name: e.target.value })}
                        placeholder="John Doe"
                        className="w-full bg-deep-blue/50 border border-card-border rounded-xl px-4 py-3 text-sm text-text-primary placeholder:text-text-secondary/40 focus:outline-none focus:border-accent-purple focus:ring-1 focus:ring-accent-purple/50 transition-all"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-text-secondary mb-1.5">Your Email</label>
                      <input
                        type="email" required value={form.email}
                        onChange={(e) => setForm({ ...form, email: e.target.value })}
                        placeholder="john@example.com"
                        className="w-full bg-deep-blue/50 border border-card-border rounded-xl px-4 py-3 text-sm text-text-primary placeholder:text-text-secondary/40 focus:outline-none focus:border-accent-purple focus:ring-1 focus:ring-accent-purple/50 transition-all"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs text-text-secondary mb-1.5">Subject</label>
                    <input
                      type="text" required value={form.subject}
                      onChange={(e) => setForm({ ...form, subject: e.target.value })}
                      placeholder="How can we help?"
                      className="w-full bg-deep-blue/50 border border-card-border rounded-xl px-4 py-3 text-sm text-text-primary placeholder:text-text-secondary/40 focus:outline-none focus:border-accent-purple focus:ring-1 focus:ring-accent-purple/50 transition-all"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-text-secondary mb-1.5">Message</label>
                    <textarea
                      required value={form.message}
                      onChange={(e) => setForm({ ...form, message: e.target.value })}
                      placeholder="Tell us more about your inquiry..."
                      rows={5}
                      className="w-full bg-deep-blue/50 border border-card-border rounded-xl px-4 py-3 text-sm text-text-primary placeholder:text-text-secondary/40 focus:outline-none focus:border-accent-purple focus:ring-1 focus:ring-accent-purple/50 transition-all resize-none"
                    />
                  </div>
                  <button type="submit" disabled={sending} className="btn-primary text-sm py-3 px-6 disabled:opacity-60 disabled:cursor-not-allowed">
                    {sending ? (
                      <><Loader2 size={16} className="animate-spin" /> Sending...</>
                    ) : (
                      <><Send size={16} /> Send Message</>
                    )}
                  </button>
                </form>
              )}
            </motion.div>

            {/* Contact Info */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 }}
              className="space-y-4"
            >
              <div className="glass-card p-5">
                <h3 className="font-heading text-sm font-semibold mb-4">Get in Touch</h3>
                <div className="space-y-4">
                  {[
                    { icon: Mail, label: "Email", value: "shecodescities@gmail.com" },
                    { icon: MapPin, label: "Location", value: "DEPI, Menofiya, Egypt" },
                    { icon: Phone, label: "Phone", value: "+20 123 456 7890" },
                    { icon: Clock, label: "Response Time", value: "Within 24 hours" },
                  ].map((item) => (
                    <div key={item.label} className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-lg bg-accent-purple/10 border border-accent-purple/20 flex items-center justify-center shrink-0">
                        <item.icon className="w-4 h-4 text-accent-purple" />
                      </div>
                      <div>
                        <div className="text-xs text-text-secondary">{item.label}</div>
                        <div className="text-sm font-medium">{item.value}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="glass-card p-5">
                <h3 className="font-heading text-sm font-semibold mb-2">Follow Us</h3>
                <p className="text-text-secondary text-xs mb-3">
                  Stay updated with the latest urban analytics insights.
                </p>
                <div className="flex gap-2">
                  {["Twitter", "LinkedIn", "GitHub"].map((s) => (
                    <span key={s} className="glass-card px-3 py-1.5 text-xs text-text-secondary hover:text-accent-purple hover:border-accent-purple/30 transition-all cursor-pointer">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </main>
    </div>
  );
}
