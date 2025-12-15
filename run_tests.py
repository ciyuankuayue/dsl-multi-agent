# run_tests.py
import unittest
import sys
import os

def run_all_tests():
    """
    测试驱动程序：发现并运行 tests 目录下所有的测试用例
    """
    print("="*60)
    print("🤖 DSL Multi-Agent - 自动化测试套件")
    print("="*60)
    
    # 定义测试目录
    test_dir = 'tests'
    
    # 使用 TestLoader 自动发现以 test_ 开头的文件
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=test_dir, pattern='test_*.py')
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n✅ 所有测试通过！系统逻辑正常。")
        return 0
    else:
        print("\n❌ 测试失败！请检查代码。")
        return 1

if __name__ == '__main__':
    sys.exit(run_all_tests())