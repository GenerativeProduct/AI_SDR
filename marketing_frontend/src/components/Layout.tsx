import React from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { 
  Rocket, 
  Activity, 
  Target, 
  Users, 
  Settings, 
  LayoutDashboard,
  MessageSquare,
  ShieldCheck
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { ThemeToggle } from './ThemeToggle';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const navItems = [
  { path: '/', label: 'Overview', icon: LayoutDashboard },
  { path: '/ingestion', label: 'Telemetry Hub', icon: Activity },
  { path: '/intelligence', label: 'Intelligence', icon: Target },
  { path: '/profiles', label: 'Profiles', icon: Users },
  { path: '/orchestration', label: 'Campaigns', icon: MessageSquare },
  { path: '/live-ops', label: 'Live Ops', icon: Activity },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export const Layout: React.FC = () => {
  const location = useLocation();

  return (
    <div className="flex h-screen w-full bg-bg-base text-text-main font-sans selection:bg-brand-indigo/10 selection:text-brand-indigo transition-colors duration-300">
      {/* Sidebar */}
      <aside className="w-72 border-r border-border-subtle bg-bg-surface flex flex-col z-20">
        <div className="p-8 flex items-center space-x-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-brand-indigo flex items-center justify-center shadow-lg shadow-brand-indigo/20">
            <Rocket className="w-6 h-6 text-white" />
          </div>
          <div>
            <span className="text-xl font-bold tracking-tight block leading-tight">Vellux</span>
            <span className="text-[10px] uppercase tracking-[0.2em] text-text-muted font-bold">Marketing Agent</span>
          </div>
        </div>
        
        <nav className="flex-1 overflow-y-auto px-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => cn(
                "flex items-center space-x-3 px-4 py-3.5 rounded-xl transition-all duration-300 group relative",
                "hover:bg-bg-elevated",
                isActive ? "text-brand-indigo" : "text-text-muted hover:text-text-main"
              )}
            >
              <item.icon className={cn("w-5 h-5 transition-transform group-hover:scale-110", location.pathname === item.path ? "text-brand-indigo" : "text-text-muted")} />
              <span className="font-semibold text-sm">{item.label}</span>
              {location.pathname === item.path && (
                <motion.div 
                  layoutId="activeNav"
                  className="absolute left-0 w-1 h-6 bg-brand-indigo rounded-r-full"
                  transition={{ type: "spring", stiffness: 300, damping: 30 }}
                />
              )}
            </NavLink>
          ))}
        </nav>
        
        <div className="p-6">
          <div className="bg-bg-elevated p-4 rounded-2xl border border-border-subtle group hover:border-brand-indigo/30 transition-colors">
            <div className="flex items-center space-x-3">
              <div className="relative">
                <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-brand-indigo to-violet-500 flex items-center justify-center font-bold text-white shadow-md">
                  A
                </div>
                <div className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-green-500 border-2 border-bg-surface rounded-full" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-bold truncate">Anurag Verma</p>
                <p className="text-[10px] text-text-muted font-bold uppercase tracking-wider">Lead Strategist</p>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0 bg-bg-base overflow-hidden relative">
        <header className="h-20 border-b border-border-subtle flex items-center justify-between px-10 bg-bg-surface/80 backdrop-blur-xl sticky top-0 z-10">
          <div className="flex flex-col">
            <h2 className="text-[10px] font-black text-text-muted uppercase tracking-[0.3em] mb-1">
              Active Protocol
            </h2>
            <p className="text-sm font-bold text-text-main flex items-center gap-2">
              <ShieldCheck size={14} className="text-brand-indigo" />
              Marketing Orchestration v4.2
            </p>
          </div>
          
          <div className="flex items-center space-x-6">
            <div className="hidden md:flex items-center space-x-3 px-4 py-2 bg-bg-elevated border border-border-subtle rounded-xl">
              <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]" />
              <span className="text-[11px] font-bold text-text-muted uppercase tracking-wider">Node: Primary-01 Connected</span>
            </div>
            <div className="w-[1px] h-6 bg-border-subtle" />
            <ThemeToggle />
          </div>
        </header>

        <section className="flex-1 overflow-y-auto relative">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
              className="p-10"
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </section>
      </main>
    </div>
  );
};
