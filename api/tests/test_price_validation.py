"""Tests for price validation utilities."""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List

try:
    from src.utils.price_validation import (
        validate_close_time,
        validate_prices,
        validate_volume,
        validate_price_data,
        filter_valid_data_points,
        get_interval_duration_minutes,
        PriceValidationError,
    )
except ImportError:
    from api.src.utils.price_validation import (
        validate_close_time,
        validate_prices,
        validate_volume,
        validate_price_data,
        filter_valid_data_points,
        get_interval_duration_minutes,
        PriceValidationError,
    )


class TestGetIntervalDurationMinutes:
    """Test interval duration calculation."""

    def test_minute_intervals(self):
        assert get_interval_duration_minutes("1m") == 1
        assert get_interval_duration_minutes("5m") == 5
        assert get_interval_duration_minutes("15m") == 15
        assert get_interval_duration_minutes("30m") == 30

    def test_hour_intervals(self):
        assert get_interval_duration_minutes("1h") == 60
        assert get_interval_duration_minutes("2h") == 120
        assert get_interval_duration_minutes("4h") == 240

    def test_day_intervals(self):
        assert get_interval_duration_minutes("1d") == 1440
        assert get_interval_duration_minutes("3d") == 4320

    def test_week_intervals(self):
        assert get_interval_duration_minutes("1w") == 10080


class TestValidateCloseTime:
    """Test close time validation."""

    def test_valid_close_time_1h(self):
        open_time = datetime(2024, 1, 15, 10, 0, 0)
        close_time = datetime(2024, 1, 15, 11, 0, 0)

        data_point = {
            "open_time": open_time.isoformat(),
            "close_time": close_time.isoformat(),
        }

        is_valid, error_msg = validate_close_time(data_point, "1h", 0)
        assert is_valid is True
        assert error_msg is None

    def test_valid_close_time_15m(self):
        open_time = datetime(2024, 1, 15, 10, 30, 0)
        close_time = datetime(2024, 1, 15, 10, 45, 0)

        data_point = {
            "open_time": open_time.isoformat(),
            "close_time": close_time.isoformat(),
        }

        is_valid, error_msg = validate_close_time(data_point, "15m", 0)
        assert is_valid is True
        assert error_msg is None

    def test_invalid_close_time_too_early(self):
        open_time = datetime(2024, 1, 15, 10, 0, 0)
        close_time = datetime(2024, 1, 15, 10, 30, 0)

        data_point = {
            "open_time": open_time.isoformat(),
            "close_time": close_time.isoformat(),
        }

        is_valid, error_msg = validate_close_time(data_point, "1h", 5)
        assert is_valid is False
        assert "Close time mismatch" in error_msg

    def test_invalid_close_time_too_late(self):
        open_time = datetime(2024, 1, 15, 10, 0, 0)
        close_time = datetime(2024, 1, 15, 12, 0, 0)

        data_point = {
            "open_time": open_time.isoformat(),
            "close_time": close_time.isoformat(),
        }

        is_valid, error_msg = validate_close_time(data_point, "1h", 10)
        assert is_valid is False
        assert "Close time mismatch" in error_msg


class TestValidatePrices:
    """Test price validation."""

    def test_valid_prices(self):
        data_point = {
            "open_price": 50000.0,
            "close_price": 50500.0,
            "high_price": 51000.0,
            "low_price": 49500.0,
        }

        is_valid, error_msg = validate_prices(data_point, 0)
        assert is_valid is True
        assert error_msg is None

    def test_high_lower_than_open(self):
        data_point = {
            "open_price": 50000.0,
            "close_price": 50500.0,
            "high_price": 49000.0,
            "low_price": 49500.0,
        }

        is_valid, error_msg = validate_prices(data_point, 0)
        assert is_valid is False
        assert "high_price" in error_msg
        assert "open_price" in error_msg

    def test_high_lower_than_close(self):
        data_point = {
            "open_price": 50000.0,
            "close_price": 50500.0,
            "high_price": 50000.0,
            "low_price": 49500.0,
        }

        is_valid, error_msg = validate_prices(data_point, 0)
        assert is_valid is False
        assert "high_price" in error_msg
        assert "close_price" in error_msg

    def test_low_higher_than_open(self):
        data_point = {
            "open_price": 50000.0,
            "close_price": 50500.0,
            "high_price": 51000.0,
            "low_price": 51000.0,
        }

        is_valid, error_msg = validate_prices(data_point, 0)
        assert is_valid is False
        assert "low_price" in error_msg
        assert "open_price" in error_msg

    def test_low_higher_than_close(self):
        data_point = {
            "open_price": 50000.0,
            "close_price": 50500.0,
            "high_price": 51000.0,
            "low_price": 52000.0,
        }

        is_valid, error_msg = validate_prices(data_point, 0)
        assert is_valid is False
        assert "low_price" in error_msg
        assert "close_price" in error_msg

    def test_equal_prices_valid(self):
        data_point = {
            "open_price": 50000.0,
            "close_price": 50000.0,
            "high_price": 50000.0,
            "low_price": 50000.0,
        }

        is_valid, error_msg = validate_prices(data_point, 0)
        assert is_valid is True


class TestValidateVolume:
    """Test volume validation."""

    def test_valid_positive_volume(self):
        data_point = {"volume": 100.5}

        is_valid, error_msg = validate_volume(data_point, 0)
        assert is_valid is True
        assert error_msg is None

    def test_invalid_zero_volume(self):
        data_point = {"volume": 0}

        is_valid, error_msg = validate_volume(data_point, 0)
        assert is_valid is False
        assert "Volume must be greater than zero" in error_msg

    def test_invalid_negative_volume(self):
        data_point = {"volume": -10.5}

        is_valid, error_msg = validate_volume(data_point, 0)
        assert is_valid is False
        assert "Volume must be greater than zero" in error_msg


class TestValidatePriceData:
    """Test comprehensive price data validation."""

    def test_all_valid_data_points(self):
        data_points = [
            {
                "open_time": datetime(2024, 1, 15, 10, 0, 0).isoformat(),
                "close_time": datetime(2024, 1, 15, 11, 0, 0).isoformat(),
                "open_price": 50000.0,
                "close_price": 50500.0,
                "high_price": 51000.0,
                "low_price": 49500.0,
                "volume": 100.5,
            }
        ]

        errors = validate_price_data(data_points, "1h")
        assert len(errors) == 0

    def test_multiple_validation_errors(self):
        data_points = [
            {
                "open_time": datetime(2024, 1, 15, 10, 0, 0).isoformat(),
                "close_time": datetime(2024, 1, 15, 11, 30, 0).isoformat(),
                "open_price": 50000.0,
                "close_price": 50500.0,
                "high_price": 49000.0,
                "low_price": 49500.0,
                "volume": 0,
            }
        ]

        errors = validate_price_data(data_points, "1h")
        assert len(errors) == 3  # Time, price, and volume

    def test_skip_validations(self):
        data_points = [
            {
                "open_time": datetime(2024, 1, 15, 10, 0, 0).isoformat(),
                "close_time": datetime(2024, 1, 15, 11, 0, 0).isoformat(),
                "open_price": 50000.0,
                "close_price": 50500.0,
                "high_price": 49000.0,
                "low_price": 49500.0,
                "volume": 0,
            }
        ]

        errors = validate_price_data(
            data_points,
            "1h",
            skip_volume_validation=True,
            skip_time_validation=True,
            skip_price_validation=True,
        )
        assert len(errors) == 0

    def test_error_details(self):
        data_points = [
            {
                "open_time": datetime(2024, 1, 15, 10, 0, 0).isoformat(),
                "close_time": datetime(2024, 1, 15, 11, 0, 0).isoformat(),
                "open_price": 50000.0,
                "close_price": 50500.0,
                "high_price": 51000.0,
                "low_price": 52000.0,
                "volume": -10,
            }
        ]

        errors = validate_price_data(data_points, "1h")
        assert len(errors) == 2

        volume_error = next(e for e in errors if e.error_type == "VOLUME_VALIDATION")
        assert volume_error.index == 0
        assert volume_error.details["volume"] == -10


class TestFilterValidDataPoints:
    """Test filtering valid data points."""

    def test_filter_all_valid(self):
        data_points = [
            {
                "open_time": datetime(2024, 1, 15, 10, 0, 0).isoformat(),
                "close_time": datetime(2024, 1, 15, 11, 0, 0).isoformat(),
                "open_price": 50000.0,
                "close_price": 50500.0,
                "high_price": 51000.0,
                "low_price": 49500.0,
                "volume": 100.5,
            },
            {
                "open_time": datetime(2024, 1, 15, 11, 0, 0).isoformat(),
                "close_time": datetime(2024, 1, 15, 12, 0, 0).isoformat(),
                "open_price": 50500.0,
                "close_price": 51000.0,
                "high_price": 51500.0,
                "low_price": 50000.0,
                "volume": 200.0,
            },
        ]

        valid_points, errors = filter_valid_data_points(data_points, "1h")
        assert len(valid_points) == 2
        assert len(errors) == 0

    def test_filter_invalid_points(self):
        data_points = [
            {
                "open_time": datetime(2024, 1, 15, 10, 0, 0).isoformat(),
                "close_time": datetime(2024, 1, 15, 11, 0, 0).isoformat(),
                "open_price": 50000.0,
                "close_price": 50500.0,
                "high_price": 51000.0,
                "low_price": 49500.0,
                "volume": 0,
            },
            {
                "open_time": datetime(2024, 1, 15, 11, 0, 0).isoformat(),
                "close_time": datetime(2024, 1, 15, 12, 0, 0).isoformat(),
                "open_price": 50500.0,
                "close_price": 51000.0,
                "high_price": 51500.0,
                "low_price": 50000.0,
                "volume": 200.0,
            },
        ]

        valid_points, errors = filter_valid_data_points(data_points, "1h")
        assert len(valid_points) == 1
        assert len(errors) == 1
        assert errors[0].index == 0


class TestPriceValidationError:
    """Test PriceValidationError exception."""

    def test_error_creation(self):
        error = PriceValidationError(
            index=5,
            error_type="VOLUME_VALIDATION",
            message="Volume must be greater than zero",
            details={"volume": -10},
        )

        assert error.index == 5
        assert error.error_type == "VOLUME_VALIDATION"
        assert error.message == "Volume must be greater than zero"
        assert error.details["volume"] == -10

    def test_error_string_representation(self):
        error = PriceValidationError(
            index=5,
            error_type="PRICE_VALIDATION",
            message="high_price is lower than open_price",
        )

        assert "high_price is lower than open_price" in str(error)
