import json
import os
import unittest
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from challenge import (
    ChallengeDateAlreadyCompleteError,
    ChallengeInactiveError,
    ChallengeRecommendationAlreadyCompleteError,
    add_challenge_completion,
    challenge_day,
    challenge_status,
    current_local_date,
    completed_nights,
    filter_uncompleted_recommendations,
    load_challenge_completions,
    recommendation_identity,
    save_challenge_completions,
)

ROOT = Path(__file__).resolve().parents[1]
MOVIES = json.loads((ROOT / "data" / "movies.json").read_text(encoding="utf-8"))


class ChallengeHelpersTests(unittest.TestCase):
    def test_october_boundaries_and_current_year(self):
        self.assertEqual(challenge_status(date(2026, 9, 30)), "upcoming")
        self.assertEqual(challenge_status(date(2026, 10, 1)), "active")
        self.assertEqual(challenge_status(date(2026, 10, 31)), "active")
        self.assertEqual(challenge_status(date(2026, 11, 1)), "completed")
        self.assertIsNone(challenge_day(date(2026, 9, 30)))
        self.assertEqual(challenge_day(date(2026, 10, 31)), 31)

    def test_identities_include_category_and_remake_year(self):
        movie_1982 = {"title": "The Thing", "year": 1982}
        movie_2011 = {"title": "The Thing", "year": 2011}
        episode = {
            "show": "The Simpsons", "episode_title": "Treehouse of Horror",
            "season": 2, "episode_number": 3,
        }
        special = {"show": "Family Guy", "episode_title": "Happy Hell-o-ween"}
        self.assertNotEqual(recommendation_identity("movie", movie_1982), recommendation_identity("movie", movie_2011))
        self.assertNotEqual(recommendation_identity("movie", movie_1982), recommendation_identity("game", movie_1982))
        self.assertEqual(recommendation_identity("episode", episode), recommendation_identity("tv", episode))
        self.assertNotEqual(recommendation_identity("tv", episode), recommendation_identity("tv", special))

    def test_one_per_date_and_no_repeated_item(self):
        movie = {"title": "The Thing", "year": 1982}
        game = {"title": "The Thing"}
        first = add_challenge_completion([], "movie", movie, date(2026, 10, 1))
        self.assertEqual(first[0]["category"], "movie")
        self.assertEqual(first[0]["title"], "The Thing (1982)")
        with self.assertRaises(ChallengeDateAlreadyCompleteError):
            add_challenge_completion(first, "game", game, date(2026, 10, 1))
        with self.assertRaises(ChallengeRecommendationAlreadyCompleteError):
            add_challenge_completion(first, "movie", movie, date(2026, 10, 2))
        with self.assertRaises(ChallengeInactiveError):
            add_challenge_completion([], "game", game, date(2026, 9, 30))
        with self.assertRaises(ChallengeInactiveError):
            add_challenge_completion([], "game", game, date(2026, 11, 1))

    def test_no_repeat_filter_is_cross_category_and_date_aware(self):
        movie = {"title": "The Thing", "year": 1982}
        other_movie = {"title": "Alien", "year": 1979}
        same_named_game = {"title": "The Thing"}
        records = add_challenge_completion([], "movie", movie, date(2026, 10, 1))
        movies = filter_uncompleted_recommendations([movie, other_movie], "movie", records, date(2026, 10, 2))
        self.assertEqual(movies, [other_movie])
        self.assertEqual(
            filter_uncompleted_recommendations([same_named_game], "game", records, date(2026, 10, 2)),
            [same_named_game],
        )
        self.assertEqual(
            filter_uncompleted_recommendations([movie], "movie", records, date(2026, 10, 1)),
            [movie],
        )
        self.assertEqual(
            filter_uncompleted_recommendations([movie], "movie", records, date(2026, 11, 1)),
            [movie],
        )

    def test_store_is_chronological_and_separate_from_legacy_watch_file(self):
        movie = {"title": "The Thing", "year": 1982}
        episode = {"show": "The Simpsons", "episode_title": "Treehouse of Horror", "season": 2, "episode_number": 3}
        game = {"title": "Phasmophobia"}
        with TemporaryDirectory() as directory:
            root = Path(directory)
            challenge_path = root / "challenge.json"
            watched_path = root / "watched_movies.json"
            watched_payload = {"version": 1, "watched": [{"title": "Old Movie", "year": 1975}]}
            watched_path.write_text(json.dumps(watched_payload), encoding="utf-8")
            original_watched = watched_path.read_bytes()

            records = add_challenge_completion([], "game", game, date(2026, 10, 3))
            records = add_challenge_completion(records, "movie", movie, date(2026, 10, 2))
            records = add_challenge_completion(records, "episode", episode, date(2026, 10, 1))
            save_challenge_completions(records, challenge_path)

            loaded = load_challenge_completions(challenge_path)
            self.assertEqual([record["date"] for record in loaded], ["2026-10-01", "2026-10-02", "2026-10-03"])
            self.assertEqual([record["category"] for record in loaded], ["tv", "movie", "game"])
            self.assertTrue(all({"date", "category", "identity", "title"} <= record.keys() for record in loaded))
            self.assertEqual(completed_nights(loaded, 2026), 3)

            save_challenge_completions([], challenge_path)
            self.assertEqual(load_challenge_completions(challenge_path), [])
            self.assertEqual(watched_path.read_bytes(), original_watched)

    def test_legacy_movie_titles_remain_excluded_without_challenge_dates(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            challenge_path = root / "challenge.json"
            watched_path = root / "watched_movies.json"
            legacy = {"version": 1, "watched": [{"title": MOVIES[0]["title"], "year": MOVIES[0]["year"]}]}
            watched_path.write_text(json.dumps(legacy), encoding="utf-8")
            save_challenge_completions([], challenge_path)
            self.assertEqual(load_challenge_completions(challenge_path), [])
            self.assertEqual(json.loads(watched_path.read_text(encoding="utf-8")), legacy)

    def test_browser_timezone_uses_local_calendar_date(self):
        before_local_midnight = datetime(2026, 10, 1, 3, 30, tzinfo=timezone.utc)
        after_local_midnight = datetime(2026, 10, 1, 9, 30, tzinfo=timezone.utc)
        zone = "America/Los_Angeles"
        self.assertEqual(current_local_date(timezone_name=zone, now=before_local_midnight), date(2026, 9, 30))
        self.assertEqual(current_local_date(timezone_name=zone, now=after_local_midnight), date(2026, 10, 1))


class ChallengeAppTests(unittest.TestCase):
    def make_app(self, root, today, watched=None):
        from streamlit.testing.v1 import AppTest

        challenge_path = root / "challenge_completions.json"
        watched_path = root / "watched_movies.json"
        if watched is not None:
            watched_path.write_text(json.dumps({"version": 1, "watched": watched}), encoding="utf-8")
        app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=20)
        app.session_state["_challenge_test_today"] = today
        app.session_state["_challenge_test_store_path"] = str(challenge_path)
        app.session_state["_challenge_test_watched_path"] = str(watched_path)
        with patch.dict(os.environ, {"TMDB_READ_ACCESS_TOKEN": ""}):
            app.run()
        self.assertEqual(len(app.exception), 0, [item.message for item in app.exception])
        return app, challenge_path, watched_path

    def click(self, app, label):
        matches = [button for button in app.button if button.label == label]
        self.assertEqual(len(matches), 1, f"Expected one button labeled {label!r}; saw {[b.label for b in app.button]}")
        matches[0].click().run()
        self.assertEqual(len(app.exception), 0, [item.message for item in app.exception])

    def test_completion_is_explicit_limited_and_separate_from_watched(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            app, challenge_path, watched_path = self.make_app(root, date(2026, 10, 1))
            self.click(app, "🎬 MOVIE")
            self.assertIn("Complete Tonight", [button.label for button in app.button])
            self.assertFalse(challenge_path.exists(), "Rolling must not create a completion")

            self.click(app, "Complete Tonight")
            records = load_challenge_completions(challenge_path)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["category"], "movie")
            self.assertFalse(watched_path.exists(), "Challenge completion must not mark a movie watched")
            self.assertNotIn("Complete Tonight", [button.label for button in app.button])
            self.assertIn("Mark as Watched", [button.label for button in app.button])

            self.click(app, "🎲 Roll Again")
            self.assertEqual(len(load_challenge_completions(challenge_path)), 1)
            self.click(app, "🔄 Choose Something Else")
            self.assertIsNone(app.session_state["category"])
            self.assertEqual(len(load_challenge_completions(challenge_path)), 1)

    def test_legacy_watched_movies_stay_excluded_and_can_be_included(self):
        all_watched = [{"title": movie["title"], "year": movie["year"]} for movie in MOVIES]
        with TemporaryDirectory() as directory:
            app, challenge_path, watched_path = self.make_app(Path(directory), date(2026, 10, 2), all_watched)
            self.click(app, "🎬 MOVIE")
            info = " ".join(element.value for element in app.info)
            self.assertIn("Every movie matching these filters is already marked as watched", info)
            self.assertEqual(load_challenge_completions(challenge_path), [])

            checkbox = next(item for item in app.checkbox if item.label == "Include watched movies in future rolls")
            checkbox.check().run()
            self.assertEqual(len(app.exception), 0, [item.message for item in app.exception])
            roll_button = next(button for button in app.button if button.label == "🎲 Roll Again")
            self.assertFalse(roll_button.disabled)
            self.assertTrue(watched_path.exists())
            self.assertEqual(load_challenge_completions(challenge_path), [])

    def test_movie_tv_game_filters_and_roll_controls_remain_available(self):
        with TemporaryDirectory() as directory:
            app, _, _ = self.make_app(Path(directory), date(2026, 9, 30))
            self.click(app, "🎬 MOVIE")
            self.assertEqual({box.label for box in app.selectbox}, {"Genre", "Scare level"})
            self.click(app, "🔄 Choose Something Else")
            self.click(app, "📺 HALLOWEEN EPISODE")
            self.assertEqual([box.label for box in app.selectbox], ["Show"])
            self.click(app, "🔄 Choose Something Else")
            self.click(app, "🎮 SPOOKY GAME")
            self.assertEqual({box.label for box in app.selectbox}, {"Genre", "Player support"})
            self.assertIn("🎲 Roll Again", [button.label for button in app.button])
            self.assertIn("🔄 Choose Something Else", [button.label for button in app.button])

    def test_october_date_injection_controls_upcoming_tv_section(self):
        with TemporaryDirectory() as directory:
            before, _, _ = self.make_app(Path(directory) / "before", date(2026, 10, 4))
            upcoming_text = " ".join(str(item.value) for item in before.markdown)
            self.assertIn("Happy Hell-o-ween", upcoming_text)
        with TemporaryDirectory() as directory:
            available, _, _ = self.make_app(Path(directory) / "available", date(2026, 10, 5))
            available_text = " ".join(str(item.value) for item in available.markdown)
            self.assertNotIn("Happy Hell-o-ween", available_text)

    def test_movie_provider_fallback_renders_without_provider_data(self):
        import streamlit as st

        st.cache_data.clear()
        with TemporaryDirectory() as directory, patch(
            "tmdb.enrich_movie", return_value={"watch_providers": {"streaming": []}}
        ):
            app, _, _ = self.make_app(Path(directory), date(2026, 10, 6))
            self.click(app, "🎬 MOVIE")
            captions = " ".join(str(item.value) for item in app.caption)
            self.assertIn("No U.S. streaming providers are listed for this movie.", captions)

    def test_challenge_reset_requires_confirmation_and_keeps_watched_file(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            watched_path = root / "watched_movies.json"
            watched_payload = {"version": 1, "watched": [{"title": MOVIES[0]["title"], "year": MOVIES[0]["year"]}]}
            watched_path.write_text(json.dumps(watched_payload), encoding="utf-8")
            before = watched_path.read_bytes()
            app, challenge_path, _ = self.make_app(root, date(2026, 10, 3), watched_payload["watched"])
            record = add_challenge_completion([], "game", {"title": "Phasmophobia"}, date(2026, 10, 2))
            save_challenge_completions(record, challenge_path)
            app.run()

            self.click(app, "Reset October challenge")
            self.assertEqual(len(load_challenge_completions(challenge_path)), 1)
            self.assertIn("Confirm challenge reset", [button.label for button in app.button])
            self.click(app, "Confirm challenge reset")
            self.assertEqual(load_challenge_completions(challenge_path), [])
            self.assertEqual(watched_path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
