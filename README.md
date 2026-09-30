# 31-nights

## TMDB movie details

Movie recommendations remain selected from the curated `data/movies.json` list. To show optional posters and TMDB details, set the TMDB API Read Access Token before starting Streamlit:

```sh
export TMDB_READ_ACCESS_TOKEN="<your TMDB API Read Access Token>"
```

Without the token or when TMDB is unavailable, the curated recommendation is shown normally. Keep the token out of source control.

This product uses the TMDB API but is not endorsed or certified by TMDB.

U.S. movie streaming availability uses TMDB data powered by JustWatch when available; listings can change.

## Watched movie history

Mark a Movie recommendation as watched to keep it out of future rolls by default. Watched titles are saved in the local, Git-ignored watched_movies.json file beside the app. The file persists across Streamlit reruns and restarts in this checkout; it is not synced to other devices. The Movie controls let you include watched titles again, review the list, or clear it. Choose Something Else resets the category and filters without clearing watched history.

## Halloween TV episode sources

Curated titles and numbered episode details were checked against the [Disney+ Simpsons Halloween guide](https://www.disneyplus.com/explore/articles/the-simpsons-treehouse-of-horror), [Hulu Community Halloween guide](https://www.hulu.com/guides/halloween-episodes), [Disney+ Family Guy Halloween guide](https://www.disneyplus.com/explore/articles/family-guy-halloween-episodes), and the [Bob's Burgers episode guide on TVmaze](https://www.tvmaze.com/shows/107/bobs-burgers/episodeguide), cross-checked against the [Bob's Burgers Halloween catalog](https://episodegadget.com/bob-s-burgers-halloween-episodes). The Family Guy standalone specials are kept without invented season or episode numbers and displayed by special year.
