import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, ArrowLeft, Loader2, Eye } from 'lucide-react';
import { analyzeProject } from '../api/client';

export default function AnalyzePage({ projectId, onAnalyzed, onBack }) {
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState(null);
  const [scenes, setScenes] = useState(null);

  useEffect(() => {
    if (!projectId) return;
    runAnalysis();
  }, [projectId]);

  const runAnalysis = async () => {
    setAnalyzing(true);
    setError(null);
    try {
      const result = await analyzeProject(projectId);
      setScenes(result.scenes);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 0.7) return 'text-emerald-400';
    if (score >= 0.4) return 'text-yellow-400';
    return 'text-slate-500';
  };

  const getScoreBar = (score) => {
    if (score >= 0.7) return 'bg-emerald-500';
    if (score >= 0.4) return 'bg-yellow-500';
    return 'bg-slate-600';
  };

  return (
    <div className="space-y-6">
      {/* ── Header ─────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-300 transition-colors"
        >
          <ArrowLeft size={16} />
          Back
        </button>
        <span className="text-xs text-slate-600 font-mono">Project: {projectId}</span>
      </div>

      {/* ── Analyzing state ────────────────────────────────────── */}
      {analyzing && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-16"
        >
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl step-active flex items-center justify-center pulse-glow">
            <Sparkles size={28} className="text-white animate-pulse" />
          </div>
          <h3 className="font-display text-lg font-semibold text-white mb-2">
            Analyzing your clips…
          </h3>
          <p className="text-sm text-slate-500 max-w-md mx-auto">
            Detecting scenes, scoring highlights, analyzing motion, faces, and audio energy.
            This may take a minute.
          </p>
          <Loader2 size={20} className="mx-auto mt-6 text-pink-400 animate-spin" />
        </motion.div>
      )}

      {/* ── Error ──────────────────────────────────────────────── */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-sm text-red-400">
          {error}
          <button
            onClick={runAnalysis}
            className="ml-3 underline hover:text-red-300"
          >
            Retry
          </button>
        </div>
      )}

      {/* ── Results ────────────────────────────────────────────── */}
      {scenes && !analyzing && (
        <>
          <div className="text-center mb-6">
            <h3 className="font-display text-lg font-semibold text-white">
              {scenes.length} Scenes Detected
            </h3>
            <p className="text-sm text-slate-500 mt-1">
              Ranked by highlight score. Top scenes will be auto-selected.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {scenes.map((scene, i) => (
              <motion.div
                key={`${scene.clip_file}-${scene.scene_index}`}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="bg-slate-800/60 rounded-xl border border-slate-700/50 overflow-hidden hover:border-slate-600 transition-colors"
              >
                {/* Thumbnail placeholder */}
                <div className="aspect-video bg-slate-900 flex items-center justify-center relative">
                  <Eye size={24} className="text-slate-700" />
                  <div className="absolute top-2 right-2 bg-black/60 rounded-md px-2 py-0.5 text-xs font-mono text-slate-300">
                    {scene.duration.toFixed(1)}s
                  </div>
                  <div className={`absolute top-2 left-2 rounded-md px-2 py-0.5 text-xs font-bold ${
                    scene.score >= 0.7 ? 'bg-emerald-500/20 text-emerald-400' :
                    scene.score >= 0.4 ? 'bg-yellow-500/20 text-yellow-400' :
                    'bg-slate-700/60 text-slate-500'
                  }`}>
                    #{i + 1}
                  </div>
                </div>

                <div className="p-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-500 truncate">
                      {scene.clip_file}
                    </span>
                    <span className={`text-sm font-bold font-mono ${getScoreColor(scene.score)}`}>
                      {(scene.score * 100).toFixed(0)}
                    </span>
                  </div>

                  {/* Score bar */}
                  <div className="h-1 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${getScoreBar(scene.score)}`}
                      style={{ width: `${scene.score * 100}%` }}
                    />
                  </div>

                  {/* Sub-scores */}
                  <div className="grid grid-cols-5 gap-1 text-center">
                    {[
                      { label: 'MOT', val: scene.motion_score },
                      { label: 'SHP', val: scene.sharpness_score },
                      { label: 'AI', val: scene.clip_score },
                      { label: 'AUD', val: scene.audio_score },
                      { label: 'FAC', val: scene.face_score },
                    ].map((s) => (
                      <div key={s.label}>
                        <div className="text-[10px] text-slate-600">{s.label}</div>
                        <div className="text-[11px] font-mono text-slate-400">
                          {(s.val * 100).toFixed(0)}
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="text-[10px] text-slate-600 text-center font-mono">
                    {scene.start_time.toFixed(1)}s — {scene.end_time.toFixed(1)}s
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Continue button */}
          <div className="flex justify-center pt-6">
            <button
              onClick={() => onAnalyzed(scenes)}
              className="flex items-center gap-2 px-8 py-3.5 rounded-xl font-display font-semibold text-sm step-active text-white hover:scale-105 transition-transform glow-pink"
            >
              <Sparkles size={18} />
              Continue to Configure
            </button>
          </div>
        </>
      )}
    </div>
  );
}
