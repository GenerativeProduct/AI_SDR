import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Zap, CheckCircle2, Globe, Search } from 'lucide-react';
import { api } from '../lib/api';

export const LiveTelemetryFeed: React.FC = () => {
  const [events, setEvents] = useState<any[]>([]);

  const fetchLiveEvents = async () => {
    try {
      const res = await api.get('/events/live?limit=10');
      setEvents(res.data);
    } catch (err) {
      console.error("Telemetry Stream Failure:", err);
    }
  };

  useEffect(() => {
    fetchLiveEvents();
    const interval = setInterval(fetchLiveEvents, 5000);
    return () => clearInterval(interval);
  }, []);

  const eventLabels: Record<string, { label: string, icon: any, color: string }> = {
    'form_submit': { label: 'New Sign Up', icon: CheckCircle2, color: 'text-emerald-500' },
    'video_play': { label: 'Watched Video', icon: Zap, color: 'text-amber-500' },
    'cta_click': { label: 'Interacted with site', icon: Globe, color: 'text-blue-500' },
    'user_identified': { label: 'Lead Verified', icon: CheckCircle2, color: 'text-emerald-500' },
    'auto_agent_dispatch': { label: 'AI Message Sent', icon: Activity, color: 'text-brand-indigo' },
    'page_view': { label: 'Product Research', icon: Search, color: 'text-slate-400' }
  };

  return (
    <div className="bg-bg-surface precision-border rounded-[32px] overflow-hidden flex flex-col h-full premium-shadow">
      <div className="p-6 border-b border-border-subtle bg-bg-elevated/10 flex items-center justify-between">
        <h4 className="text-sm font-bold flex items-center gap-2">
          <Activity size={18} className="text-brand-indigo" />
          Live Pulse Feed
        </h4>
        <div className="flex items-center gap-1.5 px-3 py-1 bg-emerald-500/5 rounded-full border border-emerald-500/10">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-[10px] font-bold uppercase text-emerald-500 tracking-tighter">Live Stream</span>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-6 space-y-5 scrollbar-hide">
        <AnimatePresence initial={false}>
          {events.map((event, idx) => {
            const config = eventLabels[event.action_type] || { label: event.action_type, icon: Activity, color: 'text-text-muted' };
            const Icon = config.icon;
            
            return (
              <motion.div
                key={event.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="relative flex gap-4 group"
              >
                {/* Timeline Line */}
                {idx !== events.length - 1 && (
                  <div className="absolute left-[11px] top-6 bottom-[-20px] w-px bg-border-subtle/50" />
                )}

                <div className="shrink-0 w-6 h-6 rounded-full bg-bg-elevated flex items-center justify-center border border-border-subtle group-hover:border-brand-indigo/30 transition-colors z-10">
                  <Icon size={12} className={config.color} />
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-0.5">
                    <p className="text-[13px] font-bold text-text-main truncate pr-2">
                      {event.name || event.email?.split('@')[0] || 'Anonymous'}
                    </p>
                    <span className="shrink-0 text-[10px] font-medium text-text-muted opacity-60">
                      {new Date(event.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <p className="text-[11px] font-medium text-text-muted">
                    {config.label}
                  </p>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
        
        {events.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center py-20 opacity-20">
            <Activity size={32} />
            <p className="text-xs font-bold uppercase tracking-widest mt-2">No activity detected</p>
          </div>
        )}
      </div>
      
      <div className="p-4 bg-bg-elevated/20 text-[10px] font-bold text-text-muted uppercase text-center border-t border-border-subtle tracking-widest text-opacity-50">
        Secure Handshake Active • 256-bit
      </div>
    </div>
  );
};
