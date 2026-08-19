import { useState, useCallback, useEffect } from 'react';
import {
  Phone, PhoneOff, Shield, Search, CheckCircle, Clock,
  AlertTriangle, MicOff, UserPlus, Users, X, Loader2
} from 'lucide-react';
import {
  LiveKitRoom,
  useVoiceAssistant,
  BarVisualizer,
  RoomAudioRenderer,
  VoiceAssistantControlBar,
} from '@livekit/components-react';
import '@livekit/components-styles';

const API_URL = 'http://localhost:8000';

interface Customer {
  id: string;
  name: string;
  phone_number: string;
  language_preference: string;
}

type View = 'home' | 'call';

export default function Dashboard() {
  const [view, setView] = useState<View>('home');
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [roomName, setRoomName] = useState<string>('');
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Fetch customers on mount
  useEffect(() => {
    fetchCustomers();
  }, []);

  const fetchCustomers = async () => {
    try {
      const res = await fetch(`${API_URL}/customers`);
      const data = await res.json();
      setCustomers(data.customers || []);
    } catch {
      // Backend might not be running yet
    }
  };

  const handleStartCall = useCallback(async (customer: Customer) => {
    setIsConnecting(true);
    setError(null);
    setSelectedCustomer(customer);
    try {
      const res = await fetch(`${API_URL}/getToken`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ participant_name: customer.name, customer_id: customer.id }),
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to get token');
      }
      const data = await res.json();
      setToken(data.token);
      setRoomName(data.room_name);
      setView('call');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Connection failed. Is the backend running?');
    } finally {
      setIsConnecting(false);
    }
  }, []);

  const handleEndCall = () => {
    setToken(null);
    setSelectedCustomer(null);
    setView('home');
    fetchCustomers(); // Refresh list
  };

  if (view === 'call' && token && selectedCustomer) {
    return (
      <CallView
        token={token}
        roomName={roomName}
        customer={selectedCustomer}
        onEnd={handleEndCall}
      />
    );
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8 flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-500">
            Continuum Banking
          </h1>
          <p className="text-slate-400 mt-1">Persistent Multilingual AI Agent — Operator Dashboard</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 transition-colors text-white px-4 py-2 rounded-xl font-medium"
        >
          <UserPlus size={16} /> New Customer
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-900/50 border border-red-700 rounded-xl text-red-300 flex justify-between items-center">
          <span>⚠️ {error}</span>
          <button onClick={() => setError(null)}><X size={14} /></button>
        </div>
      )}

      {/* Customer List */}
      <div className="bg-slate-800/60 rounded-2xl border border-slate-700 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-700 flex items-center gap-2">
          <Users size={18} className="text-blue-400" />
          <h2 className="text-lg font-semibold">Registered Customers</h2>
          <span className="ml-auto text-slate-400 text-sm">{customers.length} total</span>
          <button onClick={fetchCustomers} className="text-slate-400 hover:text-white text-xs">↻ Refresh</button>
        </div>

        {customers.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <UserPlus size={32} className="mx-auto mb-3 opacity-50" />
            <p className="font-medium">No customers yet</p>
            <p className="text-sm mt-1">Click "New Customer" to register the first one.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-700">
            {customers.map((customer) => (
              <div key={customer.id} className="px-6 py-4 flex items-center justify-between hover:bg-slate-700/30 transition-colors">
                <div>
                  <p className="font-medium text-white">{customer.name}</p>
                  <p className="text-sm text-slate-400">{customer.phone_number} · {customer.language_preference}</p>
                  <p className="text-xs text-slate-500 font-mono">{customer.id}</p>
                </div>
                <button
                  onClick={() => handleStartCall(customer)}
                  disabled={isConnecting}
                  className="flex items-center gap-2 bg-green-600 hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-white px-4 py-2 rounded-xl text-sm font-medium"
                >
                  {isConnecting && selectedCustomer?.id === customer.id ? (
                    <Loader2 size={14} className="animate-spin" />
                  ) : (
                    <Phone size={14} />
                  )}
                  Start Call
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Customer Modal */}
      {showCreateModal && (
        <CreateCustomerModal
          onClose={() => setShowCreateModal(false)}
          onCreated={() => {
            setShowCreateModal(false);
            fetchCustomers();
          }}
        />
      )}
    </div>
  );
}

// ─── Call View ──────────────────────────────────────────────────────────────

function CallView({ token, roomName, customer, onEnd }: {
  token: string;
  roomName: string;
  customer: Customer;
  onEnd: () => void;
}) {
  const livekitUrl = import.meta.env.VITE_LIVEKIT_URL || 'wss://aimanthan-3mucbuid.livekit.cloud';
  const [latency] = useState({ stt: 310, llm: 820, tts: 390 });

  return (
    <div className="p-8 max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* Header */}
      <div className="col-span-3 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-500">
            Continuum Banking
          </h1>
          <p className="text-slate-400 text-sm">{customer.name} · {customer.id}</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-slate-800 px-3 py-1.5 rounded-full border border-slate-700 text-xs">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            LIVE · {roomName}
          </div>
          <button
            onClick={onEnd}
            className="flex items-center gap-2 bg-red-700 hover:bg-red-600 transition-colors text-white px-4 py-2 rounded-xl text-sm font-medium"
          >
            <PhoneOff size={14} /> End Call
          </button>
        </div>
      </div>

      {/* LiveKit Room */}
      <LiveKitRoom
        serverUrl={livekitUrl}
        token={token}
        connect={true}
        audio={true}
        video={false}
        onDisconnected={onEnd}
        className="col-span-3 grid grid-cols-1 md:grid-cols-3 gap-6"
      >
        {/* Agent Visualizer */}
        <div className="bg-slate-800/60 p-6 rounded-2xl border border-slate-700 shadow-xl col-span-2 flex flex-col justify-between">
          <div>
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Phone className="text-blue-400" size={18} /> Live Conversation
            </h2>
            <div className="h-40 flex items-center justify-center">
              <AgentVisualizer />
            </div>
          </div>
          <div className="mt-4 flex justify-center">
            <VoiceAssistantControlBar />
            <RoomAudioRenderer />
          </div>
        </div>

        {/* Session Info */}
        <div className="bg-slate-800/60 p-6 rounded-2xl border border-slate-700 shadow-xl">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <CheckCircle className="text-green-400" size={18} /> Session Info
          </h2>
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">Customer</span>
              <span className="font-medium text-white truncate ml-2">{customer.name}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">ID</span>
              <span className="font-mono text-xs text-slate-300">{customer.id}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">Language</span>
              <span className="font-medium text-white capitalize">{customer.language_preference}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">Room</span>
              <span className="font-mono text-xs text-slate-300 truncate ml-2">{roomName}</span>
            </div>
            <div className="mt-4 pt-4 border-t border-slate-700">
              <h3 className="text-sm font-medium mb-2 text-slate-300">Task States</h3>
              <ul className="space-y-2 text-xs">
                <li className="flex items-center gap-2 text-green-400"><CheckCircle size={12} /> VERIFIED</li>
                <li className="flex items-center gap-2 text-blue-400"><Clock size={12} className="animate-spin" /> ACTIVE</li>
                <li className="flex items-center gap-2 text-slate-500"><AlertTriangle size={12} /> PENDING_AUTH</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Latency */}
        <div className="bg-slate-800/60 p-6 rounded-2xl border border-slate-700 shadow-xl col-span-2">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Search className="text-amber-400" size={18} /> System Latency
          </h2>
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: 'STT', ms: latency.stt, color: 'bg-amber-400', textColor: 'text-amber-400' },
              { label: 'LLM', ms: latency.llm, color: 'bg-purple-400', textColor: 'text-purple-400' },
              { label: 'TTS', ms: latency.tts, color: 'bg-blue-400', textColor: 'text-blue-400' },
            ].map(({ label, ms, textColor }) => (
              <div key={label} className="bg-slate-700/50 rounded-xl p-3 text-center">
                <p className="text-xs text-slate-400">{label}</p>
                <p className={`text-xl font-bold font-mono ${textColor}`}>{ms}</p>
                <p className="text-xs text-slate-500">ms</p>
              </div>
            ))}
          </div>
        </div>

        {/* Audit */}
        <div className="bg-slate-800/60 p-6 rounded-2xl border border-slate-700 shadow-xl">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Shield className="text-purple-400" size={18} /> Audit Log
          </h2>
          <div className="space-y-2 text-xs">
            {[
              { time: 'Just now', type: 'CALL_STARTED', detail: customer.id, color: 'text-green-400' },
              { time: '—', type: 'SESSION_CREATED', detail: roomName, color: 'text-blue-400' },
              { time: '—', type: 'AGENT_CONNECTED', detail: 'Deepgram STT/TTS', color: 'text-indigo-400' },
            ].map((evt, i) => (
              <div key={i} className="flex gap-2 text-slate-400">
                <span className="text-slate-500 w-12 shrink-0">{evt.time}</span>
                <span className={evt.color}>{evt.type}</span>
                <span className="truncate">{evt.detail}</span>
              </div>
            ))}
          </div>
        </div>
      </LiveKitRoom>
    </div>
  );
}

// ─── Agent Visualizer ────────────────────────────────────────────────────────

function AgentVisualizer() {
  const { state, audioTrack } = useVoiceAssistant();

  const stateLabel: Record<string, string> = {
    disconnected: 'Agent Disconnected',
    connecting: 'Connecting to Agent...',
    initializing: 'Agent Initializing...',
    listening: '🎙️ Agent is Listening',
    thinking: '🤔 Agent is Thinking...',
    speaking: '🔊 Agent is Speaking',
  };

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="text-slate-300 font-medium">{stateLabel[state] ?? state}</div>
      <div className="h-16 flex items-center justify-center">
        {audioTrack ? (
          <BarVisualizer state={state} barCount={7} trackRef={audioTrack} className="w-40" />
        ) : (
          <div className="w-40 flex items-center justify-center text-slate-600">
            <MicOff size={32} />
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Create Customer Modal ───────────────────────────────────────────────────

function CreateCustomerModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState({ name: '', phone_number: '', language_preference: 'english' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim() || !form.phone_number.trim()) {
      setError('Name and phone number are required.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/customers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to create customer');
      }
      onCreated();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to create customer');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 border border-slate-700 rounded-2xl p-6 w-full max-w-md shadow-2xl">
        <div className="flex justify-between items-center mb-5">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <UserPlus size={18} className="text-indigo-400" /> Create New Customer
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white"><X size={18} /></button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-900/50 border border-red-700 rounded-xl text-red-300 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">Full Name *</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="e.g. Aman Sharma"
              className="w-full bg-slate-700/50 border border-slate-600 rounded-xl px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Phone Number *</label>
            <input
              type="text"
              value={form.phone_number}
              onChange={(e) => setForm({ ...form, phone_number: e.target.value })}
              placeholder="e.g. +91 98765 43210"
              className="w-full bg-slate-700/50 border border-slate-600 rounded-xl px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Language Preference</label>
            <select
              value={form.language_preference}
              onChange={(e) => setForm({ ...form, language_preference: e.target.value })}
              className="w-full bg-slate-700/50 border border-slate-600 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="english">English</option>
              <option value="hindi">Hindi</option>
              <option value="marathi">Marathi</option>
              <option value="tamil">Tamil</option>
              <option value="telugu">Telugu</option>
              <option value="kannada">Kannada</option>
              <option value="bengali">Bengali</option>
            </select>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-slate-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 transition-colors text-white px-5 py-2 rounded-xl font-medium"
            >
              {loading ? <Loader2 size={14} className="animate-spin" /> : <UserPlus size={14} />}
              Create Customer
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
