import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Terminal, 
  Activity, 
  Cpu, 
  Globe, 
  Zap, 
  ArrowRight,
  Database,
  Lock,
  Wifi
} from 'lucide-react';
import { getLiveEvents } from '../lib/api';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const LiveOps: React.FC = () => {
  const [events, setEvents] = useState<any[]>([]);
  const [isLive, setIsLive] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let interval: any;
    if (isLive) {
      const fetchEvents = async () => {
        try {
          const res = await getLiveEvents(30);
          setEvents(res.data);
        } catch (e) {
          console.error("Live Ops polling failed:", e);
        }
      };
      
      fetchEvents();
      interval = setInterval(fetchEvents, 2000);
    }
    return () => clearInterval(interval);
  }, [isLive]);

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-20 h-[calc(100vh-160px)] flex flex-col">
      <header className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-brand-indigo/10 rounded-lg text-brand-indigo">
              <Activity size={20} className="animate-pulse" />
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-text-main">Live Operations Mesh</h1>
          </div>
          <p className="text-text-muted font-medium">Real-time telemetry stream from decentralized book nodes.</p>
        </div>

        <div className="flex items-center gap-4">
           <button 
             onClick={() => setIsLive(!isLive)}
             className={cn(
               "px-6 py-2.5 rounded-2xl font-black text-xs uppercase tracking-widest transition-all flex items-center gap-3 border",
               isLive ? "bg-green-500/10 text-green-500 border-green-500/20" : "bg-text-muted/10 text-text-muted border-border-subtle"
             )}
           >
             <div className={cn("w-2 h-2 rounded-full", isLive ? "bg-green-500 animate-pulse" : "bg-text-muted")} />
             {isLive ? "Stream Active" : "Stream Paused"}
           </button>
           <div className="px-6 py-2.5 bg-bg-surface border border-border-subtle rounded-2xl flex items-center gap-3">
             <Wifi size={14} className="text-brand-indigo" />
             <span className="text-xs font-bold text-text-muted">Master Key Validated</span>
           </div>
        </div>
      </header>

      {/* Cluster Monitoring Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'Cluster Throughput', value: '42.8 req/s', icon: Zap },
          { label: 'Active Ingestion Nodes', value: '12', icon: Globe },
          { label: 'Mesh Latency', value: '18ms', icon: Cpu },
          { label: 'Encryption Protocol', value: 'AES-256', icon: Lock },
        ].map((stat) => (
          <div key={stat.label} className="p-6 bg-bg-surface precision-border rounded-[32px] flex items-center gap-4 premium-shadow">
            <div className="p-3 bg-bg-elevated rounded-2xl text-brand-indigo shadow-sm">
              <stat.icon size={18} />
            </div>
            <div>
              <p className="text-[10px] font-black uppercase tracking-widest text-text-muted mb-1">{stat.label}</p>
              <p className="text-base font-bold text-text-main tracking-tight">{stat.value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Terminal View */}
      <div className="flex-1 bg-[#091b36] rounded-[40px] precision-border overflow-hidden flex flex-col premium-shadow border-4 border-white/5 shadow-2xl">
        <div className="px-10 py-6 bg-white/5 border-b border-white/10 flex items-center justify-between">
           <div className="flex items-center gap-4 text-white/40">
             <Terminal size={18} />
             <span className="text-[10px] font-black uppercase tracking-[0.3em] font-mono">Operations_Log_v4.0.2</span>
           </div>
           <div className="flex gap-2">
             <div className="w-2.5 h-2.5 rounded-full bg-white/10" />
             <div className="w-2.5 h-2.5 rounded-full bg-white/10" />
             <div className="w-2.5 h-2.5 rounded-full bg-brand-indigo/50" />
           </div>
        </div>

        <div 
          ref={scrollRef}
          className="flex-1 p-10 overflow-y-auto font-mono text-[12px] space-y-3 custom-scrollbar"
        >
          <AnimatePresence initial={false}>
            {events.map((event) => (
              <motion.div 
                key={event.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex items-start gap-6 group hover:bg-white/5 p-2 rounded-lg transition-colors border-l-2 border-transparent hover:border-brand-indigo/40"
              >
                <span className="text-white/20 whitespace-nowrap">[{new Date(event.created_at).toLocaleTimeString()}]</span>
                <span className={cn(
                  "font-black uppercase tracking-widest px-2 py-0.5 rounded text-[10px]",
                  event.segment === 'platinum' ? "bg-brand-indigo/20 text-brand-indigo" :
                  event.segment === 'gold' ? "bg-amber-500/20 text-amber-500" :
                  "bg-white/10 text-white/60"
                )}>
                  {event.type}
                </span>
                <span className="text-white/80 flex-1">
                  Node: <span className="text-brand-indigo font-bold">{event.email}</span> 
                  <span className="text-white/30 ml-2">-- Identity: {event.name || "UNIDENTIFIED"}</span>
                  {event.metadata && (
                    <span className="text-white/40 ml-4 font-light italic">meta: {JSON.stringify(event.metadata).slice(0, 50)}...</span>
                  )}
                </span>
                <div className="flex items-center gap-3">
                  <span className="text-white/20">SCORE:</span>
                  <span className="text-brand-indigo font-bold">{event.score}</span>
                  <ArrowRight size={12} className="text-white/10 group-hover:text-brand-indigo transition-colors" />
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          {events.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-white/20 space-y-4">
               <Database size={48} className="animate-pulse" />
               <p className="font-mono uppercase tracking-[0.4em] text-[10px]">Listening for decentralized events...</p>
            </div>
          )}
        </div>

        <div className="px-10 py-4 bg-white/5 border-t border-white/10 flex items-center justify-between text-[10px] font-mono font-bold text-white/30">
           <div className="flex gap-6 uppercase tracking-widest">
             <span>Protocol: JSON/RPC</span>
             <span>Cluster: Vellux-US-East-1</span>
           </div>
           <div className="flex items-center gap-2">
             <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
             <span>MESH UPTIME: 100%</span>
           </div>
        </div>
      </div>
    </div>
  );
};
