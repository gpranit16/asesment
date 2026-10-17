import React from 'react';
import { User, Bot, BookOpen, Calendar, Clock, Copy, Check } from 'lucide-react';
import ActiveNodeBadge from './ActiveNodeBadge';

export default function MessageBubble({
  message,
  onOpenCitations,
  onSelectSlot,
}) {
  const [copied, setCopied] = React.useState(false);
  const isUser = message.sender === 'user';
  const sources = message.sources || [];
  const primaryPage = message.primaryPage || 4;

  const handleCopy = () => {
    navigator.clipboard.writeText(message.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`flex w-full gap-3 py-3 px-2 sm:px-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {/* Bot Avatar */}
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20 mt-1">
          <Bot className="w-4 h-4" />
        </div>
      )}

      {/* Bubble Container */}
      <div className={`flex flex-col max-w-[85%] sm:max-w-[75%] gap-1.5 ${isUser ? 'items-end' : 'items-start'}`}>
        {/* Node Badge header on bot messages */}
        {!isUser && message.node && (
          <div className="flex items-center gap-2 mb-0.5">
            <ActiveNodeBadge node={message.node} size="sm" />
            {message.intent && (
              <span className="text-[10px] font-mono uppercase text-slate-400">
                intent: {message.intent}
              </span>
            )}
          </div>
        )}

        <div
          className={`relative px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap transition-all shadow-md ${
            isUser
              ? 'bg-gradient-to-r from-indigo-600 to-indigo-700 text-white rounded-br-xs'
              : 'glass-panel text-slate-200 border border-slate-800 rounded-bl-xs'
          }`}
        >
          {message.text}

          {/* Real-time streaming typing cursor */}
          {message.isStreaming && (
            <span className="inline-block w-1.5 h-4 ml-1 bg-indigo-400 animate-pulse align-middle" />
          )}

          {/* Quick slot chips if slot selection was offered */}
          {!isUser && message.text.includes('Which slot works best?') && (
            <div className="mt-3 pt-3 border-t border-slate-700/60 flex flex-wrap gap-2">
              <span className="w-full text-[11px] text-slate-400 font-medium">
                Quick Select Available Slot:
              </span>
              {['Tomorrow 11:00 AM', 'Tomorrow 3:00 PM', 'Friday 10:30 AM'].map((slot, i) => (
                <button
                  key={i}
                  onClick={() => onSelectSlot && onSelectSlot(slot)}
                  className="px-2.5 py-1 rounded-lg bg-indigo-600/20 hover:bg-indigo-600 border border-indigo-500/30 hover:border-indigo-400 text-xs text-indigo-300 hover:text-white font-medium transition-all"
                >
                  {slot}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Footer actions: Citations button & Copy */}
        <div className="flex items-center gap-2 text-xs text-slate-400 px-1">
          {!isUser && sources.length > 0 && (
            <button
              onClick={() => onOpenCitations && onOpenCitations(sources, primaryPage)}
              className="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 border border-purple-500/20 text-xs font-medium transition-colors"
            >
              <BookOpen className="w-3 h-3 text-purple-400" />
              <span>Verified Citations ({sources.length})</span>
            </button>
          )}

          <button
            onClick={handleCopy}
            className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-300 transition-colors"
            title="Copy message text"
          >
            {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 shadow-sm mt-1">
          <User className="w-4 h-4" />
        </div>
      )}
    </div>
  );
}
