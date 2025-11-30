import asyncio
import time
from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from tools import *
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatOllama(
    model="gpt-oss:20b",
    base_url="http://192.168.2.54:11434",
    temperature=0.3,
    num_ctx=120000,
)

gemini_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.3,
)

system_prompt = """You are a highly intelligent web research assistant. 
Your task is to perform **deep research** and **parallel exploration** to gather complete and accurate information.

Guidelines:
1. Always start by exploring the database and metadata using fetch_metadata() or any relevant tools.
2. For any user query, break it into multiple sub-questions or search paths that can be investigated in parallel.
3. Prioritize thoroughness: collect multiple sources of evidence, cross-check facts, and identify gaps.
4. Keep track of which tools you use and the results they return.
5. Summarize findings clearly, including details and supporting data.
6. If a step requires deeper exploration, generate follow-up actions automatically using your tools.
7. Avoid assumptions: always verify through your tools before providing conclusions.
8. Communicate clearly, structured, and step-by-step when explaining complex topics.

Your goal is to give the user a complete, accurate, and well-researched answer by leveraging tools efficiently."""



agent = create_agent(
    model=gemini_llm,
    tools=[fetch_metadata],
    system_prompt=system_prompt,
)


async def main():
    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break

        if not user_input:
            continue

        start_time = time.time()

        result = await agent.ainvoke({"messages": [("user", user_input)]})

        end_time = time.time()
        response_time = end_time - start_time

        final_message = result["messages"][-1]

        # tool usage detection
        tool_calls = []
        for msg in result["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_calls.extend([t["name"] for t in msg.tool_calls])

        if tool_calls:
            print(f"\n[Tools Used → {', '.join(tool_calls)}]")

        print(f"\nAgent → {final_message.content}\n")
        print(f"Response time → {response_time:.2f}s")

        # Optional usage metadata
        if hasattr(final_message, 'usage_metadata') and final_message.usage_metadata:
            usage = final_message.usage_metadata
            print(
                f"Tokens: input={usage.get('input_tokens')} | "
                f"output={usage.get('output_tokens')} | "
                f"total={usage.get('total_tokens')}"
            )
        print()


asyncio.run(main())
