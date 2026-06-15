// End-to-end + dogfood tests for the v3.2.1 dependency-bootstrapping fix.
//
// Covers the three new artifacts:
//   - requirements.lock         (pinned single source of truth)
//   - src/obs.zsh               (_obs_resolve_python 4-tier resolution)
//   - install.sh                (isolated venv bootstrap + lock-hash sentinel)
//
// Most tests are deterministic and offline: they stub the venv interpreter and
// the sentinel so the resolver/installer logic runs without touching PyPI.
// The single genuinely network-dependent test (a real `pip install`) is gated
// behind OBS_E2E=1 or CI — the ci.yml smoke-test job covers it in CI too.

const { execFileSync, spawnSync } = require('child_process');
const crypto = require('crypto');
const fs = require('fs');
const os = require('os');
const path = require('path');

const REPO_ROOT = path.join(__dirname, '..');
const OBS_SCRIPT = path.join(REPO_ROOT, 'src/obs.zsh');
const INSTALL_SCRIPT = path.join(REPO_ROOT, 'install.sh');
const LOCKFILE = path.join(REPO_ROOT, 'requirements.lock');
const PYPROJECT = path.join(REPO_ROOT, 'pyproject.toml');
const OBS_CLI = path.join(REPO_ROOT, 'src/python/obs_cli.py');
const CI_WORKFLOW = path.join(REPO_ROOT, '.github/workflows/ci.yml');

// The core deps declared in pyproject [project.dependencies]. mcp (+ its full
// transitive tree) was added in v3.3.0 for mcp_server.py, so the lock now
// carries the transitive closure too. The contract is therefore "every core
// dep present, no AI/optional extras" — not "exactly these names".
const CORE_DEPS = [
  'python-frontmatter',
  'PyYAML',
  'networkx',
  'rich',
  'requests',
  'click',
  'mcp',
];

// AI/optional extras that must never leak into the base lock.
const FORBIDDEN_EXTRAS = [
  'numpy',
  'anthropic',
  'google-genai',
  'scikit-learn',
  'markdown',
  'mistune',
  'tqdm',
  'typer',
];

// Run the real network-provisioning test only where a network + clean state are
// expected (CI, or an explicit opt-in). Keeps `npx jest` fast and offline-safe.
const E2E_ENABLED = process.env.OBS_E2E === '1' || process.env.CI === 'true';

// ---- helpers ---------------------------------------------------------------

// Resolve an ABSOLUTE zsh path once (via a normal env), so tests that override
// PATH inside the child still launch zsh — the PATH override must only affect
// resolution *inside* the sourced script, not the locating of zsh itself.
function whichBin(name) {
  const r = spawnSync('sh', ['-c', `command -v ${name}`], { encoding: 'utf8' });
  return (r.stdout || '').trim();
}
const ZSH_BIN = whichBin('zsh') || 'zsh';

function mkdtemp() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'obs-deptest-'));
}

// A minimal executable that stands in for a python interpreter. The resolver
// only checks that it is executable (`-x`); it never runs it for tier selection.
function writeStubExecutable(filePath, body = '#!/bin/sh\nexit 0\n') {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, body);
  fs.chmodSync(filePath, 0o755);
}

function sha256OfFile(filePath) {
  return crypto
    .createHash('sha256')
    .update(fs.readFileSync(filePath))
    .digest('hex');
}

// Child env with the test runner's own resolution-affecting vars stripped, so a
// developer's exported OBS_PYTHON / XDG_DATA_HOME can't leak into the test.
function cleanEnv(overrides = {}) {
  const env = { ...process.env };
  delete env.OBS_PYTHON;
  delete env.XDG_DATA_HOME;
  return { ...env, ...overrides };
}

// Source the REAL obs.zsh under a controlled env and report what OBS_PYTHON
// resolved to (stdout) plus any warnings (stderr). Sourcing via `zsh -c` does
// not trip the file's bottom execution guard, so the dispatcher stays quiet.
function resolvePython({ home, obsPython, xdg, pathValue, pathPrepend } = {}) {
  const overrides = {};
  if (home !== undefined) overrides.HOME = home;
  if (obsPython !== undefined) overrides.OBS_PYTHON = obsPython;
  if (xdg !== undefined) overrides.XDG_DATA_HOME = xdg;
  const env = cleanEnv(overrides);
  if (pathValue !== undefined) env.PATH = pathValue;
  else if (pathPrepend) env.PATH = `${pathPrepend}:${env.PATH}`;

  const res = spawnSync(
    ZSH_BIN,
    ['-c', `source "${OBS_SCRIPT}" >/dev/null; print -r -- "$OBS_PYTHON"`],
    { env, encoding: 'utf8' }
  );
  return { resolved: (res.stdout || '').trim(), stderr: res.stderr || '' };
}

// ---- requirements.lock contract -------------------------------------------

describe('requirements.lock — pinned dependency contract', () => {
  const depLines = fs
    .readFileSync(LOCKFILE, 'utf8')
    .split('\n')
    .map((l) => l.trim())
    .filter((l) => l && !l.startsWith('#'));

  test('lockfile exists', () => {
    expect(fs.existsSync(LOCKFILE)).toBe(true);
  });

  test('every dependency is exactly pinned with ==', () => {
    expect(depLines.length).toBeGreaterThan(0);
    for (const line of depLines) {
      expect(line).toMatch(/^[A-Za-z0-9_.-]+==[0-9][0-9A-Za-z.+-]*$/);
    }
  });

  test('includes every core dep and no AI/optional extras', () => {
    const names = depLines.map((l) => l.split('==')[0].toLowerCase());
    for (const core of CORE_DEPS) {
      expect(names).toContain(core.toLowerCase());
    }
    for (const extra of FORBIDDEN_EXTRAS) {
      expect(names).not.toContain(extra.toLowerCase());
    }
  });

  test('lock matches pyproject [project.dependencies] (no drift)', () => {
    const toml = fs.readFileSync(PYPROJECT, 'utf8');
    const block = toml.match(/^dependencies = \[([\s\S]*?)\]/m);
    expect(block).not.toBeNull();
    const pyNames = [...block[1].matchAll(/"([A-Za-z0-9_.-]+)\s*[><=!~]/g)].map(
      (m) => m[1]
    );
    const norm = (s) => s.toLowerCase();
    expect(pyNames.map(norm).sort()).toEqual(CORE_DEPS.map(norm).sort());
  });

  test('has no duplicate package names', () => {
    const names = depLines.map((l) => l.split('==')[0]);
    expect(new Set(names).size).toBe(names.length);
  });

  test('every pin satisfies its pyproject floor (pin >= >=floor)', () => {
    const toml = fs.readFileSync(PYPROJECT, 'utf8');
    const block = toml.match(/^dependencies = \[([\s\S]*?)\]/m)[1];
    const floors = {};
    for (const m of block.matchAll(
      /"([A-Za-z0-9_.-]+)\s*>=\s*([0-9][0-9A-Za-z.+-]*)"/g
    )) {
      floors[m[1].toLowerCase()] = m[2];
    }
    const pins = {};
    for (const line of depLines) {
      const [n, v] = line.split('==');
      pins[n.toLowerCase()] = v;
    }
    // Simple numeric-tuple compare (sufficient for the plain X.Y.Z pins here).
    const toTuple = (v) => v.split(/[.+-]/).map((p) => parseInt(p, 10) || 0);
    const gte = (a, b) => {
      const ta = toTuple(a);
      const tb = toTuple(b);
      for (let i = 0; i < Math.max(ta.length, tb.length); i++) {
        const x = ta[i] || 0;
        const y = tb[i] || 0;
        if (x !== y) return x > y;
      }
      return true; // equal satisfies >=
    };
    expect(Object.keys(floors).length).toBe(CORE_DEPS.length);
    for (const [name, floor] of Object.entries(floors)) {
      expect(pins[name]).toBeDefined();
      expect(gte(pins[name], floor)).toBe(true);
    }
  });
});

// ---- obs.zsh resolver: static structure -----------------------------------

describe('obs.zsh — python resolution structure', () => {
  const content = fs.readFileSync(OBS_SCRIPT, 'utf8');

  test('defines the _obs_resolve_python resolver', () => {
    expect(content).toMatch(/_obs_resolve_python\(\)/);
  });

  test('removed the v3.2.0 silent bare-python fallback', () => {
    expect(content).not.toContain(
      'OBS_PYTHON="${OBS_PYTHON:-$(command -v python3)}"'
    );
  });

  test('references both isolated venv locations', () => {
    expect(content).toContain('.local/share/obs/venv');
    expect(content).toContain('libexec/venv');
  });

  test('warns when falling back to ambient python', () => {
    expect(content).toMatch(/WARN/);
  });

  test('OBS_PYTHON is assigned from the resolver', () => {
    expect(content).toMatch(/OBS_PYTHON="\$\(_obs_resolve_python\)"/);
  });
});

// ---- obs.zsh resolver: behavior (dogfood real zsh) ------------------------

describe('obs.zsh — _obs_resolve_python tier selection', () => {
  test('tier 1: honors an explicit, existing $OBS_PYTHON override', () => {
    const stubDir = mkdtemp();
    const stub = path.join(stubDir, 'python');
    writeStubExecutable(stub);
    const { resolved } = resolvePython({ home: mkdtemp(), obsPython: stub });
    expect(resolved).toBe(stub);
  });

  test('tier 1: an override with trailing args validates only the interpreter path', () => {
    const stubDir = mkdtemp();
    const stub = path.join(stubDir, 'python');
    writeStubExecutable(stub);
    // e.g. OBS_PYTHON="/path/to/python -E -X utf8" — the `-x` check uses
    // ${OBS_PYTHON%% *}, but the full string is what gets used to invoke.
    const override = `${stub} -E -X utf8`;
    const { resolved } = resolvePython({
      home: mkdtemp(),
      obsPython: override,
    });
    expect(resolved).toBe(override);
  });

  test('tier 1: a non-existent $OBS_PYTHON override is ignored (falls through)', () => {
    const home = mkdtemp();
    const userVenv = path.join(home, '.local/share/obs/venv/bin/python');
    writeStubExecutable(userVenv);
    const { resolved } = resolvePython({ home, obsPython: '/no/such/python' });
    expect(resolved).toBe(userVenv);
  });

  test('tier 2: resolves the install.sh user venv', () => {
    const home = mkdtemp();
    const userVenv = path.join(home, '.local/share/obs/venv/bin/python');
    writeStubExecutable(userVenv);
    const { resolved } = resolvePython({ home });
    expect(resolved).toBe(userVenv);
  });

  test('tier 3: resolves a Homebrew formula venv via brew --prefix (no user venv)', () => {
    const brewBin = mkdtemp();
    const prefix = mkdtemp();
    const formulaPython = path.join(prefix, 'libexec/venv/bin/python');
    writeStubExecutable(formulaPython);
    // Fake brew that only answers `brew --prefix obsidian-cli-ops`.
    const brew = path.join(brewBin, 'brew');
    writeStubExecutable(
      brew,
      `#!/bin/sh\nif [ "$1" = "--prefix" ]; then echo "${prefix}"; fi\n`
    );
    // Empty HOME => no user venv, so the resolver probes brew.
    const { resolved } = resolvePython({
      home: mkdtemp(),
      pathPrepend: brewBin,
    });
    expect(resolved).toBe(formulaPython);
  });

  test('user venv (tier 2) wins over a Homebrew venv (tier 3) when both exist', () => {
    const home = mkdtemp();
    const userVenv = path.join(home, '.local/share/obs/venv/bin/python');
    writeStubExecutable(userVenv);
    // Stage a fake brew + formula venv too; the user venv must win WITHOUT the
    // resolver ever invoking `brew --prefix` (the documented tier ordering).
    const brewBin = mkdtemp();
    const prefix = mkdtemp();
    writeStubExecutable(path.join(prefix, 'libexec/venv/bin/python'));
    const brew = path.join(brewBin, 'brew');
    writeStubExecutable(
      brew,
      `#!/bin/sh\nif [ "$1" = "--prefix" ]; then echo "${prefix}"; fi\n`
    );
    const { resolved } = resolvePython({ home, pathPrepend: brewBin });
    expect(resolved).toBe(userVenv);
  });

  test('tier 2: honors XDG_DATA_HOME for the user venv location', () => {
    const xdg = mkdtemp();
    const userVenv = path.join(xdg, 'obs/venv/bin/python');
    writeStubExecutable(userVenv);
    const { resolved } = resolvePython({ home: mkdtemp(), xdg });
    expect(resolved).toBe(userVenv);
  });

  test('tier 4: falls back to ambient python3 with a loud warning', () => {
    const binDir = mkdtemp();
    const ambient = path.join(binDir, 'python3');
    writeStubExecutable(ambient);
    // PATH has python3 but no brew and no venv => ambient + warn.
    const { resolved, stderr } = resolvePython({
      home: mkdtemp(),
      pathValue: binDir,
    });
    expect(resolved).toBe(ambient);
    expect(stderr).toMatch(/WARN/);
    expect(stderr).toMatch(/dependencies may be missing/i);
  });

  test('errors (no resolution) when no python3 is available at all', () => {
    const emptyBin = mkdtemp();
    const { resolved, stderr } = resolvePython({
      home: mkdtemp(),
      pathValue: emptyBin,
    });
    expect(resolved).toBe('');
    expect(stderr).toMatch(/no python3 interpreter found/i);
  });
});

// ---- install.sh: deterministic (offline) ----------------------------------

describe('install.sh — launcher symlink + idempotency (offline)', () => {
  // Pre-stage a stub venv + matching sentinel so install.sh takes the
  // "already provisioned" branch and never reaches pip (no network).
  function stagedInstall() {
    const home = mkdtemp();
    const venvPy = path.join(home, '.local/share/obs/venv/bin/python');
    writeStubExecutable(venvPy);
    fs.writeFileSync(
      path.join(home, '.local/share/obs/.deps.sentinel'),
      sha256OfFile(LOCKFILE)
    );
    const out = execFileSync('bash', [INSTALL_SCRIPT], {
      env: cleanEnv({ HOME: home }),
      encoding: 'utf8',
    });
    return { home, out };
  }

  test('symlinks obs.zsh into ~/.config/zsh/functions', () => {
    const { home } = stagedInstall();
    const link = path.join(home, '.config/zsh/functions/obs.zsh');
    expect(fs.existsSync(link)).toBe(true);
    expect(fs.realpathSync(link)).toBe(fs.realpathSync(OBS_SCRIPT));
  });

  test('is idempotent when the lock is unchanged (no re-provision)', () => {
    const { out } = stagedInstall();
    expect(out).toMatch(/already provisioned/);
  });

  test('fails clearly when requirements.lock is missing', () => {
    // Run a copy of install.sh from a project dir that has no lockfile, so the
    // PROJECT_DIR-relative lookup misses and the script must error out.
    const projectDir = mkdtemp();
    const installCopy = path.join(projectDir, 'install.sh');
    fs.copyFileSync(INSTALL_SCRIPT, installCopy);
    fs.chmodSync(installCopy, 0o755);

    let err;
    try {
      execFileSync('bash', [installCopy], {
        env: cleanEnv({ HOME: mkdtemp() }),
        encoding: 'utf8',
        stdio: 'pipe',
      });
    } catch (e) {
      err = e;
    }
    expect(err).toBeDefined();
    expect(err.status).not.toBe(0);
    expect(`${err.stderr || ''}${err.stdout || ''}`).toMatch(
      /requirements\.lock not found/i
    );
  });
});

// ---- ci.yml: the clean-install safety net ---------------------------------

describe('ci.yml — clean-install smoke-test job', () => {
  const ci = fs.readFileSync(CI_WORKFLOW, 'utf8');

  test('defines a dedicated smoke-test job', () => {
    expect(ci).toMatch(/^\s{2}smoke-test:/m);
  });

  test('runs install.sh with no manual pip', () => {
    expect(ci).toContain('./install.sh');
    // The smoke job must not lean on the repo requirements.txt to provision.
    const smoke = ci.slice(ci.indexOf('smoke-test:'));
    expect(smoke).not.toContain('pip install -r');
  });

  test('asserts the isolated venv imports all 6 core deps', () => {
    expect(ci).toContain(
      'import frontmatter, yaml, networkx, rich, requests, click'
    );
    expect(ci).toContain('.local/share/obs/venv');
  });

  test('asserts the CLI --help exits 0 through the resolved interpreter', () => {
    expect(ci).toContain('obs_cli.py --help');
    expect(ci).toContain('OBS_PYTHON');
  });
});

// ---- install.sh: real provisioning (network, gated) -----------------------

const describeE2E = E2E_ENABLED ? describe : describe.skip;

describeE2E(
  'install.sh — clean install provisions an isolated venv (network)',
  () => {
    test('fresh install yields a venv with all 6 core deps, and obs runs', () => {
      const home = mkdtemp();
      execFileSync('bash', [INSTALL_SCRIPT], {
        env: cleanEnv({ HOME: home }),
        encoding: 'utf8',
        stdio: 'pipe',
      });

      const venvPy = path.join(home, '.local/share/obs/venv/bin/python');
      expect(fs.existsSync(venvPy)).toBe(true);

      // The exact v3.2.0 regression guard: these imports must succeed.
      execFileSync(
        venvPy,
        ['-c', 'import frontmatter, yaml, networkx, rich, requests, click'],
        {
          stdio: 'pipe',
        }
      );

      // Sentinel records the lock hash so re-runs are no-ops.
      const sentinel = fs
        .readFileSync(
          path.join(home, '.local/share/obs/.deps.sentinel'),
          'utf8'
        )
        .trim();
      expect(sentinel).toBe(sha256OfFile(LOCKFILE));

      // Dogfood: the launcher resolves to this venv, and the CLI --help exits 0
      // through it (importing obs_cli.py exercises rich/click).
      const { resolved } = resolvePython({ home });
      expect(resolved).toBe(venvPy);
      execFileSync(venvPy, [OBS_CLI, '--help'], { stdio: 'pipe' });
    }, 240000);

    test('re-provisions when a stale sentinel does not match the lock', () => {
      const home = mkdtemp();
      // Pre-stage a stale stub venv + a deliberately wrong sentinel.
      const venvPy = path.join(home, '.local/share/obs/venv/bin/python');
      writeStubExecutable(venvPy, '#!/bin/sh\necho stale\n');
      fs.writeFileSync(
        path.join(home, '.local/share/obs/.deps.sentinel'),
        'deadbeef-not-the-real-hash'
      );

      const out = execFileSync('bash', [INSTALL_SCRIPT], {
        env: cleanEnv({ HOME: home }),
        encoding: 'utf8',
        stdio: 'pipe',
      });
      expect(out).toMatch(/Provisioning isolated obs environment/);

      // The stub was replaced by a real venv with the deps installed...
      execFileSync(venvPy, ['-c', 'import rich, click'], { stdio: 'pipe' });
      // ...and the sentinel now records the real lock hash.
      const sentinel = fs
        .readFileSync(
          path.join(home, '.local/share/obs/.deps.sentinel'),
          'utf8'
        )
        .trim();
      expect(sentinel).toBe(sha256OfFile(LOCKFILE));
    }, 240000);
  }
);
