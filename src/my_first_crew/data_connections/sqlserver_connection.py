import os
from dataclasses import dataclass
from urllib.parse import quote_plus

import pyodbc


@dataclass(frozen=True)
class SQLServerProfile:
    host: str
    database: str
    user: str
    password: str
    port: int = 1433
    driver: str = "ODBC Driver 18 for SQL Server"
    encrypt: str = "yes"
    trust_certificate: str = "no"
    timeout: int = 30
    max_rows: int = 500


def load_sqlserver_profile() -> SQLServerProfile:
    return SQLServerProfile(
        host=os.getenv("SQLSERVER_HOST", ""),
        port=int(os.getenv("SQLSERVER_PORT", "1433")),
        database=os.getenv("SQLSERVER_DATABASE", ""),
        user=os.getenv("SQLSERVER_USER", ""),
        password=os.getenv("SQLSERVER_PASSWORD", ""),
        driver=os.getenv("SQLSERVER_DRIVER", "ODBC Driver 18 for SQL Server"),
        encrypt=os.getenv("SQLSERVER_ENCRYPT", "yes"),
        trust_certificate=os.getenv("SQLSERVER_TRUST_CERTIFICATE", "no"),
        timeout=int(os.getenv("SQLSERVER_QUERY_TIMEOUT", "30")),
        max_rows=int(os.getenv("SQLSERVER_MAX_ROWS", "500")),
    )


def validate_profile(profile: SQLServerProfile) -> list[str]:
    missing = []
    for field_name in ("host", "database", "user", "password"):
        if not getattr(profile, field_name):
            missing.append(field_name)
    return missing


def connection_string(profile: SQLServerProfile) -> str:
    server = profile.host if "\\" in profile.host or not profile.port else f"{profile.host},{profile.port}"
    parts = {
        "DRIVER": "{" + profile.driver + "}",
        "SERVER": server,
        "DATABASE": profile.database,
        "UID": profile.user,
        "PWD": profile.password,
        "Encrypt": profile.encrypt,
        "TrustServerCertificate": profile.trust_certificate,
        "Connection Timeout": str(profile.timeout),
    }
    return ";".join(f"{key}={value}" for key, value in parts.items())


def redacted_profile(profile: SQLServerProfile) -> dict[str, str | int]:
    return {
        "host": profile.host,
        "port": profile.port,
        "database": profile.database,
        "user": profile.user,
        "driver": profile.driver,
        "encrypt": profile.encrypt,
        "trust_certificate": profile.trust_certificate,
        "timeout": profile.timeout,
        "max_rows": profile.max_rows,
    }


def sqlalchemy_url(profile: SQLServerProfile) -> str:
    return "mssql+pyodbc:///?odbc_connect=" + quote_plus(connection_string(profile))


def connect(profile: SQLServerProfile | None = None) -> pyodbc.Connection:
    active_profile = profile or load_sqlserver_profile()
    missing = validate_profile(active_profile)
    if missing:
        raise ValueError("Thiếu cấu hình SQL Server: " + ", ".join(missing))
    return pyodbc.connect(connection_string(active_profile), timeout=active_profile.timeout)
