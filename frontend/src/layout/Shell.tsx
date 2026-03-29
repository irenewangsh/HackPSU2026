import {
  BookOpen,
  BookText,
  ClipboardList,
  Cpu,
  Fingerprint,
  Flame,
  History,
  Home,
  Layers,
  LayoutDashboard,
  Leaf,
  ListTree,
  RotateCcw,
} from "lucide-react";
import { Link, NavLink, Outlet } from "react-router-dom";

const nav = [
  { to: "/", label: "Opening", icon: BookText, external: true },
  { to: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { to: "/mediate", label: "Mediation", icon: Layers },
  { to: "/hooks", label: "OS Hooks", icon: Cpu },
  { to: "/heatmap", label: "Risk heatmap", icon: Flame },
  { to: "/timeline", label: "Authority", icon: History },
  { to: "/audit", label: "Audit log", icon: ListTree },
  { to: "/operations", label: "Rollback", icon: RotateCcw },
  { to: "/profile", label: "Profile & forget", icon: Fingerprint },
  { to: "/demo", label: "Demo script", icon: ClipboardList },
  { to: "/devpost", label: "Devpost", icon: BookOpen },
];

export function Shell() {
  return (
    <div className="relative flex min-h-screen">
      <aside className="relative z-20 flex w-64 shrink-0 flex-col border-r border-stone-200/60 bg-paper-2/90 backdrop-blur-xl">
        <div className="flex items-center gap-3 px-5 py-8">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-sage-200/80 bg-gradient-to-br from-wash-leaf/90 to-white shadow-[0_8px_32px_rgba(58,99,78,0.12)]">
            <Leaf className="h-6 w-6 text-sage-600" strokeWidth={1.75} />
          </div>
          <div>
            <p className="font-serif text-xl font-semibold leading-tight tracking-tight text-ink">
              Sentinel<span className="text-gradient">OS</span>
            </p>
            <p className="font-sans text-[11px] font-medium tracking-wide text-forest-600/80">
              Control plane
            </p>
          </div>
        </div>
        <nav className="flex flex-1 flex-col gap-0.5 px-3 pb-6">
          {nav.map((item) =>
            "external" in item && item.external ? (
              <Link
                key={item.to}
                to={item.to}
                className="flex items-center gap-3 rounded-xl px-3 py-2.5 font-sans text-[15px] text-forest-700/85 transition hover:bg-white/60 hover:text-forest-900"
              >
                <item.icon className="h-4 w-4 shrink-0 text-sage-600/90" strokeWidth={1.75} />
                {item.label}
              </Link>
            ) : (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/dashboard"}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-xl px-3 py-2.5 font-sans text-[15px] transition ${
                    isActive
                      ? "bg-white/90 font-medium text-forest-900 shadow-md shadow-stone-200/80 ring-1 ring-stone-200/60"
                      : "text-forest-700/85 hover:bg-white/60 hover:text-forest-900"
                  }`
                }
              >
                <item.icon className="h-4 w-4 shrink-0 text-sage-600/90" strokeWidth={1.75} />
                {item.label}
              </NavLink>
            )
          )}
        </nav>
        <div className="border-t border-stone-200/60 p-4 font-sans text-[11px] leading-relaxed text-forest-600/70">
          SentinelOS: Between intention and impact, a quiet layer of care.
        </div>
      </aside>

      <div className="relative z-10 flex min-h-screen min-w-0 flex-1 flex-col overflow-hidden bg-paper">
        <header className="relative flex items-center justify-between border-b border-stone-200/50 bg-paper/80 px-8 py-5 backdrop-blur-sm">
          <div className="flex items-center gap-2 text-forest-600/80">
            <Home className="h-4 w-4 text-sage-600" strokeWidth={1.75} />
            <span className="font-sans text-xs font-medium uppercase tracking-[0.22em] text-forest-600/70">
              Console
            </span>
          </div>
        </header>
        <div className="relative flex-1 px-8 py-8">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
