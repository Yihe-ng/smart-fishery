import os
import tempfile
import unittest
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.agent.context_builder import build_page_context
from app.agent.schemas import PageContextRequest
from app.agent.tool_registry import (
    get_alert_digest,
    get_device_status,
    get_feeding_recommendation,
    get_water_quality_summary,
)
from app.db.base import Base
from app.models.water import AlertRecord, WaterQualityData


class AgentRealDataTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_fd, cls.db_path = tempfile.mkstemp(suffix=".db")
        cls.engine = create_engine(
            f"sqlite:///{cls.db_path}",
            connect_args={"check_same_thread": False},
        )
        cls.TestSessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=cls.engine,
        )
        Base.metadata.create_all(bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()
        os.close(cls.db_fd)
        os.unlink(cls.db_path)

    def setUp(self):
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        session = self.TestSessionLocal()
        try:
            session.add_all(
                [
                    WaterQualityData(
                        pond_id="T001",
                        dissolved_oxygen=4.2,
                        ph_value=8.6,
                        temperature=29.5,
                        ammonia_nitrogen=0.18,
                        nitrite=0.09,
                        status="预警",
                        collect_time=datetime(2026, 2, 10, 10, 0, 0),
                    ),
                    WaterQualityData(
                        pond_id="T001",
                        dissolved_oxygen=3.2,
                        ph_value=8.9,
                        temperature=31.2,
                        ammonia_nitrogen=0.35,
                        nitrite=0.19,
                        status="危险",
                        collect_time=datetime(2026, 2, 10, 11, 0, 0),
                    ),
                    AlertRecord(
                        pond_id="T001",
                        alert_type="water_quality",
                        alert_message="溶氧偏低",
                        alert_level="critical",
                        is_resolved=0,
                        collect_time=datetime(2026, 2, 10, 11, 0, 0),
                    ),
                    AlertRecord(
                        pond_id="T001",
                        alert_type="water_quality",
                        alert_message="氨氮偏高",
                        alert_level="warning",
                        is_resolved=0,
                        collect_time=datetime(2026, 2, 10, 10, 30, 0),
                    ),
                ]
            )
            session.commit()
        finally:
            session.close()

    def test_water_quality_summary_reads_latest_database_record(self):
        session = self.TestSessionLocal()
        try:
            payload = get_water_quality_summary("T001", db=session)
        finally:
            session.close()

        self.assertEqual(payload["updatedAt"], "2026-02-10 11:00:00")
        self.assertEqual(payload["riskLevel"], "critical")
        self.assertEqual(payload["metrics"][0]["value"], 31.2)
        self.assertIn("31.2", payload["overview"])

    def test_alert_digest_reads_alert_records_table(self):
        session = self.TestSessionLocal()
        try:
            payload = get_alert_digest("T001", limit=5, db=session)
        finally:
            session.close()

        self.assertEqual(payload["total"], 2)
        self.assertEqual(payload["critical"], 1)
        self.assertEqual(payload["warning"], 1)
        self.assertEqual(payload["latest"][0]["title"], "water_quality")

    def test_device_status_falls_back_to_real_water_quality_devices_when_device_table_empty(self):
        session = self.TestSessionLocal()
        try:
            payload = get_device_status("T001", db=session)
        finally:
            session.close()

        self.assertEqual(payload["onlineCount"], 5)
        self.assertEqual(payload["offlineCount"], 0)
        self.assertEqual(payload["cameraStatus"], "online")

    def test_feeding_recommendation_uses_real_water_quality_data(self):
        session = self.TestSessionLocal()
        try:
            payload = get_feeding_recommendation("T001", db=session)
        finally:
            session.close()

        self.assertEqual(payload["waterQuality"]["dissolved_oxygen"], 3.2)
        self.assertEqual(payload["waterQuality"]["temperature"], 31.2)
        self.assertIn("投喂", payload["recommendation"])

    def test_page_context_uses_real_data_instead_of_mock_builder(self):
        session = self.TestSessionLocal()
        try:
            payload = build_page_context(
                PageContextRequest(
                    pageId="feeding",
                    routePath="/fishery/feeding",
                    pondId="T001",
                ),
                db=session,
            )
        finally:
            session.close()

        self.assertEqual(payload.pond.pondId, "T001")
        self.assertEqual(payload.updatedAt, "2026-02-10 11:00:00")
        self.assertEqual(payload.alertDigest.total, 2)
        self.assertEqual(payload.deviceStatus.onlineCount, 5)
        self.assertEqual(payload.keyMetrics[0].value, 31.2)

    def test_real_data_tools_degrade_cleanly_when_database_is_empty(self):
        session = self.TestSessionLocal()
        try:
            session.query(AlertRecord).delete()
            session.query(WaterQualityData).delete()
            session.commit()
        finally:
            session.close()

        water_session = self.TestSessionLocal()
        alert_session = self.TestSessionLocal()
        device_session = self.TestSessionLocal()
        feeding_session = self.TestSessionLocal()
        try:
            water = get_water_quality_summary("T001", db=water_session)
            alerts = get_alert_digest("T001", db=alert_session)
            devices = get_device_status("T001", db=device_session)
            feeding = get_feeding_recommendation("T001", db=feeding_session)
        finally:
            water_session.close()
            alert_session.close()
            device_session.close()
            feeding_session.close()

        self.assertEqual(water["riskLevel"], "unknown")
        self.assertEqual(alerts["total"], 0)
        self.assertEqual(devices["onlineCount"], 0)
        self.assertFalse(feeding["canFeed"])


if __name__ == "__main__":
    unittest.main()
