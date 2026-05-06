import { mediaUrl } from '../../services/http.ts';
import { escapeAttribute, escapeHtml } from '../../utils/html.ts';

function getExtension(path = '') {
  const clean = path.split('?')[0];
  const parts = clean.split('.');
  return parts.length > 1 ? parts.pop().toLowerCase() : '';
}

export function renderMediaPreview(path, title = '文件预览', sourceUrl = '') {
  if (!path) {
    return '<div class="muted">暂无可预览文件</div>';
  }
  const url = mediaUrl(path);
  const previewKey = `${title}::${path}`;
  const extension = getExtension(path);
  let body = `<a class="button-link ghost" href="${url}" target="_blank" rel="noreferrer">打开文件</a>`;

  if (['png', 'jpg', 'jpeg', 'webp', 'gif'].includes(extension)) {
    body = `
      <div class="preview-frame">
        <img src="${url}" alt="${escapeAttribute(title)}" />
      </div>
    `;
  } else if (['mp4', 'webm', 'mov', 'm4v'].includes(extension)) {
    body = `
      <div class="preview-frame">
        <video controls preload="metadata" src="${url}"></video>
      </div>
    `;
  } else if (['txt', 'md', 'json', 'log'].includes(extension)) {
    body = `
      <div class="preview-frame">
        <iframe src="${url}" title="${escapeAttribute(title)}"></iframe>
      </div>
    `;
  }

  const source = sourceUrl
    ? `<div class="storage-path">来源 URL：<a class="source-link" href="${escapeAttribute(sourceUrl)}" target="_blank" rel="noreferrer">查看原始资源</a></div>`
    : '';

  return `
    <details class="details" data-preview-key="${escapeAttribute(previewKey)}">
      <summary>预览 ${escapeHtml(title)}</summary>
      <div class="details-body">
        <div class="storage-path">存储路径：${escapeHtml(path)}</div>
        ${body}
        ${source}
      </div>
    </details>
  `;
}
