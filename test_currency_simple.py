#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试脚本
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing currency converter module...")
print("-" * 50)

try:
    from modules.currency_converter.currency_converter_module import (
        CurrencyConverterModule, 
        ExchangeRateFetcher,
        ExchangeRateGenerator,
        CURRENCIES,
        FAVORITE_CURRENCIES
    )
    print("OK: Module imported successfully")
    
    module = CurrencyConverterModule()
    print(f"OK: Module ID: {module.module_id}")
    print(f"OK: Module Name: {module.name}")
    print(f"OK: Module Category: {module.category}")
    print(f"OK: Module Version: {module.version}")
    
    print(f"OK: Total currencies: {len(CURRENCIES)}")
    print(f"OK: Favorite currencies: {FAVORITE_CURRENCIES}")
    
    print("Testing exchange rate generator...")
    rates = ExchangeRateGenerator.generate_rates("USD")
    print(f"OK: Base currency: {rates.get('base')}")
    print(f"OK: Source: {rates.get('source')}")
    
    usd_to_cny = rates.get('rates', {}).get('CNY', 0)
    print(f"OK: 1 USD = {usd_to_cny:.4f} CNY")
    
    result = ExchangeRateGenerator.convert("USD", "CNY", 100.0)
    print(f"OK: 100 USD = {result.get('result'):.4f} CNY")
    
    print("-" * 50)
    print("SUCCESS: All tests passed!")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
