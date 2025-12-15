# smart_main.py
#!/usr/bin/env python3
"""
智能多业务场景Agent主程序
支持真正的自然语言理解和多轮对话
"""

import argparse
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dsl_parser import SimpleDSLParser
from interpreter import DSLInterpreter 
from llm_client import LLMClient
from state_manager import SessionStateManager
from utils.logger import setup_logger
from utils.config import load_config

logger = setup_logger(__name__)

class SmartDSLAgent:
    """智能DSL Agent主类"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """初始化智能DSL Agent"""
        self.config = load_config(config_path)
        
        # 检查API密钥 (使用get安全访问)
        api_key = self.config.get('zhipuai', {}).get('api_key')
        if not api_key or api_key == "你的智谱API密钥":
            print("❌ 错误：未配置智谱AI API密钥")
            print("请编辑 config.yaml 文件，填入您的智谱AI API密钥")
            sys.exit(1)
        
        # 初始化各个组件
        self.dsl_parser = SimpleDSLParser()
        self.llm_client = LLMClient(
            api_key=api_key,
            model=self.config.get('zhipuai', {}).get('model', 'glm-4'),
            temperature=self.config.get('zhipuai', {}).get('temperature', 0.1)
        )
        self.state_manager = SessionStateManager()
        # 确保 interpreter 被正确初始化
        self.interpreter = DSLInterpreter(
            llm_client=self.llm_client,
            state_manager=self.state_manager
        )
        
        # 加载的脚本
        self.loaded_scripts = {}
        
    def load_script(self, script_path: str) -> str:
        """加载并解析DSL脚本"""
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
            
            # 解析脚本
            parsed_script = self.dsl_parser.parse(script_content)
            script_name = Path(script_path).stem
            
            # 保存到加载的脚本中
            self.loaded_scripts[script_name] = parsed_script
            self.interpreter.set_current_script(parsed_script)
            
            logger.info(f"成功加载脚本: {script_name}")
            return script_name
            
        except Exception as e:
            logger.error(f"加载脚本失败: {e}")
            raise
    
    def process_input(self, user_input: str, session_id: str = "default") -> str:
        """处理用户输入 - 智能对话"""
        try:
            # 处理输入
            response = self.interpreter.execute(user_input, session_id)
            
            return response
            
        except Exception as e:
            logger.error(f"处理输入时出错: {e}")
            return f"抱歉，处理您的请求时出现错误。请稍后再试。"
    
    def interactive_mode(self, script_path: str):
        """交互式模式 - 真正的智能对话"""
        print("\n" + "="*60)
        print("🤖 智能多业务场景Agent - 交互式模式")
        print("="*60)
        
        # 加载脚本
        script_name = self.load_script(script_path)
        print(f"✅ 已加载脚本: {script_name}")
        
        session_id = "smart_session"
        conversation_count = 0

        # 关键修复：调用 interpreter 的方法执行初始问候语
        initial_response = self.interpreter.execute_initial_greeting(session_id)
        
        print("\n💬 输入 'quit' 或 'exit' 退出对话")
        print("-"*60)
        
        # 显示 DSL 脚本定义的初始问候
        print(f"\n🤖 Agent: {initial_response}") 
        
        while True:
            try:
                # 获取用户输入
                user_input = input("\n👤 您: ").strip()
                
                if user_input.lower() in ['quit', 'exit', '退出', '结束', 'bye']:
                    print("\n🤖 Agent: 感谢您的使用！再见，祝您生活愉快！")
                    break
                
                if not user_input:
                    continue
                
                conversation_count += 1
                
                # 处理输入并显示响应
                print(f"\n🤖 正在思考...", end="")
                # 调用 process_input
                response = self.process_input(user_input, session_id)
                print(f"\r🤖 Agent: {response}")
                
                # 显示对话统计
                if conversation_count % 5 == 0:
                    print(f"\n📊 已进行 {conversation_count} 轮对话")
                
            except KeyboardInterrupt:
                print("\n\n⏹️  对话被中断")
                break
            except Exception as e:
                logger.error(f"交互模式出错: {e}")
                print(f"⚠️  发生错误: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="🤖 智能多业务场景Agent - 基于DSL的智能客服机器人"
    )
    
    parser.add_argument(
        "--script", "-s",
        type=str,
        default="examples/multi_business.dsl",
        help="DSL脚本文件路径（默认: examples/multi_business.dsl）"
    )
    
    parser.add_argument(
        "--config", "-c",
        type=str,
        default="config.yaml",
        help="配置文件路径（默认: config.yaml）"
    )
    
    args = parser.parse_args()
    
    # 检查脚本文件
    script_path = Path(args.script)
    if not script_path.exists():
        print(f"❌ 错误：脚本文件不存在 {args.script}")
        print("可用脚本：")
        examples_dir = Path("examples")
        if examples_dir.exists():
            for f in examples_dir.glob("*.dsl"):
                print(f"  - {f}")
        sys.exit(1)
    
    try:
        # 创建Agent实例
        print("🚀 正在启动智能多业务Agent...")
        agent = SmartDSLAgent(args.config)
        
        # 运行交互模式
        agent.interactive_mode(args.script)
        
    except FileNotFoundError as e:
        print(f"❌ 文件未找到: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 程序运行出错: {e}")
        logger.exception("程序运行出错")
        sys.exit(1)

if __name__ == "__main__":
    main()