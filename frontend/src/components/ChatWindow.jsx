import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, AlertCircle, Radio, Terminal, Bot } from 'lucide-react';
import MessageBubble from './MessageBubble';

export default function ChatWindow({
  messages = [],
  onSendMessage,
  isLoading = false,
  isStreaming = false,
  activeNode = 'router',
  nodeSteps = [],
  onOpenCitations,
  onSelectSlot,
  useStreaming = true,
  onToggleStreaming,
}) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming]);

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!input.trim() || isLoading || isStreaming) return;
    onSendMessage(input.trim());
    setInput('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex-1 flex flex-col h-[calc(100vh-65px)] bg-slate-950/20 relative">
      {/* Top Transition Bar: Shows LangGraph Node Progression */}
      {nodeSteps.length > 0 && (
        <div className="px-4 py-1.5 bg-slate-900/60 border-b border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-2 overflow-x-auto">
            <span className="text-[11px] font-mono text-slate-400 uppercase flex items-center gap-1">
              <Terminal className="w-3 h-3 text-indigo-400" /> StateGraph Flow:
            </span>
            <div className="flex items-center gap-1.5 font-mono text-[11px]">
              {nodeSteps.map((step, idx) => (
                <React.Fragment key={idx}>
                  <span
                    className={`px-2 py-0.5 rounded font-semibold ${
                      idx === nodeSteps.length - 1
                        ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {step}
                  </span>
                  {idx < nodeSteps.length - 1 && <span className="text-slate-400">➔</span>}
                </React.Fragment>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <label className="flex items-center gap-1.5 cursor-pointer text-[11px] font-mono text-slate-400 select-none">
              <Radio className={`w-3 h-3 ${useStreaming ? 'text-indigo-400' : 'text-slate-400'}`} />
              <span>SSE Stream</span>
              <input
                type="checkbox"
                checked={useStreaming}
                onChange={(e) => onToggleStreaming && onToggleStreaming(e.target.checked)}
                className="hidden"
              />
            </label>
          </div>
        </div>
      )}

      {/* Message Feed */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-2">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 max-w-lg mx-auto">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white shadow-xl shadow-indigo-500/20 mb-4 animate-bounce">
              <Bot className="w-8 h-8" />
            </div>
            <h2 className="text-xl font-bold text-white mb-2">
              Enterprise Multi-Agent Assistant
            </h2>
            <p className="text-sm text-slate-400 mb-6 leading-relaxed">
              Equipped with a LangGraph StateGraph engine, ChromaDB Employee Handbook RAG, and multi-turn transactional scheduling.
            </p>
            <div className="grid grid-cols-1 gap-2 w-full text-left">
              <button
                onClick={() => onSendMessage("Hi, I need to book a 1-on-1 Performance Review session.")}
                className="p-3 rounded-xl bg-slate-900/60 hover:bg-slate-800 border border-slate-800 text-xs text-slate-300 hover:text-white transition-all flex items-center justify-between group"
              >
                <span>📅 "Hi, I need to book a 1-on-1 Performance Review session."</span>
                <span className="text-indigo-400 opacity-0 group-hover:opacity-100 font-bold">Start ➔</span>
              </button>
              <button
                onClick={() => onSendMessage("How often are performance reviews conducted according to the handbook?")}
                className="p-3 rounded-xl bg-slate-900/60 hover:bg-slate-800 border border-slate-800 text-xs text-slate-300 hover:text-white transition-all flex items-center justify-between group"
              >
                <span>📖 "How often are performance reviews conducted according to the handbook?"</span>
                <span className="text-purple-400 opacity-0 group-hover:opacity-100 font-bold">Query ➔</span>
              </button>
            </div>
          </div>
        ) : (
          messages.map((msg, index) => (
            <MessageBubble
              key={index}
              message={msg}
              onOpenCitations={onOpenCitations}
              onSelectSlot={onSelectSlot}
            />
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-slate-950/80 border-t border-slate-800/80 backdrop-blur-md">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto flex items-end gap-2">
          <div className="flex-1 relative rounded-2xl bg-slate-900/90 border border-slate-800 focus-within:border-indigo-500/60 focus-within:ring-2 focus-within:ring-indigo-500/20 transition-all shadow-inner">
            <textarea
              ref={inputRef}
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about handbook policies, schedule reviews, or test context interleaving..."
              className="w-full resize-none bg-transparent px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none max-h-32 min-h-[44px]"
            />
          </div>

          <button
            type="submit"
            disabled={!input.trim() || isLoading || isStreaming}
            className={`p-3 rounded-2xl flex items-center justify-center transition-all ${
              !input.trim() || isLoading || isStreaming
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                : 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white hover:opacity-90 shadow-lg shadow-indigo-500/25 active:scale-95'
            }`}
          >
            {isLoading || isStreaming ? (
              <span className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </form>
        <p className="text-[11px] text-center text-slate-500 mt-2 font-mono">
          Press <kbd className="px-1 py-0.5 rounded bg-slate-800 text-slate-400">Enter</kbd> to send, <kbd className="px-1 py-0.5 rounded bg-slate-800 text-slate-400">Shift + Enter</kbd> for newline
        </p>
      </div>
    </div>
  );
}
