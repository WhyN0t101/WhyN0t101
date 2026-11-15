import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import generate_stats as gs  # noqa: E402


def repo(stars: int, langs: dict[str, int]) -> dict:
    return {
        "stargazerCount": stars,
        "languages": {"edges": [{"size": size, "node": {"name": name}} for name, size in langs.items()]},
    }


def page(repos: list[dict], has_next: bool = False) -> dict:
    return {
        "followers": {"totalCount": 7},
        "pullRequests": {"totalCount": 12},
        "issues": {"totalCount": 3},
        "repositoriesContributedTo": {"totalCount": 5},
        "contributionsCollection": {
            "totalCommitContributions": 100,
            "restrictedContributionsCount": 20,
            "contributionCalendar": {
                "totalContributions": 150,
                "weeks": [
                    {"contributionDays": [{"contributionCount": 1}, {"contributionCount": 2}]},
                    {"contributionDays": [{"contributionCount": 0}]},
                ],
            },
        },
        "repositories": {
            "totalCount": 3,
            "pageInfo": {"hasNextPage": has_next, "endCursor": None},
            "nodes": repos,
        },
    }


class AggregateTest(unittest.TestCase):
    def test_sums_across_pages_and_drops_ignored_languages(self):
        pages = [
            page([repo(2, {"Java": 100, "HTML": 999}), repo(1, {"Python": 50})], has_next=True),
            page([repo(4, {"Java": 25})]),
        ]
        stats = gs.aggregate(pages)
        self.assertEqual(stats.stars, 7)
        self.assertEqual(stats.languages, {"Java": 125, "Python": 50})
        self.assertEqual(stats.commits_year, 120)  # public + private (restricted)
        self.assertEqual(stats.weekly, [3, 0])


class TopLanguagesTest(unittest.TestCase):
    def test_folds_tail_into_other(self):
        langs = {"A": 50, "B": 30, "C": 15, "D": 5}
        result = gs.top_languages(langs, limit=2)
        self.assertEqual([name for name, _ in result], ["A", "B", "Other"])
        self.assertAlmostEqual(sum(pct for _, pct in result), 100.0)
        self.assertAlmostEqual(result[-1][1], 20.0)

    def test_empty_input(self):
        self.assertEqual(gs.top_languages({}), [])


class RenderTest(unittest.TestCase):
    def test_cards_are_well_formed_xml(self):
        stats = gs.aggregate([page([repo(1, {"C#": 10, "Rust & co": 5})])])
        for svg in (gs.render_stats(stats), gs.render_languages(gs.top_languages(stats.languages))):
            ET.fromstring(svg)  # raises on malformed markup, e.g. unescaped '&'

    def test_no_activity_does_not_divide_by_zero(self):
        ET.fromstring(gs.render_stats(gs.Stats()))


if __name__ == "__main__":
    unittest.main()
