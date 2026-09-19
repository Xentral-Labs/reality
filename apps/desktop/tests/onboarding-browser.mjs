// Actual bundled backend + fresh PostgreSQL; no mocked company setup responses.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createInterface } from 'node:readline';
import { resolve } from 'node:path';
import { mkdir, access } from 'node:fs/promises';
import { chromium } from '../build/browser/node_modules/playwright/index.mjs';

const resources = resolve(process.argv[2] || 'apps/desktop/dist/Reality Local Development.app/Contents/Resources');
const evidence = resolve('specs/239-macos-local-app/evidence');
const child = spawn(`${resources}/runtime/python/bin/python3.12`, ['-I', `${resources}/probe/local-runtime.py`], {env: {PATH: '/usr/bin:/bin'}, stdio: ['pipe','pipe','pipe']});
let diagnostics = '';
child.stderr.setEncoding('utf8');
child.stderr.on('data', chunk => {
  diagnostics = (diagnostics + chunk).slice(-12000);
  if (process.env.REALITY_DESKTOP_DEBUG === '1') process.stderr.write(chunk);
});
let browser;
let testRoot;
const exit = new Promise(resolveExit => child.once('exit', code => resolveExit(code)));
try {
  const endpoint = await new Promise((resolveEndpoint, reject) => {
    const deadline = setTimeout(() => reject(Error('Local startup timed out')), 180000);
    const lines = createInterface({input: child.stdout});
    child.once('exit', () => {clearTimeout(deadline); reject(Error('Local process exited before readiness'));});
    lines.once('line', line => {clearTimeout(deadline); try {resolveEndpoint(JSON.parse(line));} catch {reject(Error('Invalid private startup message'));}});
  });
  testRoot = endpoint.test_root;
  assert.ok(testRoot?.startsWith("/private/tmp/reality-pg-"));
  // Endpoint secrets stay in memory and are never printed or saved in screenshots.
  browser = await chromium.launch({headless: true, executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
  const context = await browser.newContext({viewport: {width: 1440, height: 960}});
  await context.addCookies([{name: endpoint.cookie_name, value: endpoint.token, url: endpoint.origin, httpOnly: true, sameSite: 'Strict'}]);
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('response', response => {
    if (process.env.REALITY_DESKTOP_DEBUG === '1' && response.status() >= 400)
      console.error(`HTTP ${response.status()} ${new URL(response.url()).pathname}`);
  });
  await page.goto(`${endpoint.origin}/app`);
  await page.getByLabel('Company name (required)').waitFor({timeout: 30000});
  const viewportFit = await page.evaluate(() => ({
    innerHeight: window.innerHeight,
    scrollHeight: document.documentElement.scrollHeight,
  }));
  assert.ok(
    viewportFit.scrollHeight <= viewportFit.innerHeight,
    `First-company setup must fit without scrolling: ${JSON.stringify(viewportFit)}`,
  );
  await page.getByRole('button', {name: 'Create company', exact: true}).waitFor({state: 'visible'});
  await mkdir(evidence, {recursive: true});
  await page.screenshot({path: `${evidence}/local-company-setup.png`});
  await page.getByLabel('Company name (required)').fill('Fresh live desktop demo');
  await page.getByLabel('Try demo data').check();
  assert.equal(await page.getByLabel('Enable live simulation').isChecked(), true);
  await page.getByLabel('Anthropic API key (optional)').fill('sk-ant-local-acceptance-test');
  await page.getByRole('button', {name: 'Create company', exact: true}).click();
  await page.waitForURL(url => Boolean(url.searchParams.get('tenant')), {timeout: 180000});
  assert.equal(new URL(page.url()).pathname, '/app', 'Creation must open Home');
  await page.locator('[data-primary-navigation]').waitFor({state: 'visible'});
  await page.getByRole('button', {name: /^Commitments .* open$/}).waitFor({state: 'visible'});
  const response = await context.request.get(`${endpoint.origin}/api/v1/bootstrap`);
  assert.equal(response.status(), 200);
  const bootstrap = await response.json();
  assert.equal(bootstrap.tenants.length, 1);
  assert.equal(bootstrap.tenants[0].name, 'Fresh live desktop demo');
  assert.equal(bootstrap.tenants[0].company_kind, 'demo');
  assert.equal(bootstrap.tenants[0].demo_data_state, 'running');
  const tenant = bootstrap.tenants[0].id;
  const payments = await context.request.get(`${endpoint.origin}/api/tenants/${tenant}/finance/payments`);
  assert.equal(payments.status(), 200);
  assert.ok((await payments.json()).items.length > 0, 'Demo must contain payments');
  const ai = await context.request.get(`${endpoint.origin}/api/tenants/${tenant}/settings/ai`);
  assert.equal(ai.status(), 200);
  assert.equal((await ai.json()).copilot.has_company_api_key, true);
  await page.getByText('Fresh live desktop demo', {exact: true}).first().waitFor({timeout: 30000});
  await page.screenshot({path: `${evidence}/local-company-open.png`});
  assert.deepEqual(errors, []);
  console.log('PASS: desktop demo + live jobs + payments + encrypted Anthropic key → Home with visible sidebar.');
} finally {
  await browser?.close();
  child.stdin.end();
  const code = await Promise.race([exit, new Promise(resolveTimeout => setTimeout(() => resolveTimeout('timeout'), 45000).unref())]);
  assert.equal(code, 0, 'Local runtime must stop and remove its disposable database');
  if (testRoot) await assert.rejects(access(testRoot), {code: 'ENOENT'});
  if (process.exitCode) console.error(diagnostics);
}
