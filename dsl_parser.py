# dsl_parser.py
import re
from typing import Dict, List, Any

class SimpleDSLParser:
    """基于行状态机的DSL解析器（支持嵌套结构）"""
    
    @staticmethod
    def parse(script_content: str) -> Dict[str, Any]:
        """
        解析 DSL 脚本
        """
        result = {'type': 'script', 'scenes': []}
        
        # 预处理：按行分割，去除空白和注释
        raw_lines = script_content.split('\n')
        lines = []
        for line in raw_lines:
            line = line.split('#')[0].strip() # 去除注释和首尾空格
            if line:
                lines.append(line)
        
        # 状态变量
        current_scene = None
        current_intent = None
        
        # 遍历每一行进行解析
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # 1. 匹配 Scene 开始: scene main {
            scene_match = re.match(r'scene\s+(\w+)\s*\{', line)
            if scene_match:
                scene_name = scene_match.group(1)
                current_scene = {
                    'type': 'scene',
                    'name': scene_name,
                    'intents': []
                }
                result['scenes'].append(current_scene)
                current_intent = None # 进入新场景，重置意图
                i += 1
                continue
            
            # 2. 匹配 Intent 开始: intent greeting {
            intent_match = re.match(r'intent\s+(\w+)\s*\{', line)
            if intent_match:
                if current_scene is None:
                    raise ValueError(f"Line {i+1}: Intent defined outside of a scene.")
                
                intent_name = intent_match.group(1)
                current_intent = {
                    'type': 'intent',
                    'name': intent_name,
                    'statements': []
                }
                current_scene['intents'].append(current_intent)
                i += 1
                continue
            
            # 3. 匹配结束大括号 }
            if line == '}':
                # 如果当前在意图里，这个 } 结束意图
                if current_intent is not None:
                    current_intent = None
                # 如果当前不在意图里但在场景里，这个 } 结束场景
                elif current_scene is not None:
                    current_scene = None
                i += 1
                continue
            
            # 4. 解析语句 (Statements)
            # 只有在 Intent 内部才解析语句
            if current_intent is not None:
                statement = SimpleDSLParser._parse_single_statement(line)
                if statement:
                    current_intent['statements'].append(statement)
            
            i += 1
            
        return result
    
    @staticmethod
    def _parse_single_statement(line: str) -> Any:
        """解析单行语句"""
        # 关键字匹配
        keywords = ['reply', 'ask', 'goto', 'set', 'validate', 'api_call']
        
        for keyword in keywords:
            if line.startswith(keyword + ' '):
                args = line[len(keyword):].strip()
                
                if keyword == 'reply':
                    return {'type': 'reply', 'message': SimpleDSLParser._clean_string(args)}
                
                elif keyword == 'ask':
                    return {'type': 'ask', 'question': SimpleDSLParser._clean_string(args)}
                
                elif keyword == 'goto':
                    return {'type': 'goto', 'scene': args}
                
                elif keyword == 'set':
                    # set var = val
                    match = re.match(r'(\w+)\s*=\s*(.+)', args)
                    if match:
                        return {
                            'type': 'set', 
                            'variable': match.group(1), 
                            'value': SimpleDSLParser._clean_string(match.group(2))
                        }
                
                elif keyword == 'api_call':
                    # api_call func(args)
                    match = re.match(r'(\w+)\((.*?)\)', args)
                    if match:
                        func_name = match.group(1)
                        args_str = match.group(2)
                        arg_list = [SimpleDSLParser._clean_string(a.strip()) for a in args_str.split(',') if a.strip()]
                        return {'type': 'api_call', 'function': func_name, 'arguments': arg_list}
                
                elif keyword == 'validate':
                    return {'type': 'validate', 'condition': args}
                    
        return None
    
    @staticmethod
    def _clean_string(text: str) -> Any:
        """清理字符串引号"""
        text = text.strip()
        # 处理引号
        if (text.startswith('"') and text.endswith('"')) or \
           (text.startswith("'") and text.endswith("'")):
            return text[1:-1]
        
        # 关键字
        if text == 'user_input':
            return 'user_input'
            
        return text