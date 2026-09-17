import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, 
  Activity, 
  Mail, 
  Zap, 
  Target,
  ExternalLink
} from 'lucide-react';
import { api, type Lead, type Event, type Campaign } from '../lib/api';

interface LeadDetailDrawerProps {
  leadId: number | null;
  onClose: () => void;
}

export const LeadDetailDrawer: React.FC<LeadDetailDrawerProps> = ({ leadId, onClose }) => {
  const [data, setData] = useState<{ profile: Lead, events: Event[], campaigns: Campaign[] } | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (leadId) {
      const fetchDetail = async () => {
        setLoading(true);
        try {
          const res = await api.get(`/leads/${leadId}`);
          setData(res.data);
        } catch (err) {
          console.error("Failed to hydrate lead intelligence:", err);
        } finally {
          setLoading(false);
        }
      };
      fetchDetail();
    }
  }, [leadId]);

  return (
    <AnimatePresence>
      {leadId && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[100]"
          />

          {/* Drawer */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed top-0 right-0 h-full w-full max-w-lg bg-bg-surface precision-border-l z-[101] overflow-y-auto premium-shadow"
          >
            <div className="p-8 space-y-10">
              {/* Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-2xl bg-brand-indigo flex items-center justify-center font-bold text-white text-xl">
                    {(data?.profile?.name || data?.profile?.email || '?')[0].toUpperCase()}
                  </div>
                  <div>
                    <h2 className="text-xl font-bold tracking-tight">{data?.profile?.name || 'Anonymous User'}</h2>
                    <p className="text-sm font-medium text-text-muted uppercase tracking-wider">{data?.profile?.email}</p>
                  </div>
                </div>
                <button 
                  onClick={onClose}
                  className="p-2 hover:bg-bg-elevated rounded-xl transition-colors text-text-muted"
                >
                  <X size={20} />
                </button>
              </div>

              {loading ? (
                <div className="flex flex-col items-center justify-center py-20 space-y-4">
                  <div className="w-8 h-8 border-4 border-brand-indigo border-t-transparent rounded-full animate-spin" />
                  <p className="text-xs font-bold uppercase tracking-widest text-text-muted">Loading Information...</p>
                </div>
              ) : data && (
                <>
                  {/* Stats Grid */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-5 rounded-3xl bg-bg-elevated/50 precision-border">
                      <p className="text-[10px] font-black uppercase tracking-widest text-text-muted mb-1">Interest Score</p>
                      <div className="flex items-center gap-2">
                        <Zap size={14} className="text-amber-500" />
                        <span className="text-2xl font-black">{data.profile.score}</span>
                      </div>
                    </div>
                    <div className="p-5 rounded-3xl bg-bg-elevated/50 precision-border">
                      <p className="text-[10px] font-black uppercase tracking-widest text-text-muted mb-1">Customer Level</p>
                      <div className="flex items-center gap-2">
                        <Target size={14} className="text-brand-indigo" />
                        <span className="text-2xl font-black uppercase">{data.profile.segment}</span>
                      </div>
                    </div>
                  </div>

                  {/* Metadata Sections */}
                  <div className="space-y-6">
                    <h3 className="text-xs font-black uppercase tracking-widest text-brand-indigo border-b border-border-subtle pb-2">Customer Profile</h3>
                    <div className="grid grid-cols-1 gap-4 text-sm font-medium">
                      <div className="flex justify-between py-2 border-b border-border-subtle/50">
                        <span className="text-text-muted">Current Role</span>
                        <span>{data.profile.title || 'Team Member'}</span>
                      </div>
                      <div className="flex justify-between py-2 border-b border-border-subtle/50">
                        <span className="text-text-muted">Company</span>
                        <span>{data.profile.company || 'Business Partner'}</span>
                      </div>
                      <div className="flex justify-between py-2 border-b border-border-subtle/50">
                        <span className="text-text-muted">Preferred Channel</span>
                        <span className="flex items-center gap-2">
                          <Mail size={12} /> {data.profile.preferred_channel}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* History Timeline */}
                  <div className="space-y-6">
                    <h3 className="text-xs font-black uppercase tracking-widest text-brand-indigo border-b border-border-subtle pb-2">Action History</h3>
                    <div className="space-y-4">
                      {data?.events?.map((event: any, i: number) => (
                        <div key={event.id} className="flex gap-4 group">
                          <div className="flex flex-col items-center">
                            <div className="w-2.5 h-2.5 rounded-full bg-brand-indigo" />
                            {i !== data.events.length - 1 && <div className="w-0.5 h-full bg-border-subtle mt-1" />}
                          </div>
                          <div className="pb-6">
                            <p className="text-[10px] text-text-muted font-bold mb-1">
                              {new Date(event.created_at).toLocaleString()}
                            </p>
                            <p className="text-sm font-bold capitalize">
                              {event.action_type.replace(/_/g, ' ')}
                            </p>
                          </div>
                        </div>
                      ))}
                      {data.events.length === 0 && (
                        <div className="py-10 text-center opacity-40">
                          <Activity size={32} className="mx-auto mb-2" />
                          <p className="text-xs font-bold uppercase tracking-widest">No Activity Yet</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Footer Actions */}
                  <div className="pt-10">
                    <button className="w-full py-4 bg-brand-indigo text-white font-bold rounded-2xl premium-shadow flex items-center justify-center gap-2 hover:bg-brand-indigo-dark transition-all">
                      <ExternalLink size={18} />
                      View Campaigns
                    </button>
                  </div>
                </>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
