import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from xml.etree import ElementTree

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from product_topics import BASE, LIMIT, publish_topics, topic_matches


class ProductTopics(unittest.TestCase):
    def test_matches_a_complete_official_label(self):
        row = {"category":"Appliances - Electronics"}
        self.assertTrue(topic_matches(row, "Electronics"))
        self.assertTrue(topic_matches(row, "Appliances"))
        self.assertFalse(topic_matches(row, "Electronic"))
        self.assertFalse(topic_matches({}, "Electronics"))

    def test_preview_keeps_archive_and_empty_groups_distinct(self):
        topics = [{"slug":"appliances","label":"Appliances"},{"slug":"electronics","label":"Electronics"},
                  {"slug":"toys-and-games","label":"Toys and games"}]
        notices = [{"title":f"Test <item> {i}","url":f"https://recalls-rappels.canada.ca/en/{i}",
                    "category":"Appliances", "archived":False,"updated":"2026-01-20"} for i in range(LIMIT+1)]
        notices.append({"title":"Archived sample","category":"Appliances - Electronics","archived":True})
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root/"product-topics.json").write_text(json.dumps(topics))
            publish_topics(root,{"built":"2026-01-22","retrievedAt":"2026-01-21T23:00:00Z","rows":notices})
            preview = (root/"records/appliances/index.html").read_text()
            self.assertIn("Snapshot retrieved 2026-01-21",preview)
            self.assertIn("13 non-archived notices · 1 archived",preview)
            self.assertIn("Test &lt;item&gt; 0",preview)
            self.assertNotIn("Test &lt;item&gt; 12",preview)
            self.assertNotIn("Archived sample",preview)
            archived = (root/"records/electronics/index.html").read_text()
            self.assertIn("0 non-archived notices · 1 archived",archived)
            self.assertIn("?category=electronics#search-title",archived)
            urls = {x.text for x in ElementTree.parse(root/"sitemap.xml").findall(".//{*}loc")}
            self.assertEqual(urls,{BASE+"records/",BASE+"records/appliances/",BASE+"records/electronics/"})
            self.assertIn("0 non-archived notices · 0 archived",(root/"records/toys-and-games/index.html").read_text())
