from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from src.database.models import AllowedMCP, MCP, User
from src.database.database import get_db

router = APIRouter(
    prefix="/mcp",
    tags=["mcp"],
)


class AllowedMCPResponse(BaseModel):
    id: int
    mcp_name: str
    mcp_description: str
    mcp_tool_calls: list
    mcp_env_keys: list

    class Config:
        orm_mode = True


class MCPCreate(BaseModel):
    allowed_mcp_id: int
    user_address: str
    mcp_json: dict
    mcp_env_keys: dict
    tool_calls_count: int = 0


class MCPResponse(BaseModel):
    id: int
    allowed_mcp_id: int
    user_address: str
    mcp_json: dict
    mcp_env_keys: dict
    tool_calls_count: int

    class Config:
        orm_mode = True


class MCPDetailsResponse(BaseModel):
    id: int
    allowed_mcp_id: int
    user_address: str
    mcp_name: str
    mcp_description: str
    mcp_json: dict
    mcp_env_keys: dict
    tool_calls_count: int

    class Config:
        orm_mode = True


@router.get("/allowed_mcps", response_model=List[AllowedMCPResponse])
async def get_allowed_mcps(db: Session = Depends(get_db)):
    """
    Retrieve all allowed MCPs.
    """
    allowed_mcps = db.query(AllowedMCP).all()
    return allowed_mcps


@router.post("/add", response_model=MCPResponse, status_code=201)
async def add_mcp(mcp: MCPCreate, db: Session = Depends(get_db)):
    """
    Add a new MCP for a user.
    """
    # Check if user exists
    user = db.query(User).filter(User.address == mcp.user_address).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if allowed MCP exists
    allowed_mcp = db.query(AllowedMCP).filter(AllowedMCP.id == mcp.allowed_mcp_id).first()
    if not allowed_mcp:
        raise HTTPException(status_code=404, detail="Allowed MCP not found")

    # Create new MCP
    new_mcp = MCP(
        allowed_mcp_id=mcp.allowed_mcp_id,
        user_address=mcp.user_address,
        mcp_json=mcp.mcp_json,
        mcp_env_keys=mcp.mcp_env_keys,
        tool_calls_count=mcp.tool_calls_count
    )

    # Add to database
    db.add(new_mcp)
    db.commit()
    db.refresh(new_mcp)

    return new_mcp


@router.get("/{user_address}/{mcp_id}", response_model=MCPDetailsResponse)
async def get_user_mcp(user_address: str, mcp_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific MCP for a user.
    """
    # Get the MCP
    mcp = db.query(MCP).filter(
        MCP.user_address == user_address,
        MCP.id == mcp_id
    ).first()

    if not mcp:
        raise HTTPException(status_code=404, detail="MCP not found")

    # Get the allowed MCP for name and description
    allowed_mcp = db.query(AllowedMCP).filter(AllowedMCP.id == mcp.allowed_mcp_id).first()
    if not allowed_mcp:
        raise HTTPException(status_code=404, detail="Allowed MCP not found")

    # Create response with combined data
    response = {
        "id": mcp.id,
        "allowed_mcp_id": mcp.allowed_mcp_id,
        "user_address": mcp.user_address,
        "mcp_name": allowed_mcp.mcp_name,
        "mcp_description": allowed_mcp.mcp_description,
        "mcp_json": mcp.mcp_json,
        "mcp_env_keys": mcp.mcp_env_keys,
        "tool_calls_count": mcp.tool_calls_count
    }

    return response


@router.get("/{user_address}", response_model=List[MCPDetailsResponse])
async def get_user_mcps(user_address: str, db: Session = Depends(get_db)):
    """
    Retrieve all MCPs for a user.
    """
    # Check if user exists
    user = db.query(User).filter(User.address == user_address).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get all user MCPs
    mcps = db.query(MCP).filter(MCP.user_address == user_address).all()
    
    # If no MCPs found, return empty list
    if not mcps:
        return []

    # Get all allowed MCPs in one query to avoid N+1 problem
    allowed_mcp_ids = [mcp.allowed_mcp_id for mcp in mcps]
    allowed_mcps = db.query(AllowedMCP).filter(AllowedMCP.id.in_(allowed_mcp_ids)).all()
    
    # Create a lookup for allowed MCPs
    allowed_mcps_map = {allowed_mcp.id: allowed_mcp for allowed_mcp in allowed_mcps}

    # Create response with combined data
    responses = []
    for mcp in mcps:
        allowed_mcp = allowed_mcps_map.get(mcp.allowed_mcp_id)
        if allowed_mcp:
            responses.append({
                "id": mcp.id,
                "allowed_mcp_id": mcp.allowed_mcp_id,
                "user_address": mcp.user_address,
                "mcp_name": allowed_mcp.mcp_name,
                "mcp_description": allowed_mcp.mcp_description,
                "mcp_json": mcp.mcp_json,
                "mcp_env_keys": mcp.mcp_env_keys,
                "tool_calls_count": mcp.tool_calls_count
            })

    return responses