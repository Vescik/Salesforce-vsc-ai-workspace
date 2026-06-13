# Pre-Promote Check

## Purpose

Use this checklist before a DevOps Center promote. It gathers evidence for human review and release approval. It does not execute deployment, approve production release automatically, or apply config records.

DevOps Center is the official Salesforce metadata promotion mechanism. IntDev is not the source of truth.

## Checklist

### Work Item

- Work Item ID:
- Work Item title:
- Acceptance criteria reviewed:
- Owner/reviewer:

### Branch

- Current branch:
- DevOps Center Work Item branch confirmed:
- Target environment branch placeholder:
- Branch name source:

### Target Environment

- Target environment:
- Environment map reviewed:
- Full Copy sandbox considerations reviewed:
- DevOps Center status:

### Metadata Summary

- Metadata components changed:
- Metadata scope matches Work Item:
- Managed package internals untouched:
- Hardcoded Salesforce ID candidates reviewed:
- Salesforce validation status:

### Precheck Report

- Local precheck command:
- Precheck output path:
- Blocking findings:
- Warnings:
- Open follow-ups:

### Config Impact

- Config impact relevant:
- Config impact status:
- Config pack skeleton status if required:
- Config sidecar owner:
- Config sidecar approval needed:
- Production config apply status:

Production config apply is not implemented in this workspace and requires future controlled tooling/manual approval.

### QA Readiness

- QA how-to-test draft path:
- Acceptance criteria coverage:
- Negative/regression tests:
- Environment-specific test data assumptions:
- QA owner approval:

### Documentation Readiness

- Technical documentation path:
- Release notes path if applicable:
- Support/rollback notes:
- Known risks documented:

### Manual Approvals

- Solution owner:
- Salesforce architect/admin:
- QA owner:
- Release/system owner:
- Config sidecar approver if required:

### Go/No-Go Recommendation

- Recommendation:
- Reason:
- Missing evidence:
- Manual approval conditions:
