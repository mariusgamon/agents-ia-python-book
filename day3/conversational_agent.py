# conversational_agent.py
import config
import asyncio
from agents import Agent, Runner, SQLiteSession

agent = Agent(
    name="ConversationalAssistant",
    model=config.DEFAULT_MODEL,
    instructions="""You are a development assistant.
    You remember the conversation context.
    You reference what was previously said when relevant.""",
)

async def main():
    session = SQLiteSession("user_123_thread_456", "conversations.db")

    questions = [
        "I'm working on a FastAPI project in Python.",
        "Which middlewares do you recommend for error handling?",
        "And for JWT authentication, how do I integrate it with what you just told me?",
    ]

    for question in questions:
        print(f"\nUser: {question}")
        result = await Runner.run(agent, question, session=session)
        print(f"Agent: {result.final_output}")

asyncio.run(main())
