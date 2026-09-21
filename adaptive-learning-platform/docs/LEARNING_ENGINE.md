# Learning Engine

## Evidence and mastery

Every attempt creates structured evidence: skill, dimension, task type, mode, difficulty, correctness, hint level, confidence, and independence. Mastery is stored separately for concept, explanation, implementation, debugging, design, and transfer. Scores are bounded estimates, not scientific probabilities.

The V1 updater is an explicit EWMA. Evidence is discounted for hints, non-independent work, and learning mode; difficulty modestly changes evidence strength. The learning rate decreases as evidence accumulates. This interface can later host BKT, IRT, or another calibrated model.

## Retrieval, spacing, and interleaving

Sessions begin with retrieval where appropriate. Review intervals start at 1, 3, 7, 14, and 30 days; strong performance advances the interval and weak performance retracts it. These are adjustable defaults, not claims of optimality. Session plans interleave older retrieval, current work, misconception rechecks, and transfer.

## Assistance and confidence

The hint ladder runs from no help through directional question, relevant concept, partial structure, partially worked step, and full explanation. Hint usage weakens evidence and contributes to `hint_dependency`. Confidence is compared with correctness; high-confidence errors create a probable misconception candidate.

## Remediation and acceleration

Repeated failure or a probable misconception triggers a short targeted explanation and a novel retest. A misconception remains active until different evidence verifies correction. Strong multidimensional evidence skips redundant instruction and moves to interleaved, ambiguous, or transfer work.

## Activity selection

Low mastery receives worked examples; moderate mastery receives interleaved application; high mastery receives transfer or acceleration. Persistent hint dependence selects faded independent practice. Two failures select remediation. Policies live in code, not hidden only in prompts.
