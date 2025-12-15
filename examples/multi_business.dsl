# examples/multi_business.dsl
scene main {
    intent greeting {
        reply "您好！我是全能智能助理。"
    }
    
    intent main_menu {
        reply "请选择您需要的服务板块：\n1. 电商购物\n2. 旅行预订\n3. 客户服务"
    }
    
    # --- 路由跳转 ---
    intent select_ecommerce {
        reply "已切换至【电商购物】模式。您可以：查价格、查订单、下单。"
        goto ecommerce_scene
    }
    
    intent select_travel {
        reply "已切换至【旅行预订】模式。您可以：查航班、订酒店。"
        goto travel_scene
    }
    
    intent select_service {
        reply "已切换至【客户服务】模式。您可以：投诉、改密码、转人工。"
        goto service_scene
    }
    
    intent default {
        reply "请选择业务板块：电商、旅行、或客服。"
        goto main_menu
    }
}

# --- 模拟电商子场景 ---
scene ecommerce_scene {
    intent query_product {
        reply "【电商】请问查什么商品？"
        set current_step = "waiting_prod"
    }
    intent provide_product_name {
        validate current_step == "waiting_prod"
        set prod = user_input
        reply "【电商】${prod} 现价 99 元。"
        set current_step = ""
    }
    intent main_menu {
        reply "返回主菜单。"
        goto main
    }
}

# --- 模拟旅行子场景 ---
scene travel_scene {
    intent query_flight {
        reply "【旅行】请问飞往哪里？"
        set current_step = "waiting_dest"
    }
    intent provide_destination {
        validate current_step == "waiting_dest"
        set dest = user_input
        reply "【旅行】去往 ${dest} 的航班已查到。"
        set current_step = ""
    }
    intent main_menu {
        reply "返回主菜单。"
        goto main
    }
}

# --- 模拟客服子场景 ---
scene service_scene {
    intent contact_human {
        reply "【客服】正在呼叫人工坐席..."
    }
    intent main_menu {
        reply "返回主菜单。"
        goto main
    }
}