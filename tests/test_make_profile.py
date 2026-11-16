import re
import sys
import unittest
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import make_profile as mp  # noqa: E402


class BuildTest(unittest.TestCase):
    def setUp(self):
        self.svg = mp.build()

    def test_is_valid_xml(self):
        ET.fromstring(self.svg)

    def test_embedded_ids_are_unique(self):
        ids = re.findall(r'\bid="([^"]+)"', self.svg)
        self.assertEqual([i for i, n in Counter(ids).items() if n > 1], [])

    def test_every_url_ref_resolves(self):
        ids = set(re.findall(r'\bid="([^"]+)"', self.svg))
        self.assertTrue(set(re.findall(r"url\(#([^)]+)\)", self.svg)) <= ids)

    def test_stack_items_present(self):
        for _, _, items in mp.STACK:
            for item in items:
                self.assertIn(f">{item}<", self.svg)


class EmbedTest(unittest.TestCase):
    def test_shifts_delays_and_prefixes_ids(self):
        out = mp.embed(mp.ASSETS / "stats.svg", "s-", 0, 0, 100, 50, delay=2.0)
        self.assertNotIn('id="g"', out)
        self.assertIn("url(#s-g)", out)
        self.assertIn("animation-delay:2.15s", out)


if __name__ == "__main__":
    unittest.main()
