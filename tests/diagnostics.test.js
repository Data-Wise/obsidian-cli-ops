const { spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

const CLI_PATH = path.resolve(__dirname, '../src/obs.zsh');
const TEMP_HOME = fs.mkdtempSync(path.join(os.tmpdir(), 'obs-test-diag-'));

function stripAnsi(str) {
  return str.replace(
    // eslint-disable-next-line no-control-regex
    /[\u001b\u009b][[()#;?]*(?:[0-9]{1,4}(?:;[0-9]{0,4})*)?[0-9A-ORZcf-nqry=><]/g,
    ''
  );
}

function runCli(args, env = {}) {
  const envCopy = { ...process.env };
  delete envCopy.VERBOSE;
  
  const result = spawnSync('zsh', ['-f', CLI_PATH, ...args], {
    env: { 
      ...envCopy, 
      HOME: TEMP_HOME,
      // Force test mode to use a dedicated test db path
      OBS_DB_PATH: path.join(TEMP_HOME, '.config/obs/vaults.db'),
      ...env 
    },
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

  // Create mock Claude Desktop directories & config files to pass doctor check
  const claudeDir1 = path.join(TEMP_HOME, 'Library/Application Support/Claude');
  const claudeDir2 = path.join(TEMP_HOME, 'Library/Application Support/Claude-3p');
  fs.mkdirSync(claudeDir1, { recursive: true });
  fs.mkdirSync(claudeDir2, { recursive: true });
  fs.writeFileSync(path.join(claudeDir1, 'claude_desktop_config.json'), JSON.stringify({ mcpServers: {} }));
  fs.writeFileSync(path.join(claudeDir2, 'claude_desktop_config.json'), JSON.stringify({ mcpServers: {} }));
});

afterAll(() => {
  fs.rmSync(TEMP_HOME, { recursive: true, force: true });
});

describe('Obsidian CLI Ops E2E - Diagnostics, Nesting Guard, and Config Helper', () => {
  let tempVaultDir1;
  let tempVaultDir2;

  beforeEach(() => {
    tempVaultDir1 = fs.mkdtempSync(path.join(os.tmpdir(), 'obs-vault-1-'));
    fs.mkdirSync(path.join(tempVaultDir1, '.obsidian'), { recursive: true });
    
    tempVaultDir2 = path.join(tempVaultDir1, 'nested-vault');
    fs.mkdirSync(path.join(tempVaultDir2, '.obsidian'), { recursive: true });
  });

  afterEach(() => {
    fs.rmSync(tempVaultDir1, { recursive: true, force: true });
  });

  test('should register and scan a vault successfully', () => {
    const result = runCli(['scan', tempVaultDir1]);
    expect(result.stdout).toContain('Scanned:');
  });

  test('should reject registering a nested/overlapping vault path due to nesting guard', () => {
    // Register the first vault
    const res1 = runCli(['scan', tempVaultDir1]);
    expect(res1.stdout).toContain('Scanned:');

    // Attempt to register a nested vault inside it
    const res2 = runCli(['scan', tempVaultDir2]);
    expect(res2.stdout + res2.stderr).toContain('nesting');
  });

  test('should run doctor successfully', () => {
    const result = runCli(['doctor', '--layer', 'python', '--layer', 'database']);
    expect(result.status).toBe(0);
    expect(result.stdout).toContain('PYTHON');
    expect(result.stdout).toContain('DATABASE');
  });
});
