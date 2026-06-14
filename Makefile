# Golden commands for the Copilot-only Salesforce AI Workspace.
#
# ai-index-schema requires Salesforce CLI auth to ORG.
# ai-index-config requires Salesforce CLI auth to ORG and only queries objects
# explicitly enabled in config/data-promotion/config-object-registry.yaml.

ORG ?= IntDev
WORK_ITEM ?= EXAMPLE-WI
QUERY ?= field ui visibility flow config
INDEX_DIR ?= .ai/context/index
WORK_ITEM_DIR ?= .ai/context/work-items/$(WORK_ITEM)
PYTHONPATH_VALUE ?= .ai/skills/python
PYTHON ?= $(shell command -v python3.11 >/dev/null 2>&1 && printf python3.11 || (command -v python >/dev/null 2>&1 && printf python || printf python3))
WORKSPACE_CONFIG ?= .ai/config/workspace.local.json
REGISTRY ?= config/data-promotion/config-object-registry.yaml
MASKING_POLICY ?= config/data-promotion/masking-policy.yaml
BASE_REF ?= HEAD~1
OUT_DIR ?= .ai/outputs/precheck
CONFIG_PACK_DIR ?= config/kimbleone-packs/$(WORK_ITEM)
KB_REPO ?=
KB_BRANCH ?= main
KB_VENDOR_DIR ?= .ai/vendor/knowledge-base
KNOWLEDGE_ROOT ?= .ai/knowledge
KNOWLEDGE_POLICY ?= .ai/knowledge/sync-policy.yaml
KNOWLEDGE_PUSH_MESSAGE ?=
KNOWLEDGE_INDEX ?= .ai/context/index/knowledge-cards.jsonl
KNOWLEDGE_SOURCE ?=
KNOWLEDGE_MANIFEST ?= .ai/templates/knowledge-import-manifest.yaml
KNOWLEDGE_SCHEMA ?= .ai/templates/schemas/knowledge-note.schema.json
KNOWLEDGE_VALIDATION_JSON ?= .ai/outputs/knowledge-import/validation-report.json
KNOWLEDGE_VALIDATION_MD ?= .ai/outputs/knowledge-import/validation-report.md
KNOWLEDGE_MAX_AGE_DAYS ?= 180
KNOWLEDGE_VALIDATE_FLAGS ?=
FORCE_APP_ROOT ?= force-app
METADATA_KNOWLEDGE_INDEX ?= .ai/context/index/metadata-knowledge-cards.jsonl
METADATA_KNOWLEDGE_SUMMARY ?= .ai/context/index/metadata-knowledge-summary.json
KNOWLEDGE_GRAPH ?= .ai/context/index/knowledge-graph.json
KNOWLEDGE_INDEX_YAML ?= .ai/context/index/knowledge-index-files.yaml
KNOWLEDGE_GRAPH_ADJACENCY_CAP ?= 200
KNOWLEDGE_DOMAIN ?= general
KNOWLEDGE_TITLE ?=
KNOWLEDGE_OWNER ?= Salesforce Platform Team
KNOWLEDGE_IMPORT_FLAGS ?=
AZURE_WIKI_REPO ?=
AZURE_WIKI_BRANCH ?= main
AZURE_WIKI_VENDOR_DIR ?= .ai/vendor/azure-wiki
WIKI_TITLE ?=
WIKI_SOURCE ?=
WIKI_MODULE ?=
WIKI_TARGET_PATH ?=
WIKI_APPROVAL_NOTE ?=
DOCS_ROOT ?= docs/workspace
DOCS_HTML ?= $(DOCS_ROOT)/html/index.html

.PHONY: help setup setup-venv configure doctor doctor-strict first-run test smoke ai-index-repo ai-index-schema ai-index-config ai-index-all ai-context ai-context-example ai-clean-context clean-ai-generated ai-list-outputs ai-check-python config-impact config-pack-skeleton knowledge-sync knowledge-sync-dry-run knowledge-index knowledge-import knowledge-import-manifest knowledge-search knowledge-validate metadata-knowledge-index knowledge-graph knowledge-index-yaml ai-context-auto ac-coverage design-lint knowledge-push-dry-run knowledge-push wiki-dry-run wiki-prepare-branch wiki-push-approved wiki-scan docs-build docs-export-pdf docs-pack docs-open-html wi-precheck wi-precheck-strict wi-scope-check mcp-salesforce-context mcp-smoke-test

help:
	@echo "Copilot-only Salesforce AI Workspace commands"
	@echo ""
	@echo "Targets:"
	@echo "  make setup"
	@echo "  make setup-venv"
	@echo "  make configure"
	@echo "  make doctor"
	@echo "  make doctor-strict"
	@echo "  make first-run"
	@echo "  make test"
	@echo "  make smoke"
	@echo "  make ai-check-python"
	@echo "  make ai-index-repo"
	@echo "  make ai-index-schema ORG=IntDev"
	@echo "  make ai-index-config ORG=IntDev"
	@echo "  make ai-index-all ORG=IntDev"
	@echo "  make ai-context WORK_ITEM=KIM-1234 QUERY=\"invoice approval\""
	@echo "  make ai-context-auto WORK_ITEM=KIM-1234"
	@echo "  make ai-context-example"
	@echo "  make ac-coverage WORK_ITEM=KIM-1234"
	@echo "  make design-lint WORK_ITEM=KIM-1234"
	@echo "  make config-impact WORK_ITEM=KIM-1234"
	@echo "  make config-pack-skeleton WORK_ITEM=KIM-1234"
	@echo "  make knowledge-sync-dry-run KB_REPO=<git-url-or-local-path>"
	@echo "  make knowledge-sync KB_REPO=<git-url-or-local-path>"
	@echo "  make knowledge-import KNOWLEDGE_SOURCE=.ai/knowledge/imports/example.txt KNOWLEDGE_DOMAIN=general KNOWLEDGE_TITLE=\"Example Knowledge Note\""
	@echo "  make knowledge-import-manifest KNOWLEDGE_MANIFEST=.ai/templates/knowledge-import-manifest.yaml"
	@echo "  make knowledge-index"
	@echo "  make knowledge-search QUERY=\"invoice approval\""
	@echo "  make knowledge-validate"
	@echo "  make metadata-knowledge-index"
	@echo "  make knowledge-graph"
	@echo "  make knowledge-push-dry-run KB_REPO=<git-url>"
	@echo "  make knowledge-push KB_REPO=<git-url>"
	@echo "  make wiki-dry-run WORK_ITEM=KIM-1234 WIKI_TITLE=\"Invoice Approval Routing\" WIKI_SOURCE=docs/architecture/KIM-1234.md AZURE_WIKI_REPO=<repo>"
	@echo "  make wiki-prepare-branch WORK_ITEM=KIM-1234 WIKI_TITLE=\"Invoice Approval Routing\" WIKI_SOURCE=docs/architecture/KIM-1234.md AZURE_WIKI_REPO=<repo>"
	@echo "  make wiki-push-approved WORK_ITEM=KIM-1234 WIKI_TITLE=\"Invoice Approval Routing\" WIKI_SOURCE=docs/architecture/KIM-1234.md AZURE_WIKI_REPO=<repo> WIKI_APPROVAL_NOTE=\"Approved by <name/date>\""
	@echo "  make wiki-scan AZURE_WIKI_VENDOR_DIR=.ai/vendor/azure-wiki"
	@echo "  make docs-build"
	@echo "  make docs-export-pdf"
	@echo "  make docs-pack"
	@echo "  make docs-open-html"
	@echo "  make ai-list-outputs WORK_ITEM=EXAMPLE-WI"
	@echo "  make ai-clean-context"
	@echo "  make clean-ai-generated"
	@echo "  make wi-precheck WORK_ITEM=KIM-1234 BASE_REF=HEAD~1"
	@echo "  make wi-precheck-strict WORK_ITEM=KIM-1234 BASE_REF=origin/main"
	@echo "  make wi-scope-check WORK_ITEM=KIM-1234 BASE_REF=HEAD~1"
	@echo "  make mcp-salesforce-context"
	@echo "  make mcp-smoke-test"
	@echo ""
	@echo "Notes:"
	@echo "  ai-index-schema requires Salesforce CLI auth to ORG=$(ORG)."
	@echo "  ai-index-config queries only enabled registry objects from $(REGISTRY)."
	@echo "  DevOps Center remains the metadata promotion mechanism; these commands do not deploy."

setup:
	$(PYTHON) -m pip install -e . --quiet
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.configuration.bootstrap \
		--config "$(WORKSPACE_CONFIG)" \
		--create-local-config \
		--print-next-steps

setup-venv:
	$(PYTHON) -m pip install -e . --quiet
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.configuration.bootstrap \
		--config "$(WORKSPACE_CONFIG)" \
		--create-local-config \
		--create-venv \
		--print-next-steps

configure:
	$(PYTHON) scripts/configure.py

doctor:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.configuration.doctor \
		--config "$(WORKSPACE_CONFIG)"

doctor-strict:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.configuration.doctor \
		--config "$(WORKSPACE_CONFIG)" \
		--strict \
		--check-salesforce-auth \
		--check-knowledge

first-run:
	$(MAKE) setup
	$(MAKE) doctor
	$(MAKE) ai-index-repo
	$(MAKE) knowledge-index

test:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m unittest discover -s .ai/skills/python/tests -p "test_*.py"

smoke:
	$(MAKE) ai-check-python
	$(MAKE) test
	$(MAKE) knowledge-index
	$(MAKE) ai-context-example
	$(MAKE) config-impact WORK_ITEM=EXAMPLE-WI
	$(MAKE) config-pack-skeleton WORK_ITEM=EXAMPLE-WI
	$(MAKE) wi-precheck WORK_ITEM=EXAMPLE-WI BASE_REF=HEAD

ai-index-repo:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.indexers.index_repo_metadata \
		--repo-root . \
		--out $(INDEX_DIR)/metadata-components.jsonl

# Requires Salesforce CLI auth to ORG. Schema-only query; no metadata retrieve/deploy.
ai-index-schema:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.indexers.index_org_schema \
		--org $(ORG) \
		--namespace KimbleOne \
		--out-dir $(INDEX_DIR)

# Requires Salesforce CLI auth to ORG. Queries only explicitly enabled registry objects.
ai-index-config:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.indexers.index_config_records \
		--org $(ORG) \
		--registry $(REGISTRY) \
		--masking-policy $(MASKING_POLICY) \
		--out $(INDEX_DIR)/config-record-cards.jsonl

ai-index-all:
	$(MAKE) ai-index-repo
	$(MAKE) knowledge-index
	$(MAKE) ai-index-schema ORG=$(ORG)
	$(MAKE) ai-index-config ORG=$(ORG)

ai-context:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.indexers.build_context_pack \
		--work-item $(WORK_ITEM) \
		--query "$(QUERY)" \
		--index-dir $(INDEX_DIR) \
		--work-item-dir $(WORK_ITEM_DIR) \
		--out $(WORK_ITEM_DIR)/context-pack.md

ai-context-example:
	$(MAKE) ai-context WORK_ITEM=EXAMPLE-WI QUERY="field ui visibility flow config"

ai-context-auto:
	@AC_QUERY="$$(PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.knowledge.extract_ac_keywords --work-item $(WORK_ITEM) --top 12 --print)"; \
	echo "Auto-extracted AC keywords: $$AC_QUERY"; \
	$(MAKE) ai-context WORK_ITEM=$(WORK_ITEM) QUERY="$$AC_QUERY"

ac-coverage:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.deployment.ac_coverage_check \
		--work-item $(WORK_ITEM) \
		--work-item-dir $(WORK_ITEM_DIR) \
		--print-summary

design-lint:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.deployment.design_lint \
		--work-item $(WORK_ITEM) \
		--work-item-dir $(WORK_ITEM_DIR)

ai-clean-context:
	rm -f .ai/context/index/*.jsonl
	rm -f .ai/context/index/*summary.json
	rm -f .ai/context/work-items/*/context-sources.json
	rm -f .ai/context/work-items/*/relevant-metadata.yaml
	rm -f .ai/context/work-items/*/relevant-schema.yaml
	rm -f .ai/context/work-items/*/relevant-config-records.yaml
	rm -f .ai/context/work-items/*/relevant-knowledge.yaml

clean-ai-generated: ai-clean-context
	find .ai/outputs -type f \( -name "*.json" -o -name "*.log" \) -delete 2>/dev/null || true

ai-list-outputs:
	@echo "$(INDEX_DIR)"
	@find $(INDEX_DIR) -maxdepth 1 -type f 2>/dev/null | sort || true
	@echo ""
	@echo "$(WORK_ITEM_DIR)"
	@find $(WORK_ITEM_DIR) -maxdepth 2 -type f 2>/dev/null | sort || true

ai-check-python:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -c "import ai_workspace.configuration.workspace_config; import ai_workspace.configuration.bootstrap; import ai_workspace.configuration.doctor; import ai_workspace.indexers.index_repo_metadata; import ai_workspace.indexers.index_org_schema; import ai_workspace.indexers.index_config_records; import ai_workspace.indexers.build_context_pack; import ai_workspace.deployment.precheck_work_item; import ai_workspace.config.config_impact; import ai_workspace.config.config_pack_builder; import ai_workspace.config.config_diff; import ai_workspace.knowledge.import_knowledge; import ai_workspace.knowledge.sync_knowledge_repo; import ai_workspace.knowledge.index_knowledge; import ai_workspace.knowledge.knowledge_search; import ai_workspace.wiki.wiki_config; import ai_workspace.wiki.wiki_git; import ai_workspace.wiki.wiki_scanner; import ai_workspace.wiki.wiki_router; import ai_workspace.wiki.wiki_page_builder; import ai_workspace.wiki.wiki_publisher; import ai_workspace.docs.export_docs; import ai_workspace.mcp.salesforce_context_mcp; print('AI workspace Python imports OK')"

config-impact:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.config.config_impact \
		--work-item $(WORK_ITEM) \
		--work-item-dir $(WORK_ITEM_DIR) \
		--index-dir $(INDEX_DIR)

config-pack-skeleton:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.config.config_pack_builder \
		--work-item $(WORK_ITEM) \
		--config-impact $(WORK_ITEM_DIR)/config-impact.yaml \
		--out-dir $(CONFIG_PACK_DIR)

knowledge-sync:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.knowledge.sync_knowledge_repo \
		--repo-url "$(KB_REPO)" \
		--branch "$(KB_BRANCH)" \
		--vendor-dir "$(KB_VENDOR_DIR)" \
		--knowledge-root "$(KNOWLEDGE_ROOT)" \
		--policy "$(KNOWLEDGE_POLICY)"

knowledge-sync-dry-run:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.knowledge.sync_knowledge_repo \
		--repo-url "$(KB_REPO)" \
		--branch "$(KB_BRANCH)" \
		--vendor-dir "$(KB_VENDOR_DIR)" \
		--knowledge-root "$(KNOWLEDGE_ROOT)" \
		--policy "$(KNOWLEDGE_POLICY)" \
		--dry-run

knowledge-index:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.knowledge.index_knowledge \
		--knowledge-root "$(KNOWLEDGE_ROOT)" \
		--out "$(KNOWLEDGE_INDEX)"

knowledge-import:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.knowledge.import_knowledge \
		--source "$(KNOWLEDGE_SOURCE)" \
		--domain "$(KNOWLEDGE_DOMAIN)" \
		--title "$(KNOWLEDGE_TITLE)" \
		--owner "$(KNOWLEDGE_OWNER)" \
		$(KNOWLEDGE_IMPORT_FLAGS)

knowledge-import-manifest:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.knowledge.import_knowledge \
		--manifest "$(KNOWLEDGE_MANIFEST)" \
		$(KNOWLEDGE_IMPORT_FLAGS)

knowledge-search:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.knowledge.knowledge_search \
		--query "$(QUERY)" \
		--index "$(KNOWLEDGE_INDEX)" \
		--top-k 10

knowledge-validate:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.knowledge.validate_knowledge \
		--knowledge-root "$(KNOWLEDGE_ROOT)" \
		--schema "$(KNOWLEDGE_SCHEMA)" \
		--max-age-days $(KNOWLEDGE_MAX_AGE_DAYS) \
		--json-out "$(KNOWLEDGE_VALIDATION_JSON)" \
		--md-out "$(KNOWLEDGE_VALIDATION_MD)" \
		$(KNOWLEDGE_VALIDATE_FLAGS)

metadata-knowledge-index:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.knowledge.metadata_to_knowledge \
		--force-app-root "$(FORCE_APP_ROOT)" \
		--out "$(METADATA_KNOWLEDGE_INDEX)" \
		--summary-out "$(METADATA_KNOWLEDGE_SUMMARY)"

knowledge-graph: knowledge-index-yaml metadata-knowledge-index
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.knowledge.build_graph \
		--knowledge-root "$(KNOWLEDGE_ROOT)" \
		--index-dir "$(INDEX_DIR)" \
		--work-items-dir ".ai/context/work-items" \
		--out "$(KNOWLEDGE_GRAPH)" \
		--adjacency-cap $(KNOWLEDGE_GRAPH_ADJACENCY_CAP)

knowledge-index-yaml:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.knowledge.index_knowledge \
		--knowledge-root "$(KNOWLEDGE_ROOT)" \
		--out "$(KNOWLEDGE_INDEX)" \
		--emit-index-yaml "$(KNOWLEDGE_INDEX_YAML)"

knowledge-push-dry-run:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.knowledge.push_knowledge \
		--vendor-dir "$(KB_VENDOR_DIR)" \
		--knowledge-root "$(KNOWLEDGE_ROOT)" \
		--repo-url "$(KB_REPO)" \
		--branch "$(KB_BRANCH)" \
		--message "$(KNOWLEDGE_PUSH_MESSAGE)" \
		--dry-run

knowledge-push:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.knowledge.push_knowledge \
		--vendor-dir "$(KB_VENDOR_DIR)" \
		--knowledge-root "$(KNOWLEDGE_ROOT)" \
		--repo-url "$(KB_REPO)" \
		--branch "$(KB_BRANCH)" \
		--message "$(KNOWLEDGE_PUSH_MESSAGE)" \
		--push

wiki-dry-run:
	@test -n "$(AZURE_WIKI_REPO)" || (echo "ERROR: AZURE_WIKI_REPO is required for wiki-dry-run." >&2; exit 2)
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.wiki.wiki_publisher \
		--work-item $(WORK_ITEM) \
		--title "$(WIKI_TITLE)" \
		--source "$(WIKI_SOURCE)" \
		--repo-url "$(AZURE_WIKI_REPO)" \
		--branch "$(AZURE_WIKI_BRANCH)" \
		--vendor-dir "$(AZURE_WIKI_VENDOR_DIR)" \
		--module "$(WIKI_MODULE)" \
		--target-path "$(WIKI_TARGET_PATH)" \
		--dry-run

wiki-prepare-branch:
	@test -n "$(AZURE_WIKI_REPO)" || (echo "ERROR: AZURE_WIKI_REPO is required for wiki-prepare-branch." >&2; exit 2)
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.wiki.wiki_publisher \
		--work-item $(WORK_ITEM) \
		--title "$(WIKI_TITLE)" \
		--source "$(WIKI_SOURCE)" \
		--repo-url "$(AZURE_WIKI_REPO)" \
		--branch "$(AZURE_WIKI_BRANCH)" \
		--vendor-dir "$(AZURE_WIKI_VENDOR_DIR)" \
		--module "$(WIKI_MODULE)" \
		--target-path "$(WIKI_TARGET_PATH)" \
		--prepare-branch

wiki-push-approved:
	@test -n "$(AZURE_WIKI_REPO)" || (echo "ERROR: AZURE_WIKI_REPO is required for wiki-push-approved." >&2; exit 2)
	@test -n "$(WIKI_APPROVAL_NOTE)" || (echo "ERROR: WIKI_APPROVAL_NOTE is required for wiki-push-approved." >&2; exit 2)
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.wiki.wiki_publisher \
		--work-item $(WORK_ITEM) \
		--title "$(WIKI_TITLE)" \
		--source "$(WIKI_SOURCE)" \
		--repo-url "$(AZURE_WIKI_REPO)" \
		--branch "$(AZURE_WIKI_BRANCH)" \
		--vendor-dir "$(AZURE_WIKI_VENDOR_DIR)" \
		--module "$(WIKI_MODULE)" \
		--target-path "$(WIKI_TARGET_PATH)" \
		--prepare-branch \
		--push \
		--approved \
		--approval-note "$(WIKI_APPROVAL_NOTE)"

wiki-scan:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.wiki.wiki_scanner \
		--wiki-dir "$(AZURE_WIKI_VENDOR_DIR)" \
		--out .ai/outputs/wiki/wiki-index.json

docs-build:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.docs.export_docs \
		--check

docs-export-pdf:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.docs.export_docs

docs-pack:
	$(MAKE) docs-build
	$(MAKE) docs-export-pdf

docs-open-html:
	@echo "$(DOCS_HTML)"

wi-precheck:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.deployment.precheck_work_item \
		--work-item $(WORK_ITEM) \
		--work-item-dir $(WORK_ITEM_DIR) \
		--base-ref $(BASE_REF) \
		--out-dir $(OUT_DIR)

wi-precheck-strict:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.deployment.precheck_work_item \
		--work-item $(WORK_ITEM) \
		--work-item-dir $(WORK_ITEM_DIR) \
		--base-ref $(BASE_REF) \
		--out-dir $(OUT_DIR) \
		--fail-on-high

wi-scope-check:
	@echo "Metadata scope validation is included in wi-precheck."
	$(MAKE) wi-precheck WORK_ITEM=$(WORK_ITEM) BASE_REF=$(BASE_REF) OUT_DIR=$(OUT_DIR)

mcp-salesforce-context:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.mcp.salesforce_context_mcp \
		--index-dir $(INDEX_DIR) \
		--context-root .ai/context

mcp-smoke-test:
	@printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | \
		PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m ai_workspace.mcp.salesforce_context_mcp \
			--index-dir $(INDEX_DIR) \
			--context-root .ai/context
