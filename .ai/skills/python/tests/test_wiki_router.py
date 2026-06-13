from __future__ import annotations

import unittest

from ai_workspace.wiki.wiki_router import propose_target_path


MODULE_MAP = {
    "modules": {
        "invoicing_billing": {
            "display_name": "Invoicing / Billing",
            "candidate_paths": ["/Invoicing", "/Billing"],
            "keywords": ["invoice", "invoicing", "billing", "finance"],
            "related_objects": [],
        }
    },
    "fallback": {
        "proposed_root": "/_Proposed",
        "unclassified_root": "/_Unclassified",
    },
}


class WikiRouterTests(unittest.TestCase):
    def test_routes_explicit_module_to_existing_section(self) -> None:
        wiki_index = {
            "pages": [{"path": "/Invoicing/Overview", "title": "Invoicing", "headings": [], "keywords": ["invoicing"], "folder": "/Invoicing"}],
            "folders": [{"path": "/Invoicing", "children": [], "has_order_file": True}],
        }

        decision = propose_target_path(
            wiki_index=wiki_index,
            module_map=MODULE_MAP,
            source_text="Invoice approval routing for billing users.",
            work_item="KIM-1234",
            title="Invoice Approval Routing",
            explicit_module="invoicing_billing",
        )

        self.assertEqual(decision["target_wiki_path"], "/Invoicing/Invoice-Approval-Routing.md")
        self.assertEqual(decision["confidence"], "high")

    def test_routes_missing_module_section_to_proposed(self) -> None:
        decision = propose_target_path(
            wiki_index={"pages": [], "folders": []},
            module_map=MODULE_MAP,
            source_text="Invoice approval routing for billing users.",
            work_item="KIM-1234",
            title="Invoice Approval Routing",
        )

        self.assertEqual(decision["target_wiki_path"], "/_Proposed/Invoicing-Billing/Invoice-Approval-Routing.md")
        self.assertEqual(decision["confidence"], "low")
        self.assertTrue(decision["warnings"])

    def test_routes_unmatched_topic_to_unclassified(self) -> None:
        decision = propose_target_path(
            wiki_index={"pages": [], "folders": []},
            module_map=MODULE_MAP,
            source_text="A topic without mapped module keywords.",
            work_item="KIM-9999",
            title="Unknown Feature",
        )

        self.assertEqual(decision["target_wiki_path"], "/_Unclassified/Unknown-Feature.md")
        self.assertEqual(decision["confidence"], "low")

    def test_blocks_path_traversal_in_explicit_target(self) -> None:
        with self.assertRaises(ValueError):
            propose_target_path(
                wiki_index={"pages": [], "folders": []},
                module_map=MODULE_MAP,
                source_text="Invoice.",
                work_item="KIM-1234",
                title="Invoice Approval Routing",
                explicit_target_path="../Secrets.md",
            )


if __name__ == "__main__":
    unittest.main()
