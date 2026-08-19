import asyncio
import os
from dotenv import load_dotenv
from livekit import api

load_dotenv()

async def clear_rooms():
    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    
    livekit_api = api.LiveKitAPI(
        url,
        api_key,
        api_secret
    )
    
    try:
        rooms = await livekit_api.room.list_rooms(api.ListRoomsRequest())
        if not rooms.rooms:
            print("No active LiveKit sessions/rooms found.")
        else:
            for room in rooms.rooms:
                print(f"Deleting LiveKit room: {room.name}")
                await livekit_api.room.delete_room(api.DeleteRoomRequest(room=room.name))
            print("All LiveKit sessions cleared successfully.")
    except Exception as e:
        print(f"Error clearing rooms: {e}")
    finally:
        await livekit_api.aclose()

if __name__ == "__main__":
    asyncio.run(clear_rooms())
