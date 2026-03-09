const { spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

const CLI_PATH = path.resolve(__dirname, '../src/obs.zsh');
const TEMP_HOME = fs.mkdtempSync(path.join(os.tmpdir(), 'obs-test-'));

function stripAnsi(str) {
  return str.replace(
    // eslint-disable-next-line no-control-regex
    /[\u001b\u009b][[()#;?]*(?:[0-9]{1,4}(?:;[0-9]{0,4})*)?[0-9A-ORZcf-nqry=><]/g,
    ''
  );
}

function runCli(args, env = {}) {
  const result = spawnSync('zsh', [CLI_PATH, ...args], {
    env: { ...process.env, HOME: TEMP_HOME, ...env },
    encoding: 'utf-8',
  });
  return {
    ...result,
    stdout: stripAnsi(result.stdout || ''),
    stderr: stripAnsi(result.stderr || ''),
  };
}

beforeAll(() => {
  const configDir = path.join(TEMP_HOME, '.config/obs');
  fs.mkdirSync(configDir, { recursive: true });
});

afterAll(() => {
  fs.rmSync(TEMP_HOME, { recursive: true, force: true });
});

describe('Obsidian CLI Ops v3.0', () => {
  test('should display help', () => {
    const result = runCli(['help']);
    expect(result.status).toBe(0);
    expect(result.stdout).toContain('obs');
  });

  test('should fail on unknown command', () => {
    const result = runCli(['foobar']);
    expect(result.stdout).toContain('Unknown command');
  });

  test('should show version', () => {
    const result = runCli(['version']);
    expect(result.status).toBe(0);
    expect(result.stdout).toContain('3.2.0');
  });

  test('should accept discover command', () => {
    const result = runCli(['discover', '/tmp']);
    expect(result.stdout).not.toContain('Unknown command');
  });

  test('should accept stats command', () => {
    const result = runCli(['stats']);
    expect(result.stdout).not.toContain('Unknown command');
  });

  test('should accept ai status command', () => {
    const result = runCli(['ai', 'status']);
    expect(result.stdout).not.toContain('Unknown command');
  });
});
