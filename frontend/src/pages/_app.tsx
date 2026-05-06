import { renderProjectsPage } from './projects/index.tsx';
import { renderProjectDashboard } from './projects/[projectId]/index.tsx';
import { renderScenePage } from './projects/[projectId]/scene.tsx';
import { renderStoryboardPage } from './projects/[projectId]/storyboard.tsx';
import { renderRendersPage } from './projects/[projectId]/renders.tsx';
import { renderFinalVideoPage } from './projects/[projectId]/final-video.tsx';

const root = document.getElementById('app');

function parseRoute() {
  const hash = location.hash || '#/projects';
  return hash.replace(/^#/, '').split('/').filter(Boolean);
}

async function render() {
  const parts = parseRoute();
  if (parts[0] !== 'projects') return (location.hash = '#/projects');
  if (parts.length === 1) return renderProjectsPage(root);
  const projectId = parts[1];
  if (parts.length === 2) return renderProjectDashboard(root, projectId);
  if (parts[2] === 'scene') return renderScenePage(root, projectId);
  if (parts[2] === 'storyboard') return renderStoryboardPage(root, projectId);
  if (parts[2] === 'renders') return renderRendersPage(root, projectId);
  if (parts[2] === 'final-video') return renderFinalVideoPage(root, projectId);
  return renderProjectsPage(root);
}

window.addEventListener('hashchange', render);
render();
