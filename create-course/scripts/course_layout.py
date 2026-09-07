"""Shared layout policy for newly generated starter courses."""

STARTER_CORE_FILES = {
    "README.md", "TODAY.md", "AGENTS.md", "CLAUDE.md",
    "curriculum/BASELINE_DIAGNOSTIC.md", "curriculum/SKILL_MAP.md",
    "curriculum/skill-tracker.csv", "curriculum/modules/M00-calibration.md",
    "practice/EVIDENCE.md", "tracking/ROADMAP.md", "tracking/DASHBOARD.md",
    "tracking/BACKLOG.md", "tracking/study-log.csv", "resources/SOURCES.md",
    "resources/source-lock.csv",
}


def starter_files(week_id: str) -> set[str]:
    return STARTER_CORE_FILES | {f"tracking/{week_id}.md"}
