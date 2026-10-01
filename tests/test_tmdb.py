import os
import unittest
from unittest.mock import patch

from tmdb import _get_tmdb_access_token, enrich_movie


class TmdbCredentialTests(unittest.TestCase):
    def test_explicit_and_environment_tokens_take_precedence(self):
        with patch.dict(os.environ, {"TMDB_READ_ACCESS_TOKEN": "environment-placeholder"}):
            self.assertEqual(
                _get_tmdb_access_token("explicit-placeholder", {"TMDB_READ_ACCESS_TOKEN": "cloud-placeholder"}),
                "explicit-placeholder",
            )
            self.assertEqual(_get_tmdb_access_token(), "environment-placeholder")

    def test_streamlit_secret_is_used_when_environment_is_empty(self):
        with patch.dict(os.environ, {"TMDB_READ_ACCESS_TOKEN": ""}):
            self.assertEqual(
                _get_tmdb_access_token(streamlit_secrets={"TMDB_READ_ACCESS_TOKEN": "cloud-placeholder"}),
                "cloud-placeholder",
            )

    def test_missing_secret_returns_none_without_api_request(self):
        with patch.dict(os.environ, {"TMDB_READ_ACCESS_TOKEN": ""}):
            self.assertIsNone(_get_tmdb_access_token({}))

    def test_movie_enrichment_gracefully_skips_when_secret_is_missing(self):
        with patch.dict(os.environ, {"TMDB_READ_ACCESS_TOKEN": ""}):
            self.assertIsNone(enrich_movie("Scream", 1996))


if __name__ == "__main__":
    unittest.main()
