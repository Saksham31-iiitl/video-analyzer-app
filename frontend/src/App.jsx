import React, { useState } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Clapperboard, Sparkles, Music, Download, Zap } from 'lucide-react';
import UploadPage from './pages/UploadPage';
import AnalyzePage from './pages/AnalyzePage';
import ConfigurePage from './pages/ConfigurePage';
import ExportPage from './pages/ExportPage';

const STEPS = [
  { id: 'upload', label: 'Upload', icon: Clapperboard },
  { id: 'analyze', label: 'Analyze', icon: Sparkles },
  { id: 'configure', label: 'Configure', icon: Music },
  { id: 'export', label: 'Export', icon: Download },
];

function StepIndicator({ currentStep }) {
  const currentIndex = STEPS.findIndex((s) => s.id === currentStep);

  return (
    <div className="flex items-center justify-center gap-2 mb-10">
      {STEPS.map((step, i) => {
        const Icon = step.icon;
        const isActive = i === currentIndex;
        const isDone = i < currentIndex;

        return (
          <React.Fragment key={step.id}>
            {i > 0 && (
              <div
                className={`h-px w-8 sm:w-12 transition-colors duration-500 ${
                  isDone ? 'bg-emerald-500' : 'bg-slate-700'
                }`}
              />
            )}
            <div className="flex flex-col items-center gap-1.5">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center transition-all duration-500 ${
                  isActive
                    ? 'step-active text-white scale-110'
                    : isDone
                    ? 'step-done text-white'
                    : 'bg-slate-800 text-slate-500'
                }`}
              >
                <Icon size={18} />
              </div>
              <span
                className={`text-xs font-medium transition-colors ${
                  isActive ? 'text-pink-400' : isDone ? 'text-emerald-400' : 'text-slate-600'
                }`}
              >
                {step.label}
              </span>
            </div>
          </React.Fragment>
        );
      })}
    </div>
  );
}

export default function App() {
  const [step, setStep] = useState('upload');
  const [projectId, setProjectId] = useState(null);
  const [scenes, setScenes] = useState([]);
  const [selectedScenes, setSelectedScenes] = useState([]);
  const [jobId, setJobId] = useState(null);

  const pageVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 },
  };

  return (
    <div className="min-h-screen bg-mesh noise">
      {/* ── Header ─────────────────────────────────────────────── */}
      <header className="pt-8 pb-4 text-center relative z-10">
        <div className="flex items-center justify-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl step-active flex items-center justify-center">
            <Zap size={20} className="text-white" />
          </div>
          <h1 className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-white">
            Auto Reel Generator
          </h1>
        </div>
        <p className="text-sm text-slate-500 font-body">
          AI-powered short reel creation from raw clips
        </p>
      </header>

      {/* ── Steps ──────────────────────────────────────────────── */}
      <div className="relative z-10">
        <StepIndicator currentStep={step} />
      </div>

      {/* ── Page Content ───────────────────────────────────────── */}
      <main className="max-w-5xl mx-auto px-4 pb-20 relative z-10">
        <AnimatePresence mode="wait">
          {step === 'upload' && (
            <motion.div key="upload" {...pageVariants} transition={{ duration: 0.3 }}>
              <UploadPage
                onUploaded={(pid) => {
                  setProjectId(pid);
                  setStep('analyze');
                }}
              />
            </motion.div>
          )}

          {step === 'analyze' && (
            <motion.div key="analyze" {...pageVariants} transition={{ duration: 0.3 }}>
              <AnalyzePage
                projectId={projectId}
                onAnalyzed={(allScenes) => {
                  setScenes(allScenes);
                  setSelectedScenes(allScenes.filter((s) => s.score >= 0.3));
                  setStep('configure');
                }}
                onBack={() => setStep('upload')}
              />
            </motion.div>
          )}

          {step === 'configure' && (
            <motion.div key="configure" {...pageVariants} transition={{ duration: 0.3 }}>
              <ConfigurePage
                projectId={projectId}
                scenes={scenes}
                selectedScenes={selectedScenes}
                setSelectedScenes={setSelectedScenes}
                onGenerate={(jid) => {
                  setJobId(jid);
                  setStep('export');
                }}
                onBack={() => setStep('analyze')}
              />
            </motion.div>
          )}

          {step === 'export' && (
            <motion.div key="export" {...pageVariants} transition={{ duration: 0.3 }}>
              <ExportPage
                jobId={jobId}
                onRestart={() => {
                  setStep('upload');
                  setProjectId(null);
                  setScenes([]);
                  setSelectedScenes([]);
                  setJobId(null);
                }}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
