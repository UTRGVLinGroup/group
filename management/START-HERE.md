# Open the website editor

Double-click **Wei Lin Website Editor** on your desktop. The editor opens in your browser and runs privately on this computer. You can also double-click **Open Website Editor.cmd** in the website folder; keep its window open while editing.

## Everyday updates

1. Choose **News** or **Courses**. Add a semester or edit an existing entry. Keep the newest semester first. Paste a full `https://` link into a news entry to make it clickable.
2. Click **Save**. This saves locally and creates a backup.
3. Return to **Overview** and click **Build & preview**. Check the result in the new tab. Allow a new tab if your browser asks.
4. Click **Create upload ZIP**. Upload the extracted ZIP contents to the existing web hosting directory, replacing the previous files. The editor does not log in to hosting or publish automatically.

**Other pages** lets you change existing text, links, and image descriptions on Home, Group, Research, and Links. It preserves the page layout. New page layouts, new link cards/group members, and image replacements still require a website edit. Use News and Courses for adding repeatable content without code.

## Publications

Weekly checks use the exact Scholar profile `3SFNLZ4AAAAJ`. New titles appear in **Publication review**. Open the source, verify that the author is this professor, then choose **Review & approve** or **Ignore**. Confirm whether the work is a publication, preprint, or unpublished manuscript. Approval saves the record locally; export and upload when ready.

Previously excluded namesake papers and consolidated duplicate records remain suppressed. Existing publications are never replaced or removed by a check. You can add or edit a paper manually in **Publications**, including when Scholar blocks an automated check.

The weekly schedule runs through Codex on this computer. Keep the computer awake, connected to the internet, and Codex running for scheduled checks. You do not need to keep the editor open. The Overview page shows the last attempt, last successful check, and any failure. A blocked or failed check leaves your publications and pending queue untouched. Use Codex’s automation controls to change or pause the schedule.

## Recovery and settings

- Unsaved changes are only in your current browser window. Save before switching sections or closing it.
- **Backups & settings** restores earlier content. Restoring also backs up the current version. After restoring, rebuild and preview before uploading.
- Enter your final HTTPS website directory under **Final website address** to add search-engine metadata on future builds. This does not connect a hosting account.
- Only upload **website-upload.zip** contents or **dist** contents. Never upload the editor, backups, management folder, or development folder.
- Keep this website folder in its current location. If you move it, the desktop shortcut and weekly task path need updating.

## Technical help

The launcher uses the existing Python installation and `requests`/`beautifulsoup4` packages. If moving to another computer, install Python 3.10+ and run `python -m pip install requests beautifulsoup4` once. Then run `Open Website Editor.cmd`. The editor binds only to `127.0.0.1:8765`. It uses a per-launch token and checks the request origin before saving.

`python management/editor.py --check` runs a single publication check. It stages candidates only and returns a nonzero exit code if the source is blocked. The queue and last-check status are in `management/review-queue.json`. The weekly automation definition is managed by Codex; `management/weekly-schedule.json` records the schedule created at setup, not a live connection to Codex’s current settings.

Before changing the editor implementation, run `python -m unittest discover -s management/tests` and `python scripts/validate.py`. Tests use temporary copies and do not alter your real content.
