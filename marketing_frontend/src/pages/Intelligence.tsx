import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ChevronRight, 
  MessageSquare, 
  Bot, 
  RefreshCcw, 
  Search,
  Sparkles,
  TrendingUp,
  Target,
  Send,
  ArrowRight,
  Zap
} from 'lucide-react';
import { api, type Lead, generateContent } from '../lib/api';

export const Intelligence: React.FC = () => {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedLeadId, setSelectedLeadId] = useState<number | null>(null);
  const [aiResponse, setAiResponse] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchLeads();
  }, []);

  const fetchLeads = async () => {
    try {
      const res = await api.get('/leads');
      setLeads(res.data);
    } catch (e) { console.error(e); }
  };

  const selectedLead = leads.find(l => l.id === selectedLeadId);

  const handleGenerate = async (topic: string) => {
    if (!selectedLead) return;
    setLoading(true);
    try {
      const res = await generateContent(selectedLead.id, topic);
      setAiResponse(res.generated_text || res.content);
    } catch (e) {
      console.error(e);
      setAiResponse("Failed to generate intelligence. Check Backend/API services.");
    } finally {
      setLoading(false);
    }
  };

  const filteredLeads = leads.filter(l => 
    (l.name?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
    (l.email?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
    (l.company?.toLowerCase() || '').includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      <header>
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-brand-indigo/10 rounded-lg text-brand-indigo">
            <Bot size={20} />
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Intelligence Engine</h1>
        </div>
        <p className="text-text-muted font-medium">AI-powered personalization and lead scoring analysis.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left: Lead Selector */}
        <aside className="lg:col-span-4 space-y-4">
          <div className="relative mb-6">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted" size={16} />
            <input 
              type="text"
              placeholder="Filter leads..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-bg-surface precision-border rounded-2xl shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-indigo/20 font-medium transition-all"
            />
          </div>

          <div className="bg-bg-surface precision-border rounded-[32px] overflow-hidden shadow-sm">
            <div className="p-5 border-b border-border-subtle bg-bg-elevated/30">
              <span className="text-[10px] font-black uppercase tracking-[.2em] text-text-muted">Target Ranking</span>
            </div>
            <div className="max-h-[600px] overflow-y-auto divide-y divide-border-subtle">
              {filteredLeads.map((lead) => (
                <button
                  key={lead.id}
                  onClick={() => setSelectedLeadId(lead.id)}
                  className={cn(
                    "w-full p-5 flex items-center justify-between transition-all group",
                    selectedLeadId === lead.id ? "bg-brand-indigo/5" : "hover:bg-bg-elevated/50"
                  )}
                >
                  <div className="flex items-center space-x-4">
                    <div className={cn(
                      "w-10 h-10 rounded-xl flex items-center justify-center font-bold text-xs border transition-colors",
                      selectedLeadId === lead.id ? "bg-brand-indigo text-white border-brand-indigo" : "bg-bg-elevated text-text-muted border-border-subtle"
                    )}>
                      {(lead.name || lead.email || '?')[0].toUpperCase()}
                    </div>
                    <div className="text-left">
                      <p className={cn("text-sm font-bold truncate transition-colors", selectedLeadId === lead.id ? "text-brand-indigo" : "text-text-main")}>{lead.name || 'Anonymous Lead'}</p>
                      <p className="text-[10px] text-text-muted font-bold uppercase tracking-wider">{lead.company || 'Private Entity'}</p>
                    </div>
                  </div>
                  <ChevronRight size={14} className={cn("transition-all", selectedLeadId === lead.id ? "text-brand-indigo translate-x-1" : "text-text-muted opacity-0 group-hover:opacity-100")} />
                </button>
              ))}
            </div>
          </div>
        </aside>

        {/* Right: Intelligence Panel */}
        <main className="lg:col-span-8 space-y-8">
          <AnimatePresence mode="wait">
            {selectedLead ? (
              <motion.div
                key={selectedLead.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-8"
              >
                {/* Lead Summary Header */}
                <div className="p-8 rounded-[40px] bg-bg-surface precision-border premium-shadow-lg flex flex-col md:flex-row gap-8 items-center border-l-8 border-l-brand-indigo">
                  <div className="w-24 h-24 rounded-3xl bg-gradient-to-tr from-brand-indigo to-violet-500 p-0.5 shadow-xl">
                    <div className="w-full h-full rounded-[22px] bg-white dark:bg-bg-surface flex items-center justify-center font-bold text-4xl text-brand-indigo">
                      {(selectedLead.name || selectedLead.email || '?')[0].toUpperCase()}
                    </div>
                  </div>
                  <div className="flex-1 text-center md:text-left">
                    <div className="inline-flex items-center px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-600 text-[10px] font-black uppercase tracking-widest mb-2 border border-amber-500/20">
                      High Growth Lead
                    </div>
                    <h2 className="text-3xl font-bold mb-1">{selectedLead.name || 'Anonymous Lead'}</h2>
                    <p className="text-lg text-text-muted font-medium">{selectedLead.title || 'Decision Maker'} @ {selectedLead.company || 'Private Entity'}</p>
                  </div>
                  <div className="flex gap-4">
                    <div className="text-center p-4 bg-bg-elevated rounded-2xl min-w-[100px] border border-border-subtle shadow-sm">
                      <p className="text-[10px] uppercase font-black tracking-widest text-text-muted mb-1">Score</p>
                      <p className="text-2xl font-bold text-brand-indigo">{selectedLead.score}</p>
                    </div>
                    <div className="text-center p-4 bg-bg-elevated rounded-2xl min-w-[100px] border border-border-subtle shadow-sm">
                      <p className="text-[10px] uppercase font-black tracking-widest text-text-muted mb-1">Tier</p>
                      <p className="text-2xl font-bold text-text-main">
                        {selectedLead.tier ? selectedLead.tier.split(' ')[1] : (selectedLead.segment === 'platinum' ? '1' : selectedLead.segment === 'gold' ? '2' : '3')}
                      </p>
                    </div>
                  </div>
                </div>

                {/* AI Interaction Area */}
                <div className="bg-bg-surface precision-border rounded-[40px] overflow-hidden premium-shadow">
                  <div className="p-8 border-b border-border-subtle bg-bg-elevated/30 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Sparkles size={20} className="text-brand-indigo" />
                      <span className="font-bold tracking-tight">AI Personalization Agent</span>
                    </div>
                    <div className="flex gap-2">
                       <span className="px-3 py-1 bg-green-500/10 border border-green-500/20 text-green-500 rounded-full text-[10px] font-black uppercase tracking-widest flex items-center gap-1.5">
                         <Zap size={10} /> Enriched Context
                       </span>
                    </div>
                  </div>

                  <div className="p-8 space-y-8">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {[
                        { icon: MessageSquare, label: 'Email Intro', color: 'text-blue-500' },
                        { icon: TrendingUp, label: 'Value Prop', color: 'text-emerald-500' },
                        { icon: Target, label: 'Objection Handle', color: 'text-amber-500' },
                      ].map((action) => (
                        <button
                          key={action.label}
                          onClick={() => handleGenerate(action.label)}
                          disabled={loading}
                          className="p-6 rounded-3xl bg-bg-elevated border border-border-subtle hover:border-brand-indigo/40 hover:bg-brand-indigo/5 transition-all text-left group"
                        >
                          <action.icon className={cn("w-6 h-6 mb-4 transition-transform group-hover:scale-110", action.color)} />
                          <p className="font-bold text-sm mb-1">{action.label}</p>
                          <p className="text-[10px] text-text-muted uppercase tracking-widest font-black flex items-center gap-1 group-hover:text-brand-indigo transition-colors">
                            Generate <ArrowRight size={10} />
                          </p>
                        </button>
                      ))}
                    </div>

                    <div className="bg-bg-elevated rounded-3xl p-8 min-h-[300px] relative precision-border">
                        {aiResponse ? (
                          <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="prose prose-sm dark:prose-invert max-w-none"
                          >
                            <p className="whitespace-pre-wrap leading-relaxed text-lg font-medium text-text-main opacity-90">
                              {aiResponse}
                            </p>
                          </motion.div>
                        ) : (
                          <div className="absolute inset-0 flex flex-col items-center justify-center text-text-muted opacity-40">
                             <Bot size={48} className="mb-4" />
                             <p className="font-bold uppercase tracking-widest text-xs">Awaiting Intelligence Request</p>
                          </div>
                        )}
                        {loading && (
                          <div className="absolute inset-0 bg-bg-surface/60 backdrop-blur-sm flex items-center justify-center rounded-3xl z-10 transition-all">
                             <div className="flex flex-col items-center gap-4">
                               <RefreshCcw className="animate-spin text-brand-indigo" size={32} />
                               <span className="font-black text-[10px] uppercase tracking-[0.3em] text-brand-indigo animate-pulse">Synthesizing Context</span>
                             </div>
                          </div>
                        )}
                    </div>

                    <div className="flex justify-end gap-4">
                       <button className="px-6 py-3 bg-bg-elevated precision-border rounded-xl font-bold text-sm hover:bg-bg-surface transition-all">
                         Save Insight
                       </button>
                       <button className="px-8 py-3 bg-brand-indigo text-white rounded-xl font-bold text-sm hover:bg-brand-indigo-hover shadow-lg shadow-brand-indigo/20 transition-all flex items-center gap-2">
                         <Send size={16} /> Deploy Strategy
                       </button>
                    </div>
                  </div>
                </div>
              </motion.div>
            ) : (
              <div className="h-[700px] flex flex-col items-center justify-center text-text-muted bg-bg-surface precision-border rounded-[40px] opacity-60">
                <Target size={64} className="mb-6 opacity-20" />
                <h3 className="text-2xl font-bold mb-2">Lead selection required</h3>
                <p className="font-medium">Select a profile from the directory to begin AI synthesis.</p>
              </div>
            )}
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
};

// Helper for conditional classes
function cn(...inputs: any[]) {
  return inputs.filter(Boolean).join(' ');
}
