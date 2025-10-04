from pydantic import BaseModel,Field
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("OPENAI_API")

if not api_key:
    raise ValueError("API key not found. Make sure it is defined in the .env file.")

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

system = """

Based on the Transcription user provides with start and end, Highilight the main parts in less then 1 min which can be directly converted into a short. highlight it such that its intresting and also keep the time staps for the clip to start and end. only select a continues Part of the video

Follow this Format and return in valid json 
[{{
start: "Start time of the clip",
content: "Highlight Text",
end: "End Time for the highlighted clip"
}}]
it should be one continues clip as it will then be cut from the video and uploaded as a tiktok video. so only have one start, end and content
Make sure that the content's length doesn't go beyond 60 seconds.

Dont say anything else, just return Proper Json. no explanation etc


IF YOU DONT HAVE ONE start AND end WHICH IS FOR THE LENGTH OF THE ENTIRE HIGHLIGHT, THEN 10 KITTENS WILL DIE, I WILL DO JSON['start'] AND IF IT DOESNT WORK THEN...

<TRANSCRIPTION>
{Transcription}

"""

# User = """
# Example
# """




def GetHighlight(Transcription):
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(
        model="gpt-4o-2024-05-13",
        temperature=0.7,
        api_key = api_key
    )

    from langchain.prompts import ChatPromptTemplate
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system",system),
            ("user",Transcription)
        ]
    )
    chain = prompt |llm.with_structured_output(JSONResponse,method="function_calling")
    response = chain.invoke({"Transcription":Transcription})
    Start,End = int(response.start), int(response.end)
    # print(f"Start is {Start}")
    # print(f"End is {End}\n\n")
    if Start==End:
        Ask = input("Error - Get Highlights again (y/n) -> ").lower()
        if Ask == "y":
            Start, End = GetHighlight(Transcription)
        return Start, End
    return Start,End

if __name__ == "__main__":
    print(GetHighlight(User))
