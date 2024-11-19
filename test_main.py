from fastapi.testclient import TestClient
from main import app, DatabaseError, ValidationError
import pytest
import os
import json
import sqlite3

client = TestClient(app)

# Test GET endpoint
def test_get_analysis_success():
    response = client.get("/analysis")
    assert response.status_code == 200
    assert "company" in response.json()
    assert "buyer" in response.json()
    assert "markdown" in response.json()

def test_post_analysis_validation_errors():
    # Test empty content - should return 422 for Pydantic validation
    response = client.post(
        "/analysis",
        json={"new_content": ""}
    )
    assert response.status_code == 422

    # Test whitespace only
    response = client.post(
        "/analysis",
        json={"new_content": "   "}
    )
    assert response.status_code == 422

    # Test content too long
    long_content = "a" * 5001
    response = client.post(
        "/analysis",
        json={"new_content": long_content}
    )
    assert response.status_code == 422

def test_database_error(monkeypatch):
    def mock_connect(*args, **kwargs):
        raise DatabaseError("Test database error")
    monkeypatch.setattr("sqlite3.connect", mock_connect)
    
    response = client.get("/analysis")
    assert response.status_code == 500
    assert "database error" in response.json()["detail"].lower()

def test_json_file_error(monkeypatch):
    def mock_connect(*args, **kwargs):
        raise sqlite3.Error("Database initialization error")
    
    monkeypatch.setattr("sqlite3.connect", mock_connect)
    response = client.post(
        "/analysis",
        json={"new_content": "test content"}
    )
    assert response.status_code == 500

# Test missing required fields
def test_missing_required_fields():
    response = client.post("/analysis", json={})
    assert response.status_code == 422  # FastAPI validation error