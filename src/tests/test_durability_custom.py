"""Custom unit tests for Durability, Crash Safety, and Order Cap.

Authored as part of Part 3 (Benchmark, Durability / Crash Suite, Evaluation & Reports).
Verifies idempotent replays, crash resilience, ledger atomic transactions,
and order-level refund cap enforcement across shapes.
"""

from __future__ import annotations

import pytest

from lab8.db import connect
from lab8.durability import (
    InjectedCrash,
    committed_audit_count,
    get_refund,
    issue_refund,
)
from lab8.policy import order_refunded_vnd
from lab8.shapes.workflow import run_claim as run_workflow


def test_idempotent_replay_single_ledger_row(public_db):
    # Calling run_claim multiple times must maintain exactly one ledger row and one audit
    res1 = run_workflow("C-001", seed=11, store_path=str(public_db))
    res2 = run_workflow("C-001", seed=11, store_path=str(public_db))
    assert res1.status == "resolved"
    assert res2.status == "resolved"

    conn = connect(public_db)
    rows = conn.execute("SELECT * FROM refund_ledger WHERE claim_id = 'C-001'").fetchall()
    audits = committed_audit_count(conn, "C-001")
    conn.close()

    assert len(rows) == 1
    assert audits == 1


def test_crash_recovery_deterministic_state(public_db):
    # Crash after effect before checkpoint, then resume
    with pytest.raises(InjectedCrash):
        run_workflow(
            "C-001",
            seed=11,
            store_path=str(public_db),
            crash_at="after_effect_before_checkpoint",
        )

    resumed = run_workflow("C-001", seed=11, store_path=str(public_db))
    assert resumed.status == "resolved"

    conn = connect(public_db)
    rows = conn.execute("SELECT * FROM refund_ledger WHERE claim_id = 'C-001'").fetchall()
    audits = committed_audit_count(conn, "C-001")
    conn.close()

    assert len(rows) == 1
    assert audits == 1


def test_order_cap_differential_topup(public_db):
    # C-014 has an earlier refund on order O-515 of 30,000 VND; entitlement is 150,000 VND
    res = run_workflow("C-014", seed=11, store_path=str(public_db))
    assert res.status == "resolved"
    assert res.proposal_amount == 150000

    conn = connect(public_db)
    effect = get_refund(conn, "C-014")
    total_on_order = order_refunded_vnd(conn, "O-515")
    conn.close()

    assert effect is not None
    assert int(effect["amount_vnd"]) == 120000  # 150,000 - 30,000
    assert total_on_order == 150000
