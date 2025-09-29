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
# 0.0 - 6.32:  Should we bring this up? I guess we have to so this just happened. We just found out that Charlie Kirk got shot9.0 - 11.48:  An awful and is he dead?14.0 - 19.92:  That's what was one of the guys out there just said okay firm in the lobby was just I was looking19.92 - 22.240000000000002:  I've been looking, I haven't seen anything that's confirmed.25.28 - 26.12:  Whoa.28.200000000000003 - 31.120000000000005:  Murder for having a different opinion from somebody else.31.120000000000005 - 31.880000000000003:  Yeah.31.880000000000003 - 33.68:  Different ideology from somebody else.35.040000000000006 - 35.6:  Yeah.35.6 - 36.44:  Yeah.36.44 - 38.32000000000001:  I mean, I don't know.38.32 - 43.88:  Beliefs that didn't align. Yep. I'm sorry. Yep. Rest in peace. We're gonna snooze. Oh45.08 - 51.88:  Jesus 27 years old maybe 30 even have a suspect. I don't know51.88 - 56.88:  So I don't, I don't, I'm literally trying to check it all on Twitter and it's all.56.88 - 57.88:  F***.57.88 - 58.88:  F***.58.88 - 59.88:  Nobody deserves it.59.88 - 60.88:  You didn't deserve that.60.88 - 61.88:  Nobody deserves that.
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
    # print(f"Start is {response.start}")
    # print(f"end is {response.end}")
    # print(f"highlight is {response.content}\n\n")
    Start,End = int(response.start), int(response.end)
    print(f"Start is {Start}")
    print(f"End is {End}\n\n")
    if Start==End:
        Ask = input("Error - Get Highlights again (y/n) -> ").lower()
        if Ask == "y":
            Start, End = GetHighlight(Transcription)
        return Start, End
    return Start,End

if __name__ == "__main__":
    print(GetHighlight(User))
