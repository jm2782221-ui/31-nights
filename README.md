# 31 Nights 🎃

**Pick a movie, Halloween episode, or spooky game for the season—and make October a 31-night challenge.**

31 Nights is a small Python and Streamlit project for finding something fun to watch or play each night. It combines curated JSON catalogs, category filters, optional TMDB movie details, a movie watch list, and an October challenge with dated cross-category completions.

## Live Demo

[Open the live demo](https://31-nights-halloween.streamlit.app/)

> **Public demo note:** The watch list and challenge history use local JSON files. On Streamlit Community Cloud, visitors share the app's file-backed state, and the platform does not guarantee that local file changes persist. Do not use the public demo for private or important personal history.

## Features

- **Three categories:** 90 movies, a curated Halloween TV episode catalog, and spooky games.
- **Category filters:** narrow movie, TV, and game recommendations using the controls available for each catalog.
- **Random picks:** roll again or choose something else without counting a challenge night.
- **October challenge:** complete at most one movie, TV episode, or game per local calendar date. Track progress out of 31, view the October calendar, and browse dated completions in order.
- **Challenge-wide no repeats:** completed recommendations are excluded from future challenge picks when their identity is clear.
- **Separate movie watch list:** watched movie titles stay excluded from movie rolls by default. You can include them again or clear that list. Marking a movie watched does not complete a challenge night, and challenge reset does not clear watched movies.
- **Movie details:** optional TMDB posters and metadata plus U.S. streaming-provider availability.
- **Upcoming TV episodes:** future availability dates appear as Coming Soon and are held out of current recommendations until available.
- **Halloween presentation:** countdown, responsive dark styling, and reduced-motion support.

## How recommendations work

The app loads movies, TV episodes, and games from the JSON files in `data/`. It applies the selected category filters, removes watched movies when the include-watched control is off, and removes items already completed during the current October challenge. A random eligible item becomes the pick. **Rolling, refreshing a pick, and marking a movie watched do not complete a night.** Use the explicit completion action on the pick to record the current local date. A second completion on the same date is blocked.

The challenge records contain a local date, category, and stable recommendation identity/title. They are stored separately from the V1.7 movie watched-title list. Resetting the challenge requires confirmation and removes only dated challenge records. Existing movie watch history has no invented dates and does not count toward challenge progress.

## Technology

- Python and Streamlit
- JSON catalogs and local JSON files for watch/challenge state
- TMDB API for optional movie enrichment and U.S. provider availability
- `unittest` and Streamlit `AppTest` for regression checks

## TMDB setup

Movie posters, metadata, and provider availability are optional. The app continues to work from its curated catalog when the token is missing or TMDB is unavailable. Provider availability can change over time and may differ by location; this app displays U.S. results.

Create a TMDB **API Read Access Token** from your TMDB account, then provide it locally using either method below. Never commit the token.

### Environment variable

Linux/macOS: `export TMDB_READ_ACCESS_TOKEN=your_token`

PowerShell: `$env:TMDB_READ_ACCESS_TOKEN = "your_token"`

### Streamlit secrets file

Create `.streamlit/secrets.toml` (this path is ignored by Git):

```toml
TMDB_READ_ACCESS_TOKEN = "your_token"
```

The environment variable takes precedence when both are present. If neither is configured, movie enrichment is skipped without exposing credentials or interrupting recommendations.

## Run locally

Requires Python 3.12 or newer. From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

On Windows PowerShell, activate the environment with `.venv\Scripts\Activate.ps1`. The original console app remains available with `python app.py`.

## Deploy on Streamlit Community Cloud

1. Connect the GitHub repository to [Streamlit Community Cloud](https://share.streamlit.io/).
2. Create an app from the `main` branch with `streamlit_app.py` as the entrypoint.
3. In **Advanced settings → Secrets**, add the same TOML key shown above. Do not add secrets to GitHub or this README.
4. Deploy and open the public app URL.

See the [Community Cloud deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) and [secrets guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).

> Community Cloud may delete files written by an app at any time. Since this project has no accounts or remote database, its file-backed watch and challenge history is shared by visitors and is not guaranteed to persist through restarts or redeployments.

## Tests

Run the complete test suite and compile the Python modules from the repository root:

```bash
python -m unittest discover -s tests -v
python -m py_compile app.py streamlit_app.py challenge.py tmdb.py
```

Validate the catalog JSON files with:

```bash
python -c "import json, pathlib; [json.loads(p.read_text(encoding='utf-8')) for p in pathlib.Path('data').glob('*.json')]; print('JSON catalogs valid')"
```

## Project layout

- `streamlit_app.py` — Streamlit experience
- `app.py` — original Python console app
- `challenge.py` — challenge record storage and date rules
- `tmdb.py` — TMDB requests and metadata validation
- `data/` — movie, TV episode, and game catalogs
- `tests/` — challenge, UI, and TMDB regression tests

## Credits

Movie information, posters, and availability are provided through TMDB. This product uses the TMDB API but is not endorsed or certified by TMDB.
