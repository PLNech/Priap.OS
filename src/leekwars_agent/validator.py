"""LeekScript code validator."""

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Error codes from LeekScript compiler
ERROR_CODES = {
    33: "undefined_reference",
    35: "unused_variable",
    # Add more as we discover them
}


@dataclass
class ValidationError:
    """A validation error from the LeekScript compiler."""
    ai_id: int
    line_start: int
    col_start: int
    line_end: int
    col_end: int
    error_code: int
    context: list[str]
    severity: int = 0

    @property
    def error_name(self) -> str:
        return ERROR_CODES.get(self.error_code, f"error_{self.error_code}")

    def format(self, code: str = None) -> str:
        """Format error for display."""
        msg = f"L{self.line_start}:{self.col_start}-{self.col_end} [{self.error_name}]"
        if self.context:
            msg += f" {', '.join(self.context)}"

        # Show code snippet if provided
        if code:
            lines = code.split('\n')
            if 0 <= self.line_start - 1 < len(lines):
                line = lines[self.line_start - 1]
                msg += f"\n  {self.line_start}| {line}"
                # Underline the error
                pointer = " " * (len(str(self.line_start)) + 2 + self.col_start) + "^" * max(1, self.col_end - self.col_start)
                msg += f"\n  {pointer}"

        return msg


def parse_save_result(result: dict) -> list[ValidationError]:
    """Parse errors from ai/save response."""
    errors = []

    # result format: {"result": {"ai_id": [[error_tuple], ...]}, "modified": timestamp}
    for ai_id, error_list in result.get("result", {}).items():
        for error in error_list:
            if len(error) >= 7:
                errors.append(ValidationError(
                    severity=error[0],
                    ai_id=error[1],
                    line_start=error[2],
                    col_start=error[3],
                    line_end=error[4],
                    col_end=error[5],
                    error_code=error[6],
                    context=error[7] if len(error) > 7 else [],
                ))

    return errors


def validate_code(api, ai_id: int, code: str) -> tuple[bool, list[ValidationError]]:
    """
    Validate LeekScript code by saving it and checking for errors.

    Returns (is_valid, errors).
    """
    result = api.save_ai(ai_id, code)
    errors = parse_save_result(result)

    # Filter to only actual errors (severity 0), not warnings
    actual_errors = [e for e in errors if e.severity == 0 and e.error_code == 33]

    return len(actual_errors) == 0, errors


def format_validation_report(code: str, errors: list[ValidationError]) -> str:
    """Format a full validation report."""
    if not errors:
        return "OK - No errors found"

    lines = [f"Found {len(errors)} issue(s):\n"]
    for error in errors:
        lines.append(error.format(code))
        lines.append("")

    return "\n".join(lines)


# --- Local validation using Java generator ---

GENERATOR_PATH = Path(__file__).parent.parent.parent / "tools" / "leek-wars-generator"


@dataclass
class LocalValidationResult:
    """Result from local Java validation."""

    success: bool
    errors: list[ValidationError]
    raw_output: str


def validate_locally(file_path: Path | str) -> LocalValidationResult:
    """
    Validate a LeekScript file using the local Java generator.

    Requires: Java 21+, generator.jar built in tools/leek-wars-generator

    Returns LocalValidationResult with success flag and parsed errors.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    generator_jar = GENERATOR_PATH / "generator.jar"
    if not generator_jar.exists():
        raise FileNotFoundError(
            f"generator.jar not found at {generator_jar}. "
            "Build with: cd tools/leek-wars-generator && ./gradlew jar"
        )

    # Copy file to generator directory (it expects files relative to cwd)
    temp_file = GENERATOR_PATH / file_path.name
    shutil.copy(file_path, temp_file)

    try:
        result = subprocess.run(
            ["java", "-jar", "generator.jar", "--analyze", "--verbose", file_path.name],
            cwd=GENERATOR_PATH,
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout + result.stderr
        success = "Analyze success!" in output

        # Parse error JSON from output (last line typically)
        errors = []
        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("[[") and line.endswith("]]"):
                try:
                    error_data = json.loads(line)
                    for err in error_data:
                        if len(err) >= 7:
                            errors.append(
                                ValidationError(
                                    severity=err[0],
                                    ai_id=err[1],
                                    line_start=err[2],
                                    col_start=err[3],
                                    line_end=err[4],
                                    col_end=err[5],
                                    error_code=err[6],
                                    context=err[7] if len(err) > 7 else [],
                                )
                            )
                except json.JSONDecodeError:
                    pass

        return LocalValidationResult(success=success, errors=errors, raw_output=output)

    finally:
        # Clean up temp file
        if temp_file.exists():
            temp_file.unlink()
