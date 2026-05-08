"""Smart feeding service."""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from typing import Dict, Optional

from sqlalchemy.orm import Session

from app.agent.real_data import agent_db_session, get_water_quality_snapshot
from app.websocket.manager import manager


class SmartFeedingService:
    """Generate feeding recommendations and execute feeder commands."""

    def __init__(self):
        self.config = {
            "dissolved_oxygen_threshold": 5.0,
            "temperature_optimal": (22, 28),
            "ph_optimal": (6.5, 8.5),
            "max_feeding_amount": 2000,
            "min_feeding_amount": 100,
            "feeding_times": ["08:00", "12:00", "18:00"],
            "feed_conversion_ratio": 1.6,
        }

    def calculate_feeding_plan(
        self,
        pond_id: str,
        current_index: int | None = None,
        fish_count: int = 1000,
        avg_fish_weight: float = 300,
        db: Optional[Session] = None,
    ) -> Dict:
        water_quality = self._load_water_quality(
            pond_id, current_index=current_index, db=db
        )
        if water_quality is None:
            return {
                "can_feed": False,
                "reason": "无法获取水质数据",
                "suggestion": "请先确认水质传感器和数据库采集链路是否正常。",
            }

        water_assessment = self._assess_water_quality(water_quality)
        if not water_assessment["suitable"]:
            return {
                "can_feed": False,
                "reason": water_assessment["reason"],
                "water_quality": {
                    "dissolved_oxygen": water_quality.dissolved_oxygen,
                    "temperature": water_quality.temperature,
                    "ph": water_quality.ph_value,
                },
            }

        total_biomass = fish_count * avg_fish_weight
        base_amount = total_biomass * 0.025
        adjustment_factors = self._calculate_adjustment_factors(water_quality)
        final_amount = base_amount * adjustment_factors["total_factor"]
        final_amount = max(
            self.config["min_feeding_amount"],
            min(final_amount, self.config["max_feeding_amount"]),
        )
        optimal_time = self._determine_optimal_time(water_quality)
        suggestion = self._generate_suggestion(
            water_quality, adjustment_factors, final_amount
        )

        return {
            "can_feed": True,
            "pond_id": pond_id,
            "recommended_amount": round(final_amount, 2),
            "optimal_time": optimal_time,
            "confidence": adjustment_factors["confidence"],
            "factors": adjustment_factors,
            "water_quality": {
                "dissolved_oxygen": water_quality.dissolved_oxygen,
                "temperature": water_quality.temperature,
                "ph": water_quality.ph_value,
                "ammonia_nitrogen": water_quality.ammonia_nitrogen,
                "nitrite": water_quality.nitrite,
            },
            "suggestion": suggestion,
            "estimated_duration": int(final_amount / 100),
        }

    def _load_water_quality(
        self,
        pond_id: str,
        current_index: int | None = None,
        db: Optional[Session] = None,
    ) -> SimpleNamespace | None:
        with agent_db_session(db) as session:
            snapshot = get_water_quality_snapshot(
                pond_id, current_index=current_index, db=session
            )
        if snapshot is None:
            return None

        return SimpleNamespace(
            dissolved_oxygen=snapshot["dissolved_oxygen"],
            temperature=snapshot["temperature"],
            ph_value=snapshot["ph"],
            ammonia_nitrogen=snapshot["ammonia_nitrogen"],
            nitrite=snapshot["nitrite"],
        )

    def _assess_water_quality(self, water_quality) -> Dict:
        reasons = []
        if water_quality.dissolved_oxygen < 3:
            return {
                "suitable": False,
                "reason": "溶解氧低于 3mg/L，建议先增氧再投喂。",
            }
        if water_quality.dissolved_oxygen < 5:
            reasons.append("溶解氧偏低")

        if water_quality.temperature < 15 or water_quality.temperature > 35:
            return {
                "suitable": False,
                "reason": f"水温 {water_quality.temperature}°C 过于极端，暂不建议投喂。",
            }

        if water_quality.ph_value < 6 or water_quality.ph_value > 9:
            return {
                "suitable": False,
                "reason": f"pH 值 {water_quality.ph_value} 异常，暂不建议投喂。",
            }

        if water_quality.ammonia_nitrogen > 1.0:
            reasons.append("氨氮偏高")
        if water_quality.nitrite > 0.2:
            reasons.append("亚硝酸盐偏高")

        if reasons:
            return {
                "suitable": True,
                "reason": "，".join(reasons) + "，建议适当降低投喂量。",
                "caution": True,
            }
        return {"suitable": True, "reason": "水质整体适宜投喂。"}

    def _calculate_adjustment_factors(self, water_quality) -> Dict:
        factors = {
            "oxygen_factor": 1.0,
            "temperature_factor": 1.0,
            "ph_factor": 1.0,
            "ammonia_factor": 1.0,
            "nitrite_factor": 1.0,
        }

        do_value = water_quality.dissolved_oxygen
        if do_value < 3:
            factors["oxygen_factor"] = 0.3
        elif do_value < 5:
            factors["oxygen_factor"] = 0.6
        elif do_value > 8:
            factors["oxygen_factor"] = 1.2

        temp = water_quality.temperature
        optimal_min, optimal_max = self.config["temperature_optimal"]
        if temp < 15 or temp > 35:
            factors["temperature_factor"] = 0.2
        elif temp < optimal_min:
            factors["temperature_factor"] = (
                0.5 + (temp - 15) / (optimal_min - 15) * 0.5
            )
        elif temp > optimal_max:
            factors["temperature_factor"] = (
                0.5 + (35 - temp) / (35 - optimal_max) * 0.5
            )

        ph_value = water_quality.ph_value
        ph_min, ph_max = self.config["ph_optimal"]
        if ph_value < 6.5 or ph_value > 8.5:
            factors["ph_factor"] = 0.7
        elif ph_value < ph_min or ph_value > ph_max:
            factors["ph_factor"] = 0.85

        ammonia = water_quality.ammonia_nitrogen
        if ammonia > 0.5:
            factors["ammonia_factor"] = 0.7
        elif ammonia > 0.3:
            factors["ammonia_factor"] = 0.85

        nitrite = water_quality.nitrite
        if nitrite > 0.1:
            factors["nitrite_factor"] = 0.8
        elif nitrite > 0.05:
            factors["nitrite_factor"] = 0.9

        total_factor = 1.0
        for factor in factors.values():
            total_factor *= factor

        deviations = [abs(factor - 1) for factor in factors.values()]
        avg_deviation = sum(deviations) / len(deviations)
        confidence = max(0.5, 1 - avg_deviation)

        factors["total_factor"] = round(total_factor, 2)
        factors["confidence"] = round(confidence, 2)
        return factors

    def _determine_optimal_time(self, water_quality) -> str:
        current_hour = datetime.now().hour
        if water_quality.dissolved_oxygen < 5:
            return "10:00"

        for time_str in self.config["feeding_times"]:
            hour = int(time_str.split(":")[0])
            if hour > current_hour:
                return time_str
        return f"明天 {self.config['feeding_times'][0]}"

    def _generate_suggestion(
        self,
        water_quality,
        factors: Dict,
        final_amount: float,
    ) -> str:
        suggestions = []
        if factors["oxygen_factor"] < 0.8:
            suggestions.append("溶解氧偏低，建议先增氧并减少投喂量")
        elif factors["oxygen_factor"] > 1.1:
            suggestions.append("溶解氧充足，可按计划投喂")

        if factors["temperature_factor"] < 0.8:
            suggestions.append("水温偏离适宜区间，需保守投喂")
        if factors["ammonia_factor"] < 0.8:
            suggestions.append("氨氮偏高，建议减料并关注换水")
        if factors["nitrite_factor"] < 0.8:
            suggestions.append("亚硝酸盐偏高，建议减少投喂")

        if not suggestions:
            suggestions.append("水质状态良好，可按推荐量投喂")

        suggestions.append(f"本次建议投喂约 {round(final_amount, 2)}g。")
        return "；".join(suggestions)

    async def execute_feeding(
        self,
        feeder_id: str,
        amount: float,
        duration: int,
    ) -> Dict:
        try:
            await manager.send_command(
                feeder_id,
                "feed",
                {"amount": amount, "duration": duration},
            )
            return {
                "success": True,
                "feeder_id": feeder_id,
                "amount": amount,
                "duration": duration,
                "status": "command_sent",
            }
        except Exception as exc:
            return {
                "success": False,
                "feeder_id": feeder_id,
                "error": str(exc),
            }


smart_feeding_service = SmartFeedingService()
