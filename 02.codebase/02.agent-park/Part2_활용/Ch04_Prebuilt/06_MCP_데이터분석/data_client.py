from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_mcp_adapters.prompts import load_mcp_prompt
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
import os

load_dotenv()
os.getenv("OPENAI_API_KEY")

model = ChatOpenAI(model="gpt-4o")

server_params = StdioServerParameters(
    command="python",
    args=["./data_server.py"],
)


async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            ##### AGENT #####
            tools = await load_mcp_tools(session)
            agent = create_react_agent(model, tools)

            ##### REQUEST & REPOND #####
            user_input = input("질문을 입력하세요: ")

            print("=====PROMPT=====")
            prompts = await load_mcp_prompt(
                session, "default_prompt", arguments={"message": user_input}
            )
            print("prompts : ", prompts)
            response = await agent.ainvoke({"messages": prompts})
            # response = await agent.ainvoke({"messages": user_input})

            # print(response)
            print("=====RESPONSE=====")
            print(response["messages"][-1].content)


import asyncio

asyncio.run(run())
