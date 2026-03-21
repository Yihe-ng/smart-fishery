"""
交互式数据插入工具
使用方法：python -m app.db.insert_fdata
"""
import sys
import os
from datetime import datetime
from typing import Optional, Any, Dict, List, Type
from sqlalchemy import inspect
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.models.user import User
from app.models.water import WaterQualityData, SensorDevice, AlertRecord


class DataInserter:
    """交互式数据插入工具"""
    
    def __init__(self):
        self.db: Session = SessionLocal()
        self.tables = {
            "1": {"name": "用户表", "model": User, "icon": "👤"},
            "2": {"name": "水质数据表", "model": WaterQualityData, "icon": "📊"},
            "3": {"name": "传感器设备表", "model": SensorDevice, "icon": "📡"},
            "4": {"name": "告警记录表", "model": AlertRecord, "icon": "⚠️"},
        }
        
        self.field_ranges = {
            "WaterQualityData": {
                "dissolved_oxygen": {"min": 0, "max": 20, "unit": "mg/L", "desc": "溶解氧"},
                "ph_value": {"min": 0, "max": 14, "unit": "", "desc": "pH值"},
                "temperature": {"min": -10, "max": 50, "unit": "℃", "desc": "温度"},
                "ammonia_nitrogen": {"min": 0, "max": 2, "unit": "mg/L", "desc": "氨氮"},
                "nitrite": {"min": 0, "max": 1, "unit": "mg/L", "desc": "亚硝酸盐"},
            },
            "User": {
                "userName": {"min": 2, "max": 50, "desc": "用户名"},
                "email": {"pattern": "email", "desc": "邮箱"},
            },
            "AlertRecord": {
                "alert_level": {"options": ["info", "warning", "critical"], "desc": "告警级别"},
            },
        }
        
        self.default_values = {
            "User": {
                "status": 1,
                "role": "user",
            },
            "WaterQualityData": {
                "status": None,
                "collect_time": None,
            },
            "SensorDevice": {
                "status": "active",
            },
            "AlertRecord": {
                "is_resolved": 0,
                "collect_time": None,
            },
        }
    
    def get_table_count(self, model: Type) -> int:
        """获取表的数据量"""
        return self.db.query(model).count()
    
    def get_table_columns(self, model: Type) -> List[Dict]:
        """获取表的列信息"""
        inspector = inspect(model)
        columns = []
        
        for column in inspector.columns:
            col_info = {
                "name": column.name,
                "type": str(column.type),
                "nullable": column.nullable,
                "primary_key": column.primary_key,
                "default": column.default,
                "python_type": column.type.python_type,
            }
            columns.append(col_info)
        
        return columns
    
    def show_main_menu(self):
        """显示主菜单"""
        print("\n" + "=" * 60)
        print("🐟 智慧渔业数据插入工具")
        print("=" * 60)
        print("\n请选择要操作的表：")
        
        for key, table_info in self.tables.items():
            count = self.get_table_count(table_info["model"])
            print(f"  [{key}] {table_info['icon']} {table_info['name']} - 当前 {count} 条数据")
        
        print("\n  [0] 退出")
        print("=" * 60)
    
    def validate_input(self, value: str, col_info: Dict, table_name: str) -> tuple[bool, Any, str]:
        """
        验证用户输入
        
        返回: (是否有效, 转换后的值, 错误信息)
        """
        col_name = col_info["name"]
        python_type = col_info["python_type"]
        
        if not value or value.strip() == "":
            if not col_info["nullable"] and not col_info["primary_key"]:
                return False, None, "此字段为必填项"
            return True, None, ""
        
        value = value.strip()
        
        try:
            if python_type == int:
                converted_value = int(value)
            elif python_type == float:
                converted_value = float(value)
            elif python_type == str:
                converted_value = value
            elif python_type == datetime:
                converted_value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            else:
                converted_value = value
        except ValueError as e:
            return False, None, f"格式错误，需要 {python_type.__name__} 类型"
        
        if table_name in self.field_ranges and col_name in self.field_ranges[table_name]:
            range_info = self.field_ranges[table_name][col_name]
            
            if "min" in range_info and "max" in range_info:
                if isinstance(converted_value, (int, float)):
                    if not (range_info["min"] <= converted_value <= range_info["max"]):
                        return False, None, f"范围应在 {range_info['min']} - {range_info['max']} 之间"
            
            if "options" in range_info:
                if converted_value not in range_info["options"]:
                    return False, None, f"可选值: {', '.join(range_info['options'])}"
            
            if "pattern" in range_info and range_info["pattern"] == "email":
                if "@" not in converted_value or "." not in converted_value:
                    return False, None, "邮箱格式不正确"
        
        return True, converted_value, ""
    
    def get_field_description(self, col_name: str, table_name: str) -> str:
        """获取字段的描述信息"""
        if table_name in self.field_ranges and col_name in self.field_ranges[table_name]:
            range_info = self.field_ranges[table_name][col_name]
            desc = range_info.get("desc", col_name)
            unit = range_info.get("unit", "")
            
            if "min" in range_info and "max" in range_info:
                return f"{desc} (范围: {range_info['min']}-{range_info['max']}{unit})"
            elif "options" in range_info:
                return f"{desc} (可选: {', '.join(range_info['options'])})"
            else:
                return desc
        
        return col_name
    
    def auto_determine_status(self, data: Dict) -> str:
        """根据水质参数自动判断状态"""
        do = data.get("dissolved_oxygen", 0)
        ph = data.get("ph_value", 7)
        nh3 = data.get("ammonia_nitrogen", 0)
        no2 = data.get("nitrite", 0)
        
        if do < 5 or ph < 6.5 or ph > 8.5 or nh3 > 0.5 or no2 > 0.1:
            return "异常"
        return "正常"
    
    def input_data(self, model: Type, table_name: str) -> Optional[Dict]:
        """输入数据"""
        columns = self.get_table_columns(model)
        data = {}
        
        print("\n" + "-" * 60)
        print(f"📝 请输入数据（带 * 为必填项，回车跳过可选字段）")
        print("-" * 60 + "\n")
        
        for col_info in columns:
            col_name = col_info["name"]
            
            if col_info["primary_key"]:
                continue
            
            is_required = not col_info["nullable"]
            desc = self.get_field_description(col_name, table_name)
            required_mark = "*" if is_required else " "
            
            default_val = None
            if table_name in self.default_values and col_name in self.default_values[table_name]:
                default_val = self.default_values[table_name][col_name]
                if default_val is None and col_name in ["collect_time", "createTime"]:
                    default_val = datetime.now()
            
            while True:
                prompt = f"{required_mark} {desc}"
                if default_val is not None:
                    if isinstance(default_val, datetime):
                        prompt += f" (默认: {default_val.strftime('%Y-%m-%d %H:%M:%S')})"
                    else:
                        prompt += f" (默认: {default_val})"
                
                prompt += ": "
                value = input(prompt)
                
                if value.strip() == "" and default_val is not None:
                    data[col_name] = default_val
                    break
                
                is_valid, converted_value, error_msg = self.validate_input(value, col_info, table_name)
                
                if is_valid:
                    if converted_value is not None:
                        data[col_name] = converted_value
                    break
                else:
                    print(f"  ❌ {error_msg}")
        
        if table_name == "WaterQualityData" and "status" not in data:
            data["status"] = self.auto_determine_status(data)
            print(f"\n  ✓ 状态自动判断为: {data['status']}")
        
        return data
    
    def preview_data(self, data: Dict, model: Type, table_name: str):
        """预览数据"""
        print("\n" + "-" * 60)
        print("📝 数据预览：")
        print("-" * 60)
        
        for key, value in data.items():
            if isinstance(value, datetime):
                value_str = value.strftime("%Y-%m-%d %H:%M:%S")
            else:
                value_str = str(value)
            
            desc = self.get_field_description(key, table_name)
            print(f"  {desc}: {value_str}")
        
        print("-" * 60)
    
    def insert_data(self, model: Type, data: Dict) -> bool:
        """插入数据到数据库"""
        try:
            instance = model(**data)
            self.db.add(instance)
            self.db.commit()
            self.db.refresh(instance)
            print(f"\n✅ 数据插入成功！ID: {instance.id}")
            return True
        except Exception as e:
            self.db.rollback()
            print(f"\n❌ 插入失败: {str(e)}")
            return False
    
    def run(self):
        """运行主循环"""
        try:
            while True:
                self.show_main_menu()
                choice = input("\n请输入选项: ").strip()
                
                if choice == "0":
                    print("\n👋 退出程序")
                    break
                
                if choice not in self.tables:
                    print("\n❌ 无效选项，请重新选择")
                    continue
                
                table_info = self.tables[choice]
                model = table_info["model"]
                table_name = model.__tablename__
                
                print(f"\n{'=' * 60}")
                print(f"{table_info['icon']} {table_info['name']}")
                print("=" * 60)
                
                data = self.input_data(model, table_name)
                
                if data is None:
                    continue
                
                self.preview_data(data, model, table_name)
                
                confirm = input("\n确认插入？: ").strip().lower()
                if confirm in ["y", "yes", "是", "确认"]:
                    self.insert_data(model, data)
                else:
                    print("\n❌ 已取消插入")
                
                continue_insert = input("\n是否继续插入？: ").strip().lower()
                if continue_insert not in ["y", "yes", "是", "继续"]:
                    print("\n按回车键返回主菜单...")
                    input()
        
        except KeyboardInterrupt:
            print("\n\n👋 程序已中断")
        finally:
            self.db.close()


def main():
    """主函数"""
    print("\n正在初始化数据库连接...")
    
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库连接成功\n")
        
        inserter = DataInserter()
        inserter.run()
    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
