import React from 'react';
import { X, BookOpen, ExternalLink, BookmarkCheck } from 'lucide-react';

export default function CitationsModal({ isOpen, onClose, sources = [], primaryPage = 4 }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/50">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                Knowledge Base Citations
                <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300">
                  Primary: Page {primaryPage}
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Grounding retrieved from public reference: <span className="font-mono text-purple-300">employee_handbook.pdf</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Citations List */}
        <div className="overflow-y-auto p-6 space-y-4">
          {sources.length === 0 ? (
            <div className="text-center py-8 text-slate-400 text-sm">
              No citations retrieved for this message.
            </div>
          ) : (
            sources.map((src, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-purple-500/40 transition-all flex flex-col gap-2"
              >
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <div className="flex items-center gap-2 font-medium">
                    <span className="px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 font-semibold">
                      Page {src.page}
                    </span>
                    <span className="text-slate-300 font-mono text-[11px]">{src.chunk_id}</span>
                  </div>
                  {src.distance !== undefined && (
                    <span className="text-[11px] font-mono text-slate-400">
                      Cosine Dist: {src.distance.toFixed(4)}
                    </span>
                  )}
                </div>
                <div className="text-xs text-slate-200 leading-relaxed font-sans bg-slate-900/40 p-3 rounded-lg border border-slate-800/50 whitespace-pre-line">
                  {src.full_text || src.snippet}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-950/80 flex items-center justify-between text-xs text-slate-400">
          <span className="flex items-center gap-1.5">
            <BookmarkCheck className="w-4 h-4 text-emerald-400" />
            Verified against ChromaDB Ingested Chunks
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
