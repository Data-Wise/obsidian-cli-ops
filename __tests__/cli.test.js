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
    expect(result.stdout).toContain('3.2.2');
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

// Regression guard: --json / --verbose are GLOBAL argparse flags on obs_cli.py,
// recognized only BEFORE the subcommand. The zsh handlers used to append them
// AFTER the subcommand, so `obs ai quality <v> --json` died with
// "unrecognized arguments: --json". The handlers now route global flags ahead of
// the "ai" token. We assert argparse never rejects them. (When the resolved
// interpreter lacks deps the core can't run at all, so this is vacuously true
// rather than flaky — it only fails if the flag is genuinely mis-positioned.)
describe('global flag routing for v3.2.0 ai commands', () => {
  for (const sub of ['merge-suggest', 'tag-suggest', 'quality']) {
    test(`obs ai ${sub} <vault> --json is not rejected by argparse`, () => {
      const { stdout, stderr } = runCli(['ai', sub, 'NOVAULT', '--json']);
      expect(stdout + stderr).not.toMatch(/unrecognized arguments/i);
    });
  }

  test('obs --verbose ai quality <vault> is not rejected by argparse', () => {
    const { stdout, stderr } = runCli([
      '--verbose',
      'ai',
      'quality',
      'NOVAULT',
    ]);
    expect(stdout + stderr).not.toMatch(/unrecognized arguments/i);
  });
});
