"""Offline tests for engines module. Run: python3 -m unittest discover tests"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from engines import Answer, _provider_citations


def _payload(**extra) -> dict:
    return {"choices": [{"message": {"content": "text"}}], **extra}


class TestProviderCitations(unittest.TestCase):
    def test_empty_when_absent(self):
        self.assertEqual(_provider_citations(_payload()), [])

    def test_perplexity_string_list(self):
        p = _payload(citations=["https://a.com/1", "https://b.com/2"])
        self.assertEqual(_provider_citations(p), ["https://a.com/1", "https://b.com/2"])

    def test_citation_objects(self):
        p = _payload(citations=[{"url": "https://a.com/1"}])
        self.assertEqual(_provider_citations(p), ["https://a.com/1"])

    def test_openai_annotations(self):
        p = {"choices": [{"message": {"content": "text", "annotations": [
            {"type": "url_citation", "url_citation": {"url": "https://a.com/1", "title": "A"}},
        ]}}]}
        self.assertEqual(_provider_citations(p), ["https://a.com/1"])

    def test_flat_annotation_shape(self):
        p = {"choices": [{"message": {"content": "text", "annotations": [
            {"type": "url_citation", "url": "https://a.com/1"},
        ]}}]}
        self.assertEqual(_provider_citations(p), ["https://a.com/1"])

    def test_deduped(self):
        p = {"choices": [{"message": {"content": "text", "annotations": [
            {"type": "url_citation", "url_citation": {"url": "https://a.com/1"}},
        ]}}], "citations": ["https://a.com/1", "https://b.com/2"]}
        self.assertEqual(_provider_citations(p), ["https://a.com/1", "https://b.com/2"])

    def test_malformed_ignored(self):
        p = _payload(citations=[None, {}, {"title": "no url"}, "https://ok.com"])
        self.assertEqual(_provider_citations(p), ["https://ok.com"])


class TestAnswer(unittest.TestCase):
    def test_not_truncated_by_default(self):
        self.assertFalse(Answer("text", []).truncated)

    def test_truncation_flag(self):
        self.assertTrue(Answer("text", [], True).truncated)


if __name__ == "__main__":
    unittest.main()
