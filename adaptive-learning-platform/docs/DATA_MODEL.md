# Data Model

Queryable learning state is normalized across `User`, `LearningMission`, `Course`, `CourseVersion`, `Phase`, `Skill`, `SkillDependency`, `Lesson`, `Activity`, `Assessment`, `AssessmentAttempt`, `AssessmentEvidence`, `SkillMastery`, `Misconception`, `HintUsage`, `ReviewSchedule`, `Source`, `SourceReference`, `LearningSession`, `Project`, `ProjectSubmission`, `ProjectEvaluation`, `Viva`, `VivaQuestion`, and `VivaResponse`.

JSON is restricted to flexible payloads such as activity content, rubrics, generated manifests, and answer artifacts. Ownership, timestamps, dimensions, confidence, assistance, source authority, freshness, review dates, and evaluation totals remain explicit columns.

The seeded demo creates the learner and fine-tuning skill state reproducibly. Course compiler output is validated independently before persistence.
