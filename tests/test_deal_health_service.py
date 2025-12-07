import unittest
from types import SimpleNamespace
from datetime import datetime, timedelta

from cmd_center.backend.services import deal_health_service
from cmd_center.backend.services.deal_health_service import DealHealthService


class FakeDealDTO:
    """Lightweight DTO stub that matches the fields DealHealthService reads."""

    def __init__(
        self,
        deal_id: int,
        title: str,
        pipeline_id: int,
        stage_id: int,
        owner_id: int,
        value: float,
        add_time: str,
        update_time: str | None,
        last_activity_date: str | None,
        status: str = "open",
    ):
        self.id = deal_id
        self.title = title
        self.pipeline_id = pipeline_id
        self.stage_id = stage_id
        self.owner_id = owner_id
        self.value = value
        self.add_time = add_time
        self.update_time = update_time
        self.last_activity_date = last_activity_date
        self.status = status


class FakePipedriveClient:
    """Fake Pipedrive client that mimics async API methods used by DealHealthService."""

    def __init__(self, pipeline_id: int, deals: list[FakeDealDTO], stages: list[dict] | None = None):
        self.pipeline_id = pipeline_id
        self.deals = deals
        self.last_status_requested = None
        self.deal_detail = None
        self.stages = stages or []

    async def get_pipeline_id(self, pipeline_name: str):
        self.last_pipeline_requested = pipeline_name
        return self.pipeline_id

    async def get_deals(self, pipeline_id: int, status: str = "open", **kwargs):
        self.last_status_requested = status
        self.last_deals_kwargs = kwargs
        return self.deals

    async def get_stages(self, pipeline_id: int | None = None):
        return self.stages

    async def get_deal(self, deal_id: int):
        if self.deal_detail and self.deal_detail.id == deal_id:
            return self.deal_detail
        return None


class DealHealthServiceTests(unittest.IsolatedAsyncioTestCase):
    """Unit tests for DealHealthService data extraction and filtering."""

    def setUp(self):
        # Patch out external dependencies.
        self.original_get_client = deal_health_service.get_pipedrive_client
        self.original_get_config = deal_health_service.get_config

        # Fake config is unused in the current service implementation.
        deal_health_service.get_config = lambda: SimpleNamespace()

    def tearDown(self):
        deal_health_service.get_pipedrive_client = self.original_get_client
        deal_health_service.get_config = self.original_get_config

    def _build_service(self, deals: list[FakeDealDTO], pipeline_id: int = 5, stages: list[dict] | None = None) -> DealHealthService:
        fake_client = FakePipedriveClient(pipeline_id=pipeline_id, deals=deals, stages=stages)
        deal_health_service.get_pipedrive_client = lambda: fake_client
        svc = DealHealthService()
        # stash client so individual tests can assert on it
        svc._fake_client = fake_client  # type: ignore[attr-defined]
        return svc

    async def test_get_overdue_deals_filters_and_sorts(self):
        now = datetime.now()
        overdue_date = (now - timedelta(days=10)).isoformat()
        recent_date = (now - timedelta(days=2)).isoformat()

        deals = [
            FakeDealDTO(
                deal_id=1,
                title="Overdue",
                pipeline_id=5,
                stage_id=101,
                owner_id=1,
                value=100.0,
                add_time=overdue_date,
                update_time=overdue_date,
                last_activity_date=overdue_date,
            ),
            FakeDealDTO(
                deal_id=2,
                title="Recent",
                pipeline_id=5,
                stage_id=1,
                owner_id=1,
                value=200.0,
                add_time=recent_date,
                update_time=recent_date,
                last_activity_date=recent_date,
            ),
            FakeDealDTO(
                deal_id=3,
                title="No activity",
                pipeline_id=5,
                stage_id=1,
                owner_id=1,
                value=50.0,
                add_time=recent_date,
                update_time=recent_date,
                last_activity_date=None,
            ),
        ]

        stages = [
            {"id": 101, "name": "Lead In", "pipeline_id": 5},
            {"id": 102, "name": "Proposal", "pipeline_id": 5},
        ]

        svc = self._build_service(deals, stages=stages)
        result = await svc.get_overdue_deals(min_days=7)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 1)
        self.assertGreaterEqual(result[0].overdue_days, 10)
        self.assertEqual(result[0].stage, "Lead In")
        # Ensure service requests open deals
        self.assertEqual(svc._fake_client.last_status_requested, "open")

    async def test_get_stuck_deals_filters_by_update_time(self):
        now = datetime.now()
        stale_update = (now - timedelta(days=45)).isoformat()
        fresh_update = (now - timedelta(days=5)).isoformat()

        deals = [
            FakeDealDTO(
                deal_id=10,
                title="Stuck",
                pipeline_id=5,
                stage_id=201,
                owner_id=1,
                value=300.0,
                add_time=stale_update,
                update_time=stale_update,
                last_activity_date=stale_update,
            ),
            FakeDealDTO(
                deal_id=11,
                title="Moving",
                pipeline_id=5,
                stage_id=202,
                owner_id=1,
                value=400.0,
                add_time=fresh_update,
                update_time=fresh_update,
                last_activity_date=fresh_update,
            ),
        ]

        stages = [
            {"id": 201, "name": "Review", "pipeline_id": 5},
            {"id": 202, "name": "Negotiation", "pipeline_id": 5},
        ]

        svc = self._build_service(deals, stages=stages)
        result = await svc.get_stuck_deals(min_days=30)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 10)
        self.assertGreaterEqual(result[0].days_in_stage, 45)
        self.assertEqual(result[0].stage, "Review")

    async def test_get_deal_detail_returns_dealbase(self):
        now_str = datetime.now().isoformat()
        detail_dto = FakeDealDTO(
            deal_id=20,
            title="Detail Deal",
            pipeline_id=5,
            stage_id=1,
            owner_id=1,
            value=500.0,
            add_time=now_str,
            update_time=now_str,
            last_activity_date=now_str,
        )

        svc = self._build_service([], pipeline_id=5)
        svc._fake_client.deal_detail = detail_dto  # type: ignore[attr-defined]

        result = await svc.get_deal_detail(20)

        self.assertIsNotNone(result)
        self.assertEqual(result.id, 20)
        self.assertEqual(result.title, "Detail Deal")
        self.assertEqual(result.value_sar, 500.0)

    async def test_get_deal_detail_handles_missing(self):
        svc = self._build_service([])
        result = await svc.get_deal_detail(999)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
