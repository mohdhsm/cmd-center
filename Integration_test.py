import unittest

from cmd_center.backend.integrations.config import get_config
from cmd_center.backend.integrations.pipedrive_client import PipedriveClient


class TestPipedriveIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration checks against the real Pipedrive API."""

    @classmethod
    def setUpClass(cls):
        cls.config = get_config()
        if not cls.config.pipedrive_api_token:
            raise unittest.SkipTest(
                "Set pipedrive_api_token in the environment/.env to run integration tests."
            )

    async def asyncSetUp(self):
        self.client = PipedriveClient(
            api_token=self.config.pipedrive_api_token,
            api_url=self.config.pipedrive_api_url,
        )

    async def asyncTearDown(self):
        await self.client.close()

    async def test_can_list_pipelines(self):
        pipelines = await self.client.get_pipelines()
        self.assertIsInstance(pipelines, list)
        if pipelines:
            self.assertIn("id", pipelines[0])
            self.assertIn("name", pipelines[0])

    async def test_can_list_users(self):
        users = await self.client.get_users()
        self.assertIsInstance(users, list)
        if users:
            self.assertIn("id", users[0])
            self.assertIn("name", users[0])


if __name__ == "__main__":
    unittest.main()
