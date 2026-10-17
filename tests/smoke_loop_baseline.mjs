/**
 * Headless smoke for the vendored loop baseline.
 *
 * Serves this repository on 127.0.0.1 and drives the system Chrome binary
 * over the DevTools protocol. Node 22+ supplies the WebSocket client, so
 * the check does not install Playwright or any other package.
 *
 *   node tests/smoke_loop_baseline.mjs
 *
 * Pass means index.html loaded ./agentropolis-loop-baseline.js from the
 * local server, the script set its runtime flag, no console error or
 * exception was reported, and no request URL touched the remote
 * loop-baseline host.
 */

import { spawn, execFileSync } from 'node:child_process';
import { createServer } from 'node:http';
import { existsSync, mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { extname, join, normalize, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(fileURLToPath(new URL('..', import.meta.url)));
const LOCAL_SUFFIX = '/agentropolis-loop-baseline.js';
const REMOTE_MARKERS = [
  'agentropolis-city-of-agents.github.io',
  'AGENTROPOLIS-DESIGN-SYSTEM/js/loop-baseline.js',
];
const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.md': 'text/plain; charset=utf-8',
};

function findChrome() {
  const candidates = [
    process.env.CHROME_PATH,
    'google-chrome',
    'google-chrome-stable',
    'chromium',
    'chromium-browser',
  ].filter(Boolean);
  for (const candidate of candidates) {
    try {
      execFileSync(candidate, ['--version'], { stdio: 'ignore' });
      return candidate;
    } catch {
      // try the next candidate
    }
  }
  throw new Error('No system Chrome or Chromium binary found for the loop-baseline smoke test');
}

function startStatic() {
  const server = createServer((req, res) => {
    const url = new URL(req.url || '/', 'http://127.0.0.1');
    if (url.pathname === '/favicon.ico') {
      res.writeHead(204);
      res.end();
      return;
    }
    let rel = decodeURIComponent(url.pathname);
    if (rel.endsWith('/')) rel += 'index.html';
    const path = normalize(join(ROOT, rel));
    if (path !== ROOT && !path.startsWith(ROOT + sep)) {
      res.writeHead(403);
      res.end('forbidden');
      return;
    }
    try {
      const body = readFileSync(path);
      res.writeHead(200, { 'content-type': MIME[extname(path)] || 'application/octet-stream' });
      res.end(body);
    } catch {
      res.writeHead(404);
      res.end('missing');
    }
  });
  return new Promise((done) => {
    server.listen(0, '127.0.0.1', () => done(server));
  });
}

function sleep(ms) {
  return new Promise((done) => setTimeout(done, ms));
}

async function readDevtoolsPort(portFile) {
  const deadline = Date.now() + 15000;
  while (Date.now() < deadline) {
    if (existsSync(portFile)) {
      const port = readFileSync(portFile, 'utf8').split('\n')[0].trim();
      if (port) return port;
    }
    await sleep(50);
  }
  throw new Error(`Chrome did not write ${portFile}`);
}

async function main() {
  const chromeBin = findChrome();
  const server = await startStatic();
  const { port } = server.address();
  const pageUrl = `http://127.0.0.1:${port}/index.html`;
  const userData = mkdtempSync(join(tmpdir(), 'loop-baseline-smoke-'));
  const chrome = spawn(chromeBin, [
    '--headless=new',
    '--disable-gpu',
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--enable-unsafe-swiftshader',
    '--no-first-run',
    '--disable-extensions',
    '--disable-background-networking',
    '--disable-component-update',
    `--user-data-dir=${userData}`,
    '--remote-debugging-port=0',
    'about:blank',
  ], { stdio: 'ignore' });

  let browser;
  try {
    const dbgPort = await readDevtoolsPort(join(userData, 'DevToolsActivePort'));
    const version = await fetch(`http://127.0.0.1:${dbgPort}/json/version`).then((response) => response.json());
    browser = new WebSocket(version.webSocketDebuggerUrl);
    await new Promise((done, reject) => {
      browser.addEventListener('open', done, { once: true });
      browser.addEventListener('error', () => reject(new Error('DevTools websocket failed')), { once: true });
    });

    let nextId = 0;
    const pending = new Map();
    const requests = [];
    const responses = [];
    const consoleEvents = [];
    const exceptions = [];

    function send(method, params = {}, sessionId) {
      const id = ++nextId;
      const payload = { id, method, params };
      if (sessionId) payload.sessionId = sessionId;
      return new Promise((done, reject) => {
        pending.set(id, { done, reject });
        browser.send(JSON.stringify(payload));
      });
    }

    browser.addEventListener('message', (event) => {
      const message = JSON.parse(event.data);
      if (message.id && pending.has(message.id)) {
        const waiter = pending.get(message.id);
        pending.delete(message.id);
        if (message.error) waiter.reject(new Error(`${message.error.message || 'CDP error'}: ${JSON.stringify(message.error)}`));
        else waiter.done(message.result);
        return;
      }
      const params = message.params || {};
      if (message.method === 'Network.requestWillBeSent') requests.push(params.request.url);
      if (message.method === 'Network.responseReceived') {
        responses.push({ url: params.response.url, status: params.response.status });
      }
      if (message.method === 'Runtime.consoleAPICalled') {
        const text = (params.args || []).map((arg) => arg.value ?? arg.description ?? '').join(' ');
        consoleEvents.push({ type: params.type, text });
      }
      if (message.method === 'Runtime.exceptionThrown') {
        const details = params.exceptionDetails || {};
        exceptions.push(details.exception?.description || details.text || 'exception');
      }
      if (message.method === 'Log.entryAdded' && params.entry) {
        consoleEvents.push({ type: params.entry.level, text: params.entry.text || '' });
      }
    });

    const { targetId } = await send('Target.createTarget', { url: 'about:blank' });
    const { sessionId } = await send('Target.attachToTarget', { targetId, flatten: true });
    await send('Network.enable', {}, sessionId);
    await send('Runtime.enable', {}, sessionId);
    await send('Log.enable', {}, sessionId);
    await send('Page.enable', {}, sessionId);
    await send('Page.navigate', { url: pageUrl }, sessionId);

    let evaluated = null;
    const deadline = Date.now() + 15000;
    while (Date.now() < deadline) {
      const result = await send('Runtime.evaluate', {
        expression: `JSON.stringify({
          flag: window.__AGENTROPOLIS_LOOP_BASELINE__ === true,
          version: window.__AGENTROPOLIS_LOOP_BASELINE_VERSION__ || null,
          host: !!document.getElementById('agentropolis-loop-baseline')
        })`,
        returnByValue: true,
      }, sessionId);
      evaluated = JSON.parse(result.result.value);
      if (evaluated.flag && evaluated.host) break;
      await sleep(100);
    }
    // Deferred scripts and Chrome's favicon probe can log after the flag flips.
    await sleep(1000);

    const remoteHits = requests.filter((url) => REMOTE_MARKERS.some((marker) => url.includes(marker)));
    const localLoads = responses.filter((item) => item.url.startsWith('http://127.0.0.1:') && item.url.endsWith(LOCAL_SUFFIX));
    const consoleErrors = consoleEvents.filter((event) => event.type === 'error' && !/favicon\.ico/.test(event.text));

    console.log(`PAGE ${pageUrl}`);
    console.log('REQUESTS');
    for (const url of requests) console.log(`  ${url}`);
    console.log(`EVAL ${JSON.stringify(evaluated)}`);
    console.log(`LOCAL ${JSON.stringify(localLoads)}`);
    console.log(`REMOTE_HITS ${remoteHits.length}`);
    console.log(`CONSOLE_ERRORS ${consoleErrors.length}`);
    console.log(`EXCEPTIONS ${exceptions.length}`);
    for (const event of consoleErrors) console.log(`CONSOLE_ERROR ${event.text}`);
    for (const exception of exceptions) console.log(`EXCEPTION ${exception.split('\n')[0]}`);

    const failures = [];
    if (!evaluated?.flag || evaluated.version !== '1.0.0' || !evaluated.host) {
      failures.push(`local script did not execute: ${JSON.stringify(evaluated)}`);
    }
    if (localLoads.length === 0 || localLoads.some((item) => item.status !== 200)) {
      failures.push(`local script was not served with status 200: ${JSON.stringify(localLoads)}`);
    }
    if (remoteHits.length) failures.push(`remote loop-baseline request: ${remoteHits.join(', ')}`);
    if (consoleErrors.length) failures.push(`console errors: ${consoleErrors.map((event) => event.text).join(' | ')}`);
    if (exceptions.length) failures.push(`exceptions: ${exceptions.map((item) => item.split('\n')[0]).join(' | ')}`);
    if (failures.length) {
      throw new Error(failures.join('\n'));
    }
    console.log(`SMOKE_OK local=http://127.0.0.1:${port}${LOCAL_SUFFIX} status=200 remote_hits=0 console_errors=0`);
  } finally {
    if (browser) browser.close();
    chrome.kill('SIGKILL');
    server.close();
    rmSync(userData, { recursive: true, force: true });
  }
}

main().catch((error) => {
  console.error(error.message || error);
  process.exit(1);
});
