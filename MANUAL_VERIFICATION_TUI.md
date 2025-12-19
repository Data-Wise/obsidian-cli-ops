# Manual Verification: TUI Performance & Navigation

Follow these steps to verify the optimized, responsive TUI architecture:

1. **Start the TUI application:**
   ```bash
   ./run_tui.sh
   ```

2. **Verify Instant Startup:**
   - The application should launch immediately to the Home Screen.
   - No scanning should block the startup.

3. **Verify Vault Discovery:**
   - Press `v` to open the Vault Browser.
   - If you have iCloud vaults, they should appear in the list.
   - If not, press `d` to trigger discovery. This should be fast and non-blocking.
   - New vaults will show as `[ unscanned ]`.

4. **Verify On-Demand Scanning:**
   - Select an `[ unscanned ]` vault and press `Enter`.
   - **Check:** The UI **must not freeze**. You should see a progress bar appear at the bottom of the screen.
   - **Check:** While scanning, try moving the selection up and down. The UI should remain responsive.

5. **Verify Navigation:**
   - Once the scan finishes, press `Enter` again on the vault.
   - **Check:** You should instantly navigate to the Note Explorer.
   - Press `Esc` to go back to the Vault Browser.
   - Press `Esc` again to go back to the Home Screen.

6. **Verify "Last Vault" Shortcut:**
   - On the Home Screen, press `n`.
   - **Check:** You should jump directly to the Note Explorer for the vault you just used.

---
**Status:** Architecture updated for performance and reliability.