"""后台任务调度器"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import asyncio
from typing import Callable

logger = logging.getLogger(__name__)

# 全局调度器实例
scheduler = AsyncIOScheduler()


def init_scheduler():
    """初始化调度器"""
    scheduler.start()
    print("后台任务调度器已启动")


def shutdown_scheduler():
    """关闭调度器"""
    scheduler.shutdown()
    print("后台任务调度器已关闭")


def add_interval_job(
    func: Callable,
    seconds: int = 60,
    args: tuple = None,
    kwargs: dict = None,
    job_id: str = None
):
    """添加定时任务（间隔执行）"""
    trigger = IntervalTrigger(seconds=seconds)
    return scheduler.add_job(
        func,
        trigger=trigger,
        args=args,
        kwargs=kwargs,
        id=job_id,
        replace_existing=True
    )


def add_cron_job(
    func: Callable,
    hour: int = 0,
    minute: int = 0,
    day: int = None,
    day_of_week: str = None,
    args: tuple = None,
    kwargs: dict = None,
    job_id: str = None
):
    """添加定时任务（Cron 表达式）；day 传每月几号，day_of_week 传 'sun'/'mon' 等或 None（每天）"""
    trigger = CronTrigger(hour=hour, minute=minute, day=day, day_of_week=day_of_week)
    return scheduler.add_job(
        func,
        trigger=trigger,
        args=args,
        kwargs=kwargs,
        id=job_id,
        replace_existing=True
    )


def remove_job(job_id: str):
    """移除定时任务"""
    scheduler.remove_job(job_id)


# ==================== 具体的后台任务 ====================

async def check_water_quality_alerts():
    """定时检查水质告警"""
    print(f"[{datetime.now()}] 执行水质告警检查...")
    # TODO: 实现水质告警检查逻辑
    # 1. 查询最新水质数据
    # 2. 检查是否超过阈值
    # 3. 发送告警通知


async def auto_feeding_task():
    """自动投喂任务"""
    print(f"[{datetime.now()}] 执行自动投喂检查...")
    # TODO: 实现智能投喂决策
    # 1. 获取当前水质
    # 2. 获取鱼类密度（AI识别）
    # 3. 计算投喂量
    # 4. 下发投喂指令


async def generate_daily_report():
    """生成日报"""
    print(f"[{datetime.now()}] 生成每日养殖报告...")
    # TODO: 生成日报逻辑
    # 1. 统计今日水质数据
    # 2. 统计投喂记录
    # 3. 统计告警记录
    # 4. 生成报告并保存


async def cleanup_old_data():
    """清理过期数据：执行存储层保留策略（app/services/retention.py）"""
    logger.info("清理过期数据...")
    try:
        from app.services.retention import (
            RetentionPolicy,
            enforce_retention,
            record_last_cleanup,
        )
        from app.services.storage import build_storage, StorageError

        storage = build_storage()
        deleted = enforce_retention(storage, RetentionPolicy.from_settings())
        record_last_cleanup(storage, deleted)
        logger.info("数据保留策略执行完成，清理对象数: %s", deleted)
    except StorageError as exc:
        logger.warning("数据清理跳过（存储后端不可用）: %s", exc)


def register_default_jobs():
    """注册默认的定时任务"""
    # 每5分钟检查一次水质告警
    add_interval_job(
        check_water_quality_alerts,
        seconds=300,
        job_id='water_quality_check'
    )
    
    # 每30分钟检查一次自动投喂
    add_interval_job(
        auto_feeding_task,
        seconds=1800,
        job_id='auto_feeding'
    )
    
    # 每天凌晨1点生成日报
    add_cron_job(
        generate_daily_report,
        hour=1,
        minute=0,
        job_id='daily_report'
    )
    
    # 每月1日凌晨3点清理数据（存储层保留策略）
    add_cron_job(
        cleanup_old_data,
        hour=3,
        minute=0,
        day=1,
        job_id='cleanup_data'
    )
    
    print("默认定时任务已注册")
