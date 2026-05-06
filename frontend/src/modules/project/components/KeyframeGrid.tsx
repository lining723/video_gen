/**
 * 关键帧网格展示组件
 * 支持动态网格布局（2×2、3×3、4×4）
 */

import React, { useState, useEffect } from 'react';
import { Spin, Modal, Button, message } from 'antd';
import { WarningOutlined } from '@ant-design/icons';
import { KeyframeData, KeyframeFrame, keyframeService } from '@/services/keyframeService';
import './KeyframeGrid.css';

interface KeyframeGridProps {
  projectId: string;
  shotId: string;
  onLoad?: () => void;
}

const KeyframeGrid: React.FC<KeyframeGridProps> = ({ projectId, shotId, onLoad }) => {
  const [keyframes, setKeyframes] = useState<KeyframeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedFrame, setSelectedFrame] = useState<number | null>(null);

  // 获取关键帧数据
  useEffect(() => {
    loadKeyframes();
  }, [projectId, shotId]);

  const loadKeyframes = async () => {
    setLoading(true);
    try {
      const data = await keyframeService.getKeyframes(projectId, shotId);
      setKeyframes(data);
      onLoad?.();
    } catch (error) {
      console.error('Failed to load keyframes:', error);
      message.error('加载关键帧失败');
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = async (position: number) => {
    try {
      await keyframeService.retryKeyframe(projectId, shotId, position);
      message.success('正在重新生成关键帧...');
      // 重新加载数据
      setTimeout(loadKeyframes, 1000);
    } catch (error) {
      console.error('Failed to retry keyframe:', error);
      message.error('重试失败');
    }
  };

  const handleDownload = async () => {
    try {
      message.loading({ content: '正在下载关键帧网格...', key: 'download' });
      await keyframeService.downloadGrid(projectId, shotId);
      message.success({ content: '下载完成', key: 'download' });
    } catch (error) {
      console.error('Failed to download grid:', error);
      message.error({ content: '下载失败', key: 'download' });
    }
  };

  // 根据grid_type计算列数
  const getGridColumns = (gridType: string): string => {
    const cols = parseInt(gridType.split('x')[0], 10);
    return `repeat(${cols}, 1fr)`;
  };

  // 渲染单个关键帧
  const renderFrame = (frame: KeyframeFrame, index: number) => {
    const { status, image_url, time_ratio, error_message } = frame;

    if (status === 'succeeded' && image_url) {
      return (
        <div
          key={index}
          className="grid-item"
          onClick={() => setSelectedFrame(index)}
        >
          <img src={image_url} alt={`帧 ${index + 1}`} />
          <span className="time-label">{(time_ratio * 100).toFixed(0)}%</span>
        </div>
      );
    }

    if (status === 'failed') {
      return (
        <div key={index} className="grid-item failed-frame">
          <WarningOutlined className="warning-icon" />
          <span className="failed-text">生成失败</span>
          {error_message && <span className="error-text">{error_message}</span>}
          <Button
            size="small"
            type="primary"
            onClick={() => handleRetry(index)}
          >
            重试
          </Button>
        </div>
      );
    }

    if (status === 'generating') {
      return (
        <div key={index} className="grid-item generating-frame">
          <Spin tip="生成中..." />
        </div>
      );
    }

    // pending状态
    return (
      <div key={index} className="grid-item pending-frame">
        <span className="pending-text">等待生成</span>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="keyframe-grid">
        <Spin tip="关键帧加载中..." />
      </div>
    );
  }

  if (!keyframes) {
    return (
      <div className="keyframe-grid">
        <p className="no-data">暂无关键帧数据</p>
      </div>
    );
  }

  return (
    <div className="keyframe-grid">
      <div className="grid-header">
        <span className="grid-info">
          网格类型：{keyframes.grid_type} | 帧数：{keyframes.frame_count}
        </span>
        <Button type="primary" onClick={handleDownload}>
          下载网格
        </Button>
      </div>

      <div
        className="grid-container"
        style={{
          display: 'grid',
          gridTemplateColumns: getGridColumns(keyframes.grid_type),
          gap: '8px',
          maxWidth: '800px',
        }}
      >
        {keyframes.frames.map((frame, index) => renderFrame(frame, index))}
      </div>

      {/* 大图预览 */}
      <Modal
        visible={selectedFrame !== null}
        onCancel={() => setSelectedFrame(null)}
        footer={null}
        width={800}
      >
        {selectedFrame !== null && keyframes.frames[selectedFrame]?.image_url && (
          <img
            src={keyframes.frames[selectedFrame].image_url!}
            alt={`关键帧 ${selectedFrame + 1}`}
            style={{ width: '100%' }}
          />
        )}
      </Modal>
    </div>
  );
};

export default KeyframeGrid;
