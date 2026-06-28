"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Brain,
  LayoutDashboard,
  Map,
  FileText,
  MessageSquare,
  LogOut,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

const menuItems = [
  { icon: LayoutDashboard, label: "Dashboard", href: "/dashboard" },
  { icon: Map, label: "Map Analysis", href: "/dashboard#map-section" },
  { icon: FileText, label: "Reports", href: "/dashboard/reports" },
  { icon: MessageSquare, label: "Contact Us", href: "/dashboard/contact" },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === "/dashboard" && pathname === "/dashboard") return true;
    if (href.startsWith("/dashboard/reports") && pathname?.startsWith("/dashboard/reports")) return true;
    return false;
  };

  return (
    <aside
      className={`fixed left-0 top-0 h-full z-40 glass-card-strong border-l-0 border-y-0 rounded-none flex flex-col transition-all duration-300 ${
        collapsed ? "w-16" : "w-64"
      }`}
    >
      <Link href="/" className="flex items-center gap-2 px-4 h-16 border-b border-card-border hover:bg-white/5 transition-colors group">
        <Brain className="w-6 h-6 text-accent-purple shrink-0 group-hover:animate-glow" />
        {!collapsed && (
          <span className="font-heading text-lg font-bold truncate">
            <span className="text-gradient">SheCodes</span> Cities
          </span>
        )}
      </Link>

      <nav className="flex-1 py-4 px-2 space-y-1">
        {menuItems.map((item) => (
          <Link
            key={item.label}
            href={item.href}
            className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 ${
              isActive(item.href)
                ? "bg-accent-purple/10 text-accent-purple border border-accent-purple/20"
                : "text-text-secondary hover:bg-white/5 hover:text-text-primary"
            }`}
          >
            <item.icon size={20} className="shrink-0" />
            {!collapsed && (
              <span className="text-sm font-medium truncate">{item.label}</span>
            )}
          </Link>
        ))}
      </nav>

      <div className="border-t border-card-border p-2 space-y-1">
        <Link
          href="/"
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-text-secondary hover:bg-white/5 hover:text-text-primary transition-all duration-200 text-sm"
        >
          <LogOut size={20} className="shrink-0" />
          {!collapsed && <span className="truncate">Logout</span>}
        </Link>

        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center justify-center px-3 py-2 rounded-xl text-text-secondary hover:bg-white/5 hover:text-text-primary transition-all duration-200"
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>
    </aside>
  );
}
