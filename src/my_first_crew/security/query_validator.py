import re
from dataclasses import dataclass


BLOCKED_SQL_TOKENS = (
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "merge",
    "truncate",
    "exec",
    "execute",
    "grant",
    "revoke",
    "attach",
    "pragma",
)


@dataclass(frozen=True)
class QueryValidationResult:
    ok: bool
    sql: str
    reason: str = ""


def normalize_sql(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip()).strip()


def validate_readonly_query(sql: str, allow_with: bool = True) -> QueryValidationResult:
    compact = normalize_sql(sql).rstrip(";")
    lowered = compact.lower()

    if not compact:
        return QueryValidationResult(False, compact, "SQL rỗng.")

    if ";" in compact:
        return QueryValidationResult(False, compact, "Không cho phép nhiều statement trong một lần gọi.")

    starts_ok = lowered.startswith("select ")
    if allow_with:
        starts_ok = starts_ok or lowered.startswith("with ")
    if not starts_ok:
        return QueryValidationResult(False, compact, "Chỉ cho phép SELECT hoặc WITH read-only.")

    for token in BLOCKED_SQL_TOKENS:
        if re.search(rf"\b{re.escape(token)}\b", lowered):
            return QueryValidationResult(False, compact, f"Không cho phép token SQL nguy hiểm: {token}.")

    if re.search(r"\bsp_[a-z0-9_]+\b", lowered):
        return QueryValidationResult(False, compact, "Không cho phép gọi stored procedure hệ thống.")

    return QueryValidationResult(True, compact)


def safe_identifier(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?", value.strip()))
