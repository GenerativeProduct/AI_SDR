import React, { useState } from 'react';
import { 
  Activity, 
  Send, 
  MousePointer2, 
  Mail, 
  FileText, 
  Share2,
  CheckCircle2,
  AlertCircle,
  Zap
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '../lib/api';

const EVENT_TYPES = [
  { id: 'web_visit', label: 'Website Visit', icon: MousePointer2, color: 'text-blue-500', bg: 'bg-blue-500/10' },
  { id: 'email_open', label: 'Email Open', icon: Mail, color: 'text-amber-500', bg: 'bg-amber-500/10' },
  { id: 'form_submit', label: 'Form Submission', icon: FileText, color: 'text-emerald-500', bg: 'bg-emerald-500/10' },
  { id: 'social_interaction', label: 'Social Engagement', icon: Share2, color: 'text-purple-500', bg: 'bg-purple-500/10' },
];

export const Ingestion: React.FC = () => {
  const [selectedEvent, setSelectedEvent] = useState(EVENT_TYPES[0].id);
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');

  const handleSimulate = async () => {
    if (!email) return;
    setStatus('loading');
    try {
      await api.post('/events', {
        email,
        event_type: selectedEvent,
        metadata: { source: 'telemetry_hub', timestamp: new Date().toISOString() }
      });
      setStatus('success');
      setTimeout(() => setStatus('idle'), 3000);
    } catch (error) {
      console.error('Simulation failed:', error);
      setStatus('error');
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-10">
      <header className="text-center">
        <div className="inline-flex items-center space-x-2 px-3 py-1 bg-brand-indigo/10 text-brand-indigo rounded-full mb-4">
          <Zap size={14} className="fill-brand-indigo" />
          <span className="text-[10px] font-black uppercase tracking-widest">Simulation Engine</span>
        </div>
        <h1 className="text-4xl font-bold tracking-tight mb-4">Telemetry Hub</h1>
        <p className="text-text-muted font-medium max-w-2xl mx-auto">
          Inject real-time events into the orchestration engine to trigger scoring protocols and campaign workflows.
        </p>
      </header>

      <div className="bg-bg-surface p-10 rounded-[40px] precision-border premium-shadow space-y-10">
        <div className="space-y-6">
          <label className="text-[11px] font-black uppercase tracking-[0.2em] text-text-muted pl-1">
            Choose Protocol
          </label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {EVENT_TYPES.map((type) => (
              <button
                key={type.id}
                onClick={() => setSelectedEvent(type.id)}
                className={cn(
                  "p-6 rounded-3xl flex flex-col items-center text-center space-y-4 transition-all duration-300 border-2",
                  selectedEvent === type.id 
                    ? "bg-bg-elevated border-brand-indigo ring-4 ring-brand-indigo/5 shadow-xl" 
                    : "bg-bg-elevated/50 border-transparent hover:border-border-subtle grayscale hover:grayscale-0"
                )}
              >
                <div className={`p-3 rounded-2xl ${type.bg} ${type.color}`}>
                  <type.icon size={24} />
                </div>
                <span className="text-xs font-bold leading-tight">{type.label}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-6 pt-6 border-t border-border-subtle">
          <label className="text-[11px] font-black uppercase tracking-[0.2em] text-text-muted pl-1">
            Target Identity (Email)
          </label>
          <div className="flex flex-col md:flex-row gap-4">
            <input 
              type="email" 
              placeholder="e.g. prospect@enterprise.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="flex-1 px-6 py-4 bg-bg-elevated border border-border-subtle rounded-2xl text-lg font-medium focus:outline-none focus:ring-2 focus:ring-brand-indigo/20 transition-all"
            />
            <button
              onClick={handleSimulate}
              disabled={status === 'loading'}
              className="px-10 py-4 bg-brand-indigo hover:bg-brand-indigo-hover text-white rounded-2xl font-bold flex items-center justify-center gap-3 transition-all shadow-lg shadow-brand-indigo/20 disabled:opacity-50"
            >
              <Send size={20} />
              <span>Simulate</span>
            </button>
          </div>
        </div>

        <AnimatePresence>
          {status !== 'idle' && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className={cn(
                "p-4 rounded-2xl flex items-center justify-center gap-3 font-bold text-sm border",
                status === 'success' ? "bg-green-500/10 text-green-500 border-green-500/20" : 
                status === 'error' ? "bg-red-500/10 text-red-500 border-red-500/20" : 
                "bg-brand-indigo/10 text-brand-indigo border-brand-indigo/20"
              )}
            >
              {status === 'loading' && <Activity className="animate-spin" size={18} />}
              {status === 'success' && <CheckCircle2 size={18} />}
              {status === 'error' && <AlertCircle size={18} />}
              <span>
                {status === 'loading' ? 'Transmitting telemetry node...' : 
                 status === 'success' ? 'Telemetry accepted by orchestration' : 
                 'Transmission failed'}
              </span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="p-8 bg-bg-surface precision-border rounded-3xl space-y-4">
          <div className="w-10 h-10 rounded-xl bg-orange-500/10 text-orange-500 flex items-center justify-center">
            <Activity size={20} />
          </div>
          <h4 className="text-lg font-bold">Node Logs</h4>
          <p className="text-sm text-text-muted leading-relaxed">
            Every simulation is cryptographically hashed and logged to the central audit trail. This ensures absolute replayability for strategy debugging.
          </p>
        </div>
        <div className="p-8 bg-bg-surface precision-border rounded-3xl space-y-4">
          <div className="w-10 h-10 rounded-xl bg-violet-500/10 text-violet-500 flex items-center justify-center">
            <Activity size={20} />
          </div>
          <h4 className="text-lg font-bold">Latency Warning</h4>
          <p className="text-sm text-text-muted leading-relaxed">
            High-density event batches may trigger rate limiting on the LLM scoring engine. Typical processing time is &lt;200ms per node.
          </p>
        </div>
      </div>
    </div>
  );
};

// Helper for conditional classes
function cn(...inputs: any[]) {
  return inputs.filter(Boolean).join(' ');
}
