import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 300000, // 5 min for video processing
});

/**
 * Upload video clips and optional music file.
 * @param {File[]} videoFiles  - Array of video File objects.
 * @param {File|null} musicFile - Optional music File object.
 * @param {function} onProgress - Upload progress callback (0–100).
 * @returns {Promise<object>} - { project_id, videos, music, message }
 */
export async function uploadFiles(videoFiles, musicFile = null, onProgress = null) {
  const formData = new FormData();
  videoFiles.forEach((file) => {
    formData.append('videos', file);
  });
  if (musicFile) {
    formData.append('music', musicFile);
  }

  const response = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded * 100) / e.total));
      }
    },
  });
  return response.data;
}

/**
 * Analyse scenes in uploaded clips.
 * @param {string} projectId
 * @param {string[]} clipPrompts - CLIP text prompts for scoring.
 * @returns {Promise<object>} - { project_id, total_scenes, scenes }
 */
export async function analyzeProject(projectId, clipPrompts = null) {
  const response = await api.post('/analyze', {
    project_id: projectId,
    clip_prompts: clipPrompts,
  });
  return response.data;
}

/**
 * Generate the final reel.
 * @param {object} params
 * @returns {Promise<object>} - { job_id, status, message }
 */
export async function generateReel({
  projectId,
  selectedScenes,
  targetDuration = 30,
  style = 'fast_cuts',
  addCaptions = false,
  transitionType = 'cut',
  musicVolume = 0.7,
}) {
  const response = await api.post('/generate', {
    project_id: projectId,
    selected_scenes: selectedScenes.map((s) => ({
      clip_file: s.clip_file,
      start_time: s.start_time,
      end_time: s.end_time,
      score: s.score,
    })),
    target_duration: targetDuration,
    style,
    add_captions: addCaptions,
    transition_type: transitionType,
    music_volume: musicVolume,
  });
  return response.data;
}

/**
 * Poll job status.
 * @param {string} jobId
 * @returns {Promise<object>} - { status, progress, output, error }
 */
export async function getJobStatus(jobId) {
  const response = await api.get(`/status/${jobId}`);
  return response.data;
}

/**
 * Get project info.
 * @param {string} projectId
 * @returns {Promise<object>}
 */
export async function getProject(projectId) {
  const response = await api.get(`/projects/${projectId}`);
  return response.data;
}

/**
 * Save edited captions back to the backend.
 * Called by CaptionEditor after the user edits caption text.
 * @param {string} jobId
 * @param {Array}  captions - [{ id, start, end, text }, ...]
 * @returns {Promise<object>} - { ok: true }
 */
export async function updateCaptions(jobId, captions) {
  const response = await api.patch(`/captions/${jobId}`, { captions });
  return response.data;
}

/**
 * Fetch the virality prediction for a completed project.
 * Use this if the backend exposes a dedicated endpoint instead of
 * embedding the score in the job status response.
 * @param {string} projectId
 * @returns {Promise<object>} - { score, breakdown }
 */
export async function getViralityScore(projectId) {
  const response = await api.get(`/virality/${projectId}`);
  return response.data;
}

export default api;
