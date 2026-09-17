import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
});

// Production Resilience Interceptor
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 403) {
      console.error("[Security] Invalid API Access Tier. Verify VELLUX_API_KEY.");
    }
    if (error.response?.status >= 500) {
      console.error("[Cluster] Strategic failure in Marketing Hub. Retrying...");
    }
    return Promise.reject(error);
  }
);

export interface Lead {
  id: number;
  email: string;
  score: number;
  segment: string;
  name: string | null;
  linkedin_url: string | null;
  preferred_channel: string;
  notes: string | null;
  created_at: string;
  // Extended fields for the premium UI
  company?: string;
  title?: string;
  tier?: string;
}

export interface Event {
  id: number;
  lead_id: number;
  action_type: string;
  metadata: string;
  created_at: string;
}

export interface Campaign {
  id: number;
  lead_id: number;
  channel: string;
  generated_content: string;
  sent_status: string;
  created_at: string;
}

export const getLeads = () => api.get<Lead[]>('/leads');
export const getLeadDetails = (id: number) => api.get<{ profile: Lead; events: Event[]; campaigns: Campaign[] }>(`/leads/${id}`);
export const createEvent = (email: string, action: string, metadata: any) => api.post('/events', { email, action, metadata });
export const updateProfile = (id: number, profile: Partial<Lead>) => api.patch(`/leads/${id}/profile`, profile);

/**
 * AI Generation wrapper. Takes a lead ID and a topic/instruction.
 * Maps the backend's 'generated_text' to 'content' for the UI.
 */
export const generateContent = async (id: number | string | null, topic: string) => {
  const response = await api.post('/ai/generate', { lead_id: id, topic });
  return {
    content: response.data.generated_text || "Intelligence synthesis failed. No content generated.",
    generated_text: response.data.generated_text
  };
};

export const sendCampaign = (leadId: number, channel: string, content: string) => 
  api.post('/campaigns/send', { lead_id: leadId, channel, content });

export const getStats = () => api.get('/stats');
export const getLiveEvents = (limit = 50) => api.get<any[]>(`/events/live?limit=${limit}`);
