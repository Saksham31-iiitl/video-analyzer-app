import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, Save, Loader2, CheckCircle2, Edit3, Clock } from 'lucide-react';
import { updateCaptions } from '../api/client';

/**
 * CaptionEditor
 * Lets users edit AI-generated caption text before final export.
 *
 * Props:
 *   jobId     {string}    The generation job ID (used to PATCH edits to backend)
 *   captions  {Array}     [{ id, start, end, text }, ...]  — from job status response
 *
 * How to use in ExportPage:
 *   {captions?.length > 0 && (
 *     <CaptionEditor jobId={jobId} captions={captions} />
 *   )}
 */
export default function CaptionEditor({ jobId, captions: initial }) {
  const [captions, setCaptions] = useState(initial);
  const [editingId, setEditingId] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (id, value) => {
    setCaptions((prev) =>
      prev.map((c) => (c.id === id ? { ...c, text: value } : c))
    );
    setSaved(false);
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      await updateCaptions(jobId, captions);
      setSaved(true);
      setEditingId(null);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to save captions');
    } finally {
      setSaving(false);
    }
  };

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toFixed(1).padStart(4, '0');
    return `${m}:${s}`;
  };

  return (
    <div className="space-y-4">
      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <h3 className="font-display text-sm font-semibold text-white flex items-center gap-2">
          <MessageSquare size={16} className="text-pink-400" />
          Caption Editor
          <span className="text-xs font-normal text-slate-500">
            ({captions.length} captions)
          </span>
        </h3>

        <button
          onClick={handleSave}
          disabled={saving || saved}
          className={`flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            saved
              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
              : 'step-active text-white hover:scale-105'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {saving ? (
            <Loader2 size={13} className="animate-spin" />
          ) : saved ? (
            <CheckCircle2 size={13} />
          ) : (
            <Save size={13} />
          )}
          {saved ? 'Saved' : 'Save All'}
        </button>
      </div>

      {/* ── Caption list ── */}
      <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
        <AnimatePresence>
          {captions.map((caption, i) => (
            <motion.div
              key={caption.id}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.04 }}
              className={`rounded-xl border p-3 transition-colors ${
                editingId === caption.id
                  ? 'border-pink-500/40 bg-pink-500/5'
                  : 'border-slate-700/50 bg-slate-800/40 hover:border-slate-600'
              }`}
            >
              {/* Timestamp row */}
              <div className="flex items-center gap-2 mb-2">
                <Clock size={11} className="text-slate-600" />
                <span className="text-[10px] font-mono text-slate-600">
                  {formatTime(caption.start)} → {formatTime(caption.end)}
                </span>
                <button
                  className="ml-auto text-slate-600 hover:text-pink-400 transition-colors"
                  onClick={() => setEditingId(editingId === caption.id ? null : caption.id)}
                >
                  <Edit3 size={12} />
                </button>
              </div>

              {/* Text — editable when row is active */}
              {editingId === caption.id ? (
                <textarea
                  value={caption.text}
                  onChange={(e) => handleChange(caption.id, e.target.value)}
                  rows={2}
                  autoFocus
                  className="w-full bg-slate-900/60 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-600 outline-none focus:border-pink-500/50 resize-none transition-colors"
                />
              ) : (
                <p className="text-sm text-slate-300 leading-snug">{caption.text}</p>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* ── Error ── */}
      {error && (
        <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-2">
          {error}
        </p>
      )}
    </div>
  );
}
