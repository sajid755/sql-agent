from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from tools import *
import time


llm = ChatOllama(
    model="gpt-oss:20b",
    base_url="http://192.168.2.54:11434",
    temperature=0.3,
    num_ctx=120000,         
    stop=None,
)

# gemini_llm = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash",
#     google_api_key=os.getenv("GOOGLE_API_KEY"),
#     temperature=0.3,
# )


system_prompt = """You are a SQL assistant. Always use your tools to explore the database first:
1. Use list_tables() to see available tables
2. Use get_table_schema() to understand structure
3. Use run_sql_query() to answer questions

IMPORTANT - When using list_tables():
- If looking for specific tables (e.g., "customer", "user", "product"), ALWAYS use pattern filtering first: list_tables(pattern="%keyword%")
- DO NOT paginate through all tables unless the user explicitly asks to see all tables
- The first list_tables() call shows total count - use that to decide if pattern filtering is needed
- Only use pagination (offset parameter) if user specifically requests more results

Never ask users about table/column names - explore yourself!"""

agent = create_agent(
    model=llm,
    tools=[run_sql_query,get_table_schema,list_tables,export_query_to_csv],
    system_prompt=system_prompt,
)


print("SQL Agent started. Type 'exit' or 'quit' to stop.\n")

THREAD_ID = "main_session"
MAX_HISTORY_MESSAGES = 5  # Keep last 5 user messages (10 total with responses)

while True:
    user_input = input("You: ").strip()

    if user_input.lower() in ['exit', 'quit']:
        print("Goodbye!")
        break

    if not user_input:
        continue

    start_time = time.time()

    # Get current state to trim history
    # config = {"configurable": {"thread_id": THREAD_ID}}
    # state = agent.get_state(config)

    # Trim message history to keep only last MAX_HISTORY_MESSAGES exchanges
    # if state.values and 'messages' in state.values:
    #     messages = state.values['messages']
    #     print(f"[DEBUG] Current message count: {len(messages)}")
    #     if len(messages) > MAX_HISTORY_MESSAGES * 2:  # *2 because each exchange has user + assistant
    #         # Keep only the last N exchanges
    #         trimmed_messages = messages[-(MAX_HISTORY_MESSAGES * 2):]
    #         print(f"[DEBUG] Trimming from {len(messages)} to {len(trimmed_messages)} messages")
    #         agent.update_state(config, {"messages": trimmed_messages})

    result = agent.invoke({"messages": [("user", user_input)]})
    end_time = time.time()

    response_time = end_time - start_time
    final_message = result['messages'][-1]

    # Collect tool calls
    tool_calls = []
    for msg in result['messages']:
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            tool_calls.extend([tc['name'] for tc in msg.tool_calls])

    if tool_calls:
        print(f"\n[Tools used: {', '.join(tool_calls)}]")

    print(f"\nAgent: {final_message.content}\n")

    # Print metadata
    print(f"Response time: {response_time:.2f}s")
    if hasattr(final_message, 'usage_metadata') and final_message.usage_metadata:
        usage = final_message.usage_metadata
        print(f"Tokens - Input: {usage.get('input_tokens', 'N/A')}, Output: {usage.get('output_tokens', 'N/A')}, Total: {usage.get('total_tokens', 'N/A')}")
    print()