"""
correct_net_amounts.py
─────────────────────
One-time migration: recalculate net_amount for every transaction where the
stored value is wrong (net_amount != round(gross_amount + fee_amount, 2)).

PayPal Reporting API returns fee_amount as a SIGNED negative number.
Correct formula: net = gross + fee   (e.g. 5.00 + (-0.59) = 4.41)

This script ONLY updates net_amount.  It never touches:
  paypal_transaction_id, transaction_date, gross_amount, fee_amount,
  description, currency, status, or any raw API records.

Usage:
    python scripts/correct_net_amounts.py [--dry-run]
"""

import os
import sys
import argparse

# ── allow running from project root or from backend/ ──────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal
from app.models import Transaction


def recalculate(gross: float, fee: float) -> float:
    """Return the correct signed net amount using PayPal's ledger formula.

    PayPal Reporting API returns fee_amount as a SIGNED negative value.
    So net = gross + fee  (e.g.  5.00 + -0.59  =  4.41).

    Demo data stores fees as UNSIGNED positive values and uses net = gross - fee.
    Those records are already correct, so we only touch rows where fee < 0.
    """
    if fee < 0:
        # Signed negative fee from PayPal Reporting API
        return round(gross + fee, 2)
    else:
        # Unsigned positive fee (Demo data or zero-fee) — already correct
        return round(gross - fee, 2)


def run(dry_run: bool = False) -> None:
    db = SessionLocal()
    try:
        all_txs = db.query(Transaction).all()

        corrections = []
        for tx in all_txs:
            gross = float(tx.gross_amount or 0.0)
            fee   = float(tx.fee_amount   or 0.0)
            expected_net = recalculate(gross, fee)

            current_net = float(tx.net_amount or 0.0)
            if abs(current_net - expected_net) > 0.001:          # floating-point tolerance
                corrections.append({
                    "db_id":      tx.id,
                    "biz_id":     tx.business_id,
                    "paypal_id":  tx.paypal_transaction_id,
                    "gross":      gross,
                    "fee":        fee,
                    "old_net":    current_net,
                    "new_net":    expected_net,
                })

        if not corrections:
            print("✅  No incorrect net_amount values found — database is already correct.")
            return

        print(f"{'DRY-RUN: ' if dry_run else ''}Found {len(corrections)} record(s) to correct:\n")
        for c in corrections:
            print(
                f"  DB id={c['db_id']}  biz={c['biz_id']}  paypal_id={c['paypal_id']}\n"
                f"    gross={c['gross']:+.2f}  fee={c['fee']:+.2f}\n"
                f"    net: {c['old_net']:+.2f}  →  {c['new_net']:+.2f}\n"
            )

        if dry_run:
            print("DRY-RUN mode — no changes written.")
            return

        # Apply corrections
        for c in corrections:
            tx = db.query(Transaction).filter(Transaction.id == c["db_id"]).one()
            tx.net_amount = c["new_net"]

        db.commit()
        print(f"✅  Applied {len(corrections)} correction(s) to net_amount.")

    except Exception as exc:
        db.rollback()
        print(f"❌  Error: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Correct net_amount values in the database.")
    parser.add_argument("--dry-run", action="store_true", help="Preview corrections without writing to DB.")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
