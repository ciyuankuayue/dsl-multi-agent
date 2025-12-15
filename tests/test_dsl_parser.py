# tests/test_dsl_parser.py
import unittest
from dsl_parser import SimpleDSLParser

class TestDSLParser(unittest.TestCase):
    
    def setUp(self):
        self.parser = SimpleDSLParser()
        self.sample_dsl = """
        scene main {
            intent greeting {
                reply "Hello"
            }
            intent check_price {
                reply "Price is $10"
                set step = "done"
            }
        }
        """

    def test_parse_structure(self):
        """测试基本的场景和意图解析结构"""
        result = self.parser.parse(self.sample_dsl)
        
        self.assertEqual(result['type'], 'script')
        self.assertEqual(len(result['scenes']), 1)
        
        scene = result['scenes'][0]
        self.assertEqual(scene['name'], 'main')
        self.assertEqual(len(scene['intents']), 2)

    def test_parse_statements(self):
        """测试语句解析准确性"""
        result = self.parser.parse(self.sample_dsl)
        intents = result['scenes'][0]['intents']
        
        # 检查 greeting 意图
        greeting_intent = next(i for i in intents if i['name'] == 'greeting')
        self.assertEqual(greeting_intent['statements'][0]['type'], 'reply')
        self.assertEqual(greeting_intent['statements'][0]['message'], 'Hello')
        
        # 检查 check_price 意图
        price_intent = next(i for i in intents if i['name'] == 'check_price')
        self.assertEqual(len(price_intent['statements']), 2)
        self.assertEqual(price_intent['statements'][1]['type'], 'set')
        self.assertEqual(price_intent['statements'][1]['variable'], 'step')
        self.assertEqual(price_intent['statements'][1]['value'], 'done')

if __name__ == '__main__':
    unittest.main()