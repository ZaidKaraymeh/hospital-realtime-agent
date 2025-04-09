from __future__ import annotations

import logging
from dotenv import load_dotenv

from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.multimodal import MultimodalAgent
from livekit.plugins import openai
from prompt import AGENT_PROMPT, WELCOME_MESSAGE
from api import AssistantFnc, WorkflowsEnum

load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("my-worker")
logger.setLevel(logging.INFO)


async def entrypoint(ctx: JobContext):
    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    participant = await ctx.wait_for_participant()

    run_multimodal_agent(ctx, participant)

    logger.info("agent started")


def run_multimodal_agent(ctx: JobContext, participant: rtc.RemoteParticipant):
    logger.info("starting multimodal agent")
    _tools = AssistantFnc()
    model = openai.realtime.RealtimeModel(
        voice="ballad",
        instructions=AGENT_PROMPT,
        modalities=["audio", "text"],
    )

    agent = MultimodalAgent(
        model=model,
        fnc_ctx=_tools,

    )
    agent.start(ctx.room, participant)

    session = model.sessions[0]
    session.conversation.item.create(
        llm.ChatMessage(
            role="assistant",
            content=WELCOME_MESSAGE
        )
    )
    session.response.create()

    @session.on("user_speech_committed")
    def on_user_speech_committed(event: llm.ChatMessage):
        if isinstance(event.content, list):
            event.content = "\n".join(
                "[image]" if isinstance(x, llm.ChatImage) else x for x in event
            )

        logger.info(f"Current workflow: {_tools._current_workflow}")

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )
