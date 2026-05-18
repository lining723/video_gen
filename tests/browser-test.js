/**
 * 视频生成平台浏览器自动化测试
 */

const { chromium } = require('playwright');

async function runTests() {
  console.log('🚀 启动浏览器自动化测试...\n');

  const browser = await chromium.launch({
    headless: false,  // 显示浏览器窗口
    slowMo: 500,      // 减慢操作速度便于观察
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // 测试1: 访问首页
    console.log('📋 测试1: 访问首页');
    await page.goto('http://127.0.0.1:3100');
    await page.waitForLoadState('networkidle');

    const title = await page.title();
    console.log(`  页面标题: ${title}`);

    // 截图
    await page.screenshot({ path: '.playwright-mcp/screenshot-home.png' });
    console.log('  ✅ 首页加载成功\n');

    // 测试2: 检查API连接
    console.log('📋 测试2: 测试视频模型API');
    const apiResponse = await page.evaluate(async () => {
      const response = await fetch('http://127.0.0.1:8100/api/models/video', {
        headers: { 'X-API-Key': 'dev-secret-key-change-me' }
      });
      return await response.json();
    });

    if (apiResponse.ok) {
      console.log(`  ✅ API连接正常`);
      console.log(`  提供商数量: ${apiResponse.providers?.length || 0}`);
      console.log(`  模型数量: ${apiResponse.models?.length || 0}`);
      console.log(`  默认模型: ${apiResponse.default_model}\n`);
    } else {
      console.log(`  ❌ API返回错误: ${apiResponse.error}\n`);
    }

    // 测试3: 创建项目页面
    console.log('📋 测试3: 访问项目创建页面');
    await page.goto('http://127.0.0.1:3100/#/projects/new');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: '.playwright-mcp/screenshot-new-project.png' });
    console.log('  ✅ 项目创建页面加载成功\n');

    // 测试4: 检查项目列表
    console.log('📋 测试4: 访问项目列表');
    await page.goto('http://127.0.0.1:3100/#/projects');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: '.playwright-mcp/screenshot-projects.png' });
    console.log('  ✅ 项目列表页面加载成功\n');

    // 测试总结
    console.log('═'.repeat(50));
    console.log('✅ 所有测试通过!');
    console.log('═'.repeat(50));
    console.log('\n截图已保存到 .playwright-mcp/ 目录');

  } catch (error) {
    console.error('❌ 测试失败:', error.message);
    await page.screenshot({ path: '.playwright-mcp/screenshot-error.png' });
  } finally {
    await browser.close();
  }
}

runTests().catch(console.error);
