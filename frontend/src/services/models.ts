/**
 * 模型配置 API 服务
 * 提供获取可用模型列表的功能
 */

import { request } from './http.ts';

export interface VideoModel {
  id: string;
  provider_id: string;
  provider_name: string;
  model_type: string;
  name: string;
  capabilities: string[];
  requires_first_frame: boolean;
  max_duration: number;
  default_resolution: string;
  default_ratio: string;
}

export interface VideoProvider {
  id: string;
  name: string;
  enabled: boolean;
  models: VideoModel[];
}

export interface VideoModelsResponse {
  ok: boolean;
  providers: VideoProvider[];
  models: VideoModel[];
  default_model: string;
}

export interface TextModel {
  id: string;
  name: string;
  provider_id: string;
  provider_name: string;
}

export interface TextModelsResponse {
  ok: boolean;
  models: TextModel[];
  default_model: string;
}

export interface ImageModelsResponse {
  ok: boolean;
  models: TextModel[];
  default_model: string;
}

/**
 * 获取可用的视频模型列表
 */
export async function listVideoModels(): Promise<VideoModelsResponse> {
  return request('/api/models/video');
}

/**
 * 获取可用的文本模型列表
 */
export async function listTextModels(): Promise<TextModelsResponse> {
  return request('/api/models/text');
}

/**
 * 获取可用的图片模型列表
 */
export async function listImageModels(): Promise<ImageModelsResponse> {
  return request('/api/models/image');
}

export const modelsService = {
  listVideoModels,
  listTextModels,
  listImageModels,
};
