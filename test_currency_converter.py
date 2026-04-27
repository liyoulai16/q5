#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
汇率换算模块测试脚本
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_module_import():
    """测试模块导入"""
    print("测试1: 导入汇率换算模块...")
    try:
        from modules.currency_converter.currency_converter_module import (
            CurrencyConverterModule, 
            ExchangeRateFetcher,
            ExchangeRateGenerator,
            CURRENCIES,
            FAVORITE_CURRENCIES
        )
        print("✓ 模块导入成功")
        return True
    except Exception as e:
        print(f"✗ 模块导入失败: {e}")
        return False

def test_module_class():
    """测试模块类"""
    print("\n测试2: 创建模块实例...")
    try:
        from modules.currency_converter.currency_converter_module import CurrencyConverterModule
        from modules.module_manager import ModuleCategory
        
        module = CurrencyConverterModule()
        
        print(f"  模块ID: {module.module_id}")
        print(f"  模块名称: {module.name}")
        print(f"  模块描述: {module.description}")
        print(f"  模块版本: {module.version}")
        print(f"  模块分类: {module.category}")
        print(f"  分类名称: {ModuleCategory.CATEGORY_NAMES.get(module.category)}")
        
        assert module.module_id == "currency_converter"
        assert module.name == "汇率换算"
        assert module.category == ModuleCategory.LIFE_TOOLS
        
        print("✓ 模块类测试成功")
        return True
    except Exception as e:
        print(f"✗ 模块类测试失败: {e}")
        return False

def test_currencies_data():
    """测试货币数据"""
    print("\n测试3: 测试货币数据...")
    try:
        from modules.currency_converter.currency_converter_module import CURRENCIES, FAVORITE_CURRENCIES
        
        print(f"  支持的货币数量: {len(CURRENCIES)}")
        print(f"  常用货币数量: {len(FAVORITE_CURRENCIES)}")
        
        for code in FAVORITE_CURRENCIES:
            currency = CURRENCIES.get(code, {})
            print(f"  - {code}: {currency.get('name', '未知')} {currency.get('flag', '')}")
        
        assert 'USD' in CURRENCIES
        assert 'CNY' in CURRENCIES
        assert 'EUR' in CURRENCIES
        
        print("✓ 货币数据测试成功")
        return True
    except Exception as e:
        print(f"✗ 货币数据测试失败: {e}")
        return False

def test_exchange_rate_generator():
    """测试模拟汇率生成器"""
    print("\n测试4: 测试模拟汇率生成器...")
    try:
        from modules.currency_converter.currency_converter_module import ExchangeRateGenerator
        
        print("  生成USD为基准的汇率...")
        rates_usd = ExchangeRateGenerator.generate_rates("USD")
        print(f"  基准货币: {rates_usd.get('base')}")
        print(f"  数据来源: {rates_usd.get('source')}")
        
        usd_to_cny = rates_usd.get('rates', {}).get('CNY', 0)
        print(f"  1 USD = {usd_to_cny:.4f} CNY")
        
        print("\n  生成CNY为基准的汇率...")
        rates_cny = ExchangeRateGenerator.generate_rates("CNY")
        print(f"  基准货币: {rates_cny.get('base')}")
        
        cny_to_usd = rates_cny.get('rates', {}).get('USD', 0)
        print(f"  1 CNY = {cny_to_usd:.6f} USD")
        
        print("\n  测试货币转换...")
        result = ExchangeRateGenerator.convert("USD", "CNY", 100.0)
        print(f"  100 USD = {result.get('result'):.4f} CNY")
        print(f"  汇率: {result.get('rate'):.6f}")
        
        print("✓ 模拟汇率生成器测试成功")
        return True
    except Exception as e:
        print(f"✗ 模拟汇率生成器测试失败: {e}")
        return False

def test_currency_format():
    """测试货币格式化"""
    print("\n测试5: 测试货币格式化...")
    try:
        from modules.currency_converter.currency_converter_module import ExchangeRateFetcher
        
        for code in ['USD', 'CNY', 'EUR', 'JPY', 'GBP']:
            display = ExchangeRateFetcher.format_currency_display(code)
            print(f"  {code}: {display}")
        
        print("✓ 货币格式化测试成功")
        return True
    except Exception as e:
        print(f"✗ 货币格式化测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("汇率换算模块测试")
    print("=" * 60)
    
    tests = [
        test_module_import,
        test_module_class,
        test_currencies_data,
        test_exchange_rate_generator,
        test_currency_format,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ 测试异常: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  测试{i+1}: {status} - {test.__name__}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过!")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查代码")
        return 1

if __name__ == '__main__':
    sys.exit(main())
