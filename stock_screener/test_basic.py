#!/usr/bin/env python3
"""
基本功能测试脚本
测试数据获取和筛选算法的基本功能
"""
import sys
import traceback
from datetime import datetime, timedelta

def test_imports():
    """测试所有必要的导入"""
    print("测试导入...")
    try:
        import flask
        import akshare as ak
        import pandas as pd
        import requests
        import openpyxl
        print("✓ 所有依赖包导入成功")
        return True
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_akshare_connection():
    """测试AkShare数据连接"""
    print("测试AkShare数据连接...")
    try:
        import akshare as ak
        # 获取少量股票数据进行测试
        data = ak.stock_zh_a_spot_em()
        if data is not None and len(data) > 0:
            print(f"✓ AkShare连接成功，获取到 {len(data)} 条股票数据")
            return True
        else:
            print("✗ AkShare连接失败，没有获取到数据")
            return False
    except Exception as e:
        print(f"✗ AkShare连接失败: {e}")
        return False

def test_data_fetcher():
    """测试数据获取模块"""
    print("测试数据获取模块...")
    try:
        from data_fetcher import StockDataFetcher
        fetcher = StockDataFetcher()
        
        # 测试获取股票列表
        stocks = fetcher.get_all_stocks()
        if stocks is not None and len(stocks) > 0:
            print(f"✓ 股票数据获取成功，共 {len(stocks)} 只股票")
            
            # 测试获取单只股票历史数据
            test_code = stocks.iloc[0]['代码']
            hist_data = fetcher.get_stock_history(test_code, days=5)
            if hist_data is not None:
                print(f"✓ 历史数据获取成功，股票 {test_code}")
                return True
            else:
                print(f"✗ 历史数据获取失败，股票 {test_code}")
                return False
        else:
            print("✗ 股票数据获取失败")
            return False
            
    except Exception as e:
        print(f"✗ 数据获取模块测试失败: {e}")
        traceback.print_exc()
        return False

def test_screener():
    """测试筛选算法"""
    print("测试筛选算法...")
    try:
        from stock_screener import StockScreener
        screener = StockScreener()
        
        print("注意：完整筛选需要较长时间，这里仅测试模块加载...")
        print("✓ 筛选模块加载成功")
        return True
        
    except Exception as e:
        print(f"✗ 筛选模块测试失败: {e}")
        traceback.print_exc()
        return False

def test_flask_app():
    """测试Flask应用"""
    print("测试Flask应用...")
    try:
        from main import app
        print("✓ Flask应用加载成功")
        return True
    except Exception as e:
        print(f"✗ Flask应用测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """运行所有测试"""
    print("A股自救股票筛选工具 - 基本功能测试")
    print("=" * 50)
    
    tests = [
        ("导入测试", test_imports),
        ("AkShare连接测试", test_akshare_connection),
        ("数据获取模块测试", test_data_fetcher),
        ("筛选算法模块测试", test_screener),
        ("Flask应用测试", test_flask_app)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n[{test_name}]")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ {test_name} 发生异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("✓ 所有测试通过！可以启动应用")
        print("启动命令: python main.py")
    elif passed >= 3:
        print("⚠ 基本功能可用，但可能存在问题")
        print("可以尝试启动应用: python main.py")
    else:
        print("✗ 多项测试失败，请检查环境配置")
    
    return passed == total

if __name__ == "__main__":
    main()