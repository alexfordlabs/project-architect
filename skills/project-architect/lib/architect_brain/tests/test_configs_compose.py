"""Tests for architect_brain.configs.gen_docker_compose."""

import unittest

from architect_brain.configs import gen_docker_compose


def _fi(decisions=None):
    return {"schema_version": "4.0", "decisions": decisions or {}, "adrs": []}


class TestGenDockerCompose(unittest.TestCase):

    def test_has_services_and_app(self):
        out = gen_docker_compose(_fi())
        self.assertIn("services:", out)
        self.assertIn("app:", out)

    def test_postgres_db_service(self):
        out = gen_docker_compose(_fi({"stack.database.engine": "postgres"}))
        self.assertIn("db:", out)
        self.assertIn("postgres:", out)

    def test_redis_cache_service(self):
        out = gen_docker_compose(_fi({"stack.cache.engine": "redis"}))
        self.assertIn("cache:", out)
        self.assertIn("redis:", out)

    def test_no_db_when_absent(self):
        self.assertNotIn("postgres:", gen_docker_compose(_fi()))

    def test_depends_on_present_when_db(self):
        out = gen_docker_compose(_fi({"stack.database.engine": "postgres"}))
        self.assertIn("depends_on:", out)

    def test_trailing_newline_and_deterministic(self):
        fi = _fi({"stack.database.engine": "postgres", "stack.cache.engine": "redis"})
        out = gen_docker_compose(fi)
        self.assertTrue(out.endswith("\n"))
        self.assertEqual(gen_docker_compose(fi), gen_docker_compose(fi))

    # ── service image tags come from researched state, not frozen ──
    def test_uses_recorded_postgres_tag(self):
        out = gen_docker_compose(_fi({
            "stack.database.engine": "postgres", "stack.versions.postgres": "16",
        }))
        self.assertIn("postgres:16-alpine", out)

    def test_postgres_falls_back_to_floor(self):
        out = gen_docker_compose(_fi({"stack.database.engine": "postgres"}))
        self.assertIn("postgres:17-alpine", out)

    def test_uses_recorded_redis_tag(self):
        out = gen_docker_compose(_fi({
            "stack.cache.engine": "redis", "stack.versions.redis": "8",
        }))
        self.assertIn("redis:8-alpine", out)

    def test_redis_falls_back_to_floor(self):
        out = gen_docker_compose(_fi({"stack.cache.engine": "redis"}))
        self.assertIn("redis:7-alpine", out)


if __name__ == "__main__":
    unittest.main()
