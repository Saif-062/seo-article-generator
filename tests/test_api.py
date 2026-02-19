"""Tests for API endpoints."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.persistence.job_store import JobStore


@pytest.fixture
def temp_jobs_dir():
    """Create a temporary directory for job storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_job_store(temp_jobs_dir):
    """Create a mock job store."""
    return JobStore(jobs_dir=temp_jobs_dir)


@pytest.fixture
def client(mock_job_store):
    """Create a test client with mocked dependencies."""
    with patch("app.api.routes.get_job_store", return_value=mock_job_store):
        with patch("app.persistence.job_store.get_job_store", return_value=mock_job_store):
            with TestClient(app) as client:
                yield client


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health check returns healthy status."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "serp_provider" in data
        assert "llm_provider" in data


class TestJobEndpoints:
    """Tests for job management endpoints."""

    def test_create_job(self, client):
        """Test creating a new job."""
        response = client.post(
            "/api/v1/jobs",
            json={
                "topic": "best productivity tools for remote teams",
                "word_count": 1500,
                "language": "en",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"

    def test_create_job_minimal(self, client):
        """Test creating a job with minimal parameters."""
        response = client.post(
            "/api/v1/jobs",
            json={"topic": "productivity tools"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "pending"

    def test_create_job_validation_error(self, client):
        """Test job creation with invalid parameters."""
        # Topic too short
        response = client.post(
            "/api/v1/jobs",
            json={"topic": "ab"},
        )
        assert response.status_code == 422

        # Word count too low
        response = client.post(
            "/api/v1/jobs",
            json={"topic": "valid topic", "word_count": 100},
        )
        assert response.status_code == 422

    def test_get_job(self, client):
        """Test getting job details."""
        # Create a job first
        create_response = client.post(
            "/api/v1/jobs",
            json={"topic": "test topic"},
        )
        job_id = create_response.json()["job_id"]

        # Get job details
        response = client.get(f"/api/v1/jobs/{job_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert data["topic"] == "test topic"

    def test_get_job_not_found(self, client):
        """Test getting a non-existent job."""
        response = client.get("/api/v1/jobs/nonexistent")
        assert response.status_code == 404

    def test_get_job_status(self, client):
        """Test getting job status."""
        # Create a job first
        create_response = client.post(
            "/api/v1/jobs",
            json={"topic": "test topic"},
        )
        job_id = create_response.json()["job_id"]

        # Get status
        response = client.get(f"/api/v1/jobs/{job_id}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert "status" in data
        assert "current_step" in data

    def test_list_jobs(self, client):
        """Test listing jobs."""
        # Create some jobs
        for i in range(3):
            client.post("/api/v1/jobs", json={"topic": f"topic {i}"})

        # List all jobs
        response = client.get("/api/v1/jobs")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_list_jobs_with_limit(self, client):
        """Test listing jobs with limit."""
        # Create some jobs
        for i in range(5):
            client.post("/api/v1/jobs", json={"topic": f"topic {i}"})

        # List with limit
        response = client.get("/api/v1/jobs?limit=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "SEO Article Generator API"
        assert "version" in data
        assert "docs" in data
