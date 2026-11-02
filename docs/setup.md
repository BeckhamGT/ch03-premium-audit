# Initial setup — 2026-11-02

Source: `GitRollTraining/ch03-premium-audit`, forked to `BeckhamGT/ch03-premium-audit`. `origin` points to the learner fork; `upstream` points to the training repository. The assignment PDF is preserved in the repository root.

Scope of this stage: repository and coding capture setup only. No stakeholder interview, classification implementation, payroll decision or employer output has been created.

Entire is installed and enabled for Codex with Git-ref checkpoints. `.entire/settings.local.json` selects `origin` for checkpoint pushes and stays untracked. `.codex/hooks.json` contains the seven generated lifecycle hooks. The learner approved the hooks through `/hooks`. After restarting Codex, automatic session-start and turn-start events were observed on 2026-11-02 at 12:30 America/New_York; the session became active and its native transcript included the new verification request. This setup chat can be preserved using `entire session attach <actual-session-id> --agent codex --force`; attachment is a genuine transcript snapshot, not proof that future hooks fire.

## Before the stakeholder interview

Hook approval and post-restart live capture have been verified with `entire status`, `entire doctor`, lifecycle logs and the native transcript. Verify commit-linked checkpoints as coding progresses. Keep recording active during later coding. The learner conducts the interview through the facilitator's channel, with their own questions, within the course limit of at most three conversations. Save the original complete Markdown export of each session under `interviews/` and commit it unchanged.

## Requirement map

| Requirement / source | Planned location or procedure | State |
|---|---|---|
| PDF: reusable Skill | `skills/class-code-assistant/SKILL.md` and supporting code | Pending interview and sources |
| PDF/README: source files and company rules | Read auditor-provided locations during each run; company codes govern | Locations pending learner interview |
| PDF: six employer CSVs | `deliverables/codes/<employer>.csv`; exact columns `class_code,payroll_allocated,rationale_ref`; USD cents; no zero-payroll rows | Pending |
| PDF: employer confirmation questions | `deliverables/audit-questions.md` | Pending source analysis |
| PDF: allocations, differences, every adjustment and supporting records | `deliverables/audit-report.md` | Pending |
| PDF: learner-owned split decisions and record basis | Actual captured coding conversation | Pending learner review of evidence |
| PDF/README: authentic interviews | `interviews/*.md`, one final complete export per session | Not started |
| PDF: real coding-session evidence | Entire checkpoint and native transcript; verify exact submitted revision later | Setup attachment and post-restart automatic capture verified; final submitted revision remains to verify |
| PDF/README: rerun and verification instructions | `README.md` | Runtime selection follows interview |

No payroll rounding, source precedence or classification exception rule is inferred at setup. No rates or premium quoting are in scope. Review unknown business definitions after the authentic interview and source review.

Skills used: awesome-skills (live catalog checked; no Entire-specific match), PDF (assignment extraction), apprentice-workspace setup (new repository scaffold), and writing-for-agents (project instruction pointers). Existing prior-project submissions were read only.

## Verified setup capture

Entire checkpoint `01M6EM2Z22TFCB26RRWKBZNSH1` contains the actual Codex session `01a19d3d-525c-7f30-9971-c3ebca144b18`. Its native transcript snapshot was parsed successfully: 129 JSONL records, 618320 bytes, including the learner setup request. This verifies the supported attachment snapshot at that point, not automatic future capture or final-revision completeness. The setup commit carries an `Entire-Checkpoint` trailer. The subsequent post-restart verification observed genuine automatic lifecycle events; the live transcript snapshot parsed successfully with 236 JSONL records, 881745 bytes and the current verification request. These observations verify this root session; delegated-session capture and final submission completeness are not claimed.

The apprentice workspace scaffold was created locally without replacing existing files. It remains uncommitted, following the setup skill's instruction to leave workspace publication to a separately approved normal commit. Assignment artifacts use the required repository paths.

The verification commit did not automatically receive an Entire checkpoint trailer. The resumed session state retains `attached_manually: true` and no worktree field from the initial attachment. Live hook events and transcript access are verified, but automatic commit linkage for this resumed session remains unverified. Same-worktree adoption was rejected by Entire as unnecessary; no session state was edited or removed. Verify a fresh session's commit-linked checkpoint before relying on automatic linkage for implementation.
