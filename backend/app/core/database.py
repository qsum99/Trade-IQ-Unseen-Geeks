"""
PostgreSQL Database Connection Module
======================================
Centralized database connection management with connection pooling.
"""

from __future__ import annotations

import os
import logging
from contextlib import contextmanager
from typing import Any

import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/quant_platform"
)


@contextmanager
def get_db_connection():
    """Get a database connection from the pool."""
    conn = psycopg.connect(DATABASE_URL, autocommit=False, row_factory=dict_row)
    try:
        yield conn
    finally:
        conn.close()


def check_db_health() -> dict:
    """Check database connectivity and return status."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                row = cur.fetchone()
                return {
                    "status": "connected",
                    "version": row[0] if row else "unknown",
                    "host": "configured"
                }
    except Exception as e:
        logger.error("PostgreSQL health check failed: %s", e)
        return {
            "status": "error",
            "error": str(e),
            "version": "unknown",
            "host": "configured"
        }


def init_database() -> bool:
    """Initialize database schema (DDL)."""
    ddl = """
    CREATE TABLE IF NOT EXISTS backtests (
        id TEXT PRIMARY KEY,
        symbol TEXT NOT NULL,
        strategy TEXT NOT NULL,
        start_date DATE,
        end_date DATE,
        initial_capital NUMERIC,
        transaction_cost NUMERIC,
        slippage NUMERIC,
        total_return NUMERIC,
        sharpe NUMERIC,
        volatility NUMERIC,
        max_drawdown NUMERIC,
        total_trades INTEGER,
        win_rate NUMERIC,
        profit_factor NUMERIC,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS backtest_trades (
        id SERIAL PRIMARY KEY,
        backtest_id TEXT REFERENCES backtests(id),
        trade_date DATE,
        side TEXT,
        price NUMERIC,
        quantity NUMERIC,
        transaction_cost NUMERIC
    );

    CREATE TABLE IF NOT EXISTS equity_curves (
        id SERIAL PRIMARY KEY,
        backtest_id TEXT REFERENCES backtests(id),
        date DATE,
        portfolio_value NUMERIC,
        benchmark_value NUMERIC
    );

    CREATE TABLE IF NOT EXISTS quantum_jobs (
        id TEXT PRIMARY KEY,
        experiment_type TEXT,
        symbols JSONB,
        parameters JSONB,
        status TEXT,
        result JSONB,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS portfolio_runs (
        id TEXT PRIMARY KEY,
        symbols JSONB,
        weights JSONB,
        expected_return NUMERIC,
        volatility NUMERIC,
        sharpe_ratio NUMERIC,
        method TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS risk_assessments (
        id TEXT PRIMARY KEY,
        symbol TEXT,
        var_historical_95 NUMERIC,
        var_parametric_95 NUMERIC,
        cvar_95 NUMERIC,
        max_drawdown NUMERIC,
        sharpe_ratio NUMERIC,
        sortino_ratio NUMERIC,
        metrics JSONB,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(ddl)
                conn.commit()
            logger.info("Database schema initialized successfully.")
            return True
    except Exception as e:
        logger.error("Failed to initialize database schema: %s", e)
        return False


def save_quantum_job(job_data: dict) -> bool:
    """Save or update a quantum hardware job in PostgreSQL."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO quantum_jobs (id, experiment_type, symbols, parameters, status, result, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                    ON CONFLICT (id) DO UPDATE SET
                        status = EXCLUDED.status,
                        result = EXCLUDED.result,
                        updated_at = NOW();
                    """,
                    (
                        job_data["id"],
                        job_data.get("experiment_type"),
                        job_data.get("symbols"),
                        job_data.get("parameters"),
                        job_data.get("status", "queued"),
                        job_data.get("result"),
                    ),
                )
                conn.commit()
        return True
    except Exception as e:
        logger.error("Failed to save quantum job %s: %s", job_data.get("id"), e)
        return False


def get_quantum_job(job_id: str) -> dict | None:
    """Retrieve a quantum job record from PostgreSQL."""
    try:
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("SELECT * FROM quantum_jobs WHERE job_id = %s;", (job_id,))
                row = cur.fetchone()
                if row:
                    # Format timestamps
                    if isinstance(row.get("created_at"), str):
                        pass  # already string
                    return row
        return None
    except Exception as e:
        logger.error("Failed to get quantum job %s: %s", job_id, e)
        return None


def list_quantum_jobs(limit: int = 50) -> list[dict]:
    """List recent quantum jobs."""
    try:
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("SELECT * FROM quantum_jobs ORDER BY created_at DESC LIMIT %s;", (limit,))
                rows = cur.fetchall()
                for row in rows:
                    if isinstance(row.get("created_at"), str):
                        pass
                return rows
    except Exception as e:
        logger.error("Failed to list quantum jobs: %s", e)
        return []


def save_portfolio_run(run_data: dict) -> bool:
    """Persist a portfolio optimization run to PostgreSQL."""
    try:
        import json
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO portfolio_runs (id, symbols, weights, expected_return, volatility, sharpe_ratio, method)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        symbols = EXCLUDED.symbols,
                        weights = EXCLUDED.weights,
                        expected_return = EXCLUDED.expected_return,
                        volatility = EXCLUDED.volatility,
                        sharpe_ratio = EXCLUDED.sharpe_ratio,
                        method = EXCLUDED.method;
                    """,
                    (
                        run_data["id"],
                        json.dumps(run_data["symbols"]),
                        json.dumps(run_data["weights"]),
                        run_data.get("expected_return"),
                        run_data.get("volatility"),
                        run_data.get("sharpe_ratio"),
                        run_data.get("method"),
                    ),
                )
                conn.commit()
        return True
    except Exception as e:
        logger.error("Failed to save portfolio run: %s", e)
        return False


def save_risk_assessment(risk_data: dict) -> bool:
    """Persist a risk assessment record to PostgreSQL."""
    try:
        import json
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO risk_assessments (
                        id, var_historical_95, var_parametric_95,
                        cvar_95, max_drawdown, sharpe_ratio, sortino_ratio, metrics
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s
                    ) ON CONFLICT (id) DO UPDATE SET
                        var_historical_95 = EXCLUDED.var_historical_95,
                        var_parametric_95 = EXCLUDED.var_parametric_95,
                        cvar_95 = EXCLUDED.cvar_95,
                        max_drawdown = EXCLUDED.max_drawdown,
                        sharpe_ratio = EXCLUDED.sharpe_ratio,
                        sortino_ratio = EXCLUDED.sortino_ratio,
                        metrics = EXCLUDED.metrics;
                    """,
                    (
                        risk_data["id"],
                        risk_data.get("var_historical_95"),
                        risk_data.get("var_parametric_95"),
                        risk_data.get("cvar_95"),
                        risk_data.get("max_drawdown"),
                        risk_data.get("sharpe_ratio"),
                        risk_data.get("sortino_ratio"),
                        json.dumps(risk_data.get("metrics", {})),
                    ),
                )
                conn.commit()
        return True
    except Exception as e:
        logger.error("Failed to save risk assessment: %s", e)
        return False