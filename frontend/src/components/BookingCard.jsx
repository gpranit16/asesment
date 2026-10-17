import React from 'react';
import { Calendar, CheckCircle2, Clock, Mail, User, Hash, AlertCircle, Copy, Check } from 'lucide-react';

export default function BookingCard({ booking = {} }) {
  const [copied, setCopied] = React.useState(false);

  const {
    service_type = 'Performance Review',
    name,
    email,
    slot,
    stage = 'idle',
    ref_id,
    confirmed = false,
  } = booking;

  const handleCopyRef = () => {
    if (!ref_id) return;
    navigator.clipboard.writeText(ref_id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getStatusBadge = () => {
    if (confirmed) {
      return (
        <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          Confirmed
        </span>
      );
    }
    if (stage === 'collecting_slot') {
      return (
        <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30 animate-pulse">
          <Clock className="w-3.5 h-3.5 text-amber-400" />
          Awaiting Slot Choice
        </span>
      );
    }
    if (stage === 'collecting_details') {
      return (
        <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-300 border border-blue-500/30 animate-pulse">
          <User className="w-3.5 h-3.5 text-blue-400" />
          Collecting Details
        </span>
      );
    }
    return (
      <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-400 border border-slate-700">
        <Clock className="w-3.5 h-3.5" />
        Idle
      </span>
    );
  };

  return (
    <div className="glass-panel rounded-2xl p-4 border border-slate-800 flex flex-col gap-3 shadow-lg transition-all hover:border-slate-700">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-emerald-500/15 text-emerald-400">
            <Calendar className="w-4 h-4" />
          </div>
          <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Transactional State
          </span>
        </div>
        {getStatusBadge()}
      </div>

      <div className="text-sm font-semibold text-slate-100 border-b border-slate-800/80 pb-2">
        {service_type}
      </div>

      {/* Booking Parameters Grid */}
      <div className="grid grid-cols-1 gap-2 text-xs">
        <div className="flex items-center justify-between p-2 rounded-lg bg-slate-900/50 border border-slate-800/60">
          <span className="text-slate-400 flex items-center gap-1.5">
            <User className="w-3.5 h-3.5 text-slate-400" /> Name:
          </span>
          <span className={`font-medium ${name ? 'text-slate-100 font-semibold' : 'text-slate-500 italic'}`}>
            {name || 'Not provided'}
          </span>
        </div>

        <div className="flex items-center justify-between p-2 rounded-lg bg-slate-900/50 border border-slate-800/60">
          <span className="text-slate-400 flex items-center gap-1.5">
            <Mail className="w-3.5 h-3.5 text-slate-400" /> Email:
          </span>
          <span className={`font-mono ${email ? 'text-slate-100' : 'text-slate-500 italic'}`}>
            {email || 'Not provided'}
          </span>
        </div>

        <div className="flex items-center justify-between p-2 rounded-lg bg-slate-900/50 border border-slate-800/60">
          <span className="text-slate-400 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-slate-400" /> Selected Slot:
          </span>
          <span className={`font-medium ${slot ? 'text-emerald-300 font-semibold' : 'text-slate-500 italic'}`}>
            {slot || 'Pending'}
          </span>
        </div>

        {ref_id && (
          <div className="flex items-center justify-between p-2 rounded-lg bg-emerald-950/40 border border-emerald-500/30">
            <span className="text-emerald-300 font-semibold flex items-center gap-1.5">
              <Hash className="w-3.5 h-3.5" /> Ref ID:
            </span>
            <div className="flex items-center gap-2">
              <span className="font-mono text-emerald-300 font-bold">{ref_id}</span>
              <button
                onClick={handleCopyRef}
                className="p-1 rounded hover:bg-emerald-800/40 text-emerald-400 transition-colors"
                title="Copy Reference ID"
              >
                {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
