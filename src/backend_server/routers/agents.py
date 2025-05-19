from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import anthropic
from typing import Optional
import json
import re
from dotenv import load_dotenv
load_dotenv()

router = APIRouter(
    prefix="/agents",
    tags=["agents"],
    responses={404: {"description": "Not found"}},
)


class LLMRequest(BaseModel):
    initial_prompt: str
    temperature: Optional[float] = 1.0
    max_tokens: Optional[int] = 1000


class LLMResponse(BaseModel):
    content: dict


@router.post("/preview", response_model=LLMResponse)
async def generate_response(request: LLMRequest):
    try:
        client = anthropic.Anthropic()
        system_prompt = """
        You are intelligent agent that can create sub agents for specific tasks, the format for the subagent goes something like this, 
        {
            "agent_slug": a short name slug of the subagent,
            "agent_task": a short description of task of subgent, 
            "inital_prompt": initial prompt of the subagent 
            "mcps": model context protocol(s) from the list as per the task of subagent in array form 
        }

        These agents are supposed to be for specific purpose, for doing a task periodically 
        {
            "polling_prompt": specify if any subagent needs to be run periodically to complete the task at hand, 
            "polling_time": duration in seconds after which the polling prompt needs to run,
            "orchestrator_slug": this will be slug for the main agent that we are going to run 
        }

        The final json output will be in this format, 
        {
            "orchestrator": {
                "polling_prompt":
                "polling_time": 
                "orchestrator_slug":
            },
            "agents": [{
                "agent_slug": ,
                "agent_task": ,
                "initial_prompt": ,
                "mcps": [ mcp list array ]
            }]
        }
        
        List of MCP to choose -> ["dextrading", "ammswap","notion","googlemaps","brave", "fetch","twitter"]
        Not necessary to use all mcps, an agent can have 0,1 or 2 mcp connected
        """
        # Add instructions to the initial prompt
        enhanced_prompt = request.initial_prompt
        
        message = client.messages.create(
            model="claude-3-7-sonnet-latest",
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": enhanced_prompt
                        }
                    ]
                }
            ]
        )
        
        # Extract JSON from the response text
        text_content = message.content[0].text
        
        # Method 1: Try to find JSON using regex pattern matching
        json_pattern = r'({[\s\S]*})'
        json_matches = re.findall(json_pattern, text_content)
        
        for potential_json in json_matches:
            try:
                # Try to parse the potential JSON string
                json_content = json.loads(potential_json)
                # If we successfully parsed JSON with our expected structure, return it
                if isinstance(json_content, dict) and ("orchestrator" in json_content or "agents" in json_content):
                    return LLMResponse(content=json_content)
            except json.JSONDecodeError:
                continue
        
        # Method 2: If the regex approach fails, try to parse the entire response as JSON
        try:
            json_content = json.loads(text_content)
            return LLMResponse(content=json_content)
        except json.JSONDecodeError:
            # If that fails too, return an error
            raise HTTPException(status_code=422, detail="Could not extract valid JSON from the LLM response")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")