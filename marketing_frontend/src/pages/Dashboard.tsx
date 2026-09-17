import React, { useEffect, useState } from 'react';
import { 
  Users, 
  Target, 
  Activity, 
  Search,
  ArrowRight,
  ShieldCheck,
  Zap,
  ChevronUp,
  ChevronDown
} from 'lucide-react';
import { motion } from 'framer-motion';
import { api, type Lead } from '../lib/api';
import { LeadDetailDrawer } from '../components/LeadDetailDrawer';
import { LiveTelemetryFeed } from '../components/LiveTelemetryFeed';
import { Sparkline } from '../components/Sparkline';

export const Dashboard: React.FC = () => {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [lastSync, setLastSync] = useState<Date>(new Date());
  const [errorCount, setErrorCount] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLeadId, setSelectedLeadId] = useState<number | null>(null);

  const fetchData = async () => {
    try {
      const [leadsRes, statsRes] = await Promise.all([
        api.get('/leads'),
        api.get('/stats')
      ]);
      setLeads(leadsRes.data);
      setStats(statsRes.data);
      setLastSync(new Date());
      setErrorCount(0);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      setErrorCount(prev => prev + 1);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const filteredLeads = leads.filter(l => 
    (l.name?.toLowerCase().includes(searchTerm.toLowerCase())) ||
    (l.email?.toLowerCase().includes(searchTerm.toLowerCase())) ||
    (l.company?.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const calculateDelta = (history: number[]) => {
    if (!history || history.length < 2) return '+0.0%';
    const last = history[history.length - 1];
    const prev = history[history.length - 2];
    if (prev === 0) return last > 0 ? '+100%' : '+0.0%';
    const delta = ((last - prev) / prev) * 100;
    return `${delta >= 0 ? '+' : ''}${delta.toFixed(1)}%`;
  };

  const statCards = [
    { label: 'All Customers', value: stats?.total_leads || 0, icon: Users, color: '#6366f1', bg: 'bg-indigo-500/10', trend: calculateDelta(stats?.velocity?.leads), history: stats?.velocity?.leads },
    { label: 'Signed Up', value: stats?.conversion_rate || '0.0%', icon: Target, color: '#10b981', bg: 'bg-emerald-500/10', trend: calculateDelta(stats?.velocity?.conversions), history: stats?.velocity?.conversions }, 
    { label: 'Active Projects', value: stats?.active_campaigns || 0, icon: Zap, color: '#f59e0b', bg: 'bg-amber-500/10', trend: calculateDelta(stats?.velocity?.campaigns), history: stats?.velocity?.campaigns },
    { label: 'AI Interaction', value: stats?.ai_responses || 0, icon: Activity, color: '#3b82f6', bg: 'bg-blue-500/10', trend: calculateDelta(stats?.velocity?.ai), history: stats?.velocity?.ai },
  ];

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-4 border-brand-indigo border-t-transparent rounded-full animate-spin" />
    </div>
  );

  return (
    <div className="space-y-12 max-w-[1600px] mx-auto pb-20">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2 mb-1">
            <span className="px-3 py-1 bg-brand-indigo/10 text-brand-indigo text-[10px] font-black uppercase tracking-widest rounded-full border border-brand-indigo/10">
              Intelligence Node
            </span>
          </div>
          <h1 className="text-4xl font-black tracking-tight text-text-main">Market Overview</h1>
          <p className="text-text-muted font-medium text-lg">Real-time fidelity monitor for your automated customer ecosystem.</p>
        </div>
        <div className="flex items-center gap-4 bg-bg-surface/50 backdrop-blur-md precision-border p-2 rounded-[24px] premium-shadow">
          <div className="flex items-center gap-3 px-4 py-2 bg-bg-surface precision-border rounded-[18px]">
            <div className={cn("w-2 h-2 rounded-full", errorCount > 0 ? "bg-red-500" : "bg-emerald-500 animate-pulse")} />
            <span className="text-[10px] font-black uppercase tracking-widest text-text-muted">
              {errorCount > 0 ? "Sync Interrupted" : "Core Systems Live"}
            </span>
          </div>
          <div className="pr-4 text-[10px] text-text-muted font-bold opacity-40 uppercase tracking-tighter">
            Last Sync: {lastSync.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        </div>
      </header>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, idx) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            className="p-8 rounded-[40px] bg-bg-surface precision-border premium-shadow group hover:border-brand-indigo/40 transition-all flex flex-col justify-between h-[280px] relative overflow-hidden"
          >
            <div className="relative z-10">
              <div className="flex items-center justify-between mb-6">
                <div className={`p-4 rounded-[24px] ${stat.bg} ring-1 ring-inset ring-brand-indigo/5`} style={{ color: stat.color }}>
                  <stat.icon size={24} strokeWidth={2.5} />
                </div>
                {/* Growth Pill */}
                <div className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-black tracking-tighter",
                  stat.trend.startsWith('+') ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/10" : "bg-red-500/10 text-red-500 border border-red-500/10"
                )}>
                  {stat.trend.startsWith('+') ? <ChevronUp size={12} strokeWidth={3} /> : <ChevronDown size={12} strokeWidth={3} />}
                  {stat.trend.replace('+', '')}
                </div>
              </div>
              <p className="text-4xl font-black text-text-main mb-1 tracking-tight">{stat.value}</p>
              <p className="text-xs font-bold uppercase tracking-widest text-text-muted opacity-60">{stat.label}</p>
            </div>
            
            <div className="absolute bottom-0 left-0 right-0 h-32 opacity-80 pointer-events-none translate-y-4">
               <Sparkline data={stat.history || [0,0,0,0,0,0,0]} color={stat.color} width={380} height={120} />
            </div>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Main Table Area */}
        <div className="lg:col-span-8 space-y-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <h3 className="text-2xl font-black text-text-main flex items-center gap-3 tracking-tight">
              <div className="w-1.5 h-6 bg-brand-indigo rounded-full" />
              Customer Identities
            </h3>
            <div className="relative group">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted group-focus-within:text-brand-indigo transition-colors" size={16} />
              <input 
                type="text" 
                placeholder="Search by identity or organization..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-12 pr-6 py-3.5 bg-bg-surface/50 precision-border rounded-[20px] text-sm font-bold focus:outline-none focus:ring-2 focus:ring-brand-indigo/10 transition-all w-full md:min-w-[400px] premium-shadow"
              />
            </div>
          </div>

          <div className="bg-bg-surface rounded-[40px] precision-border overflow-hidden premium-shadow border border-border-subtle/20">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-bg-elevated/20 text-text-muted border-b border-border-subtle/40">
                  <th className="px-8 py-5 text-[11px] font-black uppercase tracking-[0.2em]">Full Identity</th>
                  <th className="px-8 py-5 text-[11px] font-black uppercase tracking-[0.2em]">Fidelity Score</th>
                  <th className="px-8 py-5 text-[11px] font-black uppercase tracking-[0.2em]">Assignment</th>
                  <th className="px-8 py-5 text-right"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle/30">
                {filteredLeads.map((lead) => (
                  <tr 
                    key={lead.id} 
                    onClick={() => setSelectedLeadId(lead.id)}
                    className="hover:bg-bg-elevated/10 transition-all group cursor-pointer"
                  >
                    <td className="px-8 py-6">
                      <div className="flex items-center space-x-4">
                        <div className="w-11 h-11 rounded-[16px] bg-bg-elevated/50 border border-border-subtle/50 flex items-center justify-center font-black text-sm text-brand-indigo shadow-sm group-hover:scale-105 transition-transform">
                          {(lead.name || lead.email || '?')[0].toUpperCase()}
                        </div>
                        <div>
                          <p className="text-[15px] font-bold text-text-main leading-none mb-1.5">{lead.name || 'Anonymous User'}</p>
                          <p className="text-[10px] text-text-muted font-black uppercase tracking-widest">{lead.company || 'Private Entity'}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-8 py-6">
                      <div className="flex items-center space-x-3">
                        <div className="w-20 h-2 bg-bg-elevated rounded-full overflow-hidden p-0.5 border border-border-subtle/20 ring-1 ring-border-subtle/10">
                          <motion.div 
                            initial={{ width: 0 }}
                            animate={{ width: `${Math.min(lead.score, 100)}%` }}
                            className="h-full bg-brand-indigo rounded-full" 
                          />
                        </div>
                        <span className="text-xs font-black text-text-main">{lead.score}</span>
                      </div>
                    </td>
                    <td className="px-8 py-6">
                      <span className={`px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest border transition-all ${
                        lead.segment === 'platinum' 
                          ? 'bg-amber-500/10 text-amber-500 border-amber-500/20' 
                          : lead.segment === 'gold'
                          ? 'bg-indigo-500/10 text-indigo-500 border-indigo-500/20'
                          : 'bg-slate-500/10 text-slate-500 border-slate-500/20'
                      }`}>
                        {lead.segment}
                      </span>
                    </td>
                    <td className="px-8 py-6 text-right">
                       <div className="inline-flex p-2.5 rounded-xl bg-bg-elevated text-text-muted group-hover:bg-brand-indigo group-hover:text-white transition-all transform group-hover:translate-x-1 shadow-sm">
                          <ArrowRight size={18} strokeWidth={2.5} />
                       </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Sidebar Info & Telemetry Feed */}
        <div className="lg:col-span-4 space-y-8 flex flex-col h-full">
          <LiveTelemetryFeed />

          {/* Security Health Node */}
          <div className="p-8 rounded-[40px] bg-bg-surface precision-border premium-shadow relative overflow-hidden group border border-border-subtle/10">
            <div className="absolute -right-4 -top-4 w-32 h-32 bg-emerald-500/5 rounded-full blur-3xl group-hover:bg-emerald-500/10 transition-all duration-700" />
            <div className="flex items-start justify-between mb-8 relative z-10">
              <div>
                 <h4 className="text-xl font-black text-text-main tracking-tight mb-1">Defense Status</h4>
                 <p className="text-[10px] font-black text-emerald-500 uppercase tracking-widest flex items-center gap-1.5">
                   <ShieldCheck size={12} strokeWidth={3} />
                   Verified & Active
                 </p>
              </div>
              <div className="p-4 bg-emerald-500/10 rounded-[20px] text-emerald-500">
                <ShieldCheck size={28} strokeWidth={2} />
              </div>
            </div>
            
            <div className="space-y-4 mb-8 relative z-10">
               <div className="flex items-center justify-between text-[11px] font-bold">
                 <span className="text-text-muted">Security Integrity</span>
                 <span className="text-emerald-500 font-black uppercase">99.8% Perfect</span>
               </div>
               <div className="h-1.5 w-full bg-bg-elevated rounded-full overflow-hidden p-0.5 border border-border-subtle/10">
                 <motion.div 
                   initial={{ width: 0 }}
                   animate={{ width: "99.8%" }}
                   className="h-full bg-emerald-500 rounded-full" 
                 />
               </div>
            </div>

            <button className="w-full py-4 bg-bg-elevated hover:bg-bg-elevated/80 border border-border-subtle/50 text-text-main font-black text-[11px] uppercase tracking-[0.2em] rounded-2xl transition-all active:scale-95">
              Identity Audit Hub
            </button>
          </div>

          <div className="p-8 rounded-[40px] bg-bg-surface precision-border premium-shadow border border-border-subtle/10">
            <h4 className="text-[11px] font-black uppercase tracking-[0.3em] text-text-muted mb-8 flex items-center justify-between">
              Engagement Mesh
              <div className="w-2 h-2 rounded-full bg-brand-indigo animate-pulse" />
            </h4>
            <div className="space-y-7">
              {[
                { label: 'Elite (Platinum)', key: 'platinum', color: 'bg-amber-500' },
                { label: 'High Intent (Gold)', key: 'gold', color: 'bg-brand-indigo' },
                { label: 'Growth (Silver)', key: 'silver', color: 'bg-indigo-400' },
                { label: 'New (Bronze)', key: 'bronze', color: 'bg-slate-400' },
              ].map(item => {
                const count = stats?.segments?.[item.key] || 0;
                const total = stats?.total_leads || 1;
                const percentage = Math.round((count / total) * 100);
                return (
                  <div key={item.label} className="space-y-3">
                    <div className="flex justify-between text-[11px] font-black uppercase tracking-wider">
                      <span className="text-text-muted">{item.label}</span>
                      <span className="text-text-main">{percentage}%</span>
                    </div>
                    <div className="h-2 w-full bg-bg-elevated rounded-full overflow-hidden p-0.5 border border-border-subtle/10">
                      <motion.div 
                        initial={{ width: 0 }}
                        animate={{ width: `${percentage}%` }}
                        transition={{ duration: 1.5, type: 'spring' }}
                        className={`h-full ${item.color} rounded-full`} 
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      <LeadDetailDrawer 
        leadId={selectedLeadId} 
        onClose={() => setSelectedLeadId(null)} 
      />
    </div>
  );
};

function cn(...inputs: any[]) {
  return inputs.filter(Boolean).join(' ');
}
