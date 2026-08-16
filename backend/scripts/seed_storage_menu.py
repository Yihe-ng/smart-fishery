"""幂等播种"数据管理"菜单记录（按 menu_code 判重）。

用法: cd backend && python scripts/seed_storage_menu.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal  # noqa: E402
from app.models.menu import Menu  # noqa: E402


MENU = {
    "parent_id": 1,  # Fishery 目录
    "menu_name": "menus.fishery.dataManagement",
    "menu_code": "StorageStatus",
    "menu_type": 2,  # 菜单
    "icon": "ri:database-2-line",
    "path": "data-management",
    "component": "/fishery/data-management/index",
    "permission": "storage:status",
    "sort": 60,
    "status": 1,
}


def main() -> None:
    db = SessionLocal()
    try:
        existing = db.query(Menu).filter(Menu.menu_code == MENU["menu_code"]).first()
        if existing is not None:
            print(f"菜单已存在: id={existing.id} code={MENU['menu_code']}，跳过")
            return
        menu = Menu(**MENU)
        db.add(menu)
        db.commit()
        print(f"已插入菜单: id={menu.id} code={menu.menu_code} path={menu.path}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
