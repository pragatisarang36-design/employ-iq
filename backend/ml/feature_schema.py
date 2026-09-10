"""Versioned feature contract shared by model training and inference."""

FEATURE_SCHEMA_VERSION = "v1.0"
FEATURE_NAMES = (
    "cgpa",
    "internships_count",
    "projects_count",
    "certifications_count",
    "coding_score",
    "aptitude_score",
    "communication_score",
    "logical_score",
    "backlogs",
    "extracurricular_score",
)

FEATURE_LABELS = {
    "cgpa": "CGPA", "internships_count": "Internship experience",
    "projects_count": "Projects completed", "certifications_count": "Certifications",
    "coding_score": "Coding assessment", "aptitude_score": "Aptitude score",
    "communication_score": "Communication assessment", "logical_score": "Logical reasoning assessment",
    "backlogs": "Current backlogs", "extracurricular_score": "Extracurricular score",
}


def vector_from_snapshot(snapshot: dict) -> list[float]:
    """Validate and order a raw M2 feature snapshot for the approved model."""
    features = snapshot.get("features", snapshot)
    if snapshot.get("feature_schema_version") not in (None, FEATURE_SCHEMA_VERSION):
        raise ValueError("The feature snapshot schema is incompatible with the active model.")

    aliases = {"backlogs": "current_backlogs"}
    values = []
    for name in FEATURE_NAMES:
        raw = features.get(name, features.get(aliases.get(name)))
        if raw is None:
            raise ValueError(f"Required model feature '{name}' is missing.")
        try:
            values.append(float(raw))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Model feature '{name}' must be numeric.") from exc
    return values
