# tests/test_stubs.py
from typing import List, Dict, Optional
import logging

# 引入真实类的接口定义（不需要引入具体实现，只要保持签名一致）
# 这里我们模拟 llm_client.py 中的 LLMClient

class MockLLMClient:
    """
    [测试桩] 模拟 LLM 客户端。
    不调用真实 API，而是根据预设的输入返回固定的意图。
    用于测试 Interpreter 的流程控制逻辑。
    """
    def __init__(self):
        self.call_history = [] # 记录调用历史，用于验证

    def intelligent_intent_recognition(self, user_input: str, available_intents: List[str], 
                                      conversation_context: List[Dict[str, str]]) -> str:
        """模拟智能意图识别"""
        self.call_history.append({"input": user_input, "method": "intelligent"})
        
        # --- 预设的测试场景逻辑 ---
        
        # 场景1：商品查询流程
        if "袜子" in user_input and "provide_product_name_price" in available_intents:
            return "provide_product_name_price"
        
        if "查价格" in user_input or "商品查询" in user_input:
            return "query_product"
            
        # 场景2：订单查询流程
        if "123456" in user_input and "provide_order_id" in available_intents:
            return "provide_order_id"
            
        if "查订单" in user_input:
            return "query_order"
        
        # 场景3：无关问题
        if "飞机" in user_input:
            return "default"
            
        # 默认返回
        return "default"

    def fallback_intent_recognition(self, user_input: str, available_intents: List[str]) -> Optional[str]:
        """模拟规则匹配 (简单复用逻辑，或者也可以Mock)"""
        self.call_history.append({"input": user_input, "method": "fallback"})
        
        # 简单的关键词模拟
        if "查订单" in user_input:
            return "query_order"
        if "查价格" in user_input:
            return "query_product"
            
        return None