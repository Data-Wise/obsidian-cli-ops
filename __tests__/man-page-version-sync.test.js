// Anti-drift guard for the obs man page.
//
// The man page's .TH version field must track the package version, so a
// release bump can't silently leave man/man1/obs.1 stale. Models flow-cli's
// tests/test-manpage-version-sync.zsh: parser self-tests prove the guard
// catches drift, then the real assertion checks the live page.

const fs = require('fs');
const path = require('path');

const REPO_ROOT = path.resolve(__dirname, '..');
const MAN_PAGE = path.join(REPO_ROOT, 'man/man1/obs.1');
const PKG = require('../package.json');

// Parse a troff `.TH` line's source field. For
//   .TH OBS 1 "June 2026" "obsidian-cli-ops 3.2.1" "User Commands"
// the 2nd quoted field is "obsidian-cli-ops 3.2.1" → { product, version }.
// Returns null if no parseable .TH line is present.
function parseTh(contents) {
  const line = contents.split('\n').find((l) => l.startsWith('.TH'));
  if (!line) return null;
  const quoted = line.match(/"([^"]*)"/g);
  if (!quoted || quoted.length < 2) return null;
  const source = quoted[1].replace(/"/g, '').trim();
  const idx = source.lastIndexOf(' ');
  if (idx === -1) return null;
  return {
    product: source.slice(0, idx).trim(),
    version: source.slice(idx + 1).trim(),
  };
}

describe('man page version sync (obs.1)', () => {
  test('the man page is present', () => {
    expect(fs.existsSync(MAN_PAGE)).toBe(true);
  });

  // --- parser self-tests: prove the guard is not vacuous ---
  test('parser extracts product and version from a .TH line', () => {
    const th = parseTh('.TH OBS 1 "June 2026" "obsidian-cli-ops 9.9.9" "User Commands"\n');
    expect(th).toEqual({ product: 'obsidian-cli-ops', version: '9.9.9' });
  });

  test('parser detects a deliberately mismatched version', () => {
    const th = parseTh('.TH OBS 1 "June 2026" "obsidian-cli-ops 1.2.3" "User Commands"\n');
    expect(th.version).not.toBe(PKG.version);
  });

  test('parser returns null when no .TH line is present', () => {
    expect(parseTh('.SH NAME\nobs \\- a tool\n')).toBeNull();
  });

  // --- the real assertions against the live page ---
  test('obs.1 .TH product is obsidian-cli-ops', () => {
    const th = parseTh(fs.readFileSync(MAN_PAGE, 'utf-8'));
    expect(th).not.toBeNull();
    expect(th.product).toBe('obsidian-cli-ops');
  });

  test('obs.1 .TH version matches package.json version', () => {
    const th = parseTh(fs.readFileSync(MAN_PAGE, 'utf-8'));
    expect(th.version).toBe(PKG.version);
  });
});
