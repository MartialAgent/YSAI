from dotenv import load_dotenv
import os
import asyncio
import sys

from typing import Literal
from typing_extensions import TypedDict

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import MessagesState, END
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()
os.getenv("OPENAI_API_KEY")

from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4o")

######################## GRAPH STATE ########################
members = ["file_searcher", "web_searcher"]
options = members + ["FINISH"]


class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""

    next: Literal[*options]


class State(MessagesState):
    next: str


async def run():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    async with MultiServerMCPClient(
        {
            "file": {
                "url": "http://localhost:8000/sse",
                "transport": "sse",
            },
            "web": {
                "url": "http://localhost:8001/sse",
                "transport": "sse",
            },
        }
    ) as client:
        # await client.__aenter__()

        ######################## CHECK TOOLS ########################
        # Check file server tools
        file_tools = client.server_name_to_tools["file"]
        file_tool_names = {tool.name for tool in file_tools}
        assert file_tool_names == {"file_listup", "file_info", "save_file"}

        # Check web server tools
        web_tools = client.server_name_to_tools["web"]
        web_tool_names = {tool.name for tool in web_tools}
        assert web_tool_names == {"web_search", "weather_search"}

        ######################## AGENT ########################

        system_prompt = (
            "You are a supervisor tasked with managing a conversation between the"
            f" following workers: {members}. Given the following user request,"
            " respond with the worker to act next. Each worker will perform a"
            " task and respond with their results and status. When finished,"
            " respond with FINISH."
        )

        ######################## SUPERVISOR ########################
        async def supervisor_node(
            state: State,
        ) -> Command[Literal[*members, "__end__"]]:
            messages = [
                {"role": "system", "content": system_prompt},
            ] + state["messages"]
            response = await model.with_structured_output(Router).ainvoke(messages)
            goto = response["next"]  # web , file
            if goto == "FINISH":
                goto = END

            return Command(goto=goto, update={"next": goto})

        ######################## 1) FILE SEARCHER ########################
        file_searcher = create_react_agent(model, file_tools)

        async def file_search_node(state: State) -> Command[Literal["supervisor"]]:
            result = await file_searcher.ainvoke(state)
            return Command(
                update={
                    "messages": [
                        HumanMessage(
                            content=result["messages"][-1].content, name="file_searcher"
                        )
                    ]
                },
                goto="supervisor",
            )

        ######################## 2) WEB SEARCHER ########################
        web_searcher = create_react_agent(model, web_tools)

        async def web_search_node(state: State) -> Command[Literal["supervisor"]]:
            result = await web_searcher.ainvoke(state)
            return Command(
                update={
                    "messages": [
                        HumanMessage(
                            content=result["messages"][-1].content, name="web_searcher"
                        )
                    ]
                },
                goto="supervisor",
            )

        ######################## GRAPH COMPILE ########################
        graph_builder = StateGraph(State)
        graph_builder.add_edge(START, "supervisor")
        graph_builder.add_node("supervisor", supervisor_node)
        graph_builder.add_node("file_searcher", file_search_node)
        graph_builder.add_node("web_searcher", web_search_node)
        memory = MemorySaver()
        graph = graph_builder.compile(checkpointer=memory)

        ######################## SAVE GRAPH IMAGE ########################
        from PIL import Image as PILImage
        from io import BytesIO

        image_data = graph.get_graph(xray=True).draw_mermaid_png()
        image = PILImage.open(BytesIO(image_data))
        image.save("mcp_supervisor_graph.png")

        ######################## REQUEST & REPOND ########################
        config = {"configurable": {"thread_id": "1"}}
        while True:
            try:
                user_input = input("질문을 입력하세요: ")
                if user_input.lower() in ["quit", "exit", "q"]:
                    print("안녕히 가세요!")
                    break

                print("=====RESPONSE=====")
                async for namespace, chunk in graph.astream(
                    {"messages": user_input},
                    stream_mode="updates",
                    subgraphs=True,
                    config=config,
                ):
                    for node_name, node_chunk in chunk.items():
                        if "messages" in node_chunk:
                            node_chunk["messages"][-1].pretty_print()
                        else:
                            print(node_chunk)

                # async for chunk in graph.astream(
                #     {"messages": user_input},
                #     stream_mode="updates",
                #     config=config,
                # ):
                #     for node, value in chunk.items():
                #         print(node, value)
                #         if "messages" in value:
                #             value["messages"][-1].pretty_print()

            except Exception as e:
                print(f"종료합니다.{e}")
                break


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback

        traceback.print_exc()
