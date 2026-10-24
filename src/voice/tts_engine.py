import asyncio
import concurrent.futures
import os
import re
import shutil
import subprocess


class TTSEngine:
    """
    Microsoft Edge Neural TTS (edge-tts) 기반 고품질 아나운서 음성 브리핑 생성기
    (네트워크/환경 상황에 따라 edge-tts -> gTTS -> macOS say 순으로 자동 폴백)
    """

    NEURAL_VOICES = {
        "ko": "ko-KR-SunHiNeural",
        "en": "en-US-AndrewMultilingualNeural",
        "zh-CN": "zh-CN-XiaoxiaoNeural",
        "zh": "zh-CN-XiaoxiaoNeural",
    }

    def __init__(self, voice: str = "ko", rate: int = 0):
        self.lang = voice
        self.neural_voice = self.NEURAL_VOICES.get(voice, "ko-KR-SunHiNeural")
        if isinstance(rate, str) and rate.endswith("%"):
            self.edge_rate = rate
        elif isinstance(rate, int) and -50 <= rate <= 50 and rate != 0:
            self.edge_rate = f"{rate:+d}%"
        else:
            self.edge_rate = "+0%"

    @staticmethod
    def normalize_for_speech(text: str, lang: str = "ko") -> str:
        """
        TTS 낭독 시 부자연스러운 기호(·, …, ~, 대괄호 말머리, 중복 영문 병기 등)를
        실제 라디오 아나운서 호흡과 발음에 맞게 정제합니다.
        """
        cleaned = text

        # 1. 기사 말머리 대괄호 제거 (예: [기고], [글로벌 방산], [기자수첩], (종합) 등)
        cleaned = re.sub(r"\[[^\]]{1,30}\]\s*", "", cleaned)
        cleaned = re.sub(r"\((?:종합|상보|속보|단독|1보|2보)\)", "", cleaned)

        # 2. 화살표 및 클릭베이트 구분 기호 정제 (->, =>, >>, <<, ▶, ▷, |, =)
        cleaned = re.sub(r"\s*(?:->|=>|>>|<<|▶|▷|►|▻|=|\|)\s*", ", ", cleaned)

        if lang == "ko":
            # 한글 뒤 중복 영문 약어 괄호 제거 (예: 미 연준(Fed) -> 미 연준, 나토(NATO) -> 나토)
            cleaned = re.sub(r"\([A-Za-z0-9\s&.\-/]{2,20}\)", "", cleaned)

            # 한자(Hanja) 축약어 한글 독음 변환
            hanja_map = {
                "發": "발 ",
                "美": "미국 ",
                "韓": "한국 ",
                "中": "중국 ",
                "日": "일본 ",
                "北": "북한 ",
                "對": "대 ",
                "與": "여당 ",
                "野": "야당 ",
                "英": "영국 ",
                "獨": "독일 ",
                "佛": "프랑스 ",
                "俄": "러시아 ",
                "軍": "군 ",
                "尹": "윤 ",
                "金": "김 ",
                "李": "이 ",
                "前": "전 ",
                "後": "후 ",
                "重": "중 ",
                "行": "행 ",
            }
            for h, k in hanja_map.items():
                cleaned = cleaned.replace(h, k)

            # 물결표(~) 범위 표현을 자연스러운 조사로 변환 (예: 1,360~1,380 -> 1,360에서 1,380)
            cleaned = re.sub(r"(\d[\d,.]*)\s*~\s*(\d[\d,.]*)", r"\1에서 \2", cleaned)
            cleaned = cleaned.replace("~", "에서 ")

            # 발음이 어색한 영문 기술 용어 한국어 발음 보정
            cleaned = re.sub(r"\bArXiv\b", "아카이브", cleaned, flags=re.IGNORECASE)
            cleaned = cleaned.replace("S&P500", "에스앤피 500").replace("S&P 500", "에스앤피 500")
            cleaned = cleaned.replace("CoWoS-L", "코워스 엘").replace("CoWoS", "코워스")
            cleaned = cleaned.replace("HBM4", "에이치비엠 포").replace("HBM3E", "에이치비엠 쓰리이")
            cleaned = cleaned.replace("sLLM", "소형 언어모델").replace("LLM", "엘엘엠")
        elif lang in ("zh", "zh-CN"):
            cleaned = re.sub(r"(\d[\d,.]*)\s*~\s*(\d[\d,.]*)", r"\1至\2", cleaned)
        else:
            cleaned = re.sub(r"(\d[\d,.]*)\s*~\s*(\d[\d,.]*)", r"\1 to \2", cleaned)

        # 가운뎃점(·) 및 말줄임표(…)를 자연스러운 쉼표 호흡으로 변환
        cleaned = cleaned.replace("·", ", ").replace("•", ", ")
        cleaned = cleaned.replace("…", ", ").replace("...", ", ")
        cleaned = cleaned.replace("‘", "").replace("’", "").replace("'", "")
        cleaned = cleaned.replace("“", "").replace("”", "").replace('"', "")

        # 다중 공백 및 쉼표 정리
        cleaned = re.sub(r"\s*,\s*,\s*", ", ", cleaned)
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        return cleaned.strip()

    async def _save_edge_tts_async(self, text: str, mp3_path: str) -> None:
        import edge_tts

        communicate = edge_tts.Communicate(
            text=text,
            voice=self.neural_voice,
            rate=self.edge_rate,
            pitch="+0Hz",
        )
        await communicate.save(mp3_path)

    def _convert_to_m4a(self, src_audio_path: str, m4a_path: str) -> None:
        try:
            subprocess.run(
                ["afconvert", "-f", "m4af", "-d", "aac", src_audio_path, m4a_path],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            if src_audio_path != m4a_path and os.path.exists(src_audio_path):
                shutil.copy(src_audio_path, m4a_path)

    def save_audio(self, text: str, output_path: str) -> bool:
        """
        대본을 Microsoft Edge Neural TTS 기반 고품질 자연스러운 사람 음성(.mp3 및 .m4a)으로 변환 저장합니다.
        (Edge Neural TTS 실패 시 gTTS, 그 후 macOS say 순으로 자동 폴백)
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        base_path = output_path.rsplit(".", 1)[0]
        mp3_path = base_path + ".mp3"
        m4a_path = base_path + ".m4a"

        spoken_text = self.normalize_for_speech(text, self.lang)

        # 1순위: Microsoft Edge Neural TTS (자연스러운 고품질 사람 목소리)
        try:
            import edge_tts
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                        pool.submit(asyncio.run, self._save_edge_tts_async(spoken_text, mp3_path)).result()
                else:
                    loop.run_until_complete(self._save_edge_tts_async(spoken_text, mp3_path))
            except RuntimeError:
                asyncio.run(self._save_edge_tts_async(spoken_text, mp3_path))

            if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 10240:
                self._convert_to_m4a(mp3_path, m4a_path)
                return True
        except Exception as e_edge:
            print(f"[TTSEngine] Microsoft Edge Neural TTS failed ({e_edge}), falling back to gTTS...")

        # 2순위: Google Text-to-Speech (gTTS 폴백)
        try:
            from gtts import gTTS

            gtts_lang = "zh-CN" if self.lang in ("zh", "zh-CN") else self.lang
            tts = gTTS(text=spoken_text, lang=gtts_lang, slow=False)
            tts.save(mp3_path)
            if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 1024:
                self._convert_to_m4a(mp3_path, m4a_path)
                return True
        except Exception as e_gtts:
            print(f"[TTSEngine] gTTS failed ({e_gtts}), falling back to macOS native say...")

        # 3순위: 오프라인 폴백 (macOS say + afconvert)
        try:
            voice_map = {"ko": "Yuna", "en": "Samantha", "zh-CN": "Tingting", "zh": "Tingting"}
            mac_voice = voice_map.get(self.lang, "Yuna")
            aiff_path = base_path + ".aiff"
            subprocess.run(
                ["say", "-v", mac_voice, "-r", "185", "-o", aiff_path, spoken_text],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._convert_to_m4a(aiff_path, m4a_path)
            if os.path.exists(aiff_path):
                os.remove(aiff_path)
            if not os.path.exists(mp3_path) and os.path.exists(m4a_path):
                shutil.copy(m4a_path, mp3_path)
            return os.path.exists(output_path)
        except Exception as e_say:
            print(f"[TTSEngine] Fallback say+afconvert failed: {e_say}")
            return False

    def speak(self, text: str, background: bool = False):
        """
        텍스트를 실시간으로 음성 낭독 (임시 파일 생성 후 afplay 재생)
        """
        temp_audio = "/tmp/neural_tts_speak_temp.mp3"
        if self.save_audio(text, temp_audio):
            cmd = ["afplay", temp_audio]
            try:
                if background:
                    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    subprocess.run(cmd, check=True)
            except Exception as e:
                print(f"[TTSEngine] Error playing audio: {e}")
