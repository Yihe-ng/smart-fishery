def analyze_water_quality(data):
    """分析水质数据
    
    Args:
        data: 水质数据字典，包含溶解氧、pH值、温度、氨氮
    
    Returns:
        dict: 分析结果，包含分析结果和预警等级
    """
    dissolved_oxygen = data.get('dissolved_oxygen', 0)
    ph_value = data.get('ph_value', 0)
    temperature = data.get('temperature', 0)
    ammonia_nitrogen = data.get('ammonia_nitrogen', 0)
    
    # 分析结果
    analysis_result = ""
    alert_level = "normal"
    
    # 溶解氧分析
    if dissolved_oxygen < 3:
        analysis_result += "溶解氧严重不足，"
        alert_level = "critical"
    elif dissolved_oxygen < 5:
        analysis_result += "溶解氧偏低，"
        if alert_level != "critical":
            alert_level = "high"
    elif dissolved_oxygen > 8:
        analysis_result += "溶解氧过高，"
        if alert_level != "critical" and alert_level != "high":
            alert_level = "medium"
    else:
        analysis_result += "溶解氧正常，"
    
    # pH值分析
    if ph_value < 6.5:
        analysis_result += "pH值偏低，"
        if alert_level != "critical":
            alert_level = "high"
    elif ph_value > 8.5:
        analysis_result += "pH值偏高，"
        if alert_level != "critical":
            alert_level = "high"
    else:
        analysis_result += "pH值正常，"
    
    # 温度分析
    if temperature < 18:
        analysis_result += "温度偏低，"
        if alert_level != "critical" and alert_level != "high":
            alert_level = "medium"
    elif temperature > 30:
        analysis_result += "温度偏高，"
        if alert_level != "critical" and alert_level != "high":
            alert_level = "medium"
    else:
        analysis_result += "温度正常，"
    
    # 氨氮分析
    if ammonia_nitrogen > 0.5:
        analysis_result += "氨氮含量过高，"
        if alert_level != "critical":
            alert_level = "high"
    else:
        analysis_result += "氨氮含量正常，"
    
    # 去除末尾的逗号
    if analysis_result.endswith("，"):
        analysis_result = analysis_result[:-1]
    
    return {
        "analysis_result": analysis_result,
        "alert_level": alert_level
    }
