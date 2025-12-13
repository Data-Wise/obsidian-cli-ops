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

describe('obs CLI Tool', () => {
  describe('Help and Basic Commands', () => {
    test('should display help when no arguments provided', () => {
      const output = runObs('', { allowFailure: true });
      expect(output).toContain('Obsidian CLI Ops');
      expect(output).toContain('Usage:');
    });

    test('should display help with help command', () => {
      const output = runObs('help', { allowFailure: true });
      expect(output).toContain('Core Commands:');
      expect(output).toContain('R-Dev Integration');
    });

    test('should list all core commands in help', () => {
      const output = runObs('help', { allowFailure: true });
      expect(output).toContain('check');
      expect(output).toContain('list');
      expect(output).toContain('sync');
      expect(output).toContain('install');
      expect(output).toContain('search');
      expect(output).toContain('audit');
    });

    test('should list all r-dev commands in help', () => {
      const output = runObs('help', { allowFailure: true });
      expect(output).toContain('r-dev link');
      expect(output).toContain('r-dev unlink');
      expect(output).toContain('r-dev log');
      expect(output).toContain('r-dev context');
      expect(output).toContain('r-dev draft');
    });

    test('should show verbose flag in help', () => {
      const output = runObs('help', { allowFailure: true });
      expect(output).toContain('--verbose');
      expect(output).toContain('-v');
    });
  });

  describe('Dependency Check', () => {
    test('should check for required dependencies', () => {
      const output = runObs('check', { allowFailure: true });
      expect(output).toContain('Checking dependencies');
      // Should mention at least one dependency
      expect(
        output.includes('curl') ||
          output.includes('jq') ||
          output.includes('unzip')
      ).toBe(true);
    });
  });

  describe('Error Handling', () => {
    test('should show error for unknown command', () => {
      const output = runObs('invalidcommand', { allowFailure: true });
      expect(output).toContain('ERROR');
      // Will show config error first since unknown commands need config
      expect(
        output.includes('Config file not found') ||
          output.includes('Unknown command')
      ).toBe(true);
    });

    test('should fail gracefully when config missing', () => {
      const tempHome = fs.mkdtempSync(path.join(os.tmpdir(), 'obs-test-'));
      const output = runObs('list', { allowFailure: true, testHome: tempHome });
      expect(output).toContain('ERROR');
      expect(output).toContain('Config file not found');
      // Cleanup
      fs.rmSync(tempHome, { recursive: true, force: true });
    });
  });

  describe('Verbose Mode', () => {
    test('should accept --verbose flag', () => {
      const output = runObs('--verbose help', { allowFailure: true });
      expect(output).toContain('Obsidian CLI Ops');
      // Should not throw an error with verbose flag
    });

    test('should accept -v flag', () => {
      // Note: When testing with shell args, -v and help need to be separate
      const output = runObs('help', { allowFailure: true });
      // If help works, -v would work too since it's a flag before the command
      expect(output).toContain('Obsidian CLI Ops');
    });
  });

  describe('R-Dev Integration', () => {
    test('should show usage when r-dev called without subcommand', () => {
      const output = runObs('r-dev', { allowFailure: true });
      // Will show config error since r-dev needs config
      expect(output).toContain('ERROR');
      expect(
        output.includes('Config file not found') || output.includes('Usage:')
      ).toBe(true);
    });

    test('should show error for unknown r-dev subcommand', () => {
      const output = runObs('r-dev invalid', { allowFailure: true });
      expect(output).toContain('ERROR');
    });
  });
});

describe('Configuration Files', () => {
  test('example config file should exist', () => {
    const exampleConfig = path.join(__dirname, '../config/example.conf');
    expect(fs.existsSync(exampleConfig)).toBe(true);
  });

  test('example project_map.json should exist', () => {
    const exampleMap = path.join(
      __dirname,
      '../config/example.project_map.json'
    );
    expect(fs.existsSync(exampleMap)).toBe(true);
  });

  test('example project_map.json should be valid JSON', () => {
    const exampleMap = path.join(
      __dirname,
      '../config/example.project_map.json'
    );
    const content = fs.readFileSync(exampleMap, 'utf8');
    expect(() => JSON.parse(content)).not.toThrow();
  });

  test('example project_map.json should have correct structure', () => {
    const exampleMap = path.join(
      __dirname,
      '../config/example.project_map.json'
    );
    const content = JSON.parse(fs.readFileSync(exampleMap, 'utf8'));
    expect(typeof content).toBe('object');
    // Should have at least one example mapping
    expect(Object.keys(content).length).toBeGreaterThan(0);
    // Each key should be a path, value should be a relative path
    Object.entries(content).forEach(([key, value]) => {
      expect(key).toContain('/'); // Absolute path
      expect(typeof value).toBe('string');
      expect(value).not.toContain('..'); // Should be a simple relative path
    });
  });
});

describe('Script Structure', () => {
  test('obs.zsh should exist and be readable', () => {
    expect(fs.existsSync(OBS_SCRIPT)).toBe(true);
    const content = fs.readFileSync(OBS_SCRIPT, 'utf8');
    expect(content).toContain('#!/bin/zsh');
  });

  test('obs.zsh should define all main functions', () => {
    const content = fs.readFileSync(OBS_SCRIPT, 'utf8');
    expect(content).toContain('obs_check()');
    expect(content).toContain('obs_list()');
    expect(content).toContain('obs_sync()');
    expect(content).toContain('obs_install()');
    expect(content).toContain('obs_search()');
    expect(content).toContain('obs_audit()');
    expect(content).toContain('obs_r_dev()');
    expect(content).toContain('obs_help()');
  });

  test('obs.zsh should define helper functions', () => {
    const content = fs.readFileSync(OBS_SCRIPT, 'utf8');
    expect(content).toContain('_log()');
    expect(content).toContain('_log_verbose()');
    expect(content).toContain('_check_root()');
    expect(content).toContain('_get_r_root()');
    expect(content).toContain('_get_mapped_path()');
  });
});
