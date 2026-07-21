"""Offline tests for citation analysis. Run: python3 -m unittest discover tests"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from analysis import aggregate, check_citations, compute_deltas

URLS = [
    "https://g2.com/categories/pm",
    "https://www.asana.com/resources/guide",
    "https://trello.com/tour",
    "https://asana.com/blog/tips",
]


class TestCheckCitations(unittest.TestCase):
    def test_cited_found(self):
        r = check_citations("asana.com", URLS)
        self.assertTrue(r["cited"])
        self.assertEqual(r["citation_rank"], 2)
        self.assertEqual(r["citation_url"], "https://www.asana.com/resources/guide")
        self.assertEqual(r["all_citation_urls"],
                         ["https://www.asana.com/resources/guide", "https://asana.com/blog/tips"])
        self.assertEqual(r["total_citations"], 4)

    def test_www_prefix_stripped(self):
        r = check_citations("asana.com", ["https://www.asana.com/x"])
        self.assertTrue(r["cited"])

    def test_not_cited(self):
        r = check_citations("monday.com", URLS)
        self.assertFalse(r["cited"])
        self.assertIsNone(r["citation_rank"])
        self.assertIsNone(r["citation_url"])
        self.assertEqual(r["all_citation_urls"], [])

    def test_empty_source_urls(self):
        r = check_citations("asana.com", [])
        self.assertFalse(r["cited"])
        self.assertEqual(r["total_citations"], 0)

    def test_domain_input_www_stripped(self):
        r = check_citations("www.asana.com", URLS)
        self.assertTrue(r["cited"])

    def test_rank_is_one_indexed(self):
        r = check_citations("g2.com", URLS)
        self.assertEqual(r["citation_rank"], 1)


class TestAggregate(unittest.TestCase):
    def _records(self):
        return [
            {"domain": "asana.com", "engine": "perplexity", "query": "q1",
             "cited": True,  "citation_rank": 2},
            {"domain": "asana.com", "engine": "chatgpt",    "query": "q1",
             "cited": False, "citation_rank": None},
            {"domain": "trello.com", "engine": "perplexity", "query": "q1",
             "cited": True,  "citation_rank": 1},
        ]

    def test_citation_rate(self):
        agg = aggregate(self._records())
        self.assertEqual(agg["asana.com"]["citation_rate"], 0.5)
        self.assertEqual(agg["trello.com"]["citation_rate"], 1.0)

    def test_avg_rank_excludes_not_cited(self):
        agg = aggregate(self._records())
        self.assertEqual(agg["asana.com"]["avg_rank"], 2.0)

    def test_per_engine_breakdown(self):
        agg = aggregate(self._records())
        self.assertEqual(agg["asana.com"]["engines"]["perplexity"]["citation_rate"], 1.0)
        self.assertEqual(agg["asana.com"]["engines"]["chatgpt"]["citation_rate"], 0.0)


class TestDeltas(unittest.TestCase):
    def test_delta_computed(self):
        current = {"asana.com": {"citation_rate": 0.75, "avg_rank": 2.0}}
        previous = {"asana.com": {"citation_rate": 0.5,  "avg_rank": 3.0}}
        d = compute_deltas(current, previous)
        self.assertEqual(d["asana.com"]["citation_rate"]["delta"], 0.25)
        self.assertEqual(d["asana.com"]["avg_rank"]["delta"], -1.0)

    def test_new_domain_no_previous(self):
        current = {"asana.com": {"citation_rate": 0.5, "avg_rank": None}}
        d = compute_deltas(current, None)
        self.assertIsNone(d["asana.com"]["citation_rate"]["previous"])
        self.assertIsNone(d["asana.com"]["citation_rate"]["delta"])

    def test_avg_rank_none_when_never_cited(self):
        current = {"asana.com": {"citation_rate": 0.0, "avg_rank": None}}
        previous = {"asana.com": {"citation_rate": 0.5, "avg_rank": 3.0}}
        d = compute_deltas(current, previous)
        self.assertIsNone(d["asana.com"]["avg_rank"]["delta"])


if __name__ == "__main__":
    unittest.main()
