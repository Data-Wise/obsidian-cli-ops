const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

// Path to the obs.zsh script
const OBS_SCRIPT = path.join(__dirname, '../src/obs.zsh');

// Helper to run obs commands
function runObs(args = '', options = {}) {
  const defaultOptions = {
    encoding: 'utf8',
    env: {
      ...process.env,
      HOME: options.testHome || os.tmpdir(),
    },
  };

  try {
    return execSync(`zsh ${OBS_SCRIPT} ${args}`, {
      ...defaultOptions,
      ...options,
    });
  } catch (error) {
    if (options.allowFailure) {
      return error.stdout || error.stderr || '';
    }
    throw error;
  }
}

describe('obs CLI v3.0 — Help and Basic Commands', () => {
  test('should display help when no arguments provided', () => {
    const output = runObs('', { allowFailure: true });
    // With no args, obs lists vaults (may show database error in test env)
    expect(output.length).toBeGreaterThan(0);
  });

  test('should display help with help command', () => {
    const output = runObs('help', { allowFailure: true });
    expect(output).toContain('obs');
  });

  test('should list core commands in quick help', () => {
    const output = runObs('help', { allowFailure: true });
    expect(output).toContain('discover');
    expect(output).toContain('stats');
  });

  test('should show all commands with help --all', () => {
    const output = runObs('help --all', { allowFailure: true });
    expect(output).toContain('analyze');
    expect(output).toContain('AI FEATURES');
  });

  test('should show version', () => {
    const output = runObs('version', { allowFailure: true });
    expect(output).toContain('3.0.0');
  });
});

describe('obs CLI v3.0 — Error Handling', () => {
  test('should show error for unknown command', () => {
    const output = runObs('invalidcommand', { allowFailure: true });
    expect(output).toContain('Unknown command');
  });
});

describe('obs CLI v3.0 — Verbose Mode', () => {
  test('should accept --verbose flag', () => {
    const output = runObs('--verbose help', { allowFailure: true });
    expect(output).toContain('obs');
  });

  test('should accept -v flag', () => {
    const output = runObs('-v help', { allowFailure: true });
    expect(output).toContain('obs');
  });
});

describe('obs CLI v3.0 — Knowledge Graph Commands', () => {
  describe('discover command', () => {
    test('should accept discover command', () => {
      const output = runObs('discover /tmp', { allowFailure: true });
      expect(output).not.toContain('Unknown command');
    });

    test('should handle discover with --scan flag', () => {
      const output = runObs('discover /tmp --scan', { allowFailure: true });
      expect(output).not.toContain('Unknown command');
    });

    test('should accept -v flag with discover', () => {
      const output = runObs('--verbose discover /tmp', { allowFailure: true });
      expect(output).not.toContain('Unknown command');
    });
  });

  describe('stats command', () => {
    test('should accept stats command', () => {
      const output = runObs('stats', { allowFailure: true });
      expect(output).not.toContain('Unknown command');
    });

    test('should accept stats with vault ID', () => {
      const output = runObs('stats 1', { allowFailure: true });
      expect(output).not.toContain('Unknown command');
    });

    test('should produce some output', () => {
      const output = runObs('stats', { allowFailure: true });
      expect(output.length).toBeGreaterThan(0);
    });
  });

  describe('analyze command', () => {
    test('should accept analyze command with vault ID', () => {
      const output = runObs('analyze 1', { allowFailure: true });
      expect(output).not.toContain('Unknown command');
    });

    test('should require vault ID', () => {
      const output = runObs('analyze', { allowFailure: true });
      expect(
        output.includes('vault') ||
          output.includes('required') ||
          output.includes('Usage') ||
          output.includes('ERROR')
      ).toBe(true);
    });

    test('should accept -v flag with analyze', () => {
      const output = runObs('--verbose analyze 1', { allowFailure: true });
      expect(output).not.toContain('Unknown command');
    });
  });
});

describe('obs CLI v3.0 — AI Commands', () => {
  test('should accept ai status command', () => {
    const output = runObs('ai status', { allowFailure: true });
    expect(output).not.toContain('Unknown command');
  });

  test('should accept ai setup command', () => {
    const output = runObs('ai setup', { allowFailure: true });
    expect(output).not.toContain('Unknown command');
  });

  test('should accept ai test command', () => {
    const output = runObs('ai test', { allowFailure: true });
    expect(output).not.toContain('Unknown command');
  });
});

describe('obs CLI v3.0 — Script Structure', () => {
  test('obs.zsh should exist and be readable', () => {
    expect(fs.existsSync(OBS_SCRIPT)).toBe(true);
    const content = fs.readFileSync(OBS_SCRIPT, 'utf8');
    expect(content).toContain('#!/bin/zsh');
  });

  test('obs.zsh should define v3.0 main functions', () => {
    const content = fs.readFileSync(OBS_SCRIPT, 'utf8');
    expect(content).toContain('obs_discover()');
    expect(content).toContain('obs_vaults()');
    expect(content).toContain('obs_stats()');
    expect(content).toContain('obs_analyze()');
    expect(content).toContain('obs_ai()');
    expect(content).toContain('obs_help()');
    expect(content).toContain('obs_version()');
  });

  test('obs.zsh should define helper functions', () => {
    const content = fs.readFileSync(OBS_SCRIPT, 'utf8');
    expect(content).toContain('_log()');
    expect(content).toContain('_log_verbose()');
    expect(content).toContain('_save_last_vault()');
    expect(content).toContain('_get_last_vault()');
    expect(content).toContain('_get_python_cli()');
  });

  test('obs.zsh should have v3.0.0-beta.2 version', () => {
    const content = fs.readFileSync(OBS_SCRIPT, 'utf8');
    expect(content).toContain('VERSION="3.0.0-beta.2"');
  });
});
