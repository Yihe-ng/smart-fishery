from sqlalchemy import Engine, inspect, text


def ensure_growth_record_schema(engine: Engine) -> None:
    """为已有 SQLite 数据库补齐生长记录新增列，兼容无迁移工具的部署方式。"""
    if engine.dialect.name != "sqlite":
        return

    existing = {column["name"] for column in inspect(engine).get_columns("growth_records")}
    additions = {
        "detected_count": "INTEGER NOT NULL DEFAULT 0",
        "unmeasurable_count": "INTEGER NOT NULL DEFAULT 0",
        "small_count": "INTEGER NOT NULL DEFAULT 0",
        "normal_count": "INTEGER NOT NULL DEFAULT 0",
        "large_count": "INTEGER NOT NULL DEFAULT 0",
        "unassessed_count": "INTEGER NOT NULL DEFAULT 0",
        "planned_frame_count": "INTEGER",
        "completed_frame_count": "INTEGER",
        "evaluable_frame_count": "INTEGER",
        "detection_occurrence_count": "INTEGER",
        "measurable_occurrence_count": "INTEGER",
        "reference_length_cm": "FLOAT",
        "small_threshold_cm": "FLOAT",
        "large_threshold_cm": "FLOAT",
        "trimmed_mean_length_cm": "FLOAT",
        "all_measurable_avg_length_cm": "FLOAT",
    }

    with engine.begin() as connection:
        for name, definition in additions.items():
            if name not in existing:
                connection.execute(
                    text(f'ALTER TABLE growth_records ADD COLUMN "{name}" {definition}')
                )
