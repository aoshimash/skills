# Evaluation Test Cases

## Test Case 1: Simple Feature Design

**Input:** "ユーザー検索機能を追加したい"

**Expected behavior:**
1. Phase 1 (Research): Investigates existing user model, API patterns, search infrastructure. Writes research file.
2. Phase 2 (Design): Asks clarifying questions (search fields, pagination, performance). Proposes approaches. Writes plan with task breakdown.
3. Phase 3 (Annotation): Prompts user to annotate plan. Addresses annotations. Each task passes boring implementation test.
4. Phase 4 (Issue Creation): Creates parent issue + sub-issues with dependencies. Cleans up local files.

**Verification:**
- [ ] Research file contains relevant file paths and architecture analysis
- [ ] Plan has concrete code examples, not placeholders
- [ ] Each sub-issue is independently implementable
- [ ] Dependencies form a valid DAG
- [ ] Local plan/research files are deleted after issue creation

## Test Case 2: Complex Multi-Component Feature

**Input:** "認証システムをOAuth2に移行したい"

**Expected behavior:**
1. Research: Investigates current auth, session management, middleware, all auth-dependent routes.
2. Design: Multiple approach options (gradual migration vs big bang, library choices). Task breakdown includes migration steps, backward compatibility.
3. Annotation: Multiple rounds expected for a complex feature.
4. Issues: Parent + sub-issues with careful dependency ordering (infra first, then migration, then cleanup).

**Verification:**
- [ ] Research identifies ALL files touching authentication
- [ ] Design presents migration strategy options with trade-offs
- [ ] Tasks have correct dependency ordering (no circular deps)
- [ ] Sub-issues include rollback considerations where appropriate
- [ ] No sub-issue requires design judgment to implement

## Test Case 3: Bug-Driven Design

**Input:** "ログインが遅い。調査して改善計画を立てて"

**Expected behavior:**
1. Research: Profiles login flow, identifies bottlenecks, checks monitoring/logging.
2. Design: Based on findings, proposes performance improvements as tasks.
3. Issues: Each improvement is a separate sub-issue with measurable acceptance criteria.

**Verification:**
- [ ] Research includes profiling data or file-level analysis of the login flow
- [ ] Acceptance criteria include measurable performance targets
- [ ] Tasks are ordered by impact (highest impact first, lowest dependency first)

## Test Case 4: Cross-Platform (Backlog + GitHub)

**Input:** "Backlogで管理しているプロジェクトで新機能を設計したい"

**Expected behavior:**
1. Detects Backlog as issue tracker from CLAUDE.md or user input.
2. Uses `bee` CLI for issue creation.
3. Handles Backlog's parent-child issue structure.
4. Mentions dependencies in issue body (Backlog lacks built-in blocking).

**Verification:**
- [ ] Correct platform detection
- [ ] Uses `bee issue create` with `--parent` flag
- [ ] Dependencies noted in issue body since Backlog lacks blocking feature
- [ ] Priority is confirmed with user (Backlog has built-in priority levels)

## Test Case 5: Annotation Cycle Depth

**Input:** User provides annotations that change the fundamental approach

**Setup:** After plan is written, user annotates with `<!-- NOTE: completely different approach, use X instead of Y -->`

**Expected behavior:**
1. Claude reads the annotation and rewrites the affected tasks.
2. Code examples are updated to reflect the new approach.
3. Dependencies are rechecked (approach change may alter dependency graph).
4. Boring implementation test is re-run on all affected tasks.

**Verification:**
- [ ] Annotation is fully addressed (not partially)
- [ ] Code examples match the new approach
- [ ] Dependency graph is updated if needed
- [ ] No stale references to the old approach remain

---

## Evaluation Log

Record results here after each evaluation run.

| Date | Case # | Criteria passed | Criteria failed | Notes | SKILL.md revision needed? |
|------|--------|-----------------|-----------------|-------|---------------------------|
