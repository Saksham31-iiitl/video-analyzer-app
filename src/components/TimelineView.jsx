import React, { useRef } from 'react';
import { motion } from 'framer-motion';
import { GripVertical, Clock, Film } from 'lucide-react';

/**
 * TimelineView
 * Horizontal scrollable timeline showing selected scenes in order.
 * Each scene tile is proportionally sized to its duration.
 * Users can drag tiles left/right to reorder them.
 *
 * Props:
 *   scenes          {Array}     selectedScenes array from ConfigurePage
 *   onReorder       {function}  (reorderedArray) => void — update parent state
 */
export default function TimelineView({ scenes, onReorder }) {
  const dragIndex = useRef(null);
  const dragOverIndex = useRef(null);

  // ── Score colour helper (same logic as AnalyzePage) ──
  const scoreColor = (score) => {
    if (score >= 0.7) return 'border-emerald-500/60 bg-emerald-500/10';
    if (score >= 0.4) return 'border-yellow-500/60 bg-yellow-500/10';
    return 'border-slate-700 bg-slate-800/40';
  };

  const scoreDot = (score) => {
    if (score >= 0.7) return 'bg-emerald-500';
    if (score >= 0.4) return 'bg-yellow-400';
    return 'bg-slate-600';
  };

  // Total duration — used to size tiles proportionally
  const totalDuration = scenes.reduce((sum, s) => sum + s.duration, 0) || 1;

  // ── Drag-and-drop handlers ──
  const handleDragStart = (i) => { dragIndex.current = i; };

  const handleDragEnter = (i) => { dragOverIndex.current = i; };

  const handleDragEnd = () => {
    const from = dragIndex.current;
    const to = dragOverIndex.current;
    if (from === null || to === null || from === to) return;

    const reordered = [...scenes];
    const [moved] = reordered.splice(from, 1);
    reordered.splice(to, 0, moved);
    onReorder(reordered);

    dragIndex.current = null;
    dragOverIndex.current = null;
  };

  if (scenes.length === 0) {
    return (
      <div className="flex items-center justify-center h-20 rounded-xl border border-dashed border-slate-700 text-sm text-slate-600">
        No scenes selected — pick some above
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <h3 className="font-display text-sm font-semibold text-white flex items-center gap-2">
        <Film size={16} className="text-cyan-400" />
        Timeline
        <span className="text-xs font-normal text-slate-500">
          {scenes.length} clips · {totalDuration.toFixed(1)}s total
        </span>
        <span className="text-[10px] text-slate-600 ml-auto">drag to reorder</span>
      </h3>

      {/* ── Scrollable track ── */}
      <div className="overflow-x-auto pb-2">
        <div className="flex items-stretch gap-1.5 min-w-max h-20">
          {scenes.map((scene, i) => {
            // Minimum 64px width; max proportional to 600px total track
            const pct = scene.duration / totalDuration;
            const width = Math.max(64, Math.round(pct * 600));

            return (
              <motion.div
                key={`${scene.clip_file}-${scene.scene_index}-${i}`}
                draggable
                onDragStart={() => handleDragStart(i)}
                onDragEnter={() => handleDragEnter(i)}
                onDragEnd={handleDragEnd}
                onDragOver={(e) => e.preventDefault()}
                layout
                transition={{ duration: 0.2 }}
                className={`relative flex-shrink-0 rounded-xl border-2 cursor-grab active:cursor-grabbing select-none overflow-hidden ${scoreColor(scene.score)}`}
                style={{ width }}
              >
                {/* Drag handle */}
                <div className="absolute left-1 top-1/2 -translate-y-1/2 text-slate-600">
                  <GripVertical size={12} />
                </div>

                {/* Score dot */}
                <div className={`absolute top-2 right-2 w-2 h-2 rounded-full ${scoreDot(scene.score)}`} />

                {/* Content */}
                <div className="flex flex-col justify-center h-full px-5">
                  <span className="text-[10px] text-slate-500 truncate max-w-full">
                    {scene.clip_file.split('/').pop()}
                  </span>
                  <div className="flex items-center gap-1 mt-0.5">
                    <Clock size={9} className="text-slate-600" />
                    <span className="text-[10px] font-mono text-slate-400">
                      {scene.duration.toFixed(1)}s
                    </span>
                  </div>
                </div>

                {/* Scene index badge */}
                <div className="absolute bottom-1.5 left-5 text-[9px] font-mono text-slate-600">
                  #{i + 1}
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* ── Ruler ── */}
      <div className="flex text-[9px] font-mono text-slate-700 overflow-x-auto">
        {Array.from({ length: Math.ceil(totalDuration) + 1 }, (_, s) => (
          <div key={s} className="flex-shrink-0 w-[60px] border-l border-slate-800 pl-1">
            {s}s
          </div>
        ))}
      </div>
    </div>
  );
}
