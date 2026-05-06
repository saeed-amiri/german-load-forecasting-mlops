"""
Validate configs for github actions workflow.
"""

import json
import sys
import traceback
from pathlib import Path

REPORT_PATH = Path(".github/reports/config_validation_report.txt")
REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

result_lines = []
success = True


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))


try:
    from .main import PipelineConfig, load_config

    result_lines.append("Imports succeeded.")
except Exception:
    result_lines.append("Import failed:")
    result_lines.append(traceback.format_exc())
    success = False


if success:
    try:
        config: PipelineConfig = load_config(config_name="config", start_file=Path(__file__))

        result_lines.append("Config loaded successfully.")

        if getattr(config, "runtime", None) is None:
            result_lines.append("runtime is None")
            success = False

        all_attributes = json.dumps(config.model_dump(), indent=4, default=str)
        result_lines.append(f"\nConfig contents:\n{all_attributes}")

    except Exception:
        result_lines.append("Config validation failed:")
        result_lines.append(traceback.format_exc())
        success = False


REPORT_PATH.write_text("\n".join(result_lines), encoding="utf-8")


if not success:
    sys.exit(1)
