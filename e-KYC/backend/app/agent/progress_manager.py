import asyncio
import logging
from livekit.agents.voice import AgentSession

logger = logging.getLogger(__name__)

class ProcessingConversationManager:
    def __init__(self, session: AgentSession):
        self.session = session
        self._task = None

    async def start(self, document_type: str):
        """Starts the natural voice progress task."""
        if self._task:
            self._task.cancel()
        self._task = asyncio.create_task(self._speak_loop(document_type))

    async def _speak_loop(self, document_type: str):
        try:
            # 0-2 seconds: Do nothing, let the initial confirmation finish
            await asyncio.sleep(2)
            
            # 2-5 seconds
            doc_name = document_type.replace('_', ' ').title()
            self.session.say(f"I am carefully checking your {doc_name}. It will just take a moment.", allow_interruptions=False)
            await asyncio.sleep(3)
            
            # 5-8 seconds
            self.session.say("Verification is currently in progress. Please stay on the line, there is no rush.", allow_interruptions=False)
            await asyncio.sleep(3)
            
            # > 8 seconds
            self.session.say("This is taking a bit longer, but please don't worry, I am right here.", allow_interruptions=False)
            
        except asyncio.CancelledError:
            # Processing completed and cancelled this filler loop
            pass
        except Exception as e:
            logger.error(f"Error in progress speech: {e}")

    async def stop(self):
        """Stops the filler speech immediately."""
        if self._task:
            self._task.cancel()
            self._task = None
            try:
                # Forcefully interrupt any currently playing filler speech
                await self.session.interrupt(force=True)
            except Exception as e:
                logger.debug(f"Interrupting progress speech threw: {e}")
