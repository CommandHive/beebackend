import pytest
from fastapi.testclient import TestClient
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend_server.main import app
from database.database import Base, get_db
from database.models import User, AllowedMCP, MCP


# Get test database URL from environment variable or use a default
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "postgresql://admin:admin@34.47.187.64:5432/postgres")
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Test fixture for database setup/teardown
@pytest.fixture
def db_session():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create a test session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        
        # Clean up (optional - can be removed if you want to persist test data)
        # Base.metadata.drop_all(bind=engine)


# Override the get_db dependency
@pytest.fixture
def client(db_session):
    # Override the get_db dependency to use our test session
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    
    # Clean up
    app.dependency_overrides.clear()


# Fixture to create a test user
@pytest.fixture
def test_user(db_session):
    user = User(
        address="0xTestAddress123",
        points=100,
        position=1
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# Fixture to create a test allowed MCP
@pytest.fixture
def test_allowed_mcp(db_session):
    allowed_mcp = AllowedMCP(
        mcp_name="Test MCP",
        mcp_description="Test MCP Description",
        mcp_tool_calls=[{"name": "test_tool", "description": "A test tool"}],
        mcp_env_keys=["API_KEY", "SECRET_KEY"]
    )
    db_session.add(allowed_mcp)
    db_session.commit()
    db_session.refresh(allowed_mcp)
    return allowed_mcp


# Fixture to create a test MCP for a user
@pytest.fixture
def test_mcp(db_session, test_user, test_allowed_mcp):
    mcp = MCP(
        allowed_mcp_id=test_allowed_mcp.id,
        user_address=test_user.address,
        mcp_json={"config": "test_config"},
        mcp_env_keys={"API_KEY": "dummy_key", "SECRET_KEY": "dummy_secret"},
        tool_calls_count=0
    )
    db_session.add(mcp)
    db_session.commit()
    db_session.refresh(mcp)
    return mcp


def test_get_allowed_mcps(client, test_allowed_mcp):
    """Test retrieving all allowed MCPs"""
    response = client.get("/mcp/allowed_mcps")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    
    # Check if our test MCP is in the response
    assert any(mcp["id"] == test_allowed_mcp.id for mcp in data)
    found_mcp = next(mcp for mcp in data if mcp["id"] == test_allowed_mcp.id)
    assert found_mcp["mcp_name"] == test_allowed_mcp.mcp_name
    assert found_mcp["mcp_description"] == test_allowed_mcp.mcp_description


def test_add_mcp(client, test_user, test_allowed_mcp):
    """Test adding a new MCP for a user"""
    mcp_data = {
        "allowed_mcp_id": test_allowed_mcp.id,
        "user_address": test_user.address,
        "mcp_json": {"config": "new_test_config"},
        "mcp_env_keys": {"API_KEY": "new_dummy_key", "SECRET_KEY": "new_dummy_secret"},
        "tool_calls_count": 0
    }
    
    response = client.post("/mcp/add", json=mcp_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["allowed_mcp_id"] == mcp_data["allowed_mcp_id"]
    assert data["user_address"] == mcp_data["user_address"]
    assert data["mcp_json"] == mcp_data["mcp_json"]
    assert data["mcp_env_keys"] == mcp_data["mcp_env_keys"]
    assert data["tool_calls_count"] == mcp_data["tool_calls_count"]


def test_add_mcp_user_not_found(client, test_allowed_mcp):
    """Test adding a new MCP for a non-existent user"""
    mcp_data = {
        "allowed_mcp_id": test_allowed_mcp.id,
        "user_address": "0xNonExistentUser",
        "mcp_json": {"config": "test_config"},
        "mcp_env_keys": {"API_KEY": "dummy_key", "SECRET_KEY": "dummy_secret"},
        "tool_calls_count": 0
    }
    
    response = client.post("/mcp/add", json=mcp_data)
    
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_add_mcp_allowed_mcp_not_found(client, test_user):
    """Test adding a new MCP with a non-existent allowed MCP ID"""
    mcp_data = {
        "allowed_mcp_id": 9999,  # Non-existent ID
        "user_address": test_user.address,
        "mcp_json": {"config": "test_config"},
        "mcp_env_keys": {"API_KEY": "dummy_key", "SECRET_KEY": "dummy_secret"},
        "tool_calls_count": 0
    }
    
    response = client.post("/mcp/add", json=mcp_data)
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Allowed MCP not found"


def test_get_user_mcp(client, test_mcp):
    """Test retrieving a specific MCP for a user"""
    response = client.get(f"/mcp/{test_mcp.user_address}/{test_mcp.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_mcp.id
    assert data["allowed_mcp_id"] == test_mcp.allowed_mcp_id
    assert data["user_address"] == test_mcp.user_address
    assert "mcp_name" in data
    assert "mcp_description" in data
    assert data["mcp_json"] == test_mcp.mcp_json
    assert data["mcp_env_keys"] == test_mcp.mcp_env_keys
    assert data["tool_calls_count"] == test_mcp.tool_calls_count


def test_get_user_mcp_not_found(client, test_user):
    """Test retrieving a non-existent MCP for a user"""
    response = client.get(f"/mcp/{test_user.address}/9999")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "MCP not found"


def test_get_user_mcps(client, test_user, test_mcp):
    """Test retrieving all MCPs for a user"""
    response = client.get(f"/mcp/{test_user.address}")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    
    # Check if our test MCP is in the response
    assert any(mcp["id"] == test_mcp.id for mcp in data)
    found_mcp = next(mcp for mcp in data if mcp["id"] == test_mcp.id)
    assert found_mcp["allowed_mcp_id"] == test_mcp.allowed_mcp_id
    assert found_mcp["user_address"] == test_mcp.user_address
    assert found_mcp["mcp_json"] == test_mcp.mcp_json
    assert found_mcp["mcp_env_keys"] == test_mcp.mcp_env_keys
    assert found_mcp["tool_calls_count"] == test_mcp.tool_calls_count


def test_get_user_mcps_user_not_found(client):
    """Test retrieving MCPs for a non-existent user"""
    response = client.get("/mcp/0xNonExistentUser")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_get_user_mcps_empty(client, db_session):
    """Test retrieving MCPs for a user with no MCPs"""
    # Create a user with no MCPs
    user = User(
        address="0xUserWithNoMCPs",
        points=0,
        position=2
    )
    db_session.add(user)
    db_session.commit()
    
    response = client.get(f"/mcp/{user.address}")
    
    assert response.status_code == 200
    data = response.json()
    assert data == []