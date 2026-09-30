# 31-nights

## TMDB movie details

Movie recommendations remain selected from the curated `data/movies.json` list. To show optional posters and TMDB details, set the TMDB API Read Access Token before starting Streamlit:

```sh
export TMDB_READ_ACCESS_TOKEN="<your TMDB API Read Access Token>"
```

Without the token or when TMDB is unavailable, the curated recommendation is shown normally. Keep the token out of source control.

This product uses the TMDB API but is not endorsed or certified by TMDB.

U.S. movie streaming availability uses TMDB data powered by JustWatch when available; listings can change.
