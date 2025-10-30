"""
ElevenLabs Voice I/O Client for Medication Advisor.
Handles speech-to-text (STT) and text-to-speech (TTS) using ElevenLabs API.
"""

import io
import os
from typing import Optional, BinaryIO
from pathlib import Path

try:
    from elevenlabs import ElevenLabs, Voice, VoiceSettings
    from elevenlabs.client import ElevenLabs as ElevenLabsClient
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    print("Warning: elevenlabs package not installed. Run: pip install elevenlabs")

from src.utils.config import config


class ElevenLabsVoiceClient:
    """
    Client for ElevenLabs voice services.

    Features:
    - Text-to-Speech (TTS) with customizable voices
    - Speech-to-Text (STT) using ElevenLabs Scribe
    - Streaming audio support
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        voice_id: Optional[str] = None
    ):
        """
        Initialize ElevenLabs client.

        Args:
            api_key: ElevenLabs API key (defaults to config)
            voice_id: Voice ID for TTS (defaults to config or preset)
        """
        if not ELEVENLABS_AVAILABLE:
            raise ImportError(
                "elevenlabs package is required. Install with: pip install elevenlabs"
            )

        self.api_key = api_key or config.ELEVENLABS_API_KEY
        self.voice_id = voice_id or config.ELEVENLABS_VOICE_ID

        if not self.api_key:
            raise ValueError(
                "ElevenLabs API key not found. Set ELEVENLABS_API_KEY in .env file"
            )

        self.client = ElevenLabsClient(api_key=self.api_key)

        if not self.voice_id:
            self.voice_id = "21m00Tcm4TlvDq8ikWAM"  # Default: Rachel voice

    def text_to_speech(
        self,
        text: str,
        output_path: Optional[Path] = None,
        voice_id: Optional[str] = None,
        model: str = "eleven_monolingual_v1",
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        use_speaker_boost: bool = True
    ) -> bytes:
        """
        Convert text to speech using ElevenLabs TTS.

        Args:
            text: Text to convert to speech
            output_path: Optional path to save audio file
            voice_id: Voice ID (uses default if not provided)
            model: TTS model to use
            stability: Voice stability (0.0-1.0)
            similarity_boost: Voice similarity (0.0-1.0)
            style: Voice style/expression (0.0-1.0)
            use_speaker_boost: Enable speaker boost

        Returns:
            Audio bytes
        """
        voice_id = voice_id or self.voice_id

        try:
            audio_generator = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id=model,
                voice_settings=VoiceSettings(
                    stability=stability,
                    similarity_boost=similarity_boost,
                    style=style,
                    use_speaker_boost=use_speaker_boost
                )
            )

            audio_bytes = b''.join(chunk for chunk in audio_generator)

            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, 'wb') as f:
                    f.write(audio_bytes)

                print(f"Audio saved to: {output_path}")

            return audio_bytes

        except Exception as e:
            raise RuntimeError(f"TTS error: {e}")

    def speech_to_text(
        self,
        audio_file: BinaryIO,
        model: str = "scribe_v1"
    ) -> str:
        """
        Convert speech to text using ElevenLabs Scribe.

        Args:
            audio_file: Audio file object (opened in binary mode)
            model: STT model to use (scribe_v1 or scribe_v1_experimental)

        Returns:
            Transcribed text
        """
        try:
            result = self.client.speech_to_text.convert(
                file=audio_file,
                model_id=model
            )

            if hasattr(result, 'text'):
                return result.text
            else:
                return str(result)

        except Exception as e:
            raise RuntimeError(f"STT error: {e}")

    def speech_to_text_from_file(
        self,
        file_path: Path,
        model: str = "scribe_v1"
    ) -> str:
        """
        Convert audio file to text.

        Args:
            file_path: Path to audio file
            model: STT model to use (scribe_v1 or scribe_v1_experimental)

        Returns:
            Transcribed text
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        with open(file_path, 'rb') as audio_file:
            return self.speech_to_text(audio_file, model=model)

    def list_voices(self) -> list:
        """
        List available voices.

        Returns:
            List of voice objects
        """
        try:
            voices = self.client.voices.get_all()
            return voices.voices if hasattr(voices, 'voices') else []
        except Exception as e:
            print(f"Error listing voices: {e}")
            return []

    def get_voice_info(self, voice_id: Optional[str] = None) -> dict:
        """
        Get information about a voice.

        Args:
            voice_id: Voice ID (uses default if not provided)

        Returns:
            Voice information dictionary
        """
        voice_id = voice_id or self.voice_id

        try:
            voice = self.client.voices.get(voice_id)
            return {
                'voice_id': voice.voice_id,
                'name': voice.name,
                'category': getattr(voice, 'category', 'unknown'),
                'description': getattr(voice, 'description', ''),
            }
        except Exception as e:
            print(f"Error getting voice info: {e}")
            return {}


class VoiceAssistant:
    """
    Voice assistant wrapper for the medication advisor agent.
    Combines STT, agent, and TTS for voice-based Q&A.
    """

    def __init__(
        self,
        agent,
        voice_client: Optional[ElevenLabsVoiceClient] = None,
        auto_save_audio: bool = True,
        audio_output_dir: Path = None
    ):
        """
        Initialize voice assistant.

        Args:
            agent: MedicationAdvisorAgent instance
            voice_client: ElevenLabsVoiceClient instance
            auto_save_audio: Whether to save audio responses
            audio_output_dir: Directory to save audio files
        """
        self.agent = agent
        self.voice_client = voice_client or ElevenLabsVoiceClient()
        self.auto_save_audio = auto_save_audio
        self.audio_output_dir = audio_output_dir or (config.DATA_DIR / "audio_responses")

        if self.auto_save_audio:
            self.audio_output_dir.mkdir(parents=True, exist_ok=True)

    def process_voice_question(
        self,
        audio_file: Path,
        save_response_audio: bool = None
    ) -> tuple[str, str, bytes]:
        """
        Process a voice question end-to-end.

        Args:
            audio_file: Path to audio file with question
            save_response_audio: Whether to save response audio

        Returns:
            Tuple of (question_text, response_text, response_audio_bytes)
        """
        save_audio = save_response_audio if save_response_audio is not None else self.auto_save_audio

        print(f"Transcribing question from: {audio_file}")
        question_text = self.voice_client.speech_to_text_from_file(audio_file)
        print(f"Question: {question_text}")

        print("\nProcessing with agent...")
        response_text = self.agent.ask(question_text)
        print(f"Response: {response_text}")

        print("\nGenerating speech response...")
        response_audio = self.voice_client.text_to_speech(
            text=response_text,
            output_path=self.audio_output_dir / "latest_response.mp3" if save_audio else None
        )

        return question_text, response_text, response_audio

    def ask_with_voice(
        self,
        question_text: str,
        save_audio: bool = True
    ) -> bytes:
        """
        Ask a text question and get voice response.

        Args:
            question_text: The question text
            save_audio: Whether to save the audio response

        Returns:
            Audio bytes
        """
        print(f"Question: {question_text}")

        response_text = self.agent.ask(question_text)
        print(f"Response: {response_text}")

        output_path = None
        if save_audio:
            safe_filename = "".join(c for c in question_text[:50] if c.isalnum() or c in (' ', '-', '_')).strip()
            output_path = self.audio_output_dir / f"{safe_filename}.mp3"

        response_audio = self.voice_client.text_to_speech(
            text=response_text,
            output_path=output_path
        )

        return response_audio


def create_voice_client(api_key: Optional[str] = None) -> ElevenLabsVoiceClient:
    """
    Factory function to create ElevenLabs voice client.

    Args:
        api_key: Optional API key (uses config if not provided)

    Returns:
        Initialized ElevenLabsVoiceClient
    """
    return ElevenLabsVoiceClient(api_key=api_key)


if __name__ == "__main__":
    print("Testing ElevenLabs Voice Client...")

    try:
        client = create_voice_client()

        print("\nTesting TTS...")
        test_text = "Hello! I am your medication advisor assistant. How can I help you today?"

        output_path = config.DATA_DIR / "test_audio.mp3"
        audio_bytes = client.text_to_speech(test_text, output_path=output_path)

        print(f"Generated {len(audio_bytes)} bytes of audio")
        print(f"Audio saved to: {output_path}")

        print("\nListing available voices...")
        voices = client.list_voices()
        print(f"Found {len(voices)} voices:")
        for voice in voices[:5]:
            print(f"  - {voice.name} ({voice.voice_id})")

        print("\nVoice client test completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure ELEVENLABS_API_KEY is set in your .env file")
