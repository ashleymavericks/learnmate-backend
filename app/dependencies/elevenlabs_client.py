import os
from elevenlabs import generate, set_api_key
from dotenv import load_dotenv

load_dotenv()


ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

async def generate_voice(text: str, voice: str = "Adam") -> bytes:
    """
    Generate voice from text using ElevenLabs API.
    
    :param text: The text to convert to speech
    :param voice: The voice to use (default is "Adam")
    :return: Audio data as bytes
    """
    try:
        set_api_key(ELEVENLABS_API_KEY)
        audio = generate(
            text=text,
            voice=voice,
            model="eleven_monolingual_v1"
        )
        return audio
    except Exception as e:
        print(f"Error generating voice: {str(e)}")
        return b""
