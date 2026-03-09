import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, Users, Zap } from 'lucide-react';

/**
 * ViralityScore
 * Displays the AI-predicted virality score returned by the backend after generation.
 *
 * Props:
 *   score        {number}  0–100 integer from backend (e.g. job status response field "virality_score")
 *   breakdown    {object}  optional { hook_strength, pacing, audio_fit, caption_quality } each 0–100
 */
export default function ViralityScore({ score, breakdown = null }) {
  // Derive label + colour from score band
  const band =
    score >= 75
      ? { label: 'High', reach: 'High', color: 'text-emerald-400', ring: 'stroke-emerald-500', bg: 'bg-emerald-500/10 border-emerald-500/30' }
      : score >= 45
      ? { label: 'Medium', reach: 'Medium', color: 'text-yellow-400', ring: 'stroke-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/30' }
      : { label: 'Low', reach: 'Low', color: 'text-slate-400', ring: 'stroke-slate-500', bg: 'bg-slate-800/60 border-slate-700/50' };

  // SVG ring dimensions
  const r = 44;
  const circ = 2 * Math.PI * r;
  const dash = (score / 100) * circ;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className={`rounded-2xl border p-6 ${band.bg} space-y-5`}
    >
      {/* ── Header ── */}
      <div className="flex items-center gap-2">
        <TrendingUp size={18} className={band.color} />
        <h3 className="font-display text-sm font-semibold text-white">Virality Score</h3>
      </div>

      <div className="flex items-center gap-8">
        {/* ── Circular ring ── */}
        <div className="relative flex-shrink-0">
          <svg width="112" height="112" viewBox="0 0 112 112" className="-rotate-90">
            {/* Track */}
            <circle cx="56" cy="56" r={r} fill="none" stroke="#1e293b" strokeWidth="8" />
            {/* Progress */}
            <motion.circle
              cx="56"
              cy="56"
              r={r}
              fill="none"
              strokeWidth="8"
              strokeLinecap="round"
              className={band.ring}
              strokeDasharray={circ}
              initial={{ strokeDashoffset: circ }}
              animate={{ strokeDashoffset: circ - dash }}
              transition={{ duration: 1.2, ease: 'easeOut' }}
            />
          </svg>
          {/* Score label inside ring */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <motion.span
              className={`text-2xl font-bold font-mono ${band.color}`}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6 }}
            >
              {score}
            </motion.span>
            <span className="text-[10px] text-slate-600 font-mono">/100</span>
          </div>
        </div>

        {/* ── Labels ── */}
        <div className="space-y-3 flex-1">
          <div className="flex items-center gap-2">
            <Zap size={14} className={band.color} />
            <span className={`text-sm font-semibold ${band.color}`}>
              {band.label} Virality
            </span>
          </div>
          <div className="flex items-center gap-2 text-slate-400 text-sm">
            <Users size={14} />
            <span>Potential Reach: <span className="text-white font-medium">{band.reach}</span></span>
          </div>

          {/* Breakdown bars — only shown when the backend sends sub-scores */}
          {breakdown && (
            <div className="space-y-1.5 pt-1">
              {Object.entries(breakdown).map(([key, val]) => (
                <div key={key} className="flex items-center gap-2">
                  <span className="text-[10px] text-slate-600 w-20 capitalize">
                    {key.replace(/_/g, ' ')}
                  </span>
                  <div className="flex-1 h-1 bg-slate-800 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-gradient-to-r from-pink-500 to-purple-500 rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${val}%` }}
                      transition={{ duration: 0.8, delay: 0.3 }}
                    />
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono w-6 text-right">{val}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
