/**
 * Argument pass-through regression tests for src/obs.zsh.
 *
 * The wrapper must hand every argument to obs_cli.py intact and in order,
 * so argparse (not the shell) decides what a flag or a positional is.
 * Before the fix, `obs scan` read the path from $1 and only looked for
 * --name in $2/$3, so `obs scan --name X "<path>"` and `--name=X` broke.
 *
 * OBS_PYTHON points at a stub that prints its argv one per line, so these
 * tests need no Python deps and no database.
 */
const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const OBS_SCRIPT = path.join(__dirname, '../src/obs.zsh');
const ZSH =
  ['/bin/zsh', '/usr/bin/zsh', '/opt/homebrew/bin/zsh'].find(fs.existsSync) ||
  'zsh';

let tmp;
let stub;

beforeAll(() => {
  tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'obs-argv-'));
  stub = path.join(tmp, 'python-stub');
  fs.writeFileSync(
    stub,
    '#!/bin/sh\nfor a in "$@"; do printf "%s\\n" "$a"; done\n'
  );
  fs.chmodSync(stub, 0o755);
});

afterAll(() => {
  fs.rmSync(tmp, { recursive: true, force: true });
});

// Returns the argv the wrapper passed to Python, minus the obs_cli.py path.
function argvFor(...args) {
  const env = { ...process.env, HOME: tmp, OBS_PYTHON: stub };
  delete env.XDG_DATA_HOME;
  const res = spawnSync(ZSH, [OBS_SCRIPT, ...args], {
    encoding: 'utf8',
    env,
    timeout: 10000,
  });
  // _log_verbose writes to stdout, so skip anything before the stub's output.
  const lines = res.stdout.split('\n').filter((l) => l !== '');
  const start = lines.findIndex((l) => /obs_cli\.py$/.test(l));
  expect(start).toBeGreaterThanOrEqual(0);
  return lines.slice(start + 1);
}

const VAULT_PATH =
  '/Users/me/Library/Mobile Documents/iCloud~md~obsidian/Documents/My Vault';

describe('obs scan argument pass-through', () => {
  test('path first, spaced --name value', () => {
    expect(argvFor('scan', VAULT_PATH, '--name', 'Eng Vault')).toEqual([
      'scan',
      VAULT_PATH,
      '--name',
      'Eng Vault',
    ]);
  });

  test('--name before the path', () => {
    expect(argvFor('scan', '--name', 'Eng Vault', VAULT_PATH)).toEqual([
      'scan',
      '--name',
      'Eng Vault',
      VAULT_PATH,
    ]);
  });

  test('--name=value form', () => {
    expect(argvFor('scan', '--name=Eng Vault', VAULT_PATH)).toEqual([
      'scan',
      '--name=Eng Vault',
      VAULT_PATH,
    ]);
  });

  test('flags are not matched inside a path or name', () => {
    const odd = '/tmp/notes --prune --analyze';
    expect(argvFor('scan', odd)).toEqual(['scan', odd]);
  });

  test('--verbose global flag is forwarded before the subcommand', () => {
    expect(argvFor('--verbose', 'scan', VAULT_PATH, '--prune')).toEqual([
      '--verbose',
      'scan',
      VAULT_PATH,
      '--prune',
    ]);
  });
});

describe('obs discover argument pass-through', () => {
  test('--scan before a spaced path', () => {
    expect(argvFor('discover', '--scan', VAULT_PATH)).toEqual([
      'discover',
      '--scan',
      VAULT_PATH,
    ]);
  });

  test('defaults to the current directory', () => {
    expect(argvFor('discover')).toEqual(['discover', '.']);
  });
});

describe('obs stats argument pass-through', () => {
  test('no args shows global stats', () => {
    expect(argvFor('stats')).toEqual(['stats']);
  });

  test('bare spaced vault name maps to --vault', () => {
    expect(argvFor('stats', 'Obsidian Vault')).toEqual([
      'stats',
      '--vault',
      'Obsidian Vault',
    ]);
  });

  test('--json before the vault is hoisted to a global flag', () => {
    expect(argvFor('stats', '--json', 'Obsidian Vault')).toEqual([
      '--json',
      'stats',
      '--vault',
      'Obsidian Vault',
    ]);
  });

  test('--json after the vault is kept, not dropped', () => {
    expect(argvFor('stats', 'Obsidian Vault', '--json')).toEqual([
      '--json',
      'stats',
      '--vault',
      'Obsidian Vault',
    ]);
  });

  test('explicit --vault value is passed through', () => {
    expect(argvFor('stats', '--vault', 'Obsidian Vault', '--json')).toEqual([
      '--json',
      'stats',
      '--vault',
      'Obsidian Vault',
    ]);
  });

  test('a trailing --vault with no value is passed through (no hang)', () => {
    expect(argvFor('stats', '--vault')).toEqual(['stats', '--vault']);
  });

  test('--json with no vault gives global JSON stats', () => {
    expect(argvFor('stats', '--json')).toEqual(['--json', 'stats']);
  });
});

describe('obs health argument pass-through', () => {
  test('--json before a spaced vault name', () => {
    expect(argvFor('health', '--json', 'Obsidian Vault')).toEqual([
      'health',
      '--json',
      'Obsidian Vault',
    ]);
  });
});

describe('obs vault argument pass-through', () => {
  test('delete dry-run with a spaced vault name', () => {
    expect(argvFor('vault', 'delete', 'Obsidian Vault')).toEqual([
      'vault',
      'delete',
      'Obsidian Vault',
    ]);
  });

  test('delete --force with a spaced vault name', () => {
    expect(argvFor('vault', 'delete', 'Obsidian Vault', '--force')).toEqual([
      'vault',
      'delete',
      'Obsidian Vault',
      '--force',
    ]);
  });
});

describe('OBS_PYTHON resolution', () => {
  test('an interpreter path containing spaces is honored', () => {
    const dir = path.join(tmp, 'dir with spaces');
    fs.mkdirSync(dir, { recursive: true });
    const spaced = path.join(dir, 'python stub');
    fs.copyFileSync(stub, spaced);
    fs.chmodSync(spaced, 0o755);
    const env = { ...process.env, HOME: tmp, OBS_PYTHON: spaced };
    delete env.XDG_DATA_HOME;
    const res = spawnSync(ZSH, [OBS_SCRIPT, 'vault', 'info', 'My Vault'], {
      encoding: 'utf8',
      env,
    });
    const lines = res.stdout.split('\n').filter((l) => l !== '');
    expect(lines.slice(-4)).toEqual([
      expect.stringMatching(/obs_cli\.py$/),
      'vault',
      'info',
      'My Vault',
    ]);
  });

  test('a non-executable OBS_PYTHON warns before falling back', () => {
    const env = {
      ...process.env,
      HOME: tmp,
      OBS_PYTHON: path.join(tmp, 'no such python'),
    };
    delete env.XDG_DATA_HOME;
    const res = spawnSync(ZSH, [OBS_SCRIPT, 'version'], {
      encoding: 'utf8',
      env,
    });
    expect(res.stderr).toContain('OBS_PYTHON');
    expect(res.stderr).toContain('not executable');
  });
});
