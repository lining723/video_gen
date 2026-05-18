/**
 * 浏览器调试 - 捕获控制台错误
 */

const { chromium } = require('playwright');

async function debugFrontend() {
  console.log('🔍 启动浏览器调试...\n');

  const browser = await chromium.launch({
    headless: true,
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  // 收集控制台日志
  const consoleLogs = [];
  const errors = [];

  page.on('console', msg => {
    consoleLogs.push(`[${msg.type()}] ${msg.text()}`);
  });

  page.on('pageerror', error => {
    errors.push(error.message);
  });

  page.on('requestfailed', request => {
    errors.push(`请求失败: ${request.url()} - ${request.failure()?.errorText}`);
  });

  try {
    console.log('访问前端页面...');
    await page.goto('http://127.0.0.1:3100', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

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
      return app ? app.innerHTML.length : -1;
    });
    console.log('📄 #app 内容长度:', appContent);

    // 检查加载的脚本
    const scripts = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('script')).map(s => s.src || 'inline');
    });
    console.log('\n📜 加载的脚本:', scripts);

  } catch (error) {
    console.error('错误:', error.message);
  } finally {
    await browser.close();
  }
}

debugFrontend().catch(console.error);
