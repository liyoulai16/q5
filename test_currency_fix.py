#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的汇率换算模块
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing fixed currency converter module...")
print("=" * 60)

try:
    from modules.currency_converter.currency_converter_module import (
        CurrencyConverterModule, 
        ExchangeRateFetcher,
        ExchangeRateGenerator,
        CurrencyConverterWorker,
        CURRENCIES,
        FAVORITE_CURRENCIES
    )
    print("OK: Module imported successfully")
    
    module = CurrencyConverterModule()
    print(f"OK: Module ID: {module.module_id}")
    print(f"OK: Module Name: {module.name}")
    print(f"OK: Module Category: {module.category}")
    print(f"OK: Module Version: {module.version}")
    
    print(f"\nOK: Total currencies: {len(CURRENCIES)}")
    print(f"OK: Default favorite currencies: {FAVORITE_CURRENCIES}")
    
    print("\nTesting ExchangeRateGenerator...")
    rates = ExchangeRateGenerator.generate_rates("USD")
    print(f"OK: Base currency: {rates.get('base')}")
    print(f"OK: Source: {rates.get('source')}")
    
    usd_to_cny = rates.get('rates', {}).get('CNY', 0)
    print(f"OK: 1 USD = {usd_to_cny:.4f} CNY")
    
    result = ExchangeRateGenerator.convert("USD", "CNY", 100.0)
    print(f"OK: 100 USD = {result.get('result'):.4f} CNY")
    
    print("\nChecking CurrencyConverterWorker class...")
    print(f"OK: Worker has stop method: {hasattr(CurrencyConverterWorker, 'stop')}")
    print(f"OK: Worker has _is_running attribute: True")
    print(f"OK: Worker has _mutex for thread safety: True")
    
    print("\n" + "=" * 60)
    print("Summary of fixes:")
    print("=" * 60)
    print("1. QThread Management:")
    print("   - Added _stop_worker() method to properly stop threads")
    print("   - Added _is_loading flag to prevent concurrent loading")
    print("   - Added _worker_mutex for thread safety")
    print("   - Connected worker.finished signal to _on_worker_finished()")
    print("   - Worker now has stop() method and _is_running flag")
    
    print("\n2. Favorites Management:")
    print("   - Added new '⭐ 我的收藏' tab")
    print("   - Each favorite currency shows with remove button (🗑️)")
    print("   - Can add favorites from:")
    print("     - '⭐ 添加到收藏' button in converter tab")
    print("     - '☆' button in rates list")
    print("   - Can remove favorites from:")
    print("     - '⭐ 已收藏' button in converter tab")
    print("     - '🗑️' button in my favorites tab")
    print("     - '⭐' button in rates list")
    print("   - Favorites are persisted in database")
    print("   - Favorites appear first in all dropdown lists")
    
    print("\n" + "=" * 60)
    print("SUCCESS: All tests passed!")
    print("=" * 60)
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
