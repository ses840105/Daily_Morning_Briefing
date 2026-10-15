from deep_translator import MyMemoryTranslator
from concurrent.futures import ThreadPoolExecutor

def _translate_chunk(text: str, target_lang: str) -> str:
    if not text.strip(): return text
    # Map target language to MyMemory code
    target_code = "en-US" if target_lang == "en" else "zh-CN"
    try:
        return MyMemoryTranslator(source='ko-KR', target=target_code).translate(text)
    except Exception as e:
        print(f"[Translator Error] {e}")
        return text

def translate_text(text: str, target_lang: str) -> str:
    # Split text into sentences or paragraphs to avoid 500-char limit of MyMemory
    lines = text.split("\n")
    translated_lines = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        translated_lines = list(executor.map(lambda t: _translate_chunk(t, target_lang), lines))
        
    return "\n".join(translated_lines)
