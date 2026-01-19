#!/usr/bin/env python3
"""
Simple script to demonstrate Pydantic type checking in the API.
This script shows how Pydantic models validate input data automatically.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from models.api_models import PriceRequest, IntervalEnum
from datetime import datetime


def test_pydantic_validation():
    """Demonstrate Pydantic validation features."""

    print("=== Pydantic Type Checking Demo ===\n")

    # Test 1: Valid request
    print("1. Testing valid request:")
    try:
        valid_request = PriceRequest(
            symbol="BTCUSDT",
            interval=IntervalEnum.ONE_HOUR,
            limit=100,
            startdate="20240101",
            enddate="20240102",
        )
        print(f"✅ Valid request created: {valid_request}")
        print(f"   Symbol: {valid_request.symbol}")
        print(f"   Interval: {valid_request.interval}")
        print(f"   Limit: {valid_request.limit}")
        print(f"   Date range: {valid_request.startdate} to {valid_request.enddate}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    print("\n" + "=" * 50 + "\n")

    # Test 2: Invalid symbol (special characters)
    print("2. Testing invalid symbol (special characters):")
    try:
        invalid_symbol = PriceRequest(symbol="BTC-USDT")
        print(f"❌ This should have failed: {invalid_symbol}")
    except Exception as e:
        print(f"✅ Validation caught error: {str(e)}")

    print("\n" + "=" * 50 + "\n")

    # Test 3: Invalid date format
    print("3. Testing invalid date format:")
    try:
        invalid_date = PriceRequest(symbol="BTCUSDT", startdate="2024-01-01")
        print(f"❌ This should have failed: {invalid_date}")
    except Exception as e:
        print(f"✅ Validation caught error: {str(e)}")

    print("\n" + "=" * 50 + "\n")

    # Test 4: Invalid limit range
    print("4. Testing invalid limit range:")
    try:
        invalid_limit = PriceRequest(symbol="BTCUSDT", limit=2000)
        print(f"❌ This should have failed: {invalid_limit}")
    except Exception as e:
        print(f"✅ Validation caught error: {str(e)}")

    print("\n" + "=" * 50 + "\n")

    # Test 5: Case conversion
    print("5. Testing case conversion (lowercase symbol):")
    try:
        case_request = PriceRequest(symbol="btcusdt")
        print(f"✅ Symbol converted to uppercase: {case_request.symbol}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    print("\n" + "=" * 50 + "\n")

    # Test 6: Interval enum
    print("6. Testing interval enum validation:")
    try:
        enum_request = PriceRequest(
            symbol="ETHUSDT",
            interval="5m",  # String representation
        )
        print(f"✅ Interval enum created: {enum_request.interval}")
        print(f"   Interval value: {enum_request.interval.value}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    print("\n" + "=" * 50 + "\n")

    # Test 7: Required field validation
    print("7. Testing required field (symbol):")
    try:
        missing_symbol = PriceRequest(interval=IntervalEnum.ONE_HOUR)
        print(f"❌ This should have failed: {missing_symbol}")
    except Exception as e:
        print(f"✅ Validation caught error: {str(e)}")

    print("\n=== Demo Complete ===")
    print("\nBenefits of Pydantic type checking:")
    print("• Automatic input validation")
    print("• Type conversion and coercion")
    print("• Custom validation rules")
    print("• Clear error messages")
    print("• Integration with FastAPI for automatic API documentation")
    print("• Runtime type checking without performance overhead")


if __name__ == "__main__":
    test_pydantic_validation()
