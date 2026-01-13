"""Data models for database entities"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Any, Dict

@dataclass
class User:
    """User model"""
    id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    balance: int = 0
    bank_balance: int = 0
    level: int = 0
    experience: int = 0
    kills: int = 0
    deaths: int = 0
    is_protected: bool = False
    protection_end_time: Optional[float] = None
    last_work_time: Optional[float] = None
    last_daily_time: Optional[float] = None
    last_rob_time: Optional[float] = None
    is_warned: bool = False
    warning_count: int = 0
    is_muted: bool = False
    mute_end_time: Optional[float] = None
    is_banned: bool = False
    ban_reason: Optional[str] = None
    couple_id: Optional[int] = None
    couple_since: Optional[float] = None
    created_at: float = None
    updated_at: float = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Item:
    """Item model"""
    id: int
    name: str
    price: int
    emoji: str
    description: str
    added_by: Optional[int] = None
    created_at: float = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class BotSetting:
    """Bot setting model"""
    key: str
    value: Any
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Couple:
    """Couple model"""
    id: int
    user1_id: int
    user2_id: int
    couple_since: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Warning:
    """Warning model"""
    id: int
    user_id: int
    reason: str
    warned_at: float
    warned_by: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Game:
    """Game model"""
    id: int
    game_type: str
    group_id: int
    creator_id: int
    status: str  # 'waiting', 'playing', 'finished'
    players: list
    started_at: float
    ended_at: Optional[float] = None
    winner_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
