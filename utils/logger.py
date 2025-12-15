# utils/logger.py
import logging
import sys

def setup_logger(name):
    """配置并返回一个标准的日志对象"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO) # 默认级别
    
    # 防止重复添加 handler
    if not logger.handlers:
        ch = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
    return logger