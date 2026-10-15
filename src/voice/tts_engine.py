import os
import subprocess
from gtts import gTTS

class TTSEngine:
    """
    gTTS (Google Text-to-Speech)를 활용한 보다 자연스러운 음성 브리핑 생성기
    기존 macOS 내장 기계음(say) 대신 구글 음성을 제공합니다.
    """
    def __init__(self, voice: str = "ko", rate: int = 0):
        # We will use 'voice' parameter to determine the language.
        # "ko", "en", "zh-CN"
        self.lang = voice

    def save_audio(self, text: str, output_path: str) -> bool:
        """
        대본을 오디오 파일(.m4a / .mp3)로 변환 저장
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        try:
            tts = gTTS(text=text, lang=self.lang, slow=False)
            tts.save(output_path)
            return os.path.exists(output_path)
        except Exception as e:
            print(f"[TTSEngine] Error saving audio file with gTTS: {e}")
            return False

    def speak(self, text: str, background: bool = False):
        """
        텍스트를 실시간으로 음성 낭독 (임시 파일 생성 후 afplay 재생)
        """
        temp_audio = "/tmp/gtts_speak_temp.mp3"
        if self.save_audio(text, temp_audio):
            cmd = ["afplay", temp_audio]
            try:
                if background:
                    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    subprocess.run(cmd, check=True)
            except Exception as e:
                print(f"[TTSEngine] Error playing audio: {e}")
