import React from 'react';
import { Bot, RefreshCw, Copy, Check, ShieldCheck, Database, Layers } from 'lucide-react';
import ActiveNodeBadge from './ActiveNodeBadge';

export default function Header({
  activeNode = 'router',
  isStreaming = false,
  threadId = '',
  onNewSession,
  healthStatus = 'healthy',
}) {
  const [copied, setCopied] = React.useState(false);

  const handleCopyThreadId = () => {
    if (!threadId) return;
    navigator.clipboard.writeText(threadId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <header className="sticky top-0 z-40 w-full glass-panel border-b border-slate-800/80 px-4 sm:px-6 py-3 flex flex-wrap items-center justify-between gap-4">
      {/* Brand Identity */}
      <div className="flex items-center gap-3">
        <div className="relative p-2.5 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-white shadow-lg shadow-indigo-500/20">
          <Bot className="w-5 h-5" />
          <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-emerald-400 border-2 border-slate-900 rounded-full" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-base sm:text-lg font-bold text-white tracking-tight">
              Enterprise Multi-Agent AI
            </h1>
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 font-semibold">
              LangGraph + RAG
            </span>
          </div>
          <p className="text-xs text-slate-400 hidden sm:block">
            Stateful Multi-Turn Assistant • Employee Handbook Policy RAG • Transactional Scheduler
          </p>
        </div>
      </div>

      {/* Middle: Active Agent Node Live Badge */}
      <div className="flex items-center gap-3">
        <ActiveNodeBadge node={activeNode} isLive={isStreaming} />
      </div>

      {/* Right Controls: Thread ID & Session Reset */}
      <div className="flex items-center gap-2.5">
        <div className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
          <span className="text-slate-400 font-mono">Thread:</span>
          <span className="font-mono text-slate-300 max-w-[100px] truncate" title={threadId}>
            {threadId ? `${threadId.slice(0, 8)}...` : 'new'}
          </span>
          <button
            onClick={handleCopyThreadId}
            className="p-1 text-slate-400 hover:text-slate-200 transition-colors"
            title="Copy Thread ID"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        </div>

        <button
          onClick={onNewSession}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-all shadow-sm"
          title="Start fresh conversational thread"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">New Chat</span>
        </button>
      </div>
    </header>
  );
}
