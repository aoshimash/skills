# Evaluation Test Cases

## Case 1: Mixed comments — implement + reject + create issue

**Setup**: PR with 3 comment groups:
1. Bot (CodeClimate): "Method `processData` has cognitive complexity of 15 (threshold: 10)"
2. Human reviewer: "This variable name `d` is unclear. Could you rename it to `durationMs`?"
3. Human reviewer: "The error message doesn't include the original error. Should propagate it."
   + Same from another human: "Agree, we need the cause in the error chain."

**Expected behavior**:
- Group 1: Bot complexity warning → user decides to reject (keeping it for now)
- Group 2: Rename variable → user decides to implement
- Group 3: Two humans, same point → shown as one group → user decides to implement
- Commits made, replies drafted
- Bot reply: no thanks, factual ("Acknowledged. Keeping complexity at 15 for now due to [reason].")
- Human replies: brief thanks + what was done

---

## Case 2: Out-of-scope valid suggestion

**Setup**: PR adding a new API endpoint. One reviewer comments:
"While you're here, the auth middleware is missing rate limiting. This could be a security issue."

**Expected behavior**:
- Skill identifies this as potentially out of scope for the current PR
- Presents it to user as "valid point but outside this PR's scope" option
- User chooses "Create Issue"
- Issue created linking back to the PR comment
- Reply posted: "Good catch — this is outside the scope of this PR. Created #42 to track rate limiting on the auth middleware."

---

## Case 3: Purely informational comments — no reply needed

**Setup**: PR with comments:
1. GitHub Actions bot: "Coverage report: 87.3% (+0.2%)"
2. Dependabot: "This PR resolves 2 security advisories"
3. Human: "LGTM! Great work 🎤"

**Expected behavior**:
- All three filtered out as not requiring a response
- Skill reports: "No actionable comments found."

---

## Case 4: No PR found

**Setup**: User is on `main` branch with no open PR.

**Expected behavior**:
- Skill detects no PR for current branch
- Asks user for PR number or URL via AskUserQuestion
- Continues after user provides it

---

## Evaluation Log

| Date | Case | Result | Notes |
|------|------|--------|-------|
| 2026-03-22 | Main flow (PR #41) | with_skill 100% / without_skill 43% | Real Devin bot reviewed the PR, providing actual bot data for testing |
| 2026-03-22 | No-PR detection | with_skill 100% / without_skill 50% | without_skill detected no PR but didn't offer structured next step |
