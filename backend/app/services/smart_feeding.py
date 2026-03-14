"""智能投喂服务"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.websocket.manager import manager
import asyncio


class MockWaterQuality:
    """模拟水质数据"""
    def __init__(self):
        self.dissolved_oxygen = 6.8  # 溶解氧 mg/L
        self.temperature = 25.5      # 温度 ℃
        self.ph_value = 7.2           # pH值
        self.ammonia_nitrogen = 0.3   # 氨氮 mg/L
        self.nitrite = 0.05           # 亚硝酸盐 mg/L


class SmartFeedingService:
    """智能投喂服务"""
    
    def __init__(self):
        # 投喂规则配置
        self.config = {
            'dissolved_oxygen_threshold': 5.0,  # 溶解氧阈值 mg/L
            'temperature_optimal': (22, 28),     # 最佳温度范围 ℃
            'ph_optimal': (6.5, 8.5),           # 最佳 pH 范围
            'max_feeding_amount': 2000,          # 最大投喂量 g
            'min_feeding_amount': 100,           # 最小投喂量 g
            'feeding_times': ['08:00', '12:00', '18:00'],  # 默认投喂时间
            'feed_conversion_ratio': 1.6         # 饲料转化率
        }
    
    async def calculate_feeding_plan(
        self,
        pond_id: str,
        fish_count: int = 1000,
        avg_fish_weight: float = 300  # 克
    ) -> Dict:
        """
        计算智能投喂计划
        
        综合考虑：
        1. 当前水质状况
        2. 鱼类生长阶段
        3. 历史投喂效果
        4. 天气/环境因子
        """
        
        # 1. 模拟获取当前水质
        water_quality = MockWaterQuality()
        if not water_quality:
            return {
                'can_feed': False,
                'reason': '无法获取水质数据',
                'suggestion': '请检查传感器连接'
            }
        
        # 2. 评估水质是否适合投喂
        water_assessment = self._assess_water_quality(water_quality)
        if not water_assessment['suitable']:
            return {
                'can_feed': False,
                'reason': water_assessment['reason'],
                'water_quality': {
                    'dissolved_oxygen': water_quality.dissolved_oxygen,
                    'temperature': water_quality.temperature,
                    'ph': water_quality.ph_value
                }
            }
        
        # 3. 计算基础投喂量（体重的 2-3%）
        total_biomass = fish_count * avg_fish_weight  # 总生物量(g)
        base_amount = total_biomass * 0.025  # 按 2.5% 计算
        
        # 4. 应用调整因子
        adjustment_factors = self._calculate_adjustment_factors(water_quality)
        final_amount = base_amount * adjustment_factors['total_factor']
        
        # 5. 限制在合理范围内
        final_amount = max(
            self.config['min_feeding_amount'],
            min(final_amount, self.config['max_feeding_amount'])
        )
        
        # 6. 确定最佳投喂时间
        optimal_time = self._determine_optimal_time(water_quality)
        
        # 7. 生成建议
        suggestion = self._generate_suggestion(
            water_quality, adjustment_factors, final_amount
        )
        
        return {
            'can_feed': True,
            'pond_id': pond_id,
            'recommended_amount': round(final_amount, 2),
            'optimal_time': optimal_time,
            'confidence': adjustment_factors['confidence'],
            'factors': adjustment_factors,
            'water_quality': {
                'dissolved_oxygen': water_quality.dissolved_oxygen,
                'temperature': water_quality.temperature,
                'ph': water_quality.ph_value,
                'ammonia_nitrogen': water_quality.ammonia_nitrogen,
                'nitrite': water_quality.nitrite
            },
            'suggestion': suggestion,
            'estimated_duration': int(final_amount / 100)  # 假设 100g/分钟
        }
    
    def _assess_water_quality(self, water_quality) -> Dict:
        """评估水质是否适合投喂"""
        reasons = []
        
        # 检查溶解氧
        if water_quality.dissolved_oxygen < 3:
            return {
                'suitable': False,
                'reason': '溶解氧严重不足(<3mg/L)，鱼类食欲低下，建议增氧后再投喂'
            }
        elif water_quality.dissolved_oxygen < 5:
            reasons.append('溶解氧偏低')
        
        # 检查温度
        if water_quality.temperature < 15 or water_quality.temperature > 35:
            return {
                'suitable': False,
                'reason': f'温度极端({water_quality.temperature}℃)，鱼类处于应激状态，暂停投喂'
            }
        
        # 检查 pH
        if water_quality.ph_value < 6 or water_quality.ph_value > 9:
            return {
                'suitable': False,
                'reason': f'pH值异常({water_quality.ph_value})，水质不稳定，暂停投喂'
            }
        
        # 检查氨氮
        if water_quality.ammonia_nitrogen > 1.0:
            reasons.append('氨氮含量过高')
        
        # 检查亚硝酸盐
        if water_quality.nitrite > 0.2:
            reasons.append('亚硝酸盐超标')
        
        if reasons:
            return {
                'suitable': True,
                'reason': '；'.join(reasons) + '，建议适当减少投喂量',
                'caution': True
            }
        
        return {
            'suitable': True,
            'reason': '水质良好，适合投喂'
        }
    
    def _calculate_adjustment_factors(self, water_quality) -> Dict:
        """计算投喂量调整因子"""
        factors = {
            'oxygen_factor': 1.0,
            'temperature_factor': 1.0,
            'ph_factor': 1.0,
            'ammonia_factor': 1.0,
            'nitrite_factor': 1.0
        }
        
        # 溶解氧因子
        do = water_quality.dissolved_oxygen
        if do < 3:
            factors['oxygen_factor'] = 0.3
        elif do < 5:
            factors['oxygen_factor'] = 0.6
        elif do > 8:
            factors['oxygen_factor'] = 1.2
        
        # 温度因子
        temp = water_quality.temperature
        optimal_min, optimal_max = self.config['temperature_optimal']
        if temp < 15 or temp > 35:
            factors['temperature_factor'] = 0.2
        elif temp < optimal_min:
            factors['temperature_factor'] = 0.5 + (temp - 15) / (optimal_min - 15) * 0.5
        elif temp > optimal_max:
            factors['temperature_factor'] = 0.5 + (35 - temp) / (35 - optimal_max) * 0.5
        
        # pH 因子
        ph = water_quality.ph_value
        ph_min, ph_max = self.config['ph_optimal']
        if ph < 6.5 or ph > 8.5:
            factors['ph_factor'] = 0.7
        elif ph < ph_min or ph > ph_max:
            factors['ph_factor'] = 0.85
        
        # 氨氮因子
        nh3 = water_quality.ammonia_nitrogen
        if nh3 > 0.5:
            factors['ammonia_factor'] = 0.7
        elif nh3 > 0.3:
            factors['ammonia_factor'] = 0.85
        
        # 亚硝酸盐因子
        no2 = water_quality.nitrite
        if no2 > 0.1:
            factors['nitrite_factor'] = 0.8
        elif no2 > 0.05:
            factors['nitrite_factor'] = 0.9
        
        # 计算总因子和置信度
        total_factor = 1.0
        for factor in factors.values():
            total_factor *= factor
        
        # 置信度：因子越接近 1，置信度越高
        deviations = [abs(f - 1) for f in factors.values()]
        avg_deviation = sum(deviations) / len(deviations)
        confidence = max(0.5, 1 - avg_deviation)
        
        factors['total_factor'] = round(total_factor, 2)
        factors['confidence'] = round(confidence, 2)
        
        return factors
    
    def _determine_optimal_time(self, water_quality) -> str:
        """确定最佳投喂时间"""
        current_hour = datetime.now().hour
        
        # 根据溶解氧选择时间
        if water_quality.dissolved_oxygen < 5:
            # 溶氧低，选择溶氧较高的时段（通常是上午）
            return '10:00'
        
        # 正常情况，按标准时间选择下一个
        for time_str in self.config['feeding_times']:
            hour = int(time_str.split(':')[0])
            if hour > current_hour:
                return time_str
        
        # 如果今天的都过了，返回明天的第一个时间
        return f"明天 {self.config['feeding_times'][0]}"
    
    def _generate_suggestion(
        self,
        water_quality,
        factors: Dict,
        final_amount: float
    ) -> str:
        """生成投喂建议"""
        suggestions = []
        
        # 根据各因子生成建议
        if factors['oxygen_factor'] < 0.8:
            suggestions.append('溶解氧偏低，建议减少投喂量并开启增氧设备')
        elif factors['oxygen_factor'] > 1.1:
            suggestions.append('溶解氧充足，可适当增加投喂')
        
        if factors['temperature_factor'] < 0.8:
            suggestions.append('温度不适宜，鱼类食欲可能下降')
        
        if factors['ammonia_factor'] < 0.8:
            suggestions.append('氨氮含量偏高，建议减少投喂并换水')
        
        if factors['nitrite_factor'] < 0.8:
            suggestions.append('亚硝酸盐超标，建议减少投喂量')
        
        if not suggestions:
            suggestions.append('水质良好，按推荐量投喂即可')
        
        return '；'.join(suggestions)
    
    async def execute_feeding(
        self,
        feeder_id: str,
        amount: float,
        duration: int
    ) -> Dict:
        """执行投喂指令"""
        try:
            # 通过 WebSocket 发送投喂指令
            await manager.send_command(feeder_id, 'feed', {
                'amount': amount,
                'duration': duration
            })
            
            return {
                'success': True,
                'feeder_id': feeder_id,
                'amount': amount,
                'duration': duration,
                'status': 'command_sent'
            }
        except Exception as e:
            return {
                'success': False,
                'feeder_id': feeder_id,
                'error': str(e)
            }


# 全局服务实例
smart_feeding_service = SmartFeedingService()
