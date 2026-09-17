import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Shield, 
  Key, 
  Cpu, 
  Globe,
  Sparkles,
  Lock,
  Zap,
  Copy,
  Check,
  Code
} from 'lucide-react';

export const Settings: React.FC = () => {
  const [copied, setCopied] = useState(false);
  const API_KEY = "vellux_studio_2026_pk";
  const WEBHOOK_URL = "http://localhost:8000/webhook";

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const webhookSnippet = `fetch("${WEBHOOK_URL}", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-API-KEY": "${API_KEY}"
  },
  body: JSON.stringify({
    id: "evt_" + Date.now(),
    type: "external_lead_action",
    actor: { email: "prospect@enterprise.com" },
    content: { source: "main_website", value: 5000 }
  })
});`;

  const settingsSections = [
    {
      title: 'Neural Core Integration',
      icon: Cpu,
      items: [
        { label: 'LLM Model Node', value: 'HuggingFace - flan-t5-large', icon: Sparkles },
        { label: 'Contextual Engine', value: 'Active (Hyper-Personalization)', icon: Zap },
      ]
    },
    {
      title: 'Network & Security',
      icon: Shield,
      items: [
        { label: 'API Security Protocol', value: 'X-API-KEY (Restricted)', icon: Lock },
        { label: 'Outbound Proxy', value: 'Static Node: 45.23.1.92', icon: Globe },
      ]
    }
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-12 pb-20">
      <header>
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-brand-indigo/10 rounded-lg text-brand-indigo">
            <Lock size={20} />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-text-main">System Governance</h1>
        </div>
        <p className="text-text-muted font-medium">Control plane for autonomous orchestration and external data ingestion.</p>
      </header>

      {/* Integration Console */}
      <section className="bg-bg-surface precision-border rounded-[40px] overflow-hidden premium-shadow">
        <div className="px-10 py-8 border-b border-border-subtle bg-bg-elevated/30 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-2 bg-brand-indigo/10 rounded-xl text-brand-indigo">
              <Code size={20} />
            </div>
            <h3 className="font-bold tracking-tight text-xl">Developer Mesh Integration</h3>
          </div>
          <div className="flex items-center space-x-2 px-3 py-1 bg-green-500/10 border border-green-500/20 rounded-full">
            <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
            <span className="text-[10px] font-black uppercase tracking-widest text-green-500">Gateway Active</span>
          </div>
        </div>
        
        <div className="p-10 space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-4">
              <label className="text-[11px] font-black text-text-muted uppercase tracking-[0.2em] pl-1">Webhook Endpoint</label>
              <div className="flex items-center gap-2 p-4 bg-bg-elevated rounded-2xl border border-border-subtle font-mono text-xs overflow-x-auto whitespace-nowrap">
                <Globe size={14} className="text-text-muted flex-shrink-0" />
                <span className="flex-1">{WEBHOOK_URL}</span>
                <button onClick={() => copyToClipboard(WEBHOOK_URL)} className="p-2 hover:bg-bg-surface rounded-lg transition-colors">
                  <Copy size={14} className="text-brand-indigo" />
                </button>
              </div>
            </div>
            <div className="space-y-4">
              <label className="text-[11px] font-black text-text-muted uppercase tracking-[0.2em] pl-1">Master Access Key</label>
              <div className="flex items-center gap-2 p-4 bg-bg-elevated rounded-2xl border border-border-subtle font-mono text-xs">
                <Key size={14} className="text-text-muted flex-shrink-0" />
                <span className="flex-1 font-bold">●●●●●●●●●●●●●●●●</span>
                <button onClick={() => copyToClipboard(API_KEY)} className="p-2 hover:bg-bg-surface rounded-lg transition-colors">
                  {copied ? <Check size={14} className="text-green-500" /> : <Copy size={14} className="text-brand-indigo" />}
                </button>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <label className="text-[11px] font-black text-text-muted uppercase tracking-[0.2em] pl-1">Ingestion Snippet (JavaScript)</label>
            <div className="relative group">
              <pre className="p-6 bg-bg-elevated rounded-3xl border border-border-subtle font-mono text-xs overflow-x-auto leading-relaxed text-text-main/80">
                {webhookSnippet}
              </pre>
              <button 
                onClick={() => copyToClipboard(webhookSnippet)}
                className="absolute top-4 right-4 p-3 bg-bg-surface precision-border rounded-xl opacity-0 group-hover:opacity-100 transition-opacity shadow-sm"
              >
                <Copy size={16} className="text-brand-indigo" />
              </button>
            </div>
          </div>
        </div>
      </section>

      <div className="space-y-8">
        {settingsSections.map((section, sIdx) => (
          <motion.div
            key={section.title}
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: sIdx * 0.1 }}
            className="bg-bg-surface precision-border rounded-[40px] overflow-hidden premium-shadow"
          >
            <div className="px-10 py-6 border-b border-border-subtle bg-bg-elevated/30 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="p-2 bg-bg-surface precision-border rounded-xl">
                  <section.icon size={18} className="text-brand-indigo" />
                </div>
                <h3 className="font-bold tracking-tight text-lg">{section.title}</h3>
              </div>
            </div>
            
            <div className="p-10 grid grid-cols-1 md:grid-cols-2 gap-8">
              {section.items.map((item) => (
                <div key={item.label} className="p-6 bg-bg-base/50 precision-border rounded-3xl group hover:border-brand-indigo/30 transition-all flex items-start gap-4">
                  <div className="p-3 bg-white dark:bg-bg-surface precision-border rounded-2xl text-text-muted group-hover:text-brand-indigo transition-colors shadow-sm">
                    <item.icon size={20} />
                  </div>
                  <div className="flex-1">
                    <p className="text-[10px] font-black uppercase tracking-widest text-text-muted mb-1">{item.label}</p>
                    <p className="text-sm font-extrabold text-text-main group-hover:text-brand-indigo transition-colors">{item.value}</p>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Advanced Control Footer */}
      <div className="p-10 bg-brand-indigo rounded-[40px] text-white flex flex-col md:flex-row items-center justify-between gap-8 premium-shadow relative overflow-hidden group">
         <div className="absolute top-0 right-0 p-8 opacity-10 scale-150 rotate-12 group-hover:rotate-0 transition-transform duration-1000">
           <Cpu size={160} />
         </div>
         <div className="relative z-10 text-center md:text-left">
           <h4 className="text-2xl font-bold mb-2">Autonomous Governance</h4>
           <p className="text-white/70 font-medium text-sm">Monitor lead mesh health and raw telemetry traffic across the autonomous node cluster.</p>
         </div>
         <div className="flex gap-4 relative z-10">
           <button className="px-8 py-3 bg-white/10 hover:bg-white/20 backdrop-blur-md rounded-2xl font-bold text-sm transition-all border border-white/20">
             Cluster Metrics
           </button>
           <button className="px-8 py-3 bg-white text-brand-indigo rounded-2xl font-bold text-sm hover:bg-white/90 shadow-xl transition-all">
             Audit Mesh
           </button>
         </div>
      </div>
    </div>
  );
};
