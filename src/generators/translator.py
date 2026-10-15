from googletrans import Translator
import time

def _translate_chunk(text: str, target_lang: str) -> str:
    if not text.strip(): return text
    # Map target language to googletrans code
    target_code = "en" if target_lang == "en" else "zh-cn"
    try:
        translator = Translator()
        time.sleep(0.1)
        result = translator.translate(text, src='ko', dest=target_code)
        return result.text
    except Exception as e:
        print(f"[Translator Error] {e}")
        return text

def translate_text(text: str, target_lang: str) -> str:
    lines = text.split("\n")
    translated_lines = []
    
    for t in lines:
        translated_lines.append(_translate_chunk(t, target_lang))
        
    return "\n".join(translated_lines)
