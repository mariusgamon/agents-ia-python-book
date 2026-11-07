# conversational_agent_manual.py
import config
import asyncio
from agents import Agent, Runner

agent = Agent(
    name="ConversationalAssistant",
    model=config.DEFAULT_MODEL,
    instructions="""You are a development assistant.
    You remember the conversation context.
    You reference what was previously said when relevant.""",
)

async def conversation():
    """Multi-turn conversation with manual history."""
    history = []

    questions = [
        "I'm working on a FastAPI project in Python.",
        "Which middlewares do you recommend for error handling?",
        "And for JWT authentication, how do I integrate it with what you just told me?",
    ]

    for question in questions:
        print(f"\nUser: {question}")

        result = await Runner.run(
            agent,
            input=history + [{"role": "user", "content": question}],
        )

        print(f"Agent: {result.final_output}")

        # to_input_list() conserve TOUT l'historique du run :
        # message utilisateur, réponse, tool calls, handoffs, etc.
        # Bien plus complet qu'un append manuel sur final_output.
        history = result.to_input_list()

asyncio.run(conversation())
