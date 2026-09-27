# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-09-27

### Added
- Centralized color palette in `theme.py` (`COLORS`, `palette()`); widgets now adapt to light/dark theme.
- `i18n.py` translation helper with `tr()` lookup; all UI strings routed through it.
- `pyproject.toml` with project metadata, entry point `tusklavye`, ruff + pytest config.
- `.gitignore`, `LICENSE` (MIT), `CHANGELOG.md`, `requirements-dev.txt`.
- `tests/` package with pytest-compatible tests and `conftest.py` fixtures.
- GitHub Actions CI workflow (Windows + Ubuntu + macOS matrix).
- CLI args: `--version`, `--text`, `--lesson`.
- Keyboard shortcuts: `Ctrl+1..7` page switch, `Ctrl+R` retry, `Esc` pause.
- CSV export on statistics page.
- `SessionRecord` dataclass replaces 14-positional-arg `save_session`.
- `SettingsRepository.get_bool/get_int/get_float` typed accessors.
- Heatmap tooltips, chart axis labels, "no data" state respects theme.
- `TypingPageMixin` extracts duplicated `on_key_press`/save/unlock logic.
- `TypingEngine.last_expected` public property.
- Real migration framework (`_migrations` registry).

### Changed
- `closeEvent` now logs save errors and warns the user instead of silently swallowing.
- `save_session` calls on all pages wrapped in try/except with `QMessageBox` on failure.
- `_touch_streak` uses `execute_no_commit` to avoid premature commit mid-transaction.
- `Database` singleton replaced with `Database.get(path)` factory; tests no longer need `__new__` hack.
- Signal naming unified to snake_case (`key_pressed`, `stats_updated`, `retry_requested`).
- `home.py`/`achievements.py` `refresh()` updates in place instead of rebuilding UI (no flicker).
- Pinned `PySide6<6.8` to avoid Qt API breaks.
- All docstrings added to public classes; type hints completed.

### Fixed
- Silent data loss on close when `save_session` raised an exception.
- Premature commit in `save_session` via `_touch_streak` calling `execute()`.
- Theme-blind widgets (`finger_guide`, `heatmap`, `custom_text` chips) now theme-aware.
- `_reset_data` now resets `settings` table too and shows `QMessageBox` on error.
- `_import_data` validates JSON schema before applying.
- Unused imports removed across 9 files.
- `__import__("os")` replaced with top-level `import os` in `config.py`.
- Lazy `import random` / `import QMessageBox` moved to top-level.

## [1.0.0] - 2026-09-26

### Added
- Initial release: 15-lesson curriculum, timed tests, custom text, achievements, statistics, finger guide, virtual keyboard, sound feedback, dark/light themes, SQLite storage, cross-platform (Windows/macOS/Linux).