# state_manager.py
import json
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, field
from utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class SessionState:
    """会话状态"""
    session_id: str
    state_data: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)

class SessionStateManager:
    """会话状态管理器"""
    
    def __init__(self, persistence_dir: str = "sessions", session_timeout: int = 3600):
        """
        初始化状态管理器
        
        Args:
            persistence_dir: 持久化存储目录
            session_timeout: 会话超时时间（秒）
        """
        self.persistence_dir = Path(persistence_dir)
        self.persistence_dir.mkdir(parents=True, exist_ok=True) # 确保目录存在
        self.sessions: Dict[str, SessionState] = {}
        self.session_timeout = session_timeout
        self._load_persisted_sessions()
    
    def create_session(self, session_id: str, initial_state: Optional[Dict[str, Any]] = None) -> str:
        """创建新会话"""
        if session_id in self.sessions:
            logger.warning(f"会话已存在: {session_id}")
            return session_id
        
        state = SessionState(
            session_id=session_id,
            state_data=initial_state or {}
        )
        self.sessions[session_id] = state
        logger.info(f"创建新会话: {session_id}")
        self._persist_session(session_id) # 创建时立即持久化
        return session_id
    
    def get_state(self, session_id: str) -> Dict[str, Any]:
        """获取会话状态"""
        self._cleanup_expired_sessions()
        
        if session_id not in self.sessions:
            self.create_session(session_id)
        
        session = self.sessions[session_id]
        session.last_activity = time.time()
        
        # 返回深拷贝以防止外部直接修改内存状态
        return session.state_data.copy()
    
    def update_state(self, session_id: str, new_state: Dict[str, Any]):
        """更新会话状态"""
        if session_id not in self.sessions:
            self.create_session(session_id)
        
        session = self.sessions[session_id]
        session.state_data = new_state.copy()
        session.updated_at = time.time()
        session.last_activity = time.time()
        
        self._persist_session(session_id)
    
    def clear_session(self, session_id: str):
        """
        [新增] 清空指定会话的状态数据
        用于测试或重置会话
        """
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.state_data = {} # 清空数据
            session.updated_at = time.time()
            session.last_activity = time.time()
            self._persist_session(session_id) # 立即保存更改
            logger.info(f"已清空会话数据: {session_id}")
        else:
            # 如果会话不存在，创建一个空的
            self.create_session(session_id)

    def _cleanup_expired_sessions(self):
        """清理过期会话"""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if current_time - session.last_activity > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.delete_session(session_id)
    
    def _persist_session(self, session_id: str):
        """持久化会话状态"""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        session_file = self.persistence_dir / f"{session_id}.json"
        
        try:
            # 准备序列化数据
            persist_data = {
                "session_id": session.session_id,
                "state_data": session.state_data,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
                "last_activity": session.last_activity
            }
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(persist_data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"持久化会话: {session_id}")
            
        except Exception as e:
            logger.error(f"持久化会话失败 {session_id}: {e}")
    
    def _load_persisted_sessions(self):
        """
        [新增实现] 加载持久化的会话
        遍历目录下的 JSON 文件并恢复状态
        """
        if not self.persistence_dir.exists():
            return

        try:
            for session_file in self.persistence_dir.glob("*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 检查数据完整性
                    if "session_id" not in data:
                        continue
                        
                    session_id = data["session_id"]
                    
                    # 恢复 SessionState 对象
                    session = SessionState(
                        session_id=session_id,
                        state_data=data.get("state_data", {}),
                        created_at=data.get("created_at", time.time()),
                        updated_at=data.get("updated_at", time.time()),
                        last_activity=data.get("last_activity", time.time())
                    )
                    
                    self.sessions[session_id] = session
                    
                except Exception as e:
                    logger.warning(f"加载会话文件失败 {session_file}: {e}")
                    
            logger.info(f"已加载 {len(self.sessions)} 个持久化会话")
            
        except Exception as e:
            logger.error(f"遍历会话目录失败: {e}")
        
    def delete_session(self, session_id: str):
        """删除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            
        # 即使内存中没有，也要尝试删除文件
        session_file = self.persistence_dir / f"{session_id}.json"
        if session_file.exists():
            try:
                session_file.unlink()
                logger.info(f"删除会话及文件: {session_id}")
            except Exception as e:
                logger.error(f"删除会话文件失败: {e}")