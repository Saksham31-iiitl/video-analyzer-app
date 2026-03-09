import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion } from 'framer-motion';
import { Upload, Film, Music2, X, FileVideo, Loader2 } from 'lucide-react';
import { uploadFiles } from '../api/client';

export default function UploadPage({ onUploaded }) {
  const [videoFiles, setVideoFiles] = useState([]);
  const [musicFile, setMusicFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);

  // ── Video dropzone ────────────────────────────────────────────
  const onDropVideos = useCallback((accepted) => {
    const newFiles = [...videoFiles, ...accepted].slice(0, 10);
    setVideoFiles(newFiles);
    setError(null);
  }, [videoFiles]);

  const {
    getRootProps: getVideoProps,
    getInputProps: getVideoInput,
    isDragActive: videoDragActive,
  } = useDropzone({
    onDrop: onDropVideos,
    accept: { 'video/*': ['.mp4', '.mov', '.avi', '.mkv', '.webm'] },
    maxFiles: 10,
  });

  // ── Music dropzone ────────────────────────────────────────────
  const onDropMusic = useCallback((accepted) => {
    if (accepted.length > 0) {
      setMusicFile(accepted[0]);
      setError(null);
    }
  }, []);

  const {
    getRootProps: getMusicProps,
    getInputProps: getMusicInput,
    isDragActive: musicDragActive,
  } = useDropzone({
    onDrop: onDropMusic,
    accept: { 'audio/*': ['.mp3', '.wav', '.aac', '.ogg', '.m4a'] },
    maxFiles: 1,
  });

  const removeVideo = (idx) => {
    setVideoFiles((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleUpload = async () => {
    if (videoFiles.length === 0) {
      setError('Please add at least one video clip.');
      return;
    }

    setUploading(true);
    setProgress(0);
    setError(null);

    try {
      const result = await uploadFiles(videoFiles, musicFile, setProgress);
      onUploaded(result.project_id);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const formatSize = (bytes) => {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-8">
      {/* ── Video Upload Zone ──────────────────────────────────── */}
      <div>
        <h2 className="font-display text-lg font-semibold text-white mb-3 flex items-center gap-2">
          <Film size={20} className="text-pink-400" />
          Video Clips
          <span className="text-sm font-normal text-slate-500">
            ({videoFiles.length}/10)
          </span>
        </h2>

        <div
          {...getVideoProps()}
          className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-300 ${
            videoDragActive
              ? 'dropzone-active border-pink-500'
              : 'border-slate-700 hover:border-slate-500'
          }`}
        >
          <input {...getVideoInput()} />
          <Upload size={36} className="mx-auto mb-3 text-slate-500" />
          <p className="text-slate-400 font-medium">
            {videoDragActive
              ? 'Drop your clips here…'
              : 'Drag & drop video clips, or click to browse'}
          </p>
          <p className="text-xs text-slate-600 mt-1">
            MP4, MOV, AVI, MKV, WebM — up to 10 files
          </p>
        </div>

        {/* File list */}
        {videoFiles.length > 0 && (
          <div className="mt-4 space-y-2">
            {videoFiles.map((file, i) => (
              <motion.div
                key={file.name + i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex items-center gap-3 bg-slate-800/60 rounded-xl px-4 py-3 border border-slate-700/50"
              >
                <FileVideo size={18} className="text-pink-400 flex-shrink-0" />
                <span className="text-sm text-slate-300 truncate flex-1">{file.name}</span>
                <span className="text-xs text-slate-600 flex-shrink-0">{formatSize(file.size)}</span>
                <button
                  onClick={() => removeVideo(i)}
                  className="text-slate-600 hover:text-red-400 transition-colors"
                >
                  <X size={16} />
                </button>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* ── Music Upload Zone ─────────────────────────────────── */}
      <div>
        <h2 className="font-display text-lg font-semibold text-white mb-3 flex items-center gap-2">
          <Music2 size={20} className="text-purple-400" />
          Background Music
          <span className="text-xs font-normal text-slate-600 ml-1">(optional)</span>
        </h2>

        {musicFile ? (
          <div className="flex items-center gap-3 bg-slate-800/60 rounded-xl px-4 py-3 border border-purple-500/30">
            <Music2 size={18} className="text-purple-400" />
            <span className="text-sm text-slate-300 truncate flex-1">{musicFile.name}</span>
            <span className="text-xs text-slate-600">{formatSize(musicFile.size)}</span>
            <button
              onClick={() => setMusicFile(null)}
              className="text-slate-600 hover:text-red-400 transition-colors"
            >
              <X size={16} />
            </button>
          </div>
        ) : (
          <div
            {...getMusicProps()}
            className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all duration-300 ${
              musicDragActive
                ? 'dropzone-active border-purple-500'
                : 'border-slate-700/60 hover:border-slate-600'
            }`}
          >
            <input {...getMusicInput()} />
            <Music2 size={28} className="mx-auto mb-2 text-slate-600" />
            <p className="text-sm text-slate-500">Drop a music track or click to browse</p>
            <p className="text-xs text-slate-700 mt-1">MP3, WAV, AAC, OGG</p>
          </div>
        )}
      </div>

      {/* ── Error ─────────────────────────────────────────────── */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* ── Upload Button ─────────────────────────────────────── */}
      <div className="flex justify-center pt-4">
        <button
          onClick={handleUpload}
          disabled={uploading || videoFiles.length === 0}
          className={`flex items-center gap-2 px-8 py-3.5 rounded-xl font-display font-semibold text-sm transition-all duration-300 ${
            uploading || videoFiles.length === 0
              ? 'bg-slate-800 text-slate-600 cursor-not-allowed'
              : 'step-active text-white hover:scale-105 glow-pink pulse-glow'
          }`}
        >
          {uploading ? (
            <>
              <Loader2 size={18} className="animate-spin" />
              Uploading… {progress}%
            </>
          ) : (
            <>
              <Upload size={18} />
              Upload & Continue
            </>
          )}
        </button>
      </div>

      {/* Upload progress bar */}
      {uploading && (
        <div className="w-full max-w-md mx-auto">
          <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-pink-500 to-purple-500 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
