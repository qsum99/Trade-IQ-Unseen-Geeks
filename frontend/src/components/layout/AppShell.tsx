"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, type ReactNode } from "react";
import {
  BarChart3,
  FlaskConical,
  Globe,
  Layers,
  LayoutDashboard,
  Moon,
  Network,
  PieChart,
  Search,
  ShieldCheck,
  Sparkles,
  Sun,
  Target,
  Wallet,
  Zap,
  PanelLeftClose,
  PanelLeftOpen,
  Newspaper,
  type LucideIcon,
} from "lucide-react";
import { useHealth } from "@/hooks/useHealth";
import { useTheme } from "@/components/providers";
import { Badge } from "@/components/ui";
import { LiveNewsTicker } from "@/components/news/LiveNewsTicker";
import { LiveNewsModal } from "@/components/news/LiveNewsModal";

const NAV: { section: string; items: { href: string; label: string; icon: LucideIcon }[] }[] = [
  { section: "Overview", items: [{ href: "/overview", label: "Overview", icon: LayoutDashboard }] },
  {
    section: "Markets",
    items: [
      { href: "/markets", label: "Markets", icon: Globe },
      { href: "/news", label: "Live News", icon: Newspaper },
      { href: "/assets", label: "Assets", icon: Wallet },
      { href: "/analytics", label: "Analytics", icon: BarChart3 },
      { href: "/correlation", label: "Correlation", icon: Network },
    ],
  },
  {
    section: "Research",
    items: [
      { href: "/strategies", label: "Strategies", icon: Target },
      { href: "/backtesting", label: "Backtesting", icon: FlaskConical },
      { href: "/paper-trading", label: "Paper Trading", icon: Zap },
      { href: "/robustness", label: "Robustness", icon: ShieldCheck },
      { href: "/regimes", label: "Regimes", icon: Layers },
      { href: "/risk", label: "Risk & Portfolio", icon: PieChart },
    ],
  },

  {
    section: "Experimental",
    items: [
      { href: "/ai", label: "AI Research", icon: Sparkles },
    ],
  },
];

function ApiBadge() {
  const { data, isError, isPending } = useHealth();
  if (data) return <Badge tone="positive">● API Connected</Badge>;
  if (isPending) return <Badge tone="neutral">○ Connecting…</Badge>;
  if (isError) return <Badge tone="warn">● Mock data</Badge>;
  return <Badge tone="neutral">○ Offline</Badge>;
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { theme, toggle } = useTheme();
  const [collapsed, setCollapsed] = useState(false);
  const [newsModalOpen, setNewsModalOpen] = useState(false);

  if (pathname === "/") {
    return <div className="min-h-screen w-full bg-[#07090D] text-white">{children}</div>;
  }

  return (
    <div className="flex min-h-screen">
      <aside
        className={`sticky top-0 flex h-screen flex-col border-r border-(--color-edge) bg-(--color-surface) transition-all duration-600 ease-in-out ${
          collapsed ? "w-[72px]" : "w-[248px]"
        }`}
      >
        <Link href="/" className="flex items-center gap-2.5 px-3 py-4 transition-transform duration-300 hover:scale-[1.02]" title="TradeIQ Home">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/logo-dark.png"
            alt="TradeIQ Logo"
            className="h-8 w-8 shrink-0 object-contain hidden dark:block"
          />
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/logo.png"
            alt="TradeIQ Logo"
            className="h-8 w-8 shrink-0 object-contain block dark:hidden"
          />
          {!collapsed && <span className="text-[16px] font-bold tracking-tight text-(--color-ink)">TradeIQ</span>}
        </Link>
        <nav className="flex-1 overflow-y-auto px-2 pb-4">
          {NAV.map((group, gi) => (
            <div key={group.section} className={`mt-4 first:mt-1 anim-slideInLeft stagger-${gi + 1}`}>
              {!collapsed && (
                <div className="px-2 text-[11px] font-semibold tracking-wider text-(--color-muted) uppercase">
                  {group.section}
                </div>
              )}
              {group.items.map((item) => {
                const active = pathname === item.href || pathname.startsWith(item.href + "/");
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    title={item.label}
                    className={`mt-0.5 flex items-center gap-2.5 rounded-lg px-2 py-1.5 text-sm transition-all duration-600 ${
                      active
                        ? "bg-(--color-elev) font-medium"
                        : "text-(--color-muted) hover:bg-(--color-elev) hover:text-(--color-ink) hover:translate-x-0.5"
                    }`}
                  >
                    <Icon size={16} strokeWidth={1.8} className="shrink-0" />
                    {!collapsed && item.label}
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>
        <button
          onClick={() => setCollapsed((c) => !c)}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="flex items-center gap-2 border-t border-(--color-edge) px-4 py-3 text-left text-xs text-(--color-muted) transition-colors duration-600 hover:text-(--color-ink)"
        >
          {collapsed ? <PanelLeftOpen size={16} /> : <><PanelLeftClose size={16} /> Collapse</>}
        </button>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 flex items-center gap-3 border-b border-(--color-edge) bg-(--color-surface) px-6 py-2.5">
          {/* Live News Ticker strictly to the left of the navigation bar */}
          <LiveNewsTicker onOpenTerminal={() => setNewsModalOpen(true)} />

          <div className="hidden xl:flex max-w-xs flex-1 items-center gap-2 rounded-lg bg-(--color-elev) px-3 py-1.5 text-sm text-(--color-muted) transition-all duration-600 focus-within:ring-1 focus-within:ring-(--color-info)">
            <Search size={14} className="shrink-0" />
            <input
              placeholder="Search assets, strategies, backtests…"
              className="w-full bg-transparent outline-none placeholder:text-(--color-muted)"
            />
            <span className="text-xs">⌘K</span>
          </div>
          <div className="ml-auto flex items-center gap-3">
            <Link
              href="/ai"
              className="flex items-center gap-1.5 rounded-lg bg-purple-600/10 px-3 py-1.5 text-xs font-medium text-purple-400 transition-all duration-600 hover:bg-purple-600/20 hover:scale-105"
              title="Ask AI"
            >
              <Sparkles size={13} />
              Ask AI
            </Link>
            <ApiBadge />
            <button
              onClick={toggle}
              title="Toggle theme"
              className="rounded-lg border border-(--color-edge) p-2 transition-all duration-600 hover:scale-105 hover:border-(--color-muted)"
            >
              {theme === "dark" ? <Sun size={15} /> : <Moon size={15} />}
            </button>
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-(--color-elev) text-xs font-semibold">
              HJ
            </div>
          </div>
        </header>
        <main className="mx-auto w-full max-w-[1400px] flex-1 p-8">{children}</main>
        <LiveNewsModal isOpen={newsModalOpen} onClose={() => setNewsModalOpen(false)} />
      </div>
    </div>
  );
}
