# interpreter.py
import re
from typing import Dict, List, Any, Optional, Union

from utils.logger import setup_logger
logger = setup_logger(__name__)

# [ConversationState, DSLInterpreter.__init__, set_current_script, execute_initial_greeting, execute, _get_available_intents 方法保持不变]
# -----------------------------------------------------------------------------------------------------------------------------------------
class ConversationState:
    """对话状态"""
    
    def __init__(self):
        self.history: List[Dict[str, str]] = []
        self.current_scene: str = "main"
        self.current_intent: str = ""
        self.variables: Dict[str, Any] = {}
        self.last_response: str = ""
        self.variables['current_step'] = ""
        self.variables['user_input'] = ""
        self.variables['result'] = ""
    
    def add_to_history(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        if len(self.history) > 20:
            self.history = self.history[-20:]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "history": self.history.copy(),
            "current_scene": self.current_scene,
            "current_intent": self.current_intent,
            "variables": self.variables.copy(),
            "last_response": self.last_response
        }
    
    def from_dict(self, state_dict: Dict[str, Any]):
        self.history = state_dict.get("history", []).copy()
        self.current_scene = state_dict.get("current_scene", "main")
        self.current_intent = state_dict.get("current_intent", "")
        self.variables = state_dict.get("variables", {}).copy()
        self.last_response = state_dict.get("last_response", "")
        for key in ['current_step', 'user_input', 'result']:
            if key not in self.variables:
                self.variables[key] = ""


class DSLInterpreter:
    """DSL解释器"""
    
    def __init__(self, llm_client, state_manager):
        self.llm_client = llm_client
        self.state_manager = state_manager
        self.current_script: Optional[Dict[str, Any]] = None
        self.state = ConversationState()
    
    def set_current_script(self, script: Dict[str, Any]):
        self.current_script = script
        if script and script.get('scenes'):
            self.state.current_scene = script['scenes'][0]['name']
    
    def execute_initial_greeting(self, session_id: str = "default") -> str:
        try:
            session_state = self.state_manager.get_state(session_id)
            self.state.from_dict(session_state)
            
            greeting_resp = self._execute_dsl_intent("greeting", "") 
            menu_resp = self._execute_dsl_intent("main_menu", "") 

            response = ""
            if greeting_resp and greeting_resp != "未找到意图的处理逻辑": response += greeting_resp
            if menu_resp and menu_resp != "未找到意图的处理逻辑":
                 if response: response += "\n"
                 response += menu_resp
            
            if not response: response = self._get_default_response("greeting")
            
            self.state.add_to_history("assistant", response)
            self.state_manager.update_state(session_id, self.state.to_dict())
            return response
        except Exception as e:
            logger.error(f"执行初始问候失败: {e}")
            return "系统初始化失败。"

    def execute(self, user_input: str, session_id: str = "default") -> str:
        try:
            session_state = self.state_manager.get_state(session_id)
            self.state.from_dict(session_state)
            self.state.variables['user_input'] = user_input
            
            available_intents = self._get_available_intents()
            intent_name = None
            response = None
            
            # 1. 规则匹配
            intent_name = self.llm_client.fallback_intent_recognition(user_input, available_intents)
            if intent_name:
                logger.info(f"执行层: 规则匹配命中意图 '{intent_name}'")
                response = self._execute_dsl_intent(intent_name, user_input)
            
            # 2. LLM 理解 (如果规则未命中，或者规则命中的意图执行中断/无回复)
            if not response:
                if not intent_name:
                    intent_name = self.llm_client.intelligent_intent_recognition(
                        user_input=user_input,
                        available_intents=available_intents,
                        conversation_context=self.state.history
                    )
                    logger.info(f"执行层: LLM 识别意图 '{intent_name}'")
                
                response = self._execute_dsl_intent(intent_name, user_input)
            
            # 3. 最终兜底
            if not response:
                if intent_name != "default" and "default" in available_intents:
                    response = self._execute_dsl_intent("default", user_input)
                
                if not response or response == "未找到意图的处理逻辑":
                     response = self._get_default_response(intent_name)

            self.state.current_intent = intent_name if intent_name else "N/A"
            self.state.add_to_history("user", user_input) 
            self.state.add_to_history("assistant", response)
            self.state.last_response = response
            self.state_manager.update_state(session_id, self.state.to_dict())
            
            return response
            
        except Exception as e:
            logger.error(f"执行出错: {e}")
            return f"系统错误: {e}"
    
    def _get_available_intents(self) -> List[str]:
        if not self.current_script: return ["greeting", "default"]
        all_intents = set()
        for scene in self.current_script.get('scenes', []):
            for intent in scene.get('intents', []):
                all_intents.add(intent['name'])
        return list(all_intents)

    # -----------------------------------------------------------------------------------------------------------------------------------------
    # ⚠️ 修正：确保 reply 后继续执行 set/goto，但 validate 失败必须中断
    def _execute_dsl_intent(self, intent_name: str, user_input: str) -> Optional[str]:
        """执行DSL意图"""
        if not self.current_script: return None
        
        intent_definition = None
        for scene in self.current_script.get('scenes', []):
            intent_definition = next((i for i in scene.get('intents', []) if i.get('name') == intent_name), None)
            if intent_definition: break
        
        if not intent_definition: return "未找到意图的处理逻辑"
        
        final_response = None
        for statement in intent_definition.get('statements', []):
            result = self._execute_statement(statement, user_input)
            
            # ⚠️ 关键修复 2：如果 validate 返回 False，立即停止该意图的执行，并返回 None（无回复）
            if result is False:
                logger.warning(f"意图 {intent_name} 执行被 validate 中断，返回 None")
                return None 
            
            # 如果结果是字符串（reply/ask），记录为最终回复
            if isinstance(result, str):
                final_response = result
                # ⚠️ 关键修复 1：不在这里 break，允许后续的 set/goto 语句被执行
        
        # 返回收集到的回复（如果存在），否则返回 None
        return final_response
    
    # -----------------------------------------------------------------------------------------------------------------------------------------
    # ⚠️ 修正：确保 validate 失败时返回 False
    def _execute_statement(self, statement: Dict[str, Any], user_input: str) -> Union[str, bool, None]:
        """
        执行单个语句
        Returns:
            str: 如果是 reply/ask
            False: 如果 validate 失败 (中断信号)
            None: 其他情况 (继续执行)
        """
        stmt_type = statement.get('type')
        
        if stmt_type == 'reply' or stmt_type == 'ask':
            key = 'message' if stmt_type == 'reply' else 'question'
            return self._replace_variables(statement.get(key, ''))
        
        elif stmt_type == 'goto':
            scene_name = statement.get('scene')
            if scene_name: self.state.current_scene = scene_name
            return None
        
        elif stmt_type == 'set':
            variable = statement.get('variable')
            value = statement.get('value')
            if variable and value is not None:
                final_value = self._replace_variables(str(value))
                if final_value == "user_input":
                    self.state.variables[variable] = user_input
                else:
                    self.state.variables[variable] = final_value
                logger.info(f"SET {variable} = {self.state.variables[variable]}")
            return None
        
        elif stmt_type == 'api_call':
            function = statement.get('function')
            arguments = statement.get('arguments', [])
            arg_values = [self._replace_variables(str(arg)) for arg in arguments]
            mock_result = f"【模拟数据: {function} 返回正常】"
            self.state.variables['result'] = mock_result
            logger.info(f"API CALL {function} -> {mock_result}")
            return None
        
        elif stmt_type == 'validate':
            condition = statement.get('condition')
            match = re.match(r'(\w+)\s*==\s*"(.*?)"', condition)
            if match:
                var_name = match.group(1)
                expected_value = match.group(2)
                current_value = self.state.variables.get(var_name, "")
                
                if current_value == expected_value:
                    logger.info(f"Validate pass: {var_name}=='{current_value}'")
                    return None 
                else:
                    logger.warning(f"Validate FAIL: {var_name} is '{current_value}', expected '{expected_value}'")
                    # ⚠️ 关键修正：返回 False 作为中断信号
                    return False 
            
            logger.warning(f"跳过无法解析的 validate: {condition}")
            return None

        return None
    
    def _replace_variables(self, text: str) -> str:
        if not isinstance(text, str): return text
        def replacer(match):
            var_name = match.group(1).strip()
            return str(self.state.variables.get(var_name, f"${{{var_name}}}"))
        return re.sub(r'\$\{(\w+)\}', replacer, text)
    
    def _get_default_response(self, intent_name: str) -> str:
        default_responses = {
            "greeting": "您好！我是智能客服助手。",
            "default": "抱歉，我没有听懂。请告诉我您是想【查价格】还是【查订单】？",
            "help": "请告诉我您需要什么帮助？"
        }
        return default_responses.get(intent_name, default_responses["default"])