# tests/test_state_manager.py
import unittest
import shutil
from pathlib import Path
from state_manager import SessionStateManager

class TestStateManager(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = "tests/temp_db"
        self.manager = SessionStateManager(persistence_dir=self.test_dir)
        
    def tearDown(self):
        # 清理测试产生的临时文件
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)

    def test_create_and_get_session(self):
        session_id = "sess_1"
        self.manager.create_session(session_id, {"var": 1})
        
        state = self.manager.get_state(session_id)
        self.assertEqual(state["var"], 1)

    def test_update_persistence(self):
        session_id = "sess_2"
        self.manager.create_session(session_id)
        
        # 更新状态
        self.manager.update_state(session_id, {"step": "active"})
        
        # 重新初始化管理器 (模拟重启服务)
        new_manager = SessionStateManager(persistence_dir=self.test_dir)
        loaded_state = new_manager.get_state(session_id)
        
        # 验证数据是否持久化
        self.assertEqual(loaded_state["step"], "active")

if __name__ == '__main__':
    unittest.main()