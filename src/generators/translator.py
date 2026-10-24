from googletrans import Translator
import time

def _translate_chunk(text: str, target_lang: str, src_lang: str = None) -> str:
    if not text.strip(): return text
    # Map target language to googletrans code
    if target_lang == "en":
        target_code = "en"
        src_code = src_lang or "ko"
    elif target_lang in ("zh", "zh-cn", "zh-CN"):
        target_code = "zh-cn"
        src_code = src_lang or "ko"
    elif target_lang == "ko":
        target_code = "ko"
        src_code = src_lang or "auto"
    else:
        target_code = target_lang
        src_code = src_lang or "auto"

    try:
        translator = Translator()
        time.sleep(0.1)
        result = translator.translate(text, src=src_code, dest=target_code)
        return result.text
    except Exception as e:
        print(f"[Translator Error] {e}")
        return text

def translate_text(text: str, target_lang: str, src_lang: str = None) -> str:
    lines = text.split("\n")
    translated_lines = []
    
    for t in lines:
        translated_lines.append(_translate_chunk(t, target_lang, src_lang=src_lang))
        
    return "\n".join(translated_lines)
