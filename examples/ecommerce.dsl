# examples/ecommerce.dsl
# 电商客服场景DSL脚本

scene main {
    intent greeting {
        reply "您好！欢迎来到智能电商客服。"
    }
    
    intent main_menu {
        reply "请选择服务类型：\n1. 商品查询 (查价格/库存)\n2. 订单管理 (查订单)\n3. 下单购买\n请输入对应的数字或描述您的需求。"
    }
    
    # --- 商品查询模块 ---
    intent query_product {
        reply "请问您想查询什么商品的价格？"
        set current_step = "waiting_product_name_price"
    }
    
    intent provide_product_name_price {
        validate current_step == "waiting_product_name_price"
        set product_name = user_input
        api_call get_price(product_name)
        set price_result = result
        reply "您查询的${product_name}的价格是：${price_result}"
        set current_step = ""
        goto ask_further_help
    }
    
    # --- 订单管理模块 ---
    intent query_order {
        reply "请提供您的订单号："
        set current_step = "waiting_order_id"
    }
    
    intent provide_order_id {
        validate current_step == "waiting_order_id"
        set order_id = user_input
        api_call get_order_status(order_id)
        set status_result = result
        reply "订单号 ${order_id} 的状态是: ${status_result}"
        set current_step = ""
        goto ask_further_help
    }
    
    # --- 下单模块 (新增) ---
    intent place_order {
        reply "请问您要购买什么商品？"
        set current_step = "waiting_buy_product"
    }
    
    intent provide_buy_product {
        validate current_step == "waiting_buy_product"
        set buy_product = user_input
        # 模拟下单API
        api_call place_order_api(buy_product)
        set order_result = result
        reply "下单成功！您购买的 ${buy_product} 正在处理中。\n${order_result}"
        set current_step = ""
        goto ask_further_help
    }
    
    # --- 通用模块 ---
    intent ask_further_help {
        reply "请问还有其他可以帮您的吗？"
    }
    
    intent farewell {
        reply "感谢您的使用，再见！"
    }
    
    intent default {
        reply "抱歉，我没有理解您的意思。您可以说：查价格、查订单、下单等。"
        goto main_menu
    }
}