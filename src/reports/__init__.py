"""GenAI report generation layer (Bryan's scope).

Structured report schemas, prompt engineering, confidence calibration,
report generation, and quality evaluation for the radiology
second-opinion pipeline. See:

- `schemas.py`      — Task 4.7 (Pydantic report models)
- `prompts.py`       — Task 4.8 (prompt engineering)
- `calibration.py`   — Task 5.7 (confidence calibration & uncertainty)
- `generator.py`     — Tasks 5.8 / 5.9 / 6.10 (report generation pipeline,
                        differential ranking, guideline references)
- `style.py`         — Task 5.10 (radiology report register)
- `evaluation.py`    — Tasks 6.9 / 7.8 (report quality evaluation)
"""

from src.reports.generator import generate_report
from src.reports.schemas import RadiologyReport

__all__ = ["generate_report", "RadiologyReport"]
