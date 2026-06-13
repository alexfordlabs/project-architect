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
        # Floor = newest stable at plugin-release time (PG 18 as of 2026-06).
        out = gen_docker_compose(_fi({"stack.database.engine": "postgres"}))
        self.assertIn("postgres:18-alpine", out)

    def test_uses_recorded_redis_tag(self):
        out = gen_docker_compose(_fi({
            "stack.cache.engine": "redis", "stack.versions.redis": "7.4",
        }))
        self.assertIn("redis:7.4-alpine", out)

    def test_redis_falls_back_to_floor(self):
        # Floor = newest stable at plugin-release time (Redis 8 as of 2026-06).
        out = gen_docker_compose(_fi({"stack.cache.engine": "redis"}))
        self.assertIn("redis:8-alpine", out)

    # ── tiger-panther: a recorded NUMERIC pin must be honored, not floored ──
    def test_uses_recorded_postgres_tag_when_pin_is_int(self):
        # set-decision json-parses a bare `17` to int 17; _pin's old
        # isinstance(str) guard silently discarded it and shipped the floor
        # (postgres:18). The recorded version must win over the floor.
        out = gen_docker_compose(_fi({
            "stack.database.engine": "postgres", "stack.versions.postgres": 17,
        }))
        self.assertIn("postgres:17-alpine", out)
        self.assertNotIn("postgres:18-alpine", out)

    def test_float_pin_is_refused_floored_not_corrupted(self):
        # A float version pin is irrecoverably ambiguous (json parses 3.10 -> 3.1,
        # 20.0 -> the non-existent tag node:20.0), so usable_pin REFUSES it: the
        # FLOOR is used (and check 36 flags it) rather than silently shipping a
        # corrupted version. set-decision keeps stack.versions.* as strings, so a
        # float only arrives via legacy/hand-edited state.
        out = gen_docker_compose(_fi({
            "stack.cache.engine": "redis", "stack.versions.redis": 7.4,
        }))
        self.assertIn("redis:8-alpine", out)        # FLOOR, not the float
        self.assertNotIn("redis:7.4-alpine", out)

    # ── tiger-panther: managed PaaS / serverless stack gets no self-hosted db ──
    def test_no_self_hosted_db_for_managed_supabase_stack(self):
        # Backend on Supabase edge functions (Deno) + managed Supabase hosting
        # manages Postgres — a self-hosted `db:` service is wrong.
        out = gen_docker_compose(_fi({
            "stack.database.engine": "postgresql",
            "stack.backend.framework": "supabase_edge_functions",
            "stack.hosting.provider": "supabase",
        }))
        self.assertNotIn("db:", out)
        self.assertNotIn("postgres:", out)


if __name__ == "__main__":
    unittest.main()
