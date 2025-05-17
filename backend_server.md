# BeeBackend API Documentation

This document provides documentation for the API endpoints available in the BeeBackend service.

## Base URL

All API endpoints are relative to the base URL of the deployed service (e.g., `http://localhost:8000`).

## API Endpoints

### Users API

#### Get All Users

```bash
curl -X GET "http://localhost:8000/users/"
```

Response:
```json
[
  {
    "address": "string",
    "points": 0,
    "position": null
  }
]
```

#### Create User

```bash
curl -X POST "http://localhost:8000/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "address": "string",
    "points": 0,
    "position": null
  }'
```

Response:
```json
{
  "address": "string",
  "points": 0,
  "position": null
}
```

### MCP API

#### Get All Allowed MCPs

```bash
curl -X GET "http://localhost:8000/mcp/allowed_mcps"
```

Response:
```json
[
  {
    "id": 0,
    "mcp_name": "string",
    "mcp_description": "string",
    "mcp_tool_calls": [],
    "mcp_env_keys": []
  }
]
```

#### Add MCP

```bash
curl -X POST "http://localhost:8000/mcp/add" \
  -H "Content-Type: application/json" \
  -d '{
    "allowed_mcp_id": 0,
    "user_address": "string",
    "mcp_json": {},
    "mcp_env_keys": {},
    "tool_calls_count": 0
  }'
```

Response:
```json
{
  "id": 0,
  "allowed_mcp_id": 0,
  "user_address": "string",
  "mcp_json": {},
  "mcp_env_keys": {},
  "tool_calls_count": 0
}
```

#### Get Specific User MCP

```bash
curl -X GET "http://localhost:8000/mcp/{user_address}/{mcp_id}"
```

Replace `{user_address}` with the user's address and `{mcp_id}` with the MCP ID.

Response:
```json
{
  "id": 0,
  "allowed_mcp_id": 0,
  "user_address": "string",
  "mcp_name": "string",
  "mcp_description": "string",
  "mcp_json": {},
  "mcp_env_keys": {},
  "tool_calls_count": 0
}
```

#### Get All User MCPs

```bash
curl -X GET "http://localhost:8000/mcp/{user_address}"
```

Replace `{user_address}` with the user's address.

Response:
```json
[
  {
    "id": 0,
    "allowed_mcp_id": 0,
    "user_address": "string",
    "mcp_name": "string",
    "mcp_description": "string", 
    "mcp_json": {},
    "mcp_env_keys": {},
    "tool_calls_count": 0
  }
]
```

### Health API

#### Health Check

```bash
curl -X GET "http://localhost:8000/health/"
```

Response:
```json
{
  "status": "healthy",
  "message": "Service is running"
}
```

#### Health Info

```bash
curl -X GET "http://localhost:8000/health/info"
```

Response:
```json
{
  "status": "healthy",
  "service_name": "BeeBackend",
  "version": "0.1.0"
}
```

## Running the Server

To start the backend server, you can use the included script:

```bash
./start_server.sh
```

Or manually run:

```bash
uvicorn src.backend_server.main:app --reload --host 0.0.0.0 --port 8000
```