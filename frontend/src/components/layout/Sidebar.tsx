"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  Users, LayoutDashboard, MessageSquare, BarChart2,
  Settings, FolderOpen, X, CheckCircle2, Zap,
} from "lucide-react";

const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Personas", href: "/personas", icon: Users },
  { name: "Simulations", href: "/simulations", icon: BarChart2 },
  { name: "Conversations", href: "/conversations", icon: MessageSquare },
  { name: "Projects", href: "/projects", icon: FolderOpen },
  { name: "Settings", href: "/settings", icon: Settings },
];

const PRO_FEATURES = [
  "Unlimited persona imports",
  "Simulations up to 500 personas",
  "Priority Gemini API quota",
  "Advanced analytics & charts",
  "PDF/CSV report export",
  "Team collaboration (coming soon)",
];

const PLANS = [
  { name: "Starter", price: "Free", cta: "Current Plan", current: true, features: ["50 personas", "5 simulations/mo", "Basic analytics"] },
  { name: "Pro", price: "₹2,999/mo", cta: "Upgrade to Pro", current: false, features: ["Unlimited personas", "Unlimited simulations", "Advanced analytics", "Report generation", "Priority support"] },
  { name: "Enterprise", price: "Custom", cta: "Contact Sales", current: false, features: ["Everything in Pro", "Team access", "Custom integrations", "Dedicated support", "SLA guarantees"] },
];

export function Sidebar() {
  const pathname = usePathname();
  const [showUpgrade, setShowUpgrade] = useState(false);

  return (
    <>
      <div className="flex h-full w-64 flex-col border-r bg-zinc-950 text-zinc-50 shrink-0">
        {/* Logo */}
        <div className="flex h-14 items-center border-b border-zinc-800 px-4">
          <div className="flex flex-col leading-none">
            <span className="text-2xl font-black tracking-wider text-amber-400">AARU</span>
            <span className="text-[9px] font-semibold tracking-[0.25em] text-zinc-500 uppercase -mt-0.5">India</span>
          </div>
        </div>

        {/* Nav */}
        <div className="flex-1 overflow-auto py-4">
          <nav className="grid gap-0.5 px-2">
            {navigation.map((item) => {
              const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                      : "text-zinc-400 hover:bg-zinc-900 hover:text-white"
                  }`}
                >
                  <item.icon className="h-4 w-4 shrink-0" />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Pro CTA */}
        <div className="border-t border-zinc-800 p-3">
          <div className="rounded-xl bg-gradient-to-br from-amber-950/60 to-zinc-900 p-4 border border-amber-800/40">
            <div className="flex items-center gap-1.5 mb-1">
              <Zap className="h-3.5 w-3.5 text-amber-400" />
              <h4 className="text-sm font-semibold text-amber-300">Upgrade to Pro</h4>
            </div>
            <p className="text-xs text-zinc-400 mb-3">Unlock unlimited personas and high-fidelity simulations.</p>
            <button
              onClick={() => setShowUpgrade(true)}
              className="w-full rounded-md bg-amber-500 px-3 py-1.5 text-xs font-semibold text-black hover:bg-amber-400 transition-colors"
            >
              View Plans
            </button>
          </div>
        </div>
      </div>

      {/* Upgrade Modal */}
      {showUpgrade && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50 animate-in fade-in">
          <div className="w-full max-w-3xl bg-white dark:bg-zinc-950 rounded-2xl shadow-2xl border overflow-hidden">
            <div className="p-6 border-b flex items-start justify-between">
              <div>
                <h2 className="text-xl font-bold">Choose Your Plan</h2>
                <p className="text-sm text-muted-foreground mt-0.5">Scale your research with <span className="text-amber-500 font-semibold">Aaru India</span>'s powerful simulation engine.</p>
              </div>
              <button onClick={() => setShowUpgrade(false)} className="rounded-full p-1.5 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="p-6 grid grid-cols-3 gap-4">
              {PLANS.map((plan) => (
                <div
                  key={plan.name}
                  className={`rounded-xl border p-5 flex flex-col gap-3 relative ${
                    plan.name === "Pro"
                      ? "border-black dark:border-white shadow-lg ring-1 ring-black dark:ring-white"
                      : "border-zinc-200 dark:border-zinc-800"
                  }`}
                >
                  {plan.name === "Pro" && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-black dark:bg-white text-white dark:text-black text-[10px] font-bold px-3 py-1 rounded-full">
                      MOST POPULAR
                    </div>
                  )}
                  <div>
                    <p className="font-bold text-base">{plan.name}</p>
                    <p className="text-2xl font-black mt-0.5">{plan.price}</p>
                  </div>
                  <ul className="space-y-1.5 flex-1">
                    {plan.features.map((f) => (
                      <li key={f} className="flex items-center gap-1.5 text-xs text-muted-foreground">
                        <CheckCircle2 className="h-3.5 w-3.5 text-green-500 shrink-0" />{f}
                      </li>
                    ))}
                  </ul>
                  <button
                    className={`w-full rounded-lg py-2 text-sm font-semibold transition-colors ${
                      plan.current
                        ? "bg-zinc-100 dark:bg-zinc-800 text-zinc-500 cursor-default"
                        : plan.name === "Pro"
                        ? "bg-black dark:bg-white text-white dark:text-black hover:opacity-90"
                        : "border border-zinc-300 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-900"
                    }`}
                    onClick={() => {
                      if (!plan.current && plan.name !== "Enterprise") {
                        alert("Payment integration coming soon! For now, all features are available in the free tier.");
                      } else if (plan.name === "Enterprise") {
                        alert("Contact us at hello@aaru.ai to discuss enterprise pricing.");
                      }
                    }}
                  >
                    {plan.cta}
                  </button>
                </div>
              ))}
            </div>
            <div className="px-6 pb-6 text-center text-xs text-muted-foreground">
              All plans include a 14-day free trial. No credit card required to start.
            </div>
          </div>
        </div>
      )}
    </>
  );
}
