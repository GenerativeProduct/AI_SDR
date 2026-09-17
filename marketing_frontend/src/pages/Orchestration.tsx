import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Mail, 
  MessageSquare, 
  Globe, 
  Bot, 
  Sparkles,
  RefreshCcw,
  Settings2,
  Clock,
  ShieldCheck,
  Search,
  ChevronRight,
  Cpu
} from 'lucide-react';
import { api, type Lead, generateContent, sendCampaign } from '../lib/api';

export const Orchestration: React.FC = () => {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedLeadId, setSelectedLeadId] = useState<number | null>(null);
  const [selectedLeadDetail, setSelectedLeadDetail] = useState<any>(null);
  const [selectedAgent, setSelectedAgent] = useState<'email' | 'sms' | 'social'>('email');
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
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

  useEffect(() => {
    if (selectedLeadId) {
      const fetchDetail = async () => {
        try {
          const res = await api.get(`/leads/${selectedLeadId}`);
          setSelectedLeadDetail(res.data);
        } catch (e) { console.error(e); }
      };
      fetchDetail();
    }
  }, [selectedLeadId]);

  const selectedLead = leads.find(l => l.id === selectedLeadId);

  const handleGenerate = async () => {
    if (!selectedLead) return;
    setLoading(true);
    try {
      const res = await generateContent(selectedLead.id, `Campaign draft for ${selectedAgent} channel`);
      setContent(res.content);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const handleSend = async () => {
    if (!selectedLeadId || !content) return;
    setSending(true);
    try {
      await sendCampaign(selectedLeadId, selectedAgent, content);
      // Refresh detail to show in history
      const res = await api.get(`/leads/${selectedLeadId}`);
      setSelectedLeadDetail(res.data);
      setContent('');
    } catch (e) { console.error(e); }
    finally { setSending(false); }
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
            <MessageSquare size={20} />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-text-main">Campaign Hub</h1>
        </div>
        <p className="text-text-muted font-medium">Manage your customer outreach and automated campaigns.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Lead Sidebar */}
        <aside className="lg:col-span-4 space-y-4">
          <div className="relative mb-6">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted" size={16} />
            <input 
              type="text"
              placeholder="Search leads..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-bg-surface precision-border rounded-2xl shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-indigo/20 font-medium transition-all"
            />
          </div>

          <div className="bg-bg-surface precision-border rounded-[32px] overflow-hidden shadow-sm">
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
                      "w-10 h-10 rounded-xl flex items-center justify-center font-bold text-xs border transition-colors shadow-sm",
                      selectedLeadId === lead.id ? "bg-brand-indigo text-white border-brand-indigo" : "bg-bg-elevated text-text-muted border-border-subtle"
                    )}>
                      {(lead.name || lead.email || '?')[0].toUpperCase()}
                    </div>
                    <div className="text-left">
                      <p className={cn("text-sm font-bold truncate transition-colors", selectedLeadId === lead.id ? "text-brand-indigo" : "text-text-main")}>{lead.name || 'Anonymous User'}</p>
                      <span className="text-[10px] text-text-muted font-bold uppercase tracking-wider">{lead.company || 'Private Business'}</span>
                    </div>
                  </div>
                  <ChevronRight size={14} className={cn("transition-all", selectedLeadId === lead.id ? "text-brand-indigo translate-x-1" : "text-text-muted opacity-0 group-hover:opacity-100")} />
                </button>
              ))}
            </div>
          </div>
        </aside>

        {/* Orchestration Control Plane */}
        <main className="lg:col-span-8 space-y-8">
          <AnimatePresence mode="wait">
            {selectedLeadId ? (
              <motion.div
                key={selectedLeadId}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-8"
              >
                {/* Deployment Workbench */}
                <div className="bg-bg-surface precision-border rounded-[40px] overflow-hidden premium-shadow">
                  <div className="p-8 border-b border-border-subtle bg-bg-elevated/30 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Settings2 size={20} className="text-brand-indigo" />
                      <span className="font-bold tracking-tight">Message Builder</span>
                    </div>
                    <div className="flex items-center px-3 py-1 bg-green-500/10 border border-green-500/20 rounded-full">
                      <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse mr-2" />
                      <span className="text-[10px] font-black uppercase tracking-widest text-green-500">Ready to Send</span>
                    </div>
                  </div>

                  <div className="p-10 space-y-10">
                    {/* Agent Swarm Selection */}
                    <div className="space-y-6">
                        <label className="text-[11px] font-black uppercase tracking-[0.2em] text-text-muted text-center block">How to Send</label>
                        <div className="grid grid-cols-4 gap-4">
                          {[
                            { id: 'email', icon: Mail, label: 'Email', desc: 'Send Message' },
                            { id: 'sms', icon: MessageSquare, label: 'Text / SMS', desc: 'Direct Phone' },
                            { id: 'social', icon: Globe, label: 'Social', desc: 'Network Hub' },
                            { id: 'auto_agent', icon: Cpu, label: 'AI Pilot', desc: 'Automated' },
                          ].map(agent => (
                          <button
                            key={agent.id}
                            onClick={() => setSelectedAgent(agent.id as any)}
                            className={cn(
                              "p-6 rounded-3xl border-2 transition-all text-center group",
                              selectedAgent === agent.id 
                                ? "bg-bg-elevated border-brand-indigo shadow-lg ring-4 ring-brand-indigo/5" 
                                : "bg-bg-elevated/50 border-transparent hover:border-border-subtle grayscale hover:grayscale-0"
                            )}
                          >
                            <agent.icon size={24} className={cn("mx-auto mb-3 transition-transform group-hover:scale-110", selectedAgent === agent.id ? "text-brand-indigo" : "text-text-muted")} />
                            <p className="font-bold text-xs">{agent.label}</p>
                            <p className="text-[9px] text-text-muted font-bold tracking-widest uppercase mt-1 opacity-60">{agent.desc}</p>
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="space-y-4 pt-6 border-t border-border-subtle">
                      <div className="flex items-center justify-between mb-2">
                        <label className="text-[11px] font-black uppercase tracking-[0.2em] text-text-muted pl-1">Your Message</label>
                        <button 
                          onClick={handleGenerate}
                          disabled={loading}
                          className="text-[10px] font-black uppercase tracking-widest text-brand-indigo flex items-center gap-2 hover:opacity-80 disabled:opacity-50"
                        >
                          {loading ? <RefreshCcw size={12} className="animate-spin" /> : <Sparkles size={12} />}
                          AI Help
                        </button>
                      </div>
                      <div className="relative">
                        <textarea 
                          rows={10}
                          value={content}
                          onChange={(e) => setContent(e.target.value)}
                          placeholder="AI is ready to help you write a message..."
                          className="w-full p-8 bg-bg-elevated border border-border-subtle rounded-3xl text-lg font-medium leading-relaxed focus:outline-none focus:ring-2 focus:ring-brand-indigo/20 transition-all resize-none"
                        />
                        <AnimatePresence>
                          {loading && (
                            <motion.div 
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              className="absolute inset-0 bg-bg-surface/40 backdrop-blur-sm flex items-center justify-center rounded-3xl"
                            >
                              <div className="flex flex-col items-center gap-3">
                                 <RefreshCcw size={32} className="animate-spin text-brand-indigo" />
                                 <span className="font-black text-[10px] uppercase tracking-[0.3em] text-brand-indigo">AI is writing...</span>
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    </div>

                    <div className="flex justify-between items-center bg-bg-elevated p-6 rounded-3xl border border-border-subtle">
                        <div className="flex items-center gap-3">
                          <Bot className="text-brand-indigo" size={24} />
                          <div className="text-left">
                            <p className="text-xs font-bold uppercase tracking-widest text-text-muted">Target Identity</p>
                            <p className="text-sm font-bold">{selectedLead?.name || 'Anonymous'} &lt;{selectedLead?.email}&gt;</p>
                          </div>
                        </div>
                        <button
                          onClick={handleSend}
                          disabled={sending || !content}
                          className="px-12 py-4 bg-brand-indigo hover:bg-brand-indigo-hover text-white rounded-2xl font-bold flex items-center space-x-3 transition-all shadow-xl shadow-brand-indigo/20 disabled:opacity-50"
                        >
                          <span>Send Message</span>
                        </button>
                    </div>
                  </div>
                </div>

                {/* Historical Audit Ledger */}
                <div className="bg-bg-surface precision-border rounded-[40px] overflow-hidden premium-shadow">
                  <div className="p-8 border-b border-border-subtle bg-bg-elevated/30 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Clock size={20} className="text-brand-indigo" />
                      <span className="font-bold tracking-tight">Past Messages</span>
                    </div>
                  </div>
                  <div className="p-8">
                    {selectedLeadDetail?.campaigns?.length > 0 ? (
                      <div className="space-y-4">
                        {selectedLeadDetail.campaigns.map((camp: any) => (
                          <div key={camp.id} className="p-5 bg-bg-elevated rounded-2xl border border-border-subtle flex items-start justify-between group">
                            <div className="flex gap-4">
                              <div className="mt-1 p-2 bg-brand-indigo/10 text-brand-indigo rounded-lg">
                                {camp.channel === 'email' ? <Mail size={16} /> : <Cpu size={16} />}
                              </div>
                              <div>
                                <p className="text-sm font-bold line-clamp-1">{camp.generated_content}</p>
                                <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest mt-1">
                                  {new Date(camp.created_at).toLocaleString()} • {camp.channel}
                                </p>
                              </div>
                            </div>
                            <span className="px-2 py-0.5 bg-green-500/10 text-green-500 text-[9px] font-black uppercase tracking-widest rounded border border-green-500/20">
                              {camp.sent_status}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="py-12 text-center opacity-40">
                        <MessageSquare className="mx-auto mb-3" size={32} />
                        <p className="text-xs font-black uppercase tracking-widest">No previous dispatch records</p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="p-6 bg-bg-surface precision-border rounded-3xl flex items-center justify-between group hover:border-brand-indigo/30 transition-all">
                    <div className="flex items-center gap-4">
                      <div className="p-2 bg-bg-elevated rounded-xl text-emerald-500">
                        <ShieldCheck size={18} />
                      </div>
                      <div>
                        <p className="text-[10px] font-black uppercase tracking-widest text-text-muted">Security</p>
                        <p className="text-sm font-extrabold">Protected</p>
                      </div>
                    </div>
                  </div>
                  <div className="p-6 bg-bg-surface precision-border rounded-3xl flex items-center justify-between group hover:border-brand-indigo/30 transition-all">
                    <div className="flex items-center gap-4">
                      <div className="p-2 bg-bg-elevated rounded-xl text-blue-500">
                        <Clock size={18} />
                      </div>
                      <div>
                        <p className="text-[10px] font-black uppercase tracking-widest text-text-muted">Speed</p>
                        <p className="text-sm font-extrabold">Fast</p>
                      </div>
                    </div>
                  </div>
                  <div className="p-6 bg-bg-surface precision-border rounded-3xl flex items-center justify-between group hover:border-brand-indigo/30 transition-all">
                    <div className="flex items-center gap-4">
                      <div className={cn("p-2 bg-bg-elevated rounded-xl text-violet-500")}>
                        <Bot size={18} />
                      </div>
                      <div>
                        <p className="text-[10px] font-black uppercase tracking-widest text-text-muted">AI Help</p>
                        <p className="text-sm font-extrabold">Online</p>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            ) : (
              <div className="h-[700px] flex flex-col items-center justify-center text-text-muted bg-bg-surface precision-border rounded-[40px] opacity-60">
                <MessageSquare size={64} className="mb-6 opacity-20" />
                <h3 className="text-2xl font-bold mb-2">Select a Customer</h3>
                <p className="font-medium">Pick a customer from the list to start sending messages.</p>
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
