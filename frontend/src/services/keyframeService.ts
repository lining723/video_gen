/**
 * 关键帧API服务
 * 提供关键帧数据获取和下载功能
 */

export type KeyframeStatus = 'pending' | 'generating' | 'succeeded' | 'failed';

export interface KeyframeFrame {
  position: number;
  time_ratio: number;
  image_url?: string;
  thumbnail_url?: string;
  status: KeyframeStatus;
  error_message?: string;
}

export interface KeyframeData {
  grid_type: '2x2' | '3x3' | '4x4';
  frame_count: number;
  frames: KeyframeFrame[];
}

export interface ProjectKeyframesStatus {
  project_id: string;
  total_shots: number;
  completed_shots: number;
  generating_shots: number;
  failed_shots: number;
  total_frames: number;
  succeeded_frames: number;
  failed_frames: number;
  shots: Array<{
    shot_id: string;
    status: string;
    grid_type: string;
    frame_count: number;
    succeeded_count: number;
    failed_count: number;
  }>;
}

const API_BASE = '/api';

/**
 * 获取指定镜头的关键帧
 */
export async function getKeyframes(projectId: string, shotId: string): Promise<KeyframeData> {
  const response = await fetch(`${API_BASE}/projects/${projectId}/shots/${shotId}/keyframes`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(error.error || 'Failed to fetch keyframes');
  }

  const data = await response.json();
  return data;
}

/**
 * 获取项目关键帧状态汇总
 */
export async function getProjectKeyframesStatus(projectId: string): Promise<ProjectKeyframesStatus> {
  const response = await fetch(`${API_BASE}/projects/${projectId}/keyframes/status`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(error.error || 'Failed to fetch keyframes status');
  }

  const data = await response.json();
  return data;
}

/**
 * 重试生成指定的关键帧
 */
export async function retryKeyframe(
  projectId: string,
  shotId: string,
  position: number
): Promise<{ retry_count: number; message: string }> {
  const response = await fetch(
    `${API_BASE}/projects/${projectId}/shots/${shotId}/keyframes/${position}/retry`,
    { method: 'POST' }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(error.error || 'Failed to retry keyframe');
  }

  const data = await response.json();
  return data;
}

/**
 * 下载关键帧网格图片
 */
export async function downloadGrid(projectId: string, shotId: string): Promise<void> {
  // 获取关键帧数据
  const keyframes = await getKeyframes(projectId, shotId);

  // 使用Canvas合并图片
  await downloadGridAsImage(keyframes, shotId);
}

/**
 * 使用Canvas合并图片并下载
 */
async function downloadGridAsImage(keyframes: KeyframeData, shotId: string): Promise<void> {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');

  if (!ctx) {
    throw new Error('Canvas context not available');
  }

  // 计算网格尺寸
  const cols = parseInt(keyframes.grid_type.split('x')[0], 10);
  const rows = parseInt(keyframes.grid_type.split('x')[1], 10);
  const frameSize = 300; // 每帧大小300x300

  canvas.width = cols * frameSize;
  canvas.height = rows * frameSize;

  // 加载所有图片
  const imagePromises = keyframes.frames
    .filter(frame => frame.image_url)
    .map(async (frame) => {
      try {
        return await loadImage(frame.image_url!);
      } catch (error) {
        console.error(`Failed to load image at position ${frame.position}:`, error);
        return null;
      }
    });

  const images = await Promise.all(imagePromises);

  // 绘制到Canvas
  images.forEach((img, index) => {
    if (img) {
      const col = index % cols;
      const row = Math.floor(index / cols);
      ctx.drawImage(img, col * frameSize, row * frameSize, frameSize, frameSize);
    }
  });

  // 触发下载
  const url = canvas.toDataURL('image/png');
  const a = document.createElement('a');
  a.href = url;
  a.download = `keyframe-grid-${shotId}.png`;
  a.click();
}

/**
 * 加载图片
 */
function loadImage(url: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = url;
  });
}

export const keyframeService = {
  getKeyframes,
  getProjectKeyframesStatus,
  retryKeyframe,
  downloadGrid,
};
