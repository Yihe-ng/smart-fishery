from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String
from sqlalchemy.sql import func

from app.db.base import Base


class Menu(Base):
    """持久化菜单、页面和按钮权限。"""

    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, nullable=False, default=0, index=True)
    menu_name = Column(String(128), nullable=False)
    menu_code = Column(String(128), nullable=False)
    menu_type = Column(Integer, nullable=False, default=2)
    icon = Column(String(128), nullable=True)
    path = Column(String(256), nullable=True)
    component = Column(String(256), nullable=True)
    permission = Column(String(128), nullable=True)
    sort = Column(Integer, nullable=False, default=0)
    status = Column(Integer, nullable=False, default=1, index=True)
    roles = Column(JSON, nullable=True)
    keep_alive = Column(Boolean, nullable=True)
    is_hide = Column(Boolean, nullable=True)
    is_hide_tab = Column(Boolean, nullable=True)
    link = Column(String(512), nullable=True)
    is_iframe = Column(Boolean, nullable=True)
    show_badge = Column(Boolean, nullable=True)
    show_text_badge = Column(String(64), nullable=True)
    fixed_tab = Column(Boolean, nullable=True)
    active_path = Column(String(256), nullable=True)
    is_full_page = Column(Boolean, nullable=True)
    create_time = Column(DateTime, server_default=func.now(), nullable=False)
    update_time = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def role_list(self) -> Optional[List[str]]:
        """将 JSON 角色字段规范化为前端可消费的列表。"""
        if not self.roles:
            return None
        return [str(role) for role in self.roles]
