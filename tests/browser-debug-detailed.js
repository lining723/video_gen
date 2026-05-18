/**
 * 详细浏览器调试 - 捕获所有错误和状态
 */

const { chromium } = require('playwright');

async function debugFrontend() {
  console.log('🔍 启动详细浏览器调试...\n');

  const browser = await chromium.launch({
    headless: true,
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  // 收集所有日志
  const consoleLogs = [];
  const errors = [];
  const requests = [];

  page.on('console', msg => {
    consoleLogs.push(`[${msg.type()}] ${msg.text()}`);
  });

  page.on('pageerror', error => {
    errors.push(`页面错误: ${error.message}\n${error.stack}`);
  });

  page.on('requestfailed', request => {
    errors.push(`请求失败: ${request.url()} - ${request.failure()?.errorText}`);
  });

  page.on('request', request => {
    requests.push(`请求: ${request.method()} ${request.url()}`);
  });

  page.on('response', response => {
    if (!response.ok()) {
      errors.push(`响应错误: ${response.status()} ${response.url()}`);
    }
  });

  try {
    console.log('访问前端页面...');
    await page.goto('http://127.0.0.1:3100', { waitUntil: 'networkidle' });

    // 等待更长时间让页面渲染
    await page.waitForTimeout(3000);

    // 输出请求日志
    console.log('\n📋 网络请求:');
    requests.forEach(r => console.log(`  ${r}`));

    // 输出控制台日志
    console.log('\n📋 控制台日志:');
    if (consoleLogs.length === 0) {
      console.log('  (无)');
    } else {
      consoleLogs.forEach(log => console.log(`  ${log}`));
    }

    // 输出错误
    console.log('\n❌ 错误:');
    if (errors.length === 0) {
      console.log('  (无)');
    } else {
      errors.forEach(err => console.log(`  ${err}`));
    }

    // 检查页面内容
    const bodyContent = await page.evaluate(() => document.body.innerHTML);
    console.log('\n📄 页面内容长度:', bodyContent.length);

    // 检查 #app 元素
    const appContent = await page.evaluate(() => {
      const app = document.getElementById('app');
      return app ? app.innerHTML : 'NOT FOUND';
    });
    console.log('📄 #app 内容:', appContent.substring(0, 500));

    // 检查加载的脚本
    const scripts = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('script')).map(s => ({
        src: s.src || 'inline',
        type: s.type || 'text/javascript',
        content: s.src ? null : s.textContent?.substring(0, 100)
      }));
    });
    console.log('\n📜 加载的脚本:', JSON.stringify(scripts, null, 2));

    // 截图
    await page.screenshot({ path: '.playwright-mcp/screenshot-debug.png', fullPage: true });
    console.log('\n📸 截图已保存到 .playwright-mcp/screenshot-debug.png');

  } catch (error) {
    console.error('错误:', error.message);
  } finally {
    await browser.close();
  }
}

debugFrontend().catch(console.error);
