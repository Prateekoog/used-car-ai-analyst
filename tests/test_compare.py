"""Checks that the answer checker accepts right answers and rejects wrong ones."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from run_eval import compare

GOLD = [("Diesel", 639727.77), ("Petrol", 375688.97)]

def test_exact_match():
    assert compare(GOLD, GOLD) == "pass"

def test_row_order_and_column_order_ignored():
    assert compare([(375688.97, "Petrol"), (639727.77, "Diesel")], GOLD) == "pass"

def test_extra_column_allowed():
    assert compare([("Diesel", 639727.77, 3658), ("Petrol", 375688.97, 2973)], GOLD) == "pass"

def test_rounding_tolerated():
    assert compare([("diesel", 639728), ("petrol", 375689)], GOLD) == "pass"

def test_wrong_value_rejected():
    assert compare([("Diesel", 600000), ("Petrol", 375688.97)], GOLD) == "wrong_values"

def test_missing_row_rejected():
    assert compare([("Diesel", 639727.77)], GOLD) == "wrong_row_count"

def test_percentage_scale_rejected():
    assert compare([(0.0843,)], [(8.43,)]) == "wrong_values"
