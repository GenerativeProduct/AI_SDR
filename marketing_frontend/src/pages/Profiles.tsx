import React, { useEffect, useState } from 'react';
import { 
  Users, 
  Globe, 
  Mail, 
  MessageCircle, 
  Save,
  CheckCircle2,
  AlertCircle,
  Building2,
  Briefcase,
  Layers,
  Search,
  ChevronRight
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { api, type Lead, updateProfile } from '../lib/api';

export const Profiles: React.FC = () => {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedLeadId, setSelectedLeadId] = useState<number | null>(null);
  const [formData, setFormData] = useState<Partial<Lead>>({});
  const [status, setStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');
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

  const handleSelectLead = (lead: Lead) => {
    setSelectedLeadId(lead.id);
    setFormData(lead);
    setStatus('idle');
  };

  const handleSave = async () => {
    if (!selectedLeadId || !formData) return;
    setStatus('saving');
    try {
      await updateProfile(selectedLeadId, formData);
      setStatus('success');
      fetchLeads();
      setTimeout(() => setStatus('idle'), 3000);
    } catch (e) {
      console.error(e);
      setStatus('error');
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
            <Users size={20} />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-text-main">Lead Directory</h1>
        </div>
        <p className="text-text-muted font-medium">Management of 360° customer profiles and orchestration metadata.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Lead List */}
        <aside className="lg:col-span-4 space-y-4">
          <div className="relative mb-6">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted" size={16} />
            <input 
              type="text"
              placeholder="Search directory..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-bg-surface precision-border rounded-2xl shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-indigo/20 font-medium transition-all"
            />
          </div>

          <div className="bg-bg-surface precision-border rounded-[32px] overflow-hidden shadow-sm">
            <div className="max-h-[700px] overflow-y-auto divide-y divide-border-subtle">
              {filteredLeads.map((lead) => (
                <button
                  key={lead.id}
                  onClick={() => handleSelectLead(lead)}
                  className={cn(
                    "w-full p-5 flex items-center justify-between transition-all group",
                    selectedLeadId === lead.id ? "bg-brand-indigo/5" : "hover:bg-bg-elevated/50"
                  )}
                >
                  <div className="flex items-center space-x-4">
                    <div className={cn(
                      "w-10 h-10 rounded-xl flex items-center justify-center font-bold text-xs ring-1 ring-border-subtle shadow-sm transition-all",
                      selectedLeadId === lead.id ? "bg-brand-indigo text-white ring-brand-indigo" : "bg-bg-elevated text-text-muted"
                    )}>
                      {(lead.name || lead.email || '?')[0].toUpperCase()}
                    </div>
                    <div className="text-left">
                      <p className={cn("text-sm font-bold truncate transition-colors", selectedLeadId === lead.id ? "text-brand-indigo" : "text-text-main")}>{lead.name || 'Anonymous Lead'}</p>
                      <p className="text-[10px] text-text-muted font-bold uppercase tracking-wider">{lead.company || 'Enterprise Partner'}</p>
                    </div>
                  </div>
                  <ChevronRight size={14} className={cn("transition-all", selectedLeadId === lead.id ? "text-brand-indigo translate-x-1" : "text-text-muted opacity-0 group-hover:opacity-100")} />
                </button>
              ))}
            </div>
          </div>
        </aside>

        {/* Profile Editor */}
        <main className="lg:col-span-8">
          <AnimatePresence mode="wait">
            {selectedLeadId ? (
              <motion.div
                key={selectedLeadId}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-6"
              >
                <div className="bg-bg-surface precision-border rounded-[40px] overflow-hidden premium-shadow">
                  <div className="p-8 border-b border-border-subtle bg-bg-elevated/30 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Layers size={20} className="text-brand-indigo" />
                      <span className="font-bold tracking-tight">Identity Management</span>
                    </div>
                    <div className="flex items-center gap-2">
                       <span className="px-3 py-1 bg-brand-indigo/10 text-brand-indigo rounded-full text-[10px] font-black uppercase tracking-widest border border-brand-indigo/20">
                         {formData.segment || 'Bronze'}
                       </span>
                    </div>
                  </div>

                  <div className="p-10 space-y-10">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                      {/* Name */}
                      <div className="space-y-2">
                        <label className="text-[11px] font-black text-text-muted uppercase tracking-[0.2em] pl-1">Full Name</label>
                        <div className="relative group">
                          <Users className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted group-focus-within:text-brand-indigo transition-colors" size={18} />
                          <input 
                            type="text" 
                            value={formData.name || ''}
                            onChange={(e) => setFormData({...formData, name: e.target.value})}
                            className="w-full pl-12 pr-6 py-4 bg-bg-elevated border border-border-subtle rounded-2xl text-lg font-bold focus:outline-none focus:ring-2 focus:ring-brand-indigo/20 transition-all"
                          />
                        </div>
                      </div>

                      {/* Email */}
                      <div className="space-y-2">
                        <label className="text-[11px] font-black text-text-muted uppercase tracking-[0.2em] pl-1">Primary Email</label>
                        <div className="relative group">
                          <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted group-focus-within:text-brand-indigo transition-colors" size={18} />
                          <input 
                            type="email" 
                            value={formData.email || ''}
                            onChange={(e) => setFormData({...formData, email: e.target.value})}
                            className="w-full pl-12 pr-6 py-4 bg-bg-elevated border border-border-subtle rounded-2xl text-lg font-bold focus:outline-none focus:ring-2 focus:ring-brand-indigo/20 transition-all"
                          />
                        </div>
                      </div>

                      {/* Title */}
                      <div className="space-y-2">
                        <label className="text-[11px] font-black text-text-muted uppercase tracking-[0.2em] pl-1">Professional Title</label>
                        <div className="relative group">
                          <Briefcase className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted group-focus-within:text-brand-indigo transition-colors" size={18} />
                          <input 
                            type="text" 
                            value={formData.title || ''}
                            onChange={(e) => setFormData({...formData, title: e.target.value})}
                            className="w-full pl-12 pr-6 py-4 bg-bg-elevated border border-border-subtle rounded-2xl text-lg font-bold focus:outline-none focus:ring-2 focus:ring-brand-indigo/20 transition-all"
                          />
                        </div>
                      </div>

                      {/* Company */}
                      <div className="space-y-2">
                        <label className="text-[11px] font-black text-text-muted uppercase tracking-[0.2em] pl-1">Enterprise Unit</label>
                        <div className="relative group">
                          <Building2 className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted group-focus-within:text-brand-indigo transition-colors" size={18} />
                          <input 
                            type="text" 
                            value={formData.company || ''}
                            onChange={(e) => setFormData({...formData, company: e.target.value})}
                            className="w-full pl-12 pr-6 py-4 bg-bg-elevated border border-border-subtle rounded-2xl text-lg font-bold focus:outline-none focus:ring-2 focus:ring-brand-indigo/20 transition-all"
                          />
                        </div>
                      </div>

                      {/* LinkedIn */}
                      <div className="space-y-2 md:col-span-2">
                        <label className="text-[11px] font-black text-text-muted uppercase tracking-[0.2em] pl-1">Professional Discovery URL</label>
                        <div className="relative group">
                          <Globe className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted group-focus-within:text-brand-indigo transition-colors" size={18} />
                          <input 
                            type="text" 
                            placeholder="https://linkedin.com/in/..."
                            value={formData.linkedin_url || ''}
                            onChange={(e) => setFormData({...formData, linkedin_url: e.target.value})}
                            className="w-full pl-12 pr-6 py-4 bg-bg-elevated border border-border-subtle rounded-2xl text-lg font-bold focus:outline-none focus:ring-2 focus:ring-brand-indigo/20 transition-all"
                          />
                        </div>
                      </div>
                    </div>

                    <div className="space-y-4 pt-4">
                      <label className="text-[11px] font-black text-text-muted uppercase tracking-[0.2em] pl-1 text-center block">Channel Optimization Preference</label>
                      <div className="flex flex-wrap justify-center gap-4">
                        {[
                          { id: 'email', label: 'E-mail', icon: Mail },
                          { id: 'sms', label: 'SMS', icon: MessageCircle },
                          { id: 'linkedin_dm', label: 'LinkedIn DM', icon: Globe },
                        ].map(chan => (
                          <button
                            key={chan.id}
                            className={cn(
                              "px-8 py-3 rounded-2xl flex items-center space-x-3 border-2 transition-all font-bold text-sm",
                              "hover:border-brand-indigo/50",
                              formData.preferred_channel === chan.id 
                                ? "bg-brand-indigo text-white border-brand-indigo shadow-lg shadow-brand-indigo/20" 
                                : "bg-bg-elevated text-text-muted border-transparent"
                            )}
                            onClick={() => setFormData({...formData, preferred_channel: chan.id})}
                          >
                            <chan.icon size={18} />
                            <span>{chan.label}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="p-8 bg-bg-elevated/50 border-t border-border-subtle flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <AnimatePresence>
                        {status === 'saving' && <motion.div initial={{opacity:0}} animate={{opacity:1}}><CheckCircle2 className="animate-pulse text-brand-indigo" size={20} /></motion.div>}
                        {status === 'success' && <motion.div initial={{scale:0}} animate={{scale:1}} className="text-green-500 flex items-center gap-2 font-bold text-xs uppercase tracking-widest"><CheckCircle2 size={18} /> Profile Synchronized</motion.div>}
                        {status === 'error' && <motion.div initial={{scale:0}} animate={{scale:1}} className="text-red-500 flex items-center gap-2 font-bold text-xs uppercase tracking-widest"><AlertCircle size={18} /> Update Failed</motion.div>}
                      </AnimatePresence>
                    </div>
                    <button
                      onClick={handleSave}
                      disabled={status === 'saving'}
                      className="px-12 py-4 bg-brand-indigo hover:bg-brand-indigo-hover text-white rounded-2xl font-bold flex items-center space-x-3 transition-all shadow-xl shadow-brand-indigo/20 disabled:opacity-50"
                    >
                      <Save size={20} />
                      <span>Update Profile</span>
                    </button>
                  </div>
                </div>
              </motion.div>
            ) : (
              <div className="h-[700px] flex flex-col items-center justify-center text-text-muted bg-bg-surface precision-border rounded-[40px] opacity-60">
                <Users size={64} className="mb-6 opacity-20" />
                <h3 className="text-2xl font-bold mb-2">Profile not selected</h3>
                <p className="font-medium">Browse the enterprise directory to manage identity nodes.</p>
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
