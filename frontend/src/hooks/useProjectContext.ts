export function getProjectIdFromHash() {
  const match = location.hash.match(/projects\/([^/]+)/);
  return match ? match[1] : '';
}
