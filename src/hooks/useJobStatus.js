import { useState, useEffect, useRef } from 'react';
import { getJobStatus } from '../api/client';

/**
 * Poll a generation job until it completes or fails.
 * @param {string|null} jobId - Job ID to poll (null = inactive).
 * @param {number} interval - Polling interval in ms.
 * @returns {{ status, progress, output, error }}
 */
export function useJobStatus(jobId, interval = 1500) {
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState(0);
  const [output, setOutput] = useState(null);
  const [error, setError] = useState(null);
  // New: populated when backend returns them on completion
  const [viralityScore, setViralityScore] = useState(null);
  const [captions, setCaptions] = useState(null);
  const timerRef = useRef(null);

  useEffect(() => {
    if (!jobId) return;

    setStatus('processing');
    setProgress(0);
    setOutput(null);
    setError(null);
    setViralityScore(null);
    setCaptions(null);

    const poll = async () => {
      try {
        const data = await getJobStatus(jobId);
        setStatus(data.status);
        setProgress(data.progress || 0);

        if (data.status === 'done') {
          setOutput(data.output);
          // Backend may embed these in the done response
          if (data.virality_score != null) setViralityScore(data.virality_score);
          if (data.captions) setCaptions(data.captions);
          clearInterval(timerRef.current);
        } else if (data.status === 'failed') {
          setError(data.error || 'Generation failed');
          clearInterval(timerRef.current);
        }
      } catch (err) {
        setError(err.message);
        clearInterval(timerRef.current);
      }
    };

    poll(); // immediate first check
    timerRef.current = setInterval(poll, interval);

    return () => clearInterval(timerRef.current);
  }, [jobId, interval]);

  return { status, progress, output, error, viralityScore, captions };
}
