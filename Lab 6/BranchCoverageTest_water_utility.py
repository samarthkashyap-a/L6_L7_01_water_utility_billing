
import pytest
from water_utility_billing import calculate_water_bill, check_meter_tampering


def test_invalid_accounts_type():
    with pytest.raises(ValueError):
        calculate_water_bill("invalid", 10.0)


def test_negative_base_fee():
    with pytest.raises(ValueError):
        calculate_water_bill([], -1.0)


def test_inactive_account():
    result = calculate_water_bill(
        [{"is_active": False, "usage_blocks": [30]}], 10.0
    )
    assert result["total_billed"] == 0.0


def test_active_account_defaults():
    result = calculate_water_bill([{}], 10.0)
    assert result == {"total_billed": 0.0, "status": "NO_ACTIVITY"}


def test_empty_usage_blocks():
    result = calculate_water_bill(
        [{"is_active": True, "usage_blocks": []}], 10.0
    )
    assert result["total_billed"] == 10.0


def test_zero_and_negative_usage():
    result = calculate_water_bill(
        [{"is_active": True, "usage_blocks": [0, -10]}], 10.0
    )
    assert result["total_billed"] == 10.0


def test_usage_at_lower_tier_boundary():
    result = calculate_water_bill(
        [{"is_active": True, "usage_blocks": [1, 50]}], 0.0
    )
    assert result["total_billed"] == 76.5


def test_usage_above_50():
    result = calculate_water_bill(
        [{"is_active": True, "usage_blocks": [51]}], 0.0
    )
    assert result["total_billed"] == 127.5


def test_usage_exactly_100():
    result = calculate_water_bill(
        [{"is_active": True, "usage_blocks": [100]}], 0.0
    )
    assert result["total_billed"] == 250.0


def test_residential_usage_over_100_breaks_loop():
    result = calculate_water_bill(
        [{"is_active": True, "is_commercial": False,
          "usage_blocks": [101, 20]}], 0.0
    )
    assert result["total_billed"] == 454.5


def test_commercial_usage_over_100_continues_loop():
    result = calculate_water_bill(
        [{"is_active": True, "is_commercial": True,
          "usage_blocks": [101, 20]}], 0.0
    )
    assert result["total_billed"] == 383.5


def test_leak_waiver_above_200():
    result = calculate_water_bill(
        [{"is_active": True, "has_leak_waiver": True,
          "usage_blocks": [150]}], 10.0
    )
    assert result["total_billed"] == 635.0


def test_leak_waiver_at_or_below_200():
    result = calculate_water_bill(
        [{"is_active": True, "has_leak_waiver": True,
          "usage_blocks": [100]}], 10.0
    )
    assert result["total_billed"] == 210.0


def test_no_activity():
    result = calculate_water_bill([], 10.0)
    assert result["status"] == "NO_ACTIVITY"


def test_excessive_flags():
    result = calculate_water_bill(
        [{"is_active": True,
          "usage_blocks": [0, 0, 0, 0, 0, 0]}], 10.0
    )
    assert result["status"] == "EXCESSIVE_FLAGS"


def test_flag_count_at_threshold():
    result = calculate_water_bill(
        [{"is_active": True, "usage_blocks": [0, 0, 0, 0, 0]}], 10.0
    )
    assert result["status"] == "NORMAL"


def test_zero_total_with_no_accounts():
    result = calculate_water_bill([], 0.0)
    assert result == {"total_billed": 0.0, "status": "NO_ACTIVITY"}


def test_empty_meter_matrix():
    assert check_meter_tampering([]) == "NO_DATA"


def test_empty_meter():
    assert check_meter_tampering([[]]) == "CLEAR"


def test_positive_meter_readings():
    assert check_meter_tampering([[1, 2, 3]]) == "CLEAR"


def test_one_negative_reading():
    assert check_meter_tampering([[1, -1, 2]]) == "CLEAR"


def test_consecutive_negative_readings():
    assert check_meter_tampering([[1, -1, -2]]) == "TAMPER_SUSPECTED"


def test_nonnegative_reading_resets_counter():
    assert check_meter_tampering([[-1, 0, -2]]) == "CLEAR"


def test_tampering_in_second_meter():
    assert check_meter_tampering([[1, 2], [-1, -2]]) == "TAMPER_SUSPECTED"
