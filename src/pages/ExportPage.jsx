import React from 'react';
import { motion } from 'framer-motion';
import {
  Download, RefreshCw, Loader2, CheckCircle2,
  XCircle, Share2, Film,
} from 'lucide-react';
import { useJobStatus } from '../hooks/useJobStatus';
import ViralityScore from '../components/ViralityScore';
import CaptionEditor from '../components/CaptionEditor';

export default function ExportPage({ jobId, onRestart }) {
  const { status, progress, output, error, viralityScore, captions } = useJobStatus(jobId, 1500);

  return (
    <div className="max-w-lg mx-auto text-center space-y-8 py-8">
      {/* ── Processing ─────────────────────────────────────────── */}
      {status === 'processing' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <div className="w-20 h-20 mx-auto mb-6 rounded-2xl step-active flex items-center justify-center pulse-glow">
            <Film size={32} className="text-white" />
          </div>

          <h2 className="font-display text-xl font-bold text-white mb-2">
            Creating your reel…
          </h2>
          <p className="text-sm text-slate-500 mb-8">
            Trimming clips, syncing to beats, adding transitions, and rendering.
          </p>

          {/* Progress bar */}
          <div className="w-full max-w-sm mx-auto mb-3">
            <div className="h-2.5 bg-slate-800 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-pink-500 via-purple-500 to-cyan-500 rounded-full"
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
          </div>
          <p className="text-sm font-mono text-slate-400">{progress}%</p>

          {/* Stage labels */}
          <div className="mt-6 space-y-2">
            {[
              { min: 0, label: 'Detecting beats…', icon: '🎵' },
              { min: 20, label: 'Assembling scenes…', icon: '✂️' },
              { min: 50, label: 'Generating captions…', icon: '💬' },
              { min: 70, label: 'Rendering final video…', icon: '🎬' },
            ].map((stage) => {
              const active = progress >= stage.min && progress < (stage.min + 25);
              const done = progress >= stage.min + 25;
              return (
                <div
                  key={stage.min}
                  className={`flex items-center gap-2 justify-center text-sm transition-all ${
                    active ? 'text-white' : done ? 'text-emerald-400/60' : 'text-slate-700'
                  }`}
                >
                  {done ? (
                    <CheckCircle2 size={14} className="text-emerald-400" />
                  ) : active ? (
                    <Loader2 size={14} className="animate-spin text-pink-400" />
                  ) : (
                    <span className="w-3.5 h-3.5 rounded-full bg-slate-800 inline-block" />
                  )}
                  <span>{stage.icon} {stage.label}</span>
                </div>
              );
            })}
          </div>
        </motion.div>
      )}

      {/* ── Success ────────────────────────────────────────────── */}
      {status === 'done' && output && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4 }}
        >
          <div className="w-20 h-20 mx-auto mb-6 rounded-2xl step-done flex items-center justify-center">
            <CheckCircle2 size={36} className="text-white" />
          </div>

          <h2 className="font-display text-xl font-bold text-white mb-2">
            Your reel is ready! 🎉
          </h2>
          <p className="text-sm text-slate-500 mb-8">
            Download it or share directly to your socials.
          </p>

          {/* Video preview */}
          <div className="rounded-2xl overflow-hidden border border-slate-700/50 bg-black mb-6">
            <video
              src={output}
              controls
              className="w-full max-h-[500px]"
              style={{ aspectRatio: '9/16', maxWidth: '300px', margin: '0 auto' }}
            />
          </div>

          <div className="flex items-center justify-center gap-3">
            <a
              href={output}
              download="my-reel.mp4"
              className="flex items-center gap-2 px-6 py-3 rounded-xl font-display font-semibold text-sm step-active text-white hover:scale-105 transition-transform glow-pink"
            >
              <Download size={18} />
              Download Reel
            </a>

            <button
              onClick={() => {
                if (navigator.share) {
                  navigator.share({ title: 'My Auto Reel', url: output });
                } else {
                  navigator.clipboard.writeText(window.location.origin + output);
                  alert('Link copied to clipboard!');
                }
              }}
              className="flex items-center gap-2 px-5 py-3 rounded-xl font-display font-semibold text-sm bg-slate-800 text-slate-300 hover:bg-slate-700 transition-colors border border-slate-700"
            >
              <Share2 size={16} />
              Share
            </button>
          </div>

          {/* ── Virality Score ── rendered whenever backend returns it ── */}
          {viralityScore != null && (
            <div className="mt-8 text-left">
              <ViralityScore score={viralityScore} />
            </div>
          )}

          {/* ── Caption Editor ── only shown when captions were generated ── */}
          {captions?.length > 0 && (
            <div className="mt-6 text-left bg-slate-800/40 rounded-2xl border border-slate-700/50 p-5">
              <CaptionEditor jobId={jobId} captions={captions} />
            </div>
          )}
        </motion.div>
      )}

      {/* ── Error ──────────────────────────────────────────────── */}
      {status === 'failed' && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-red-500/20 flex items-center justify-center">
            <XCircle size={36} className="text-red-400" />
          </div>

          <h2 className="font-display text-xl font-bold text-white mb-2">
            Generation Failed
          </h2>
          <p className="text-sm text-red-400/80 mb-6 max-w-sm mx-auto">
            {error || 'An unexpected error occurred during rendering.'}
          </p>
        </motion.div>
      )}

      {/* ── Restart ────────────────────────────────────────────── */}
      {(status === 'done' || status === 'failed') && (
        <button
          onClick={onRestart}
          className="flex items-center gap-2 mx-auto px-5 py-2.5 rounded-xl text-sm text-slate-400 bg-slate-800/60 border border-slate-700/50 hover:bg-slate-800 transition-colors"
        >
          <RefreshCw size={15} />
          Create another reel
        </button>
      )}
    </div>
  );
}
