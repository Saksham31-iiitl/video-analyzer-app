import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  ArrowLeft, Zap, Clock, Type, Volume2,
  Scissors, Check, Loader2, Wand2,
} from 'lucide-react';
import { generateReel } from '../api/client';
import TimelineView from '../components/TimelineView';

const STYLES = [
  { id: 'fast_cuts',      name: 'Fast Cuts',      emoji: '⚡', desc: 'Energetic, beat-synced' },
  { id: 'cinematic',      name: 'Cinematic',      emoji: '🎬', desc: 'Smooth crossfades' },
  { id: 'vlog_energy',    name: 'Vlog',            emoji: '🗣️', desc: 'Face-focused' },
  { id: 'meme_captions',  name: 'Meme Captions',  emoji: '😂', desc: 'Bold text overlays' },
  { id: 'aesthetic',      name: 'Aesthetic',       emoji: '🌸', desc: 'Dreamy & soft' },
  { id: 'hype',           name: 'Hype',            emoji: '🔥', desc: 'Ultra-fast action' },
];

const TRANSITIONS = [
  { id: 'cut', name: 'Hard Cut' },
  { id: 'crossfade', name: 'Crossfade' },
];

const DURATIONS = [15, 30, 45, 60];

export default function ConfigurePage({
  projectId,
  scenes,
  selectedScenes,
  setSelectedScenes,
  onGenerate,
  onBack,
}) {
  const [style, setStyle] = useState('fast_cuts');
  const [duration, setDuration] = useState(30);
  const [transition, setTransition] = useState('cut');
  const [addCaptions, setAddCaptions] = useState(false);
  const [musicVolume, setMusicVolume] = useState(0.7);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);

  const toggleScene = (scene) => {
    const key = `${scene.clip_file}-${scene.scene_index}`;
    const isSelected = selectedScenes.some(
      (s) => `${s.clip_file}-${s.scene_index}` === key
    );
    if (isSelected) {
      setSelectedScenes((prev) =>
        prev.filter((s) => `${s.clip_file}-${s.scene_index}` !== key)
      );
    } else {
      setSelectedScenes((prev) => [...prev, scene]);
    }
  };

  const isSelected = (scene) =>
    selectedScenes.some(
      (s) => `${s.clip_file}-${s.scene_index}` === `${scene.clip_file}-${scene.scene_index}`
    );

  const handleGenerate = async () => {
    if (selectedScenes.length === 0) {
      setError('Select at least one scene.');
      return;
    }
    setGenerating(true);
    setError(null);

    try {
      const result = await generateReel({
        projectId,
        selectedScenes,
        targetDuration: duration,
        style,
        addCaptions,
        transitionType: transition,
        musicVolume,
      });
      onGenerate(result.job_id);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Generation failed');
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* ── Header ─────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-300 transition-colors"
        >
          <ArrowLeft size={16} />
          Back
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* ── Left: Scene Selection ─────────────────────────────── */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="font-display text-base font-semibold text-white flex items-center gap-2">
            <Scissors size={18} className="text-pink-400" />
            Select Scenes
            <span className="text-xs font-normal text-slate-500">
              ({selectedScenes.length} selected)
            </span>
          </h3>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 max-h-[400px] overflow-y-auto pr-1">
            {scenes.map((scene, i) => {
              const selected = isSelected(scene);
              return (
                <motion.button
                  key={`${scene.clip_file}-${scene.scene_index}`}
                  onClick={() => toggleScene(scene)}
                  whileTap={{ scale: 0.97 }}
                  className={`relative rounded-xl border-2 overflow-hidden text-left transition-all duration-200 ${
                    selected
                      ? 'border-pink-500 bg-pink-500/5'
                      : 'border-slate-700/50 bg-slate-800/40 hover:border-slate-600'
                  }`}
                >
                  <div className="aspect-video bg-slate-900 flex items-center justify-center">
                    <span className="text-xs font-mono text-slate-600">
                      {scene.duration.toFixed(1)}s
                    </span>
                    {selected && (
                      <div className="absolute top-1.5 right-1.5 w-5 h-5 rounded-full bg-pink-500 flex items-center justify-center">
                        <Check size={12} className="text-white" />
                      </div>
                    )}
                    <div className="absolute bottom-1.5 left-1.5 text-[10px] font-mono text-slate-400 bg-black/50 px-1.5 py-0.5 rounded">
                      Score: {(scene.score * 100).toFixed(0)}
                    </div>
                  </div>
                </motion.button>
              );
            })}
          </div>
        </div>

        {/* ── Timeline ─────────────────────────────────────────── */}
        {selectedScenes.length > 0 && (
          <div className="lg:col-span-2">
            <TimelineView
              scenes={selectedScenes}
              onReorder={setSelectedScenes}
            />
          </div>
        )}

        {/* ── Right: Settings ──────────────────────────────────── */}
        <div className="space-y-6">
          {/* Style */}
          <div>
            <h3 className="font-display text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <Wand2 size={16} className="text-purple-400" />
              Editing Style
            </h3>
            <div className="space-y-2">
              {STYLES.map((s) => (
                <button
                  key={s.id}
                  onClick={() => setStyle(s.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all text-sm ${
                    style === s.id
                      ? 'bg-purple-500/10 border border-purple-500/40 text-white'
                      : 'bg-slate-800/40 border border-transparent text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <span className="text-lg">{s.emoji}</span>
                  <div>
                    <div className="font-medium">{s.name}</div>
                    <div className="text-[11px] text-slate-500">{s.desc}</div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Duration */}
          <div>
            <h3 className="font-display text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <Clock size={16} className="text-cyan-400" />
              Duration
            </h3>
            <div className="flex gap-2">
              {DURATIONS.map((d) => (
                <button
                  key={d}
                  onClick={() => setDuration(d)}
                  className={`flex-1 py-2 rounded-lg text-sm font-mono font-medium transition-all ${
                    duration === d
                      ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/40'
                      : 'bg-slate-800/40 text-slate-500 border border-transparent hover:border-slate-700'
                  }`}
                >
                  {d}s
                </button>
              ))}
            </div>
          </div>

          {/* Transition */}
          <div>
            <h3 className="font-display text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <Zap size={16} className="text-yellow-400" />
              Transition
            </h3>
            <div className="flex gap-2">
              {TRANSITIONS.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setTransition(t.id)}
                  className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${
                    transition === t.id
                      ? 'bg-yellow-500/15 text-yellow-400 border border-yellow-500/40'
                      : 'bg-slate-800/40 text-slate-500 border border-transparent hover:border-slate-700'
                  }`}
                >
                  {t.name}
                </button>
              ))}
            </div>
          </div>

          {/* Music Volume */}
          <div>
            <h3 className="font-display text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <Volume2 size={16} className="text-green-400" />
              Music Volume — {Math.round(musicVolume * 100)}%
            </h3>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={musicVolume}
              onChange={(e) => setMusicVolume(parseFloat(e.target.value))}
              className="w-full accent-green-500"
            />
          </div>

          {/* Captions toggle */}
          <div>
            <label className="flex items-center gap-3 cursor-pointer">
              <div
                className={`w-10 h-5 rounded-full transition-colors relative ${
                  addCaptions ? 'bg-pink-500' : 'bg-slate-700'
                }`}
                onClick={() => setAddCaptions(!addCaptions)}
              >
                <div
                  className={`w-4 h-4 rounded-full bg-white absolute top-0.5 transition-transform ${
                    addCaptions ? 'translate-x-5' : 'translate-x-0.5'
                  }`}
                />
              </div>
              <div className="flex items-center gap-2">
                <Type size={16} className="text-pink-400" />
                <span className="text-sm text-slate-300">Auto Captions (Whisper)</span>
              </div>
            </label>
          </div>
        </div>
      </div>

      {/* ── Error ──────────────────────────────────────────────── */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* ── Generate Button ────────────────────────────────────── */}
      <div className="flex justify-center pt-4">
        <button
          onClick={handleGenerate}
          disabled={generating || selectedScenes.length === 0}
          className={`flex items-center gap-2 px-10 py-4 rounded-xl font-display font-bold text-base transition-all duration-300 ${
            generating || selectedScenes.length === 0
              ? 'bg-slate-800 text-slate-600 cursor-not-allowed'
              : 'step-active text-white hover:scale-105 glow-pink pulse-glow'
          }`}
        >
          {generating ? (
            <>
              <Loader2 size={20} className="animate-spin" />
              Generating…
            </>
          ) : (
            <>
              <Zap size={20} />
              Generate Reel
            </>
          )}
        </button>
      </div>
    </div>
  );
}
