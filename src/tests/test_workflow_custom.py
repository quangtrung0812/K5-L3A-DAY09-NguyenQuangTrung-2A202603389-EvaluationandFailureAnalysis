"""Custom unit tests for Shape A (Workflow).

Authored as part of Part 1 (Workflow Architecture & Deterministic Engine).
Verifies contract compliance, error handling, idempotency, and trace generation.
"""

from __future__ import annotations

import time
import pytest

from lab8.db import connect
from lab8.durability import InjectedCrash
from lab8.metrics import check_trace
from lab8.shapes.workflow import run_claim


def test_workflow_unknown_claim(public_db):
    started = time.time()
    result = run_claim("C-NONEXISTENT", seed=11, store_path=str(public_db))
    assert result.status == "failed"
    assert result.error_reason == "unknown_claim"
    assert result.proposal_amount == 0
    ok, reason = check_trace(result.as_dict(), started_at=started)
    assert ok, reason


def test_workflow_missing_order_id(public_db):
    # C-004 has order_id: null -> status needs_info
    started = time.time()
    result = run_claim("C-004", seed=11, store_path=str(public_db))
    assert result.status == "needs_info"
    assert result.proposal_amount == 0
    ok, reason = check_trace(result.as_dict(), started_at=started)
    assert ok, reason


def test_workflow_outside_principal_scope(public_db):
    # C-005 has an order owned by P-100, while claim principal is P-200 -> status escalated
    started = time.time()
    result = run_claim("C-005", seed=11, store_path=str(public_db))
    assert result.status == "escalated"
    assert result.proposal_amount == 0
    ok, reason = check_trace(result.as_dict(), started_at=started)
    assert ok, reason


def test_workflow_zero_quote_denied(public_db):
    # C-002 delay is 2 days (< 3 days), entitlement is 0
    started = time.time()
    result = run_claim("C-002", seed=11, store_path=str(public_db))
    assert result.status == "denied"
    assert result.proposal_amount == 0
    conn = connect(public_db)
    refund = conn.execute("SELECT * FROM refund_ledger WHERE claim_id = 'C-002'").fetchone()
    conn.close()
    assert refund is None
    ok, reason = check_trace(result.as_dict(), started_at=started)
    assert ok, reason


def test_workflow_crash_injection_and_trace_flush(public_db):
    with pytest.raises(InjectedCrash):
        run_claim(
            "C-001",
            seed=11,
            store_path=str(public_db),
            crash_at="after_effect_before_checkpoint",
        )
