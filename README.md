# 🤖 SmartDSLAgent - 基于 DSL 与 LLM 的智能多业务 Agent

**SmartDSLAgent** 是一个融合了 **领域特定语言 (DSL)** 规则引擎与 **大语言模型 (LLM)** 语义理解能力的智能对话系统框架。

该项目旨在解决传统规则式机器人不够灵活、纯 LLM 机器人难以控制业务流程的问题。通过自定义的 DSL 脚本定义业务逻辑，结合智谱 AI (GLM-4) 的意图识别能力，实现了精确控制与自然交互的完美平衡。

---

## ✨ 核心特性

* **🧠 三层意图识别架构**：
    1.  **规则优先层**：基于关键词的毫秒级精确匹配，优先处理明确指令。
    2.  **LLM 语义层**：基于上下文的深度语义理解，解决“查袜子”与“查价格”的歧义，精准区分“发起请求”与“回答问题”。
    3.  **兜底保障层**：优雅处理未知请求，引导用户回到业务主线。
* **📝 自定义 DSL 语言**：使用简洁的类 C/JSON 风格脚本语言定义场景 (`scene`)、意图 (`intent`) 和流程控制 (`goto`, `validate`)，业务逻辑修改无需动代码。
* **💾 会话状态管理**：支持多轮对话，内置变量存储 (`set`)、槽位填充与 JSON 文件持久化机制。
* **🌍 多业务场景支持**：一套架构支持电商、旅行、客服等多种业务，支持业务间的动态路由切换。
* **🛡️ 健壮的工程实践**：包含完整的单元测试、集成测试桩 (Test Stubs) 和自动化测试驱动。

---

## 📂 项目结构

```text
DSL-Multi-Agent/
├── examples/                  # DSL 业务脚本范例
│   ├── ecommerce.dsl          # 电商场景（查价格、下单）
│   ├── travel_booking.dsl     # 旅行场景（订机票、酒店）
│   ├── customer_service.dsl   # 客服场景（报修、转人工）
│   └── multi_business.dsl     # [推荐] 多业务路由综合场景
├── tests/                     # 测试套件
│   ├── __init__.py
│   ├── test_dsl_parser.py     # DSL 解析器单元测试
│   ├── test_interpreter.py    # 解释器流程集成测试
│   ├── test_state_manager.py  # 状态持久化测试
│   └── test_stubs.py          # LLM Mock 测试桩
├── utils/                     # 工具模块
│   ├── __init__.py
│   ├── config.py              # 配置加载
│   └── logger.py              # 日志配置
├── config.yaml                # 配置文件 (API Key)
├── dsl_parser.py              # DSL 语法解析器 (支持嵌套结构)
├── interpreter.py             # 核心解释器 (三层逻辑引擎)
├── llm_client.py              # LLM 客户端 (Prompt Engineering)
├── state_manager.py           # 会话状态管理器
├── smart_main.py              # 程序主入口
├── run_tests.py               # 自动化测试驱动
└── requirements.txt           # 项目依赖
🚀 快速开始1. 
环境准备确保您的环境安装了 Python 3.8+。
Bash
# 1. 安装依赖
pip install -r requirements.txt
requirements.txt 内容：
Plaintextzhipuai
PyYAML
2. 配置 API 
密钥打开 config.yaml 文件，填入您的智谱 AI API Key：
YAML
zhipuai:
  api_key: "您的智谱API密钥_粘贴在这里"  # <--- 请务必修改这里
  model: "glm-4"
  temperature: 0.1
3. 运行 Agent
方式一：
运行综合多业务场景（推荐）这是模拟超级 App 的入口，支持在电商、旅行、客服之间切换。Bashpython smart_main.py -s examples/multi_business.dsl
方式二：
运行特定业务场景Bashpython smart_main.py -s examples/ecommerce.dsl
📖 DSL 语法指南
本项目使用一套自定义 DSL 来描述对话逻辑。
核心概念
Scene (场景): 业务逻辑的容器，如 main。
Intent (意图): 用户的具体动作，如 query_product。
Statements (语句): 执行的具体指令。
语法范例代码段
# 定义一个场景
scene main {
    # 定义意图：查询商品
    intent query_product {
        reply "请问您想查询什么商品？"
        # 设置当前步骤，用于上下文校验
        set current_step = "waiting_product_name"
    }

    # 定义意图：提供商品名 (用于回答上一问)
    intent provide_product_name {
        # 验证当前步骤，防止流程跳跃
        validate current_step == "waiting_product_name"
        
        # 获取用户输入并赋值给变量
        set product = user_input
        
        # 调用模拟API (仅作演示，不产生真实网络请求)
        api_call get_price(product)
        
        # 使用 ${变量名} 进行插值
        reply "${product} 的价格是：${result}"
        
        # 清空步骤，重置状态
        set current_step = ""
        
        # 跳转到其他意图
        goto ask_more
    }
}
支持的指令
指令,说明,示例
reply,机器人回复文本,"reply ""您好"""
set,设置变量,"set key = ""value"" 或 set item = user_input"
validate,验证条件，失败则中断,"validate step == ""waiting"""
goto,跳转场景或意图,goto main_menu
api_call,模拟 API 调用,api_call check_stock(item)
🧪 测试与验证
本项目包含完整的自动化测试套件，使用 测试桩 (Mock) 技术，无需消耗 API Token 即可验证核心逻辑。
运行所有测试
Bash
python run_tests.py
测试内容说明
DSL 解析测试 (test_dsl_parser.py): 验证嵌套大括号、多行语句的解析准确性。
解释器流程测试 (test_interpreter.py):
验证规则匹配优先逻辑。
验证上下文 Slot Filling (如“查价格” -> “袜子”的流程)。
验证 validate 失败后的阻断机制。
状态持久化测试 (test_state_manager.py):
 验证会话数据能否正确保存到磁盘并加载。
 🧠 技术原理：如何解决“死循环”与“误识别”？在传统 LLM 意图识别中，用户输入“袜子”往往会被误识别为“发起查询”，导致机器人重复反问“查什么？”。本项目通过以下机制彻底解决该问题：
 System Prompt 强化：在 llm_client.py 中明确定义了意图边界，强制区分“发起请求”与“回答问题”。
 上下文历史注入：将最近的对话历史传给 LLM。如果助手上一句问的是“查什么商品？”，LLM 会被强制引导识别为参数填充意图 (provide_...)。
 状态机校验：DSL 中的 validate current_step == ... 确保只有在特定流程节点下，参数填充意图才会被执行。
 规则过滤：对于“飞机几点飞”等无关问题，通过 Prompt 约束 LLM 返回 default，避免幻觉回复。