# utils/config.py
import yaml
from pathlib import Path

def load_config(config_path: str = "config.yaml"):
    """加载 YAML 配置文件"""
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"配置文件未找到: {config_path}")
        
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        
    return config