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
        대본을 오디오 파일(.mp3 및 .m4a)로 변환 저장
        gTTS로 MP3를 생성한 후, macOS 환경의 경우 afconvert를 통해 정품 AAC .m4a로 변환하여
        Safari, Chrome 등 모든 브라우저 및 플레이어 호환성을 100% 확보합니다.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        base_path = output_path.rsplit('.', 1)[0]
        mp3_path = base_path + ".mp3"
        m4a_path = base_path + ".m4a"

        try:
            tts = gTTS(text=text, lang=self.lang, slow=False)
            tts.save(mp3_path)
            
            # macOS afconvert로 AAC .m4a 변환
            try:
                subprocess.run(
                    ["afconvert", "-f", "m4af", "-d", "aac", mp3_path, m4a_path],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except Exception:
                if mp3_path != m4a_path:
                    import shutil
                    shutil.copy(mp3_path, m4a_path)

            return os.path.exists(output_path)
        except Exception as e:
            print(f"[TTSEngine] gTTS offline or failed ({e}), falling back to macOS native say + afconvert...")
            try:
                voice_map = {"ko": "Yuna", "en": "Samantha", "zh-CN": "Tingting", "zh": "Tingting"}
                mac_voice = voice_map.get(self.lang, "Yuna")
                aiff_path = base_path + ".aiff"
                subprocess.run(
                    ["say", "-v", mac_voice, "-r", "185", "-o", aiff_path, text],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                subprocess.run(
                    ["afconvert", "-f", "m4af", "-d", "aac", aiff_path, m4a_path],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                if os.path.exists(aiff_path):
                    os.remove(aiff_path)
                if not os.path.exists(mp3_path) and os.path.exists(m4a_path):
                    import shutil
                    shutil.copy(m4a_path, mp3_path)
                return os.path.exists(output_path)
            except Exception as e2:
                print(f"[TTSEngine] Fallback say+afconvert failed: {e2}")
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
