"""Price data validation utilities for Binance API responses."""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class PriceValidationError(Exception):
    """Custom exception for price validation errors."""

    def __init__(
        self,
        index: int,
        error_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.index = index
        self.error_type = error_type
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


def get_interval_duration_minutes(interval_value: str) -> int:
    """Get the duration of an interval in minutes.

    Args:
        interval_value: Binance interval string (e.g., "1m", "1h", "1d")

    Returns:
        Duration in minutes
    """
    interval_mapping = {
        "1m": 1,
        "3m": 3,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "2h": 120,
        "4h": 240,
        "6h": 360,
        "8h": 480,
        "12h": 720,
        "1d": 1440,
        "3d": 4320,
        "1w": 10080,
        "1M": 43200,
    }
    return interval_mapping.get(interval_value, 60)


def validate_close_time(
    data_point: Dict[str, Any], interval_value: str, index: int
) -> Tuple[bool, Optional[str]]:
    """Validate that close_time is at the end of the expected timeframe.

    Args:
        data_point: The data point dictionary containing open_time and close_time
        interval_value: The interval string (e.g., "1h")
        index: Index of the data point for error reporting

    Returns:
        Tuple of (is_valid, error_message)
    """
    open_time = data_point.get("open_time")
    close_time = data_point.get("close_time")

    if not isinstance(open_time, (datetime, str)) or not isinstance(
        close_time, (datetime, str)
    ):
        return True, None

    if isinstance(open_time, str):
        try:
            open_time = datetime.fromisoformat(open_time.replace("Z", "+00:00"))
        except ValueError:
            return True, None

    if isinstance(close_time, str):
        try:
            close_time = datetime.fromisoformat(close_time.replace("Z", "+00:00"))
        except ValueError:
            return True, None

    expected_duration = get_interval_duration_minutes(interval_value)
    expected_close_time = open_time + timedelta(minutes=expected_duration)

    time_diff = abs((close_time - expected_close_time).total_seconds())

    if time_diff > 60:
        error_msg = f"Close time mismatch: expected ~{expected_close_time.isoformat()}, got {close_time.isoformat()}"
        return False, error_msg

    return True, None


def validate_prices(
    data_point: Dict[str, Any], index: int
) -> Tuple[bool, Optional[str]]:
    """Validate that open, close, high, and low prices are logically consistent.

    Validations:
    - High price must be greater than or equal to both open and close prices
    - Low price must be less than or equal to both open and close prices

    Args:
        data_point: The data point dictionary containing prices
        index: Index of the data point for error reporting

    Returns:
        Tuple of (is_valid, error_message)
    """
    open_price = data_point.get("open_price", 0)
    close_price = data_point.get("close_price", 0)
    high_price = data_point.get("high_price", 0)
    low_price = data_point.get("low_price", 0)

    errors = []

    if high_price < open_price:
        errors.append(
            f"high_price ({high_price}) is lower than open_price ({open_price})"
        )

    if high_price < close_price:
        errors.append(
            f"high_price ({high_price}) is lower than close_price ({close_price})"
        )

    if low_price > open_price:
        errors.append(
            f"low_price ({low_price}) is higher than open_price ({open_price})"
        )

    if low_price > close_price:
        errors.append(
            f"low_price ({low_price}) is higher than close_price ({close_price})"
        )

    if errors:
        error_msg = f"Price validation failed: {'; '.join(errors)}"
        return False, error_msg

    return True, None


def validate_volume(
    data_point: Dict[str, Any], index: int
) -> Tuple[bool, Optional[str]]:
    """Validate that volume is greater than zero.

    Args:
        data_point: The data point dictionary containing volume
        index: Index of the data point for error reporting

    Returns:
        Tuple of (is_valid, error_message)
    """
    volume = data_point.get("volume", 0)

    if volume <= 0:
        error_msg = f"Volume must be greater than zero, got {volume}"
        return False, error_msg

    return True, None


def validate_price_data(
    data_points: List[Dict[str, Any]],
    interval_value: str,
    skip_volume_validation: bool = False,
    skip_time_validation: bool = False,
    skip_price_validation: bool = False,
) -> List[PriceValidationError]:
    """Validate all price data points from Binance API response.

    Performs three types of validation:
    1. Close time validation: Ensures close_time is at the end of the expected timeframe
    2. Price validation: Ensures open/close are within high/low bounds
    3. Volume validation: Ensures volume is greater than zero

    Args:
        data_points: List of transformed price data points
        interval_value: The interval string for time validation
        skip_volume_validation: Skip volume validation if True
        skip_time_validation: Skip close_time validation if True
        skip_price_validation: Skip price consistency validation if True

    Returns:
        List of validation errors (empty if all valid)
    """
    errors = []

    for index, data_point in enumerate(data_points):
        if not skip_time_validation:
            is_valid, error_msg = validate_close_time(data_point, interval_value, index)
            if not is_valid:
                errors.append(
                    PriceValidationError(
                        index=index,
                        error_type="CLOSE_TIME_VALIDATION",
                        message=error_msg,
                        details={
                            "open_time": data_point.get("open_time"),
                            "close_time": data_point.get("close_time"),
                            "interval": interval_value,
                        },
                    )
                )

        if not skip_price_validation:
            is_valid, error_msg = validate_prices(data_point, index)
            if not is_valid:
                errors.append(
                    PriceValidationError(
                        index=index,
                        error_type="PRICE_VALIDATION",
                        message=error_msg,
                        details={
                            "open_price": data_point.get("open_price"),
                            "high_price": data_point.get("high_price"),
                            "low_price": data_point.get("low_price"),
                            "close_price": data_point.get("close_price"),
                        },
                    )
                )

        if not skip_volume_validation:
            is_valid, error_msg = validate_volume(data_point, index)
            if not is_valid:
                errors.append(
                    PriceValidationError(
                        index=index,
                        error_type="VOLUME_VALIDATION",
                        message=error_msg,
                        details={"volume": data_point.get("volume")},
                    )
                )

    return errors


def filter_valid_data_points(
    data_points: List[Dict[str, Any]],
    interval_value: str,
    skip_volume_validation: bool = False,
    skip_time_validation: bool = False,
    skip_price_validation: bool = False,
) -> Tuple[List[Dict[str, Any]], List[PriceValidationError]]:
    """Filter out invalid data points and return errors.

    Args:
        data_points: List of transformed price data points
        interval_value: The interval string for time validation
        skip_volume_validation: Skip volume validation if True
        skip_time_validation: Skip close_time validation if True
        skip_price_validation: Skip price consistency validation if True

    Returns:
        Tuple of (filtered_data_points, validation_errors)
    """
    errors = validate_price_data(
        data_points,
        interval_value,
        skip_volume_validation,
        skip_time_validation,
        skip_price_validation,
    )

    invalid_indices = {error.index for error in errors}
    valid_data_points = [
        dp for idx, dp in enumerate(data_points) if idx not in invalid_indices
    ]

    return valid_data_points, errors
