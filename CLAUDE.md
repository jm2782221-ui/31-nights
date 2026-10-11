# 31 Nights — Claude Code project guide

Halloween movie / TV-episode / spooky-game randomizer with an October 31-night
challenge. Python + Streamlit, no database, no accounts. Current release: **V2.0**.
GitHub (`main`) is the source of truth; the live demo deploys from `main` on
Streamlit Community Cloud (https://31-nights-halloween.streamlit.app/).

## Ground rules

- **Continue, don't rebuild.** Preserve existing behavior and on-disk user data
  formats. No redesigns or new features without the owner's sign-off.
- **Never commit secrets.** The TMDB token lives only in the
  `TMDB_READ_ACCESS_TOKEN` environment variable or `.streamlit/secrets.toml`
  (git-ignored). Never print it, log it, or put it in tests, docs, or commits.
  Tests use placeholder strings and must not make network calls.
- **Never commit user state.** `watched_movies.json` and
  `challenge_completions.json` are git-ignored runtime files. Don't delete or
  rewrite a developer's local copies; tests must use temp paths (see below).
- Work on a branch and open a PR into `main`; pushing to `main` redeploys the
  public demo.

## Commands

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run streamlit_app.py                       # run the app
```

Required before every commit (all three must pass):

```bash
python -m unittest discover -s tests -v
python -m py_compile app.py streamlit_app.py challenge.py tmdb.py
python -c "import json, pathlib; [json.loads(p.read_text(encoding='utf-8')) for p in pathlib.Path('data').glob('*.json')]; print('JSON catalogs valid')"
```

Then read `git diff` / `git status` before calling work done. The
`missing ScriptRunContext` lines printed during tests are harmless AppTest noise.

## Architecture

| File | Role |
| --- | --- |
| `streamlit_app.py` | Entire Streamlit UI (~830 lines): theme CSS, catalog loading, filters, watched-movie storage, challenge card + calendar, top-level script flow. This is the Community Cloud entrypoint. |
| `challenge.py` | Pure logic + storage for the October challenge: local-date resolution, status, stable identities, validation, atomic save. No Streamlit import. |
| `tmdb.py` | Stdlib-only (`urllib`) TMDB client: title/year matching, metadata, US watch providers, token lookup. Returns `None` on any failure. |
| `app.py` | Original V1.0 console app with hardcoded lists. Legacy; kept runnable, not connected to `data/`. |
| `data/*.json` | Curated catalogs: 90 movies, 63 TV episodes, 5 games. |
| `tests/` | `unittest` + Streamlit `AppTest` (18 tests). |

Only dependency: `streamlit==1.64.0` (pinned). README states Python 3.12+;
verified on 3.13.

### Catalog schemas

- `movies.json`: `title`, `year` (int), `genre`, `scare_level` (int 1–5).
- `tv_episodes.json`: `show`, `episode_title`, `season`, `episode_number`
  (both `null` for specials), optional `special_year`, optional
  `available_date` (ISO date; episode is held in "Coming Soon" until then).
- `games.json`: `title`, `genre`, `player_support`
  (`single-player` | `multiplayer` | `both`).

`(title, year)` for movies and `(show, episode_title, season, episode_number)`
for episodes are identity keys — **renaming a catalog entry orphans saved user
history** (see Known issues). Treat renames as data migrations.

### Runtime state (git-ignored, repo root)

- `watched_movies.json` — `{"version": 1, "watched": [{"title", "year"}]}`.
  Undated movie watch list (V1.7). Only excludes movies from rolls.
- `challenge_completions.json` —
  `{"version": 1, "completions": [{"date", "category", "identity", "title"}]}`.
  `category` is `movie` | `tv` | `game`; `identity` is a JSON-array string from
  `recommendation_identity()`.

The two stores are deliberately independent: marking a movie watched never
completes a night, and Reset Challenge never touches the watch list. Both are
written atomically (temp file + `os.replace`).

### Behavior rules worth knowing

- **Local date**: `current_local_date()` uses the browser timezone
  (`st.context.timezone`), falling back to server date. Countdown, challenge
  day, "Coming Soon", and the daily pick reset all use this one `today`.
- **Challenge**: active only in October; one completion per local date; an
  item can be completed once per October (per year). Completed items are
  filtered out of rolls only while tonight is still open.
- **Category naming**: the UI/session key is `"episode"`; challenge records use
  `"tv"`. `challenge._category_key()` maps between them. Easy to trip on.
- **TMDB**: env var beats Streamlit secret; results cached 6 h via
  `st.cache_data`; match requires same release year and ≥0.85 title similarity.
  The app must keep working with no token and with TMDB down.
- **Streamlit rerun model**: the script runs top to bottom on every
  interaction; the challenge card is rendered *before* the pick is chosen.

### Test hooks

`streamlit_app.py` reads three session-state keys so `AppTest` can inject
state: `_challenge_test_today` (a `date`), `_challenge_test_store_path`,
`_challenge_test_watched_path`. Keep these working; new UI tests should use
them with a `TemporaryDirectory` and patch `TMDB_READ_ACCESS_TOKEN` to `""`.

## Conventions

- Stdlib first; adding a dependency needs a reason and a pinned version.
- Validate everything read from disk or TMDB; fail soft (empty list / `None`),
  never crash the page or leak credentials in an error.
- Escape any catalog/user text placed into `unsafe_allow_html` markup
  (`html.escape`, as the calendar does).
- Keep `challenge.py` free of Streamlit so it stays unit-testable.
- Honor `prefers-reduced-motion` and keep visible focus styles when touching CSS.
- Bump any JSON `version` field and write a migration if a store format changes.
- Commit style follows history: imperative summary, version noted when a
  release is cut (e.g. "Add streaming availability for V1.6").

## Known issues (assessed 2026-10-11, not yet fixed)

1. **Challenge card "Tonight's Pick" is wrong.** It is drawn before the pick is
   chosen, so it shows "Choose a category…" right after choosing one and lags
   one interaction behind. For TV it never shows at all (`"episode"` vs `"tv"`
   key mismatch in `show_challenge_card`).
2. **Crash on "Complete Tonight" with no pick.** When filters/watch list leave
   no recommendation, the button still renders; clicking raises an uncaught
   `ValueError` (TV would raise `AttributeError`).
3. **Watch history can be silently dropped.** `save_watched_movies` rewrites the
   file from the current catalog, discarding entries whose title/year is no
   longer in `movies.json`. The expander count also includes those entries
   while the list doesn't.
4. Duplicate "Every movie… already marked as watched" notice.
5. `challenge_status()` returns `"completed"` for every Nov–Dec date and
   `"upcoming"` Jan–Sep; fine today, but "completed" means "month over".
6. Legacy `app.py`: countdown goes negative after Oct 31; catalog diverged.
7. Public demo shares one state file among all visitors and Community Cloud
   may wipe it (documented in README).

## Technical debt

- `streamlit_app.py` mixes CSS, storage, logic, and page flow at module level;
  watched-movie storage belongs beside `challenge.py`.
- Tests: no coverage for TMDB matching/provider parsing, calendar markup,
  watched-movie save/load, or the bugs above. Test file is still named
  `test_v1_8_challenge.py`. No CI.
- `use_container_width` is on Streamlit's deprecation path (`width="stretch"`).
- No catalog schema validation beyond "parses as JSON"; 26 movie genres, many
  near-duplicates (e.g. "Creature feature" vs "Creature horror"), fragment the
  filter.
- Games catalog has only 5 entries — too few for a game-heavy challenge.
- No `.streamlit/config.toml`, no `.env.example` (though `.gitignore` allows one),
  no version constant or git tags.

## Roadmap (proposed; needs owner approval)

1. **V2.0.1 — stabilization**: fix issues 1–4 with regression tests; add CI
   (GitHub Actions running the three pre-commit checks).
2. **V2.1 — data quality**: catalog schema validator in tests, genre
   normalization, expand games, add 2026 specials.
3. **V2.2 — maintainability**: extract watched-movie storage and theme into
   modules; rename/split tests; TMDB unit tests with mocked responses.
4. **V3.0 — persistence** (only if the public demo should hold real history):
   per-visitor state instead of a shared server file.
