"""
Audio transcription using xAI STT or OpenAI Whisper.
"""
import logging
import httpx
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ai_provider import transcribe_file, using_xai

logger = logging.getLogger(__name__)

class TranscriptionService:
    """Handles audio transcription with timeout and retry logic"""
    
    def __init__(self, config: dict, openai_api_key: str):
        self.config = config
        self.openai_api_key = openai_api_key
        
    def transcribe(self, audio_file_path: str) -> Optional[str]:
        """
        Transcribe audio file using xAI STT or OpenAI Whisper.
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Transcribed text or None if failed
        """
        try:
            text = self._transcribe_with_retry(audio_file_path)
            logger.info("Transcription successful")
            return text
        except Exception as e:
            logger.error(f"Transcription failed after retries: {e}")
            return None
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        reraise=True
    )
    def _transcribe_with_retry(self, audio_file_path: str) -> Optional[str]:
        return transcribe_file(audio_file_path)
