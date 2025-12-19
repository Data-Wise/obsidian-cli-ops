# Manual Verification: Note Explorer & Last Vault Logic

Follow these steps to verify the implementation of Phase 1:

1. **Start the TUI application:**
   ```bash
   python src/python/tui/app.py
   ```

2. **Navigate to Vaults:**
   - Press `v` on the Home screen.
   - You should see the Vault Browser.

3. **Select a Vault:**
   - Use arrow keys to highlight a vault.
   - Press `Enter`.
   - **Verification:** You should be taken to the **Note Explorer** screen for that vault.

4. **Test Search:**
   - Type in the search box at the top.
   - **Verification:** The note list should filter in real-time as you type.

5. **Test Preview & Metadata:**
   - Select a note in the table using arrow keys.
   - **Verification:** The preview pane (right-top) and metadata pane (right-bottom) should update with the note's content and details.

6. **Test Navigation Back:**
   - Press `Esc` to go back to the Vault Browser.
   - Press `Esc` again to go back to the Home screen.

7. **Test "Last Vault" Shortcuts:**
   - On the Home screen, press `n` (Notes).
   - **Verification:** You should be taken **directly** to the Note Explorer for the vault you previously selected, without having to pick it again.
   - Go back to Home (`Esc` twice).
   - Press `g` (Graph).
   - **Verification:** You should be taken to the Graph Visualizer for that same vault.

---
**Status:** Phase 1 implementation complete and unit-tested.
