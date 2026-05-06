const ESCAPE_LOOKUP = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
};

export function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => ESCAPE_LOOKUP[char]);
}

export function escapeAttribute(value) {
  return escapeHtml(value);
}

export function preserveLineBreaks(value) {
  return escapeHtml(value).replace(/\n/g, '<br />');
}
