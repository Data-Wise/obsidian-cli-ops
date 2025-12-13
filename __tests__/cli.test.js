const { spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

const CLI_PATH = path.resolve(__dirname, '../src/obs.zsh');
const TEMP_HOME = fs.mkdtempSync(path.join(os.tmpdir(), 'obs-test-'));

function stripAnsi(str) {
  return str.replace(/[\u001b\u009b][[()#;?]*(?:[0-9]{1,4}(?:;[0-9]{0,4})*)?[0-9A-ORZcf-nqry=><]/g, '');
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
  fs.writeFileSync(path.join(configDir, 'config'), 'OBS_ROOT="/tmp/mock_root"\nVAULTS=("VaultA")');
  fs.writeFileSync(path.join(configDir, 'project_map.json'), '{}');
});

afterAll(() => {
  fs.rmSync(TEMP_HOME, { recursive: true, force: true });
});

describe('Obsidian CLI Ops', () => {
  test('should display help', () => {
    const result = runCli(['help']);
    expect(result.status).toBe(0);
    expect(result.stdout).toContain('Usage: obs');
    expect(result.stdout).toContain('Obsidian CLI Ops');
  });

  test('should fail on unknown command', () => {
    const result = runCli(['foobar']);
    expect(result.stdout).toContain('[ERROR] Unknown command');
  });

  test('r-dev link should fail if not in R project', () => {
    const result = runCli(['r-dev', 'link', 'Some/Path']);
    expect(result.stdout).toContain('[ERROR] Not inside an R Project');
  });
});
