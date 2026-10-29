
import pytest
from water_utility_billing import calculate_water_bill, check_meter_tampering


def test_single_active_residential():
    accounts = [{"is_active": True, "is_commercial": False,
                 "has_leak_waiver": False, "usage_blocks": [30]}]
    result = calculate_water_bill(accounts, 10.0)
    assert result == {"total_billed": 55.0, "status": "NORMAL"}


def test_invalid_accounts():
    with pytest.raises(ValueError):
        calculate_water_bill("invalid", 10.0)


def test_negative_base_fee():
    with pytest.raises(ValueError):
        calculate_water_bill([], -1)


def test_inactive_account():
    result = calculate_water_bill(
        [{"is_active": False, "usage_blocks": [50]}], 10.0
    )
    assert result["total_billed"] == 0.0


def test_empty_usage_blocks():
    result = calculate_water_bill(
        [{"is_active": True, "usage_blocks": []}], 10.0
    )
    assert result["total_billed"] == 10.0


def test_nonpositive_usage():
    result = calculate_water_bill(
        [{"is_active": True, "usage_blocks": [0, -5]}], 10.0
    )
    assert result["total_billed"] == 10.0


def test_usage_between_1_and_50():
    result = calculate_water_bill(
        [{"is_active": True, "usage_blocks": [20]}], 0.0
    )
    assert result["total_billed"] == 30.0


def test_usage_between_51_and_100():
    result = calculate_water_bill(
        [{"is_active": True, "usage_blocks": [75]}], 0.0
    )
    assert result["total_billed"] == 187.5


def test_residential_usage_over_100():
    result = calculate_water_bill(
        [{"is_active": True, "is_commercial": False,
          "usage_blocks": [120, 20]}], 0.0
    )
    assert result["total_billed"] == 540.0


def test_commercial_usage_over_100():
    result = calculate_water_bill(
        [{"is_active": True, "is_commercial": True,
          "usage_blocks": [120]}], 0.0
    )
    assert result["total_billed"] == 420.0


def test_leak_waiver_applied():
    result = calculate_water_bill(
        [{"is_active": True, "has_leak_waiver": True,
          "usage_blocks": [150]}], 10.0
    )
    assert result["total_billed"] == 635.0


def test_leak_waiver_not_applied_below_threshold():
    result = calculate_water_bill(
        [{"is_active": True, "has_leak_waiver": True,
          "usage_blocks": [10]}], 10.0
    )
    assert result["total_billed"] == 25.0


def test_no_activity_status():
    result = calculate_water_bill([], 10.0)
    assert result["status"] == "NO_ACTIVITY"


def test_excessive_flags_status():
    result = calculate_water_bill(
        [{"is_active": True, "usage_blocks": [0, 0, 0, 0, 0, 0]}],
        10.0
    )
    assert result["status"] == "EXCESSIVE_FLAGS"


def test_empty_meter_readings():
    assert check_meter_tampering([]) == "NO_DATA"


def test_clear_meter_readings():
    assert check_meter_tampering([[1, 2, 0, 3]]) == "CLEAR"


def test_single_negative_reading():
    assert check_meter_tampering([[1, -1, 2]]) == "CLEAR"


def test_two_consecutive_negative_readings():
    assert check_meter_tampering([[1, -1, -2]]) == "TAMPER_SUSPECTED"


def test_negative_readings_reset_by_nonnegative():
    assert check_meter_tampering([[-1, 0, -2]]) == "CLEAR"


def test_tampering_in_later_meter():
    assert check_meter_tampering([[1, 2], [-1, -2]]) == "TAMPER_SUSPECTED"
