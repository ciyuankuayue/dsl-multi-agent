# llm_client.py
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from zhipuai import ZhipuAI
from utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class LLMConfig:
    api_key: str
    model: str = "glm-4"
    temperature: float = 0.1
    max_tokens: int = 256
    timeout: int = 30

class LLMClient:
    """基于智谱AI的LLM客户端，支持多业务场景意图识别"""
    
    def __init__(self, api_key: str, model: str = "glm-4", temperature: float = 0.1):
        self.config = LLMConfig(api_key=api_key, model=model, temperature=temperature)
        self.client = ZhipuAI(api_key=api_key)
        
        # --- 全场景意图描述映射 (强化上下文逻辑) ---
        self.intent_descriptions = {
            # --- 通用基础 ---
            "greeting": "用户打招呼，如你好、开始。",
            "farewell": "用户再见、结束对话。",
            "main_menu": "用户请求返回主菜单。",
            "ask_further_help": "用户询问还有什么功能。",
            "default": "无法识别或与当前业务无关的问题。",
            
            # --- 电商业务 (重点修复) ---
            # 关键：强调“发起”必须是完整的请求，或者在非回答状态下
            "query_product": "【发起查询】用户主动要求查价格。例：'查价格'、'我想买东西'。❌注意：如果用户只说了一个商品名（如'袜子'）且助手刚才问了'查什么'，绝对不要选这个！",
            
            # 关键：强调“回答”的触发条件
            "provide_product_name": "【回答参数】用户提供商品名称。✅触发条件：助手上一句问了'请问查什么商品'，用户回答'袜子'、'蛋糕'等。",
            
            "query_order": "【发起查询】用户查订单状态、查物流。",
            "provide_order_id": "【回答参数】用户提供订单号。✅触发条件：助手上一句问了'请提供订单号'。",
            "place_order": "【发起查询】用户想要下单购买。",
            "provide_buy_product": "【回答参数】用户提供要购买的商品名。",

            # --- 旅行预订 ---
            "query_flight": "【发起查询】用户查询航班。",
            "provide_destination": "【回答参数】用户提供目的地（如北京）。✅触发条件：助手问了'飞往哪里'。",
            "book_hotel": "【发起查询】用户想要预订酒店。",
            "provide_checkin_date": "【回答参数】用户提供日期。",
            
            # --- 客户服务 ---
            "report_issue": "【发起查询】用户投诉、反馈问题。",
            "provide_issue_detail": "【回答参数】用户描述问题细节。",
            "contact_human": "【发起查询】用户要求转人工。",
            "faq_password": "【发起查询】用户询问密码问题。",
            
            # --- 多业务路由 ---
            "select_ecommerce": "用户选择进入'电商购物'模式。",
            "select_travel": "用户选择进入'旅行预订'模式。",
            "select_service": "用户选择进入'客户服务'模式。",
        }
        
        # 强化 System Prompt，教 LLM 判断“是不是在回答问题”
        self.system_prompt_intent = """你是一个业务意图识别助手。
核心任务：区分【发起请求】和【回答问题】。

判断逻辑：
1. **看对话历史**：这是最重要的！
   - 如果助手上一句是“请问查什么商品？”，用户输入“袜子”，这一定是 `provide_product_name`，绝不是 `query_product`。
   - 如果助手上一句是“请提供订单号？”，用户输入“123”，这一定是 `provide_order_id`。
   
2. **看用户输入**：
   - 如果是动词+名词（“查袜子价格”），倾向于【发起请求】。
   - 如果纯名词（“袜子”），且上下文在等待输入，倾向于【回答问题】。

3. **路由选择**：
   - 如果用户输入菜单名（“电商”、“旅行”），选择对应的 `select_...` 意图。
"""
    
    def intelligent_intent_recognition(self, user_input: str, available_intents: List[str], 
                                      conversation_context: List[Dict[str, str]]) -> str:
        if not available_intents: return "default"

        try:
            history_str = "无"
            if conversation_context:
                # 取最近 2 条即可，过多的历史反而干扰
                recent_msgs = conversation_context[-2:]
                history_list = []
                for msg in recent_msgs:
                    role = "用户" if msg.get("role") == "user" else "助手"
                    content = msg.get("content", "")
                    history_list.append(f"{role}: {content}")
                history_str = "\n".join(history_list)
            
            # 过滤意图
            all_target_intents = list(set(available_intents + ["default"]))
            intents_desc_list = []
            for intent in all_target_intents:
                desc = self.intent_descriptions.get(intent, "业务操作")
                intents_desc_list.append(f"- {intent}: {desc}")
            
            prompt = f"""
【对话历史 (注意助手的最后一个问题)】：
{history_str}

【用户当前输入】："{user_input}"

【可用意图列表】：
{chr(10).join(intents_desc_list)}

【判断】：基于对话历史，用户是在发起新请求还是在回答问题？请返回意图名称。"""
            
            messages = [
                {"role": "system", "content": self.system_prompt_intent},
                {"role": "user", "content": prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            if response.choices:
                intent = response.choices[0].message.content.strip().replace("'", "").replace('"', "")
                if intent in all_target_intents:
                    logger.info(f"LLM识别意图: '{user_input[:15]}...' -> '{intent}'")
                    return intent
            return "default"
                
        except Exception as e:
            logger.error(f"LLM识别异常: {e}")
            return "default"

    def fallback_intent_recognition(self, user_input: str, available_intents: List[str]) -> Optional[str]:
        """规则匹配"""
        user_input_lower = user_input.lower()
        
        # ⚠️ 注意：这里不要放纯名词（如“袜子”），只放强意图词
        keyword_intent_map = {
            'greeting': ['你好', '您好', '开始'],
            'farewell': ['再见', '拜拜', '结束'],
            'main_menu': ['主菜单', '返回菜单', '退出'],
            
            'query_product': ['价格', '商品查询', '价钱'],
            'query_order': ['订单', '物流', '快递'],
            'place_order': ['下单', '购买'],
            
            'query_flight': ['航班', '机票', '飞往'],
            'book_hotel': ['酒店', '宾馆', '住宿'],
            
            'report_issue': ['投诉', '坏了', '故障', '报错'],
            'contact_human': ['人工', '转人工', '真人'],
            'faq_password': ['忘记密码', '改密码'],
            
            # 路由关键词 (保持短语匹配)
            'select_ecommerce': ['电商', '购物', '买东西'],
            'select_travel': ['旅行', '旅游', '订票'],
            'select_service': ['客服', '客户', '服务'],
        }
        
        for intent_name, keywords in keyword_intent_map.items():
            if intent_name in available_intents:
                for keyword in keywords:
                    if keyword in user_input_lower:
                        logger.info(f"规则匹配成功: '{user_input[:15]}...' -> '{intent_name}'")
                        return intent_name
        return None