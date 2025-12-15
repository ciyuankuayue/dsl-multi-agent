# tests/test_interpreter.py
import unittest
from interpreter import DSLInterpreter
from state_manager import SessionStateManager
from tests.test_stubs import MockLLMClient # 导入桩

class TestInterpreterFlow(unittest.TestCase):
    
    def setUp(self):
        # 1. 设置桩和管理器
        self.mock_llm = MockLLMClient()
        # 使用内存临时目录或清理逻辑，这里简化直接用默认
        self.state_manager = SessionStateManager(persistence_dir="tests/temp_sessions")
        
        # 2. 初始化解释器
        self.interpreter = DSLInterpreter(self.mock_llm, self.state_manager)
        
        # 3. 手动构造一个简单的测试用 Script 对象 (模拟 DSL 解析后的结果)
        # 这样可以隔离 DSL Parser 的潜在 Bug，专注于测试解释器逻辑
        self.test_script = {
            'type': 'script',
            'scenes': [{
                'name': 'main',
                'intents': [
                    {
                        'name': 'greeting',
                        'statements': [{'type': 'reply', 'message': 'Welcome'}]
                    },
                    {
                        'name': 'query_product',
                        'statements': [
                            {'type': 'reply', 'message': 'What product?'},
                            {'type': 'set', 'variable': 'step', 'value': 'wait_prod'}
                        ]
                    },
                    {
                        'name': 'provide_product_name_price',
                        'statements': [
                            # 验证变量 step 必须为 wait_prod
                            {'type': 'validate', 'condition': 'current_step == "wait_prod"'}, 
                            {'type': 'set', 'variable': 'product', 'value': 'user_input'},
                            {'type': 'reply', 'message': 'Price for ${product} is $99'},
                            {'type': 'set', 'variable': 'step', 'value': ''}
                        ]
                    },
                    {
                        'name': 'default',
                        'statements': [{'type': 'reply', 'message': 'Sorry?'}]
                    }
                ]
            }]
        }
        self.interpreter.set_current_script(self.test_script)
        self.session_id = "test_session_001"
        self.state_manager.clear_session(self.session_id) # 确保干净的开始

    def test_rule_match_flow(self):
        """测试层级1：规则匹配 (查价格)"""
        # 桩中定义了 "查价格" -> query_product
        response = self.interpreter.execute("我要查价格", self.session_id)
        
        self.assertEqual(self.interpreter.state.current_intent, "query_product")
        self.assertEqual(response, "What product?")
        # 验证变量是否设置
        state = self.state_manager.get_state(self.session_id)
        self.assertEqual(state['variables'].get('step'), 'wait_prod')

    def test_llm_flow_with_context(self):
        """测试层级2：LLM 上下文理解 (查价格 -> 袜子)"""
        # 第一步：设置前置状态 (模拟已经问了问题)
        self.interpreter.state.variables['current_step'] = 'wait_prod' 
        self.state_manager.update_state(self.session_id, self.interpreter.state.to_dict())
        
        # 第二步：输入 "袜子"
        # 桩中定义了 "袜子" -> provide_product_name_price (如果可用意图包含它)
        response = self.interpreter.execute("袜子", self.session_id)
        
        # 验证意图
        self.assertEqual(self.interpreter.state.current_intent, "provide_product_name_price")
        # 验证变量替换 (${product} -> 袜子)
        self.assertEqual(response, "Price for 袜子 is $99")

    def test_validation_failure(self):
        """测试验证失败 (Validate Fail)"""
        # 状态中 step 为空，但意图要求 step == "wait_prod"
        self.interpreter.state.variables['current_step'] = '' 
        self.state_manager.update_state(self.session_id, self.interpreter.state.to_dict())
        
        # 桩会返回 provide_product_name_price，但 validate 应该失败
        response = self.interpreter.execute("袜子", self.session_id)
        
        # 因为 validate 失败，且没有其他匹配，应该会落入 default
        # 或者在我们的实现中，validate 失败返回 None，然后 execute 尝试 default
        self.assertIn("Sorry", response) # Default response

if __name__ == '__main__':
    unittest.main()