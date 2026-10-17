import React from 'react';
import { GitBranch, BookOpen, Calendar, ShieldAlert, Cpu } from 'lucide-react';

const NODE_CONFIG = {
  router: {
    label: 'Router Node',
    sub: 'Intent Classifier & Guardrails',
    color: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
    dot: 'bg-cyan-400',
    icon: GitBranch,
  },
  faq_rag_node: {
    label: 'FAQ RAG Node',
    sub: 'ChromaDB Document Retrieval',
    color: 'bg-purple-500/15 text-purple-300 border-purple-500/30',
    dot: 'bg-purple-400',
    icon: BookOpen,
  },
  booking_node: {
    label: 'Booking Tool Node',
    sub: 'Transactional Slot Execution',
    color: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
    dot: 'bg-emerald-400',
    icon: Calendar,
  },
  guardrail_node: {
    label: 'Guardrail Node',
    sub: 'Security Policy Defense',
    color: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
    dot: 'bg-rose-400',
    icon: ShieldAlert,
  },
};

export default function ActiveNodeBadge({ node = 'router', isLive = false, size = 'md' }) {
  const config = NODE_CONFIG[node] || {
    label: node || 'Active Node',
    sub: 'State Orchestration',
    color: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30',
    dot: 'bg-indigo-400',
    icon: Cpu,
  };

  const Icon = config.icon;

  if (size === 'sm') {
    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${config.color}`}>
        <span className={`w-1.5 h-1.5 rounded-full ${config.dot} ${isLive ? 'animate-ping' : ''}`} />
        <Icon className="w-3 h-3" />
        {config.label}
      </span>
    );
  }

  return (
    <div className={`flex items-center gap-2.5 px-3 py-1.5 rounded-xl border transition-all ${config.color} ${isLive ? 'ring-2 ring-indigo-500/30 node-pulse' : ''}`}>
      <div className="relative flex items-center justify-center">
        <span className={`w-2.5 h-2.5 rounded-full ${config.dot}`} />
        {isLive && (
          <span className={`absolute w-4 h-4 rounded-full ${config.dot} opacity-75 animate-ping`} />
        )}
      </div>
      <div className="flex flex-col text-left">
        <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider">
          <Icon className="w-3.5 h-3.5" />
          <span>{config.label}</span>
          {isLive && <span className="text-[10px] bg-indigo-500/30 px-1 rounded text-white animate-pulse">LIVE</span>}
        </div>
        <span className="text-[10px] opacity-75 font-mono">{config.sub}</span>
      </div>
    </div>
  );
}
