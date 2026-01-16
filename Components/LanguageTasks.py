from typing import List
from pydantic import BaseModel,Field
from dotenv import load_dotenv
import os

load_dotenv()

# Azure OpenAI configuration
azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
azure_openai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")

if not azure_openai_api_key:
    raise ValueError("Azure OpenAI API key not found. Make sure AZURE_OPENAI_API_KEY is defined in the .env file.")
if not azure_openai_endpoint:
    raise ValueError("Azure OpenAI endpoint not found. Make sure AZURE_OPENAI_ENDPOINT is defined in the .env file.")
if not azure_openai_deployment:
    raise ValueError("Azure OpenAI deployment name not found. Make sure AZURE_OPENAI_DEPLOYMENT_NAME is defined in the .env file.")

class JSONResponse(BaseModel):
    """
    The response should strictly follow the following structure: -
     [
        {
        start: "Start time of the clip",
        content: "Highlight Text",
        end: "End Time for the highlighted clip"
        }
     ]
    """
    start: float = Field(description="Start time of the clip")
    content: str= Field(description="Highlight Text")
    end: float = Field(description="End time for the highlighted clip")

class MultipleHighlightsResponse(BaseModel):
    """
    Response for multiple highlights selection
    """
    highlights: List[JSONResponse] = Field(description="List of selected highlights")

system = """
The input contains a timestamped transcription of a video.
Select a 2-minute segment from the transcription that contains something interesting, useful, surprising, controversial, or thought-provoking.
The selected text should contain only complete sentences.
Do not cut the sentences in the middle.
The selected text should form a complete thought.
Return a JSON object with the following structure:
## Output 
{{{{
    start: "Start time of the segment in seconds (number)",
    content: "The transcribed text from the selected segment (clean text only, NO timestamps)",
    end: "End time of the segment in seconds (number)"
}}}}
"""

system_multiple = """
The input contains a timestamped transcription of a video.
Select {num_clips} distinct 2-minute segments from the transcription that contain something interesting, useful, surprising, controversial, or thought-provoking.
Each selected text should contain only complete sentences.
Do not cut the sentences in the middle.
Each selected text should form a complete thought.
Ensure the segments don't overlap and are well-spaced throughout the video.
Return a JSON object with the following structure:
## Output 
{{{{
    "highlights": [
        {{{{
            "start": Start time of the first segment in seconds (number),
            "content": "The transcribed text from the first selected segment (clean text only, NO timestamps)",
            "end": End time of the first segment in seconds (number)
        }}}},
        {{{{
            "start": Start time of the second segment in seconds (number),
            "content": "The transcribed text from the second segment (clean text only, NO timestamps)",
            "end": End time of the second segment in seconds (number)
        }}}}
        // ... continue for all {num_clips} segments
    ]
}}}}
"""

# User = """
# Example
# """




def GetMultipleHighlights(Transcription, num_clips=3):
    """
    Get multiple highlights from transcription
    """
    from langchain_openai import AzureChatOpenAI
    
    try:
        llm = AzureChatOpenAI(
            deployment_name=azure_openai_deployment,
            api_version=azure_openai_api_version,
            azure_endpoint=azure_openai_endpoint,
            api_key=azure_openai_api_key,
            temperature=1.0,
        )

        from langchain.prompts import ChatPromptTemplate
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_multiple.format(num_clips=num_clips)),
                ("user", Transcription)
            ]
        )
        chain = prompt | llm.with_structured_output(MultipleHighlightsResponse, method="function_calling")
        
        print(f"Calling LLM for {num_clips} highlights selection...")
        response = chain.invoke({"Transcription": Transcription})
        
        # Validate response
        if not response or not hasattr(response, 'highlights'):
            print("ERROR: LLM returned empty or invalid response")
            return []
        
        highlights = []
        for i, highlight in enumerate(response.highlights[:num_clips]):  # Limit to requested number
            try:
                start = int(highlight.start)
                end = int(highlight.end)
                
                # Validate times
                if start < 0 or end < 0:
                    print(f"WARNING: Skipping highlight {i+1} - negative time values (Start: {start}s, End: {end}s)")
                    continue
                
                if end <= start:
                    print(f"WARNING: Skipping highlight {i+1} - invalid time range (Start: {start}s, End: {end}s)")
                    continue
                
                highlights.append({
                    'start': start,
                    'end': end,
                    'content': highlight.content
                })
                
                print(f"\nHighlight {i+1}: {start}s - {end}s ({end-start}s duration)")
                print(f"Content: {highlight.content[:100]}{'...' if len(highlight.content) > 100 else ''}")
                
            except (ValueError, TypeError) as e:
                print(f"WARNING: Skipping highlight {i+1} - could not parse times: {e}")
                continue
        
        if not highlights:
            print("ERROR: No valid highlights found")
            return []
        
        print(f"\n{'='*60}")
        print(f"FOUND {len(highlights)} VALID HIGHLIGHTS")
        print(f"{'='*60}\n")
        
        return highlights
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"ERROR IN GetMultipleHighlights FUNCTION:")
        print(f"{'='*60}")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception message: {str(e)}")
        print(f"\nTranscription length: {len(Transcription)} characters")
        print(f"First 200 chars: {Transcription[:200]}...")
        print(f"{'='*60}\n")
        import traceback
        traceback.print_exc()
        return []


def GetHighlight(Transcription):
    from langchain_openai import AzureChatOpenAI
    
    try:
        llm = AzureChatOpenAI(
            deployment_name=azure_openai_deployment,
            api_version=azure_openai_api_version,
            azure_endpoint=azure_openai_endpoint,
            api_key=azure_openai_api_key,
            temperature=1.0,
        )

        from langchain.prompts import ChatPromptTemplate
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system",system),
                ("user",Transcription)
            ]
        )
        chain = prompt |llm.with_structured_output(JSONResponse,method="function_calling")
        
        print("Calling LLM for highlight selection...")
        response = chain.invoke({"Transcription":Transcription})
        
        # Validate response
        if not response:
            print("ERROR: LLM returned empty response")
            return None, None
        
        if not hasattr(response, 'start') or not hasattr(response, 'end'):
            print(f"ERROR: Invalid response structure: {response}")
            return None, None
        
        try:
            Start = int(response.start)
            End = int(response.end)
        except (ValueError, TypeError) as e:
            print(f"ERROR: Could not parse start/end times from response")
            print(f"  response.start: {response.start}")
            print(f"  response.end: {response.end}")
            print(f"  Error: {e}")
            return None, None
        
        # Validate times
        if Start < 0 or End < 0:
            print(f"ERROR: Negative time values - Start: {Start}s, End: {End}s")
            return None, None
        
        if End <= Start:
            print(f"ERROR: Invalid time range - Start: {Start}s, End: {End}s (end must be > start)")
            return None, None
        
        # Log the selected segment
        print(f"\n{'='*60}")
        print(f"SELECTED SEGMENT DETAILS:")
        print(f"Time: {Start}s - {End}s ({End-Start}s duration)")
        print(f"Content: {response.content}")
        print(f"{'='*60}\n")
        
        if Start==End:
            Ask = input("Error - Get Highlights again (y/n) -> ").lower()
            if Ask == "y":
                Start, End = GetHighlight(Transcription)
            return Start, End
        return Start,End
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"ERROR IN GetHighlight FUNCTION:")
        print(f"{'='*60}")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception message: {str(e)}")
        print(f"\nTranscription length: {len(Transcription)} characters")
        print(f"First 200 chars: {Transcription[:200]}...")
        print(f"{'='*60}\n")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    print(GetHighlight(User))
