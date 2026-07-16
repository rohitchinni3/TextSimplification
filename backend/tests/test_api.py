"""Integration tests for the FastAPI routes."""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestSimplifyEndpoint:
    def test_basic_request(self):
        resp = client.post(
            "/api/v1/simplify",
            json={"text": "Scientists utilize sophisticated methodologies.", "target_fk_grade": 6.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "simplified_text" in data
        assert "original_fk_grade" in data
        assert "final_fk_grade" in data
        assert "target_fk_grade" in data
        assert "target_met" in data
        assert "attempts" in data
        assert "provider_mode" in data

    def test_default_target_grade(self):
        resp = client.post(
            "/api/v1/simplify",
            json={"text": "Hello world."},
        )
        assert resp.status_code == 200
        assert resp.json()["target_fk_grade"] == 6.0

    def test_custom_max_attempts(self):
        resp = client.post(
            "/api/v1/simplify",
            json={"text": "Hello world.", "target_fk_grade": 5.0, "max_attempts": 2},
        )
        assert resp.status_code == 200
        assert resp.json()["attempts"] <= 2

    def test_empty_text_returns_422(self):
        resp = client.post(
            "/api/v1/simplify",
            json={"text": "", "target_fk_grade": 6.0},
        )
        assert resp.status_code == 422

    def test_whitespace_only_text_returns_422(self):
        resp = client.post(
            "/api/v1/simplify",
            json={"text": "   ", "target_fk_grade": 6.0},
        )
        assert resp.status_code == 422

    def test_target_grade_below_range_returns_422(self):
        resp = client.post(
            "/api/v1/simplify",
            json={"text": "Hello.", "target_fk_grade": 0},
        )
        assert resp.status_code == 422

    def test_target_grade_above_range_returns_422(self):
        resp = client.post(
            "/api/v1/simplify",
            json={"text": "Hello.", "target_fk_grade": 19},
        )
        assert resp.status_code == 422

    def test_provider_mode_is_mock(self):
        resp = client.post(
            "/api/v1/simplify",
            json={"text": "The cat sat on the mat.", "target_fk_grade": 6.0},
        )
        assert resp.status_code == 200
        assert resp.json()["provider_mode"] == "mock"

    def test_missing_text_field_returns_422(self):
        resp = client.post(
            "/api/v1/simplify",
            json={"target_fk_grade": 6.0},
        )
        assert resp.status_code == 422
