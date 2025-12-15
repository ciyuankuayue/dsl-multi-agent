# examples/customer_service.dsl
scene main {
    intent greeting {
        reply "您好！这里是客户服务中心。"
    }
    
    intent main_menu {
        reply "自助服务：\n1. 投诉反馈\n2. 忘记密码\n3. 转人工客服"
    }
    
    intent report_issue {
        reply "很抱歉给您带来不便。请简要描述您遇到的问题："
        set current_step = "waiting_issue"
    }
    
    intent provide_issue_detail {
        validate current_step == "waiting_issue"
        set issue = user_input
        api_call submit_ticket(issue)
        set ticket_id = result
        reply "反馈已收到。工单号：${ticket_id}，我们会尽快处理。"
        set current_step = ""
    }
    
    intent faq_password {
        reply "重置密码请访问官网：www.example.com/reset，或在设置中点击'忘记密码'。"
    }
    
    intent contact_human {
        reply "正在为您转接人工客服，请稍候...（当前排队人数：3人）"
    }
    
    intent default {
        reply "您可以说：投诉、忘记密码、转人工。"
        goto main_menu
    }
}