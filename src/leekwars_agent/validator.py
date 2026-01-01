"""LeekScript code validator."""

from dataclasses import dataclass
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
