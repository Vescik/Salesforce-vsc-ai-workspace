<#
.SYNOPSIS
    Windows PowerShell command surface for the Salesforce AI Workspace.
.DESCRIPTION
    Run all workspace commands on Windows without requiring GNU make.
    Usage: .\scripts\workspace.ps1 <target> [parameters]
.EXAMPLE
    .\scripts\workspace.ps1 help
    .\scripts\workspace.ps1 setup
    .\scripts\workspace.ps1 doctor
    .\scripts\workspace.ps1 first-run
    .\scripts\workspace.ps1 ai-index-repo
    .\scripts\workspace.ps1 ai-index-schema -Org IntDev
    .\scripts\workspace.ps1 ai-context -WorkItem KIM-1234 -Query "invoice approval"
    .\scripts\workspace.ps1 knowledge-sync
    .\scripts\workspace.ps1 knowledge-sync-dry-run
    .\scripts\workspace.ps1 knowledge-search -Query "invoice approval"
    .\scripts\workspace.ps1 knowledge-create -KnowledgeSource ".ai/knowledge/imports/note.txt" -KnowledgeDomain "billing" -KnowledgeTitle "Invoice Rules"
    .\scripts\workspace.ps1 knowledge-validate
    .\scripts\workspace.ps1 knowledge-graph
    .\scripts\workspace.ps1 wiki-dry-run -WorkItem KIM-1234 -WikiTitle "Invoice Routing" -WikiSource "docs/architecture/KIM-1234.md"
    .\scripts\workspace.ps1 wi-precheck -WorkItem KIM-1234 -BaseRef "HEAD~1"
    .\scripts\workspace.ps1 wi-precheck-strict -WorkItem KIM-1234 -BaseRef "origin/main"
#>

param(
    [Parameter(Position = 0, Mandatory = $true)]
    [string]$Target,

    [string]$Org                  = "",
    [string]$WorkItem             = "EXAMPLE-WI",
    [string]$Query                = "field ui visibility flow config",
    [string]$IndexDir             = ".ai/context/index",
    [string]$WorkItemDir          = "",
    [string]$WorkspaceConfig      = ".ai/config/workspace.local.json",
    [string]$Registry             = "config/data-promotion/config-object-registry.yaml",
    [string]$MaskingPolicy        = "config/data-promotion/masking-policy.yaml",
    [string]$BaseRef              = "HEAD~1",
    [string]$OutDir               = ".ai/outputs/precheck",
    [string]$ConfigPackDir        = "",
    [string]$KbRepo               = "",
    [string]$KbBranch             = "",
    [string]$KbVendorDir          = "",
    [string]$KnowledgeRoot        = "",
    [string]$KnowledgePolicy      = ".ai/knowledge/sync-policy.yaml",
    [string]$KnowledgeIndex       = ".ai/context/index/knowledge-cards.jsonl",
    [string]$KnowledgeSource      = "",
    [string]$KnowledgeManifest    = ".ai/templates/knowledge-import-manifest.yaml",
    [string]$KnowledgeSchema      = ".ai/templates/schemas/knowledge-note.schema.json",
    [string]$KnowledgeValidationJson = ".ai/outputs/knowledge-import/validation-report.json",
    [string]$KnowledgeValidationMd = ".ai/outputs/knowledge-import/validation-report.md",
    [int]$KnowledgeMaxAgeDays     = 180,
    [string]$KnowledgeValidateFlags = "",
    [string]$KnowledgeDomain      = "general",
    [string]$KnowledgeTitle       = "",
    [string]$KnowledgeOwner       = "Salesforce Platform Team",
    [string]$KnowledgeImportFlags = "",
    [string]$KnowledgeSearchFlags = "",
    [string]$ForceAppRoot         = "force-app",
    [string]$MetadataKnowledgeIndex = ".ai/context/index/metadata-knowledge-cards.jsonl",
    [string]$MetadataKnowledgeSummary = ".ai/context/index/metadata-knowledge-summary.json",
    [string]$KnowledgeGraph       = ".ai/context/index/knowledge-graph.json",
    [string]$KnowledgeIndexYaml   = ".ai/context/index/knowledge-index-files.yaml",
    [int]$KnowledgeGraphAdjacencyCap = 200,
    [string]$AzureWikiRepo        = "",
    [string]$AzureWikiBranch      = "",
    [string]$AzureWikiVendorDir   = "",
    [string]$WikiTitle            = "",
    [string]$WikiSource           = "",
    [string]$WikiModule           = "",
    [string]$WikiTargetPath       = "",
    [string]$WikiApprovalNote     = "",
    [string]$DocsRoot             = "docs/workspace",
    [string]$KnowledgePushMessage = ""
)

$ErrorActionPreference = "Stop"

# ── Python detection ──────────────────────────────────────────────────────────
function Find-Python {
    if (Get-Command python3.11 -ErrorAction SilentlyContinue) { return "python3.11" }
    if (Get-Command python     -ErrorAction SilentlyContinue) { return "python" }
    return "python3"
}

$script:PythonCmd      = Find-Python
$script:PythonPathVal  = ".ai/skills/python"
$script:WorkspaceConfigData = $null

function Read-WorkspaceConfig {
    if ($null -ne $script:WorkspaceConfigData) { return $script:WorkspaceConfigData }
    $script:WorkspaceConfigData = $false
    if ($WorkspaceConfig -and (Test-Path $WorkspaceConfig)) {
        try {
            $script:WorkspaceConfigData = Get-Content -Raw -Path $WorkspaceConfig | ConvertFrom-Json
        }
        catch {
            Write-Warning "Could not read workspace config '$WorkspaceConfig': $($_.Exception.Message)"
        }
    }
    return $script:WorkspaceConfigData
}

function Get-ConfigString {
    param([string[]]$PathParts)
    $node = Read-WorkspaceConfig
    foreach ($part in $PathParts) {
        if (($null -eq $node) -or ($node -eq $false)) { return "" }
        $property = $node.PSObject.Properties[$part]
        if ($null -eq $property) { return "" }
        $node = $property.Value
    }
    if (($null -eq $node) -or ($node -eq $false)) { return "" }
    return [string]$node
}

function Get-EnvString {
    param([string]$Name)
    if (-not $Name) { return "" }
    $item = Get-Item "Env:$Name" -ErrorAction SilentlyContinue
    if ($null -eq $item) { return "" }
    return [string]$item.Value
}

function Resolve-Setting {
    param(
        [string]$CurrentValue,
        [string]$EnvName,
        [string[]]$ConfigPath,
        [string]$DefaultValue = ""
    )
    if ($CurrentValue) { return $CurrentValue }
    $envValue = Get-EnvString $EnvName
    if ($envValue) { return $envValue }
    $configValue = Get-ConfigString $ConfigPath
    if ($configValue) { return $configValue }
    return $DefaultValue
}

$Org = Resolve-Setting $Org "SF_DEV_ORG_ALIAS" @("salesforce", "default_dev_org_alias") "IntDev"
$KbRepo = Resolve-Setting $KbRepo "KB_REPO" @("knowledge_base", "repo_url") ""
$KbBranch = Resolve-Setting $KbBranch "KB_BRANCH" @("knowledge_base", "branch") "main"
$KbVendorDir = Resolve-Setting $KbVendorDir "" @("paths", "knowledge_vendor_dir") ".ai/vendor/knowledge-base"
$KnowledgeRoot = Resolve-Setting $KnowledgeRoot "" @("paths", "knowledge_root") ".ai/knowledge"
$AzureWikiRepo = Resolve-Setting $AzureWikiRepo "AZURE_WIKI_REPO" @("azure_wiki", "repo_url") ""
$AzureWikiBranch = Resolve-Setting $AzureWikiBranch "AZURE_WIKI_BRANCH" @("azure_wiki", "branch") "main"
$AzureWikiVendorDir = Resolve-Setting $AzureWikiVendorDir "AZURE_WIKI_VENDOR_DIR" @("azure_wiki", "vendor_dir") ".ai/vendor/azure-wiki"

# Computed defaults
if (-not $WorkItemDir)  { $WorkItemDir  = ".ai/context/work-items/$WorkItem" }
if (-not $ConfigPackDir){ $ConfigPackDir = "config/kimbleone-packs/$WorkItem" }
$DocsHtml = "$DocsRoot/html/index.html"

# ── Helper: run Python with PYTHONPATH set ────────────────────────────────────
function Invoke-Py {
    param([string[]]$Arguments)
    $env:PYTHONPATH = $script:PythonPathVal
    & $script:PythonCmd @Arguments
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

# ── Helper: require a non-empty parameter ─────────────────────────────────────
function Require-Param {
    param([string]$Value, [string]$Name)
    if (-not $Value) {
        Write-Error "ERROR: -$Name is required for target '$Target'."
        exit 2
    }
}

# ── Targets ───────────────────────────────────────────────────────────────────

function Invoke-Help {
    Write-Host "Copilot-only Salesforce AI Workspace — Windows commands"
    Write-Host ""
    Write-Host "Usage: .\scripts\workspace.ps1 <target> [parameters]"
    Write-Host ""
    Write-Host "Targets:"
    Write-Host "  setup"
    Write-Host "  setup-venv"
    Write-Host "  configure"
    Write-Host "  doctor"
    Write-Host "  doctor-strict"
    Write-Host "  first-run"
    Write-Host "  test"
    Write-Host "  smoke"
    Write-Host "  ai-check-python"
    Write-Host "  ai-index-repo"
    Write-Host "  ai-index-schema              -Org IntDev"
    Write-Host "  ai-index-config              -Org IntDev"
    Write-Host "  ai-index-all                 -Org IntDev"
    Write-Host "  ai-context                   -WorkItem KIM-1234 -Query 'invoice approval'"
    Write-Host "  ai-context-auto              -WorkItem KIM-1234"
    Write-Host "  ai-context-example"
    Write-Host "  ac-coverage                  -WorkItem KIM-1234"
    Write-Host "  design-lint                  -WorkItem KIM-1234"
    Write-Host "  ai-clean-context"
    Write-Host "  clean-ai-generated"
    Write-Host "  ai-list-outputs              -WorkItem KIM-1234"
    Write-Host "  config-pack-skeleton         -WorkItem KIM-1234"
    Write-Host "  knowledge-sync               [-KbRepo <git-url-or-local-path>]"
    Write-Host "  knowledge-sync-dry-run       [-KbRepo <git-url-or-local-path>]"
    Write-Host "  knowledge-index"
    Write-Host "  knowledge-create             -KnowledgeSource <file> -KnowledgeDomain <domain> -KnowledgeTitle <title>"
    Write-Host "  knowledge-create-dry-run     -KnowledgeSource <file> -KnowledgeDomain <domain> -KnowledgeTitle <title>"
    Write-Host "  knowledge-create-manifest    -KnowledgeManifest <yaml>"
    Write-Host "  knowledge-import             -KnowledgeSource <file> -KnowledgeDomain <domain> -KnowledgeTitle <title>  # alias"
    Write-Host "  knowledge-import-manifest    -KnowledgeManifest <yaml>  # alias"
    Write-Host "  knowledge-search             -Query 'invoice approval'"
    Write-Host "  knowledge-validate"
    Write-Host "  metadata-knowledge-index"
    Write-Host "  knowledge-index-yaml"
    Write-Host "  knowledge-graph"
    Write-Host "  knowledge-push-dry-run       [-KbRepo <git-url>]"
    Write-Host "  knowledge-push               [-KbRepo <git-url>]"
    Write-Host "  wiki-dry-run                 -WorkItem KIM-1234 -WikiTitle '...' -WikiSource docs/... [-AzureWikiRepo <url>]"
    Write-Host "  wiki-prepare-branch          -WorkItem KIM-1234 -WikiTitle '...' -WikiSource docs/... [-AzureWikiRepo <url>]"
    Write-Host "  wiki-push-approved           -WorkItem KIM-1234 -WikiTitle '...' -WikiSource docs/... [-AzureWikiRepo <url>] -WikiApprovalNote 'Approved by ...'"
    Write-Host "  wiki-scan                    -AzureWikiVendorDir .ai/vendor/azure-wiki"
    Write-Host "  docs-build"
    Write-Host "  docs-export-pdf"
    Write-Host "  docs-pack"
    Write-Host "  docs-open-html"
    Write-Host "  wi-precheck                  -WorkItem KIM-1234 -BaseRef HEAD~1"
    Write-Host "  wi-precheck-strict           -WorkItem KIM-1234 -BaseRef origin/main"
    Write-Host "  wi-scope-check               -WorkItem KIM-1234 -BaseRef HEAD~1"
    Write-Host "  mcp-salesforce-context"
    Write-Host "  mcp-smoke-test"
    Write-Host ""
    Write-Host "Notes:"
    Write-Host "  ai-index-schema requires Salesforce CLI auth to -Org $Org."
    Write-Host "  ai-index-config queries only enabled registry objects from $Registry."
    Write-Host "  KB and Azure Wiki commands use local config/environment defaults when URLs are omitted."
    Write-Host "  DevOps Center remains the metadata promotion mechanism; these commands do not deploy."
}

function Invoke-Setup {
    & $script:PythonCmd -m pip install -e . --quiet
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    $env:PYTHONPATH = $script:PythonPathVal
    & $script:PythonCmd -m ai_workspace.configuration.bootstrap `
        --config $WorkspaceConfig `
        --create-local-config `
        --print-next-steps
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

function Invoke-SetupVenv {
    & $script:PythonCmd -m pip install -e . --quiet
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    $env:PYTHONPATH = $script:PythonPathVal
    & $script:PythonCmd -m ai_workspace.configuration.bootstrap `
        --config $WorkspaceConfig `
        --create-local-config `
        --create-venv `
        --print-next-steps
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

function Invoke-Configure {
    & $script:PythonCmd "scripts/configure.py" `
        --config $WorkspaceConfig
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

function Invoke-Doctor {
    Invoke-Py @(
        "-m", "ai_workspace.configuration.doctor",
        "--config", $WorkspaceConfig
    )
}

function Invoke-DoctorStrict {
    Invoke-Py @(
        "-m", "ai_workspace.configuration.doctor",
        "--config", $WorkspaceConfig,
        "--strict",
        "--check-salesforce-auth",
        "--check-knowledge"
    )
}

function Invoke-FirstRun {
    Invoke-Setup
    Invoke-Doctor
    Invoke-AiIndexRepo
    Invoke-KnowledgeIndex
}

function Invoke-Test {
    Invoke-Py @(
        "-m", "unittest", "discover",
        "-s", ".ai/skills/python/tests",
        "-p", "test_*.py"
    )
}

function Invoke-Smoke {
    Invoke-AiCheckPython
    Invoke-Test
    Invoke-KnowledgeIndex
    $script:WorkItem = "EXAMPLE-WI"; $script:WorkItemDir = ".ai/context/work-items/EXAMPLE-WI"
    Invoke-AiContextExample
    Invoke-ConfigImpact
    Invoke-ConfigPackSkeleton
    $script:BaseRef = "HEAD"; Invoke-WiPrecheck
}

function Invoke-AiIndexRepo {
    Invoke-Py @(
        "-m", "ai_workspace.indexers.index_repo_metadata",
        "--repo-root", ".",
        "--out", "$IndexDir/metadata-components.jsonl"
    )
}

function Invoke-AiIndexSchema {
    Invoke-Py @(
        "-m", "ai_workspace.indexers.index_org_schema",
        "--org", $Org,
        "--namespace", "KimbleOne",
        "--out-dir", $IndexDir
    )
}

function Invoke-AiIndexConfig {
    Invoke-Py @(
        "-m", "ai_workspace.indexers.index_config_records",
        "--org", $Org,
        "--registry", $Registry,
        "--masking-policy", $MaskingPolicy,
        "--out", "$IndexDir/config-record-cards.jsonl"
    )
}

function Invoke-AiIndexAll {
    Invoke-AiIndexRepo
    Invoke-KnowledgeIndex
    Invoke-AiIndexSchema
    Invoke-AiIndexConfig
}

function Invoke-AiContext {
    Invoke-Py @(
        "-m", "ai_workspace.indexers.build_context_pack",
        "--work-item", $WorkItem,
        "--query", $Query,
        "--index-dir", $IndexDir,
        "--work-item-dir", $WorkItemDir,
        "--out", "$WorkItemDir/context-pack.md"
    )
}

function Invoke-AiContextExample {
    $script:WorkItem    = "EXAMPLE-WI"
    $script:WorkItemDir = ".ai/context/work-items/EXAMPLE-WI"
    $script:Query       = "field ui visibility flow config"
    Invoke-AiContext
}

function Invoke-AiContextAuto {
    $env:PYTHONPATH = $script:PythonPathVal
    $output = & $script:PythonCmd -m ai_workspace.knowledge.extract_ac_keywords `
        --work-item $WorkItem `
        --work-item-dir $WorkItemDir `
        --top 12 `
        --print
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    $lines = @($output) | Where-Object { $_ -and ($_ -notmatch "^WARNING:") }
    $acQuery = ($lines -join " ").Trim()
    if ($acQuery) {
        Write-Host "Auto-extracted AC keywords: $acQuery"
        $script:Query = $acQuery
    } else {
        Write-Warning "No AC keywords extracted; using -Query '$Query'."
    }
    Invoke-AiContext
}

function Invoke-AcCoverage {
    Invoke-Py @(
        "-m", "ai_workspace.deployment.ac_coverage_check",
        "--work-item", $WorkItem,
        "--work-item-dir", $WorkItemDir,
        "--print-summary"
    )
}

function Invoke-DesignLint {
    Invoke-Py @(
        "-m", "ai_workspace.deployment.design_lint",
        "--work-item", $WorkItem,
        "--work-item-dir", $WorkItemDir
    )
}

function Invoke-AiCleanContext {
    $patterns = @(
        ".ai/context/index/*.jsonl",
        ".ai/context/index/*summary.json",
        ".ai/context/work-items/*/context-sources.json",
        ".ai/context/work-items/*/relevant-metadata.yaml",
        ".ai/context/work-items/*/relevant-schema.yaml",
        ".ai/context/work-items/*/relevant-config-records.yaml",
        ".ai/context/work-items/*/relevant-knowledge.yaml"
    )
    foreach ($p in $patterns) {
        Get-Item $p -ErrorAction SilentlyContinue | Remove-Item -Force
    }
    Write-Host "Context cleaned."
}

function Invoke-CleanAiGenerated {
    Invoke-AiCleanContext
    Get-ChildItem ".ai/outputs" -Recurse -Include "*.json","*.log" -ErrorAction SilentlyContinue |
        Remove-Item -Force
    Write-Host "AI-generated outputs cleaned."
}

function Invoke-AiListOutputs {
    Write-Host $IndexDir
    Get-ChildItem $IndexDir -MaxDepth 1 -File -ErrorAction SilentlyContinue |
        Sort-Object FullName | ForEach-Object { Write-Host $_.FullName }
    Write-Host ""
    Write-Host $WorkItemDir
    Get-ChildItem $WorkItemDir -Depth 2 -File -ErrorAction SilentlyContinue |
        Sort-Object FullName | ForEach-Object { Write-Host $_.FullName }
}

function Invoke-AiCheckPython {
    $imports = @(
        "ai_workspace.configuration.workspace_config",
        "ai_workspace.configuration.bootstrap",
        "ai_workspace.configuration.doctor",
        "ai_workspace.indexers.index_repo_metadata",
        "ai_workspace.indexers.index_org_schema",
        "ai_workspace.indexers.index_config_records",
        "ai_workspace.indexers.build_context_pack",
        "ai_workspace.knowledge.extract_ac_keywords",
        "ai_workspace.deployment.ac_coverage_check",
        "ai_workspace.deployment.design_lint",
        "ai_workspace.deployment.precheck_work_item",
        "ai_workspace.config.config_impact",
        "ai_workspace.config.config_pack_builder",
        "ai_workspace.config.config_diff",
        "ai_workspace.knowledge.create_knowledge",
        "ai_workspace.knowledge.import_knowledge",
        "ai_workspace.knowledge.semantic",
        "ai_workspace.knowledge.sync_knowledge_repo",
        "ai_workspace.knowledge.index_knowledge",
        "ai_workspace.knowledge.knowledge_search",
        "ai_workspace.knowledge.validate_knowledge",
        "ai_workspace.knowledge.metadata_to_knowledge",
        "ai_workspace.knowledge.build_graph",
        "ai_workspace.wiki.wiki_config",
        "ai_workspace.wiki.wiki_git",
        "ai_workspace.wiki.wiki_scanner",
        "ai_workspace.wiki.wiki_router",
        "ai_workspace.wiki.wiki_page_builder",
        "ai_workspace.wiki.wiki_publisher",
        "ai_workspace.docs.export_docs",
        "ai_workspace.mcp.salesforce_context_mcp"
    )
    $importStr = ($imports | ForEach-Object { "import $_" }) -join "; "
    Invoke-Py @("-c", "$importStr; print('AI workspace Python imports OK')")
}

function Invoke-ConfigImpact {
    Invoke-Py @(
        "-m", "ai_workspace.config.config_impact",
        "--work-item", $WorkItem,
        "--work-item-dir", $WorkItemDir,
        "--index-dir", $IndexDir
    )
}

function Invoke-ConfigPackSkeleton {
    Invoke-Py @(
        "-m", "ai_workspace.config.config_pack_builder",
        "--work-item", $WorkItem,
        "--config-impact", "$WorkItemDir/config-impact.yaml",
        "--out-dir", $ConfigPackDir
    )
}

function Invoke-KnowledgeSync {
    Require-Param $KbRepo "KbRepo"
    Invoke-Py @(
        "-m", "ai_workspace.knowledge.sync_knowledge_repo",
        "--repo-url", $KbRepo,
        "--branch", $KbBranch,
        "--vendor-dir", $KbVendorDir,
        "--knowledge-root", $KnowledgeRoot,
        "--policy", $KnowledgePolicy
    )
}

function Invoke-KnowledgeSyncDryRun {
    Require-Param $KbRepo "KbRepo"
    Invoke-Py @(
        "-m", "ai_workspace.knowledge.sync_knowledge_repo",
        "--repo-url", $KbRepo,
        "--branch", $KbBranch,
        "--vendor-dir", $KbVendorDir,
        "--knowledge-root", $KnowledgeRoot,
        "--policy", $KnowledgePolicy,
        "--dry-run"
    )
}

function Invoke-KnowledgeIndex {
    Invoke-Py @(
        "-m", "ai_workspace.knowledge.index_knowledge",
        "--knowledge-root", $KnowledgeRoot,
        "--out", $KnowledgeIndex
    )
}

function Invoke-KnowledgeCreate {
    Require-Param $KnowledgeSource "KnowledgeSource"
    $args = @(
        "-m", "ai_workspace.knowledge.create_knowledge",
        "--source", $KnowledgeSource,
        "--domain", $KnowledgeDomain,
        "--title", $KnowledgeTitle,
        "--owner", $KnowledgeOwner
    )
    if ($KnowledgeImportFlags) {
        $args += $KnowledgeImportFlags -split "\s+"
    }
    Invoke-Py $args
}

function Invoke-KnowledgeCreateDryRun {
    $script:KnowledgeImportFlags = ($KnowledgeImportFlags + " --dry-run").Trim()
    Invoke-KnowledgeCreate
}

function Invoke-KnowledgeCreateManifest {
    $args = @(
        "-m", "ai_workspace.knowledge.create_knowledge",
        "--manifest", $KnowledgeManifest
    )
    if ($KnowledgeImportFlags) {
        $args += $KnowledgeImportFlags -split "\s+"
    }
    Invoke-Py $args
}

function Invoke-KnowledgeImport {
    Invoke-KnowledgeCreate
}

function Invoke-KnowledgeImportManifest {
    Invoke-KnowledgeCreateManifest
}

function Invoke-KnowledgeSearch {
    $args = @(
        "-m", "ai_workspace.knowledge.knowledge_search",
        "--query", $Query,
        "--index", $KnowledgeIndex,
        "--top-k", "10"
    )
    if ($KnowledgeSearchFlags) {
        $args += $KnowledgeSearchFlags -split "\s+"
    }
    Invoke-Py $args
}

function Invoke-KnowledgeValidate {
    $args = @(
        "-m", "ai_workspace.knowledge.validate_knowledge",
        "--knowledge-root", $KnowledgeRoot,
        "--schema", $KnowledgeSchema,
        "--max-age-days", [string]$KnowledgeMaxAgeDays,
        "--json-out", $KnowledgeValidationJson,
        "--md-out", $KnowledgeValidationMd
    )
    if ($KnowledgeValidateFlags) {
        $args += $KnowledgeValidateFlags -split "\s+"
    }
    Invoke-Py $args
}

function Invoke-MetadataKnowledgeIndex {
    Invoke-Py @(
        "-m", "ai_workspace.knowledge.metadata_to_knowledge",
        "--force-app-root", $ForceAppRoot,
        "--out", $MetadataKnowledgeIndex,
        "--summary-out", $MetadataKnowledgeSummary
    )
}

function Invoke-KnowledgeIndexYaml {
    Invoke-Py @(
        "-m", "ai_workspace.knowledge.index_knowledge",
        "--knowledge-root", $KnowledgeRoot,
        "--out", $KnowledgeIndex,
        "--emit-index-yaml", $KnowledgeIndexYaml
    )
}

function Invoke-KnowledgeGraph {
    Invoke-KnowledgeIndexYaml
    Invoke-MetadataKnowledgeIndex
    Invoke-Py @(
        "-m", "ai_workspace.knowledge.build_graph",
        "--knowledge-root", $KnowledgeRoot,
        "--index-dir", $IndexDir,
        "--work-items-dir", ".ai/context/work-items",
        "--out", $KnowledgeGraph,
        "--adjacency-cap", [string]$KnowledgeGraphAdjacencyCap
    )
}

function Invoke-KnowledgePushDryRun {
    Require-Param $KbRepo "KbRepo"
    $a = @(
        "-m", "ai_workspace.knowledge.push_knowledge",
        "--vendor-dir", $KbVendorDir,
        "--knowledge-root", $KnowledgeRoot,
        "--repo-url", $KbRepo,
        "--branch", $KbBranch,
        "--dry-run"
    )
    if ($KnowledgePushMessage) { $a += "--message", $KnowledgePushMessage }
    Invoke-Py $a
}

function Invoke-KnowledgePush {
    Require-Param $KbRepo "KbRepo"
    $a = @(
        "-m", "ai_workspace.knowledge.push_knowledge",
        "--vendor-dir", $KbVendorDir,
        "--knowledge-root", $KnowledgeRoot,
        "--repo-url", $KbRepo,
        "--branch", $KbBranch,
        "--push"
    )
    if ($KnowledgePushMessage) { $a += "--message", $KnowledgePushMessage }
    Invoke-Py $a
}

function Invoke-WikiDryRun {
    Require-Param $AzureWikiRepo "AzureWikiRepo"
    Invoke-Py @(
        "-m", "ai_workspace.wiki.wiki_publisher",
        "--work-item", $WorkItem,
        "--title", $WikiTitle,
        "--source", $WikiSource,
        "--repo-url", $AzureWikiRepo,
        "--branch", $AzureWikiBranch,
        "--vendor-dir", $AzureWikiVendorDir,
        "--module", $WikiModule,
        "--target-path", $WikiTargetPath,
        "--dry-run"
    )
}

function Invoke-WikiPrepareBranch {
    Require-Param $AzureWikiRepo "AzureWikiRepo"
    Invoke-Py @(
        "-m", "ai_workspace.wiki.wiki_publisher",
        "--work-item", $WorkItem,
        "--title", $WikiTitle,
        "--source", $WikiSource,
        "--repo-url", $AzureWikiRepo,
        "--branch", $AzureWikiBranch,
        "--vendor-dir", $AzureWikiVendorDir,
        "--module", $WikiModule,
        "--target-path", $WikiTargetPath,
        "--prepare-branch"
    )
}

function Invoke-WikiPushApproved {
    Require-Param $AzureWikiRepo    "AzureWikiRepo"
    Require-Param $WikiApprovalNote "WikiApprovalNote"
    Invoke-Py @(
        "-m", "ai_workspace.wiki.wiki_publisher",
        "--work-item", $WorkItem,
        "--title", $WikiTitle,
        "--source", $WikiSource,
        "--repo-url", $AzureWikiRepo,
        "--branch", $AzureWikiBranch,
        "--vendor-dir", $AzureWikiVendorDir,
        "--module", $WikiModule,
        "--target-path", $WikiTargetPath,
        "--prepare-branch",
        "--push",
        "--approved",
        "--approval-note", $WikiApprovalNote
    )
}

function Invoke-WikiScan {
    Invoke-Py @(
        "-m", "ai_workspace.wiki.wiki_scanner",
        "--wiki-dir", $AzureWikiVendorDir,
        "--out", ".ai/outputs/wiki/wiki-index.json"
    )
}

function Invoke-DocsBuild {
    Invoke-Py @("-m", "ai_workspace.docs.export_docs", "--check")
}

function Invoke-DocsExportPdf {
    Invoke-Py @("-m", "ai_workspace.docs.export_docs")
}

function Invoke-DocsPack {
    Invoke-DocsBuild
    Invoke-DocsExportPdf
}

function Invoke-DocsOpenHtml {
    Write-Host $DocsHtml
    if (Test-Path $DocsHtml) {
        Start-Process $DocsHtml
    }
}

function Invoke-WiPrecheck {
    Invoke-Py @(
        "-m", "ai_workspace.deployment.precheck_work_item",
        "--work-item", $WorkItem,
        "--work-item-dir", $WorkItemDir,
        "--base-ref", $BaseRef,
        "--out-dir", $OutDir
    )
}

function Invoke-WiPrecheckStrict {
    Invoke-Py @(
        "-m", "ai_workspace.deployment.precheck_work_item",
        "--work-item", $WorkItem,
        "--work-item-dir", $WorkItemDir,
        "--base-ref", $BaseRef,
        "--out-dir", $OutDir,
        "--fail-on-high"
    )
}

function Invoke-WiScopeCheck {
    Write-Host "Metadata scope validation is included in wi-precheck."
    Invoke-WiPrecheck
}

function Invoke-McpSalesforceContext {
    Invoke-Py @(
        "-m", "ai_workspace.mcp.salesforce_context_mcp",
        "--index-dir", $IndexDir,
        "--context-root", ".ai/context"
    )
}

function Invoke-McpSmokeTest {
    $json = '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
    $env:PYTHONPATH = $script:PythonPathVal
    $json | & $script:PythonCmd -m ai_workspace.mcp.salesforce_context_mcp `
        --index-dir $IndexDir `
        --context-root ".ai/context"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

# ── Dispatch ──────────────────────────────────────────────────────────────────

switch ($Target) {
    "help"                    { Invoke-Help }
    "setup"                   { Invoke-Setup }
    "setup-venv"              { Invoke-SetupVenv }
    "configure"               { Invoke-Configure }
    "doctor"                  { Invoke-Doctor }
    "doctor-strict"           { Invoke-DoctorStrict }
    "first-run"               { Invoke-FirstRun }
    "test"                    { Invoke-Test }
    "smoke"                   { Invoke-Smoke }
    "ai-check-python"         { Invoke-AiCheckPython }
    "ai-index-repo"           { Invoke-AiIndexRepo }
    "ai-index-schema"         { Invoke-AiIndexSchema }
    "ai-index-config"         { Invoke-AiIndexConfig }
    "ai-index-all"            { Invoke-AiIndexAll }
    "ai-context"              { Invoke-AiContext }
    "ai-context-auto"         { Invoke-AiContextAuto }
    "ai-context-example"      { Invoke-AiContextExample }
    "ac-coverage"             { Invoke-AcCoverage }
    "design-lint"             { Invoke-DesignLint }
    "ai-clean-context"        { Invoke-AiCleanContext }
    "clean-ai-generated"      { Invoke-CleanAiGenerated }
    "ai-list-outputs"         { Invoke-AiListOutputs }
    "config-impact"           { Invoke-ConfigImpact }
    "config-pack-skeleton"    { Invoke-ConfigPackSkeleton }
    "knowledge-sync"          { Invoke-KnowledgeSync }
    "knowledge-sync-dry-run"  { Invoke-KnowledgeSyncDryRun }
    "knowledge-index"         { Invoke-KnowledgeIndex }
    "knowledge-create"        { Invoke-KnowledgeCreate }
    "knowledge-create-dry-run" { Invoke-KnowledgeCreateDryRun }
    "knowledge-create-manifest" { Invoke-KnowledgeCreateManifest }
    "knowledge-import"        { Invoke-KnowledgeImport }
    "knowledge-import-manifest" { Invoke-KnowledgeImportManifest }
    "knowledge-search"        { Invoke-KnowledgeSearch }
    "knowledge-validate"      { Invoke-KnowledgeValidate }
    "metadata-knowledge-index" { Invoke-MetadataKnowledgeIndex }
    "knowledge-index-yaml"    { Invoke-KnowledgeIndexYaml }
    "knowledge-graph"         { Invoke-KnowledgeGraph }
    "knowledge-push-dry-run"  { Invoke-KnowledgePushDryRun }
    "knowledge-push"          { Invoke-KnowledgePush }
    "wiki-dry-run"            { Invoke-WikiDryRun }
    "wiki-prepare-branch"     { Invoke-WikiPrepareBranch }
    "wiki-push-approved"      { Invoke-WikiPushApproved }
    "wiki-scan"               { Invoke-WikiScan }
    "docs-build"              { Invoke-DocsBuild }
    "docs-export-pdf"         { Invoke-DocsExportPdf }
    "docs-pack"               { Invoke-DocsPack }
    "docs-open-html"          { Invoke-DocsOpenHtml }
    "wi-precheck"             { Invoke-WiPrecheck }
    "wi-precheck-strict"      { Invoke-WiPrecheckStrict }
    "wi-scope-check"          { Invoke-WiScopeCheck }
    "mcp-salesforce-context"  { Invoke-McpSalesforceContext }
    "mcp-smoke-test"          { Invoke-McpSmokeTest }
    default {
        Write-Error "Unknown target: '$Target'. Run: .\scripts\workspace.ps1 help"
        exit 1
    }
}
