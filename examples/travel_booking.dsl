# examples/travel_booking.dsl
scene main {
    intent greeting {
        reply "您好！我是您的旅行助手。"
    }
    
    intent main_menu {
        reply "我可以帮您：\n1. 查询航班\n2. 预订酒店"
    }
    
    # --- 航班查询 ---
    intent query_flight {
        reply "请问您想飞往哪个城市？"
        set current_step = "waiting_destination"
    }
    
    intent provide_destination {
        validate current_step == "waiting_destination"
        set destination = user_input
        api_call search_flights(destination)
        set flight_info = result
        reply "为您找到去往 ${destination} 的航班：\n${flight_info}"
        set current_step = ""
        goto ask_more
    }
    
    # --- 酒店预订 ---
    intent book_hotel {
        reply "请问您计划什么日期入住？"
        set current_step = "waiting_checkin_date"
    }
    
    intent provide_checkin_date {
        validate current_step == "waiting_checkin_date"
        set date = user_input
        api_call search_hotels(date)
        set hotel_info = result
        reply "已为您查询 ${date} 的推荐酒店：\n${hotel_info}"
        set current_step = ""
        goto ask_more
    }
    
    intent ask_more {
        reply "还需要查其他行程吗？"
    }
    
    intent default {
        reply "抱歉，我只负责旅行预订。请说：查航班、订酒店。"
        goto main_menu
    }
}