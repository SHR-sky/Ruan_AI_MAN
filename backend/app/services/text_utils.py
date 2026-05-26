import re


_NUMBER_MAP = {
    "0": "零", "1": "一", "2": "二", "3": "三", "4": "四",
    "5": "五", "6": "六", "7": "七", "8": "八", "9": "九",
}
_UNIT_MAP = ["", "十", "百", "千"]
_BIG_UNIT_MAP = ["", "万", "亿", "万亿"]


def _small_number_to_cn(num_str: str) -> str:
    if num_str == "0":
        return "零"
    if len(num_str) > len(_UNIT_MAP):
        return "".join(_NUMBER_MAP.get(d, d) for d in num_str)
    digits = list(num_str)
    length = len(digits)
    result = ""
    for i, d in enumerate(digits):
        if d != "0":
            result += _NUMBER_MAP[d] + _UNIT_MAP[length - 1 - i]
        else:
            if i < length - 1 and result and not result.endswith("零"):
                result += "零"
    return result


def number_to_chinese(text: str) -> str:
    """将文本中的阿拉伯数字转为中文读法"""
    def _replace_num(match):
        num_str = match.group(0)
        if "." in num_str:
            parts = num_str.split(".")
            int_part = parts[0]
            dec_part = parts[1]
            int_cn = _small_number_to_cn(int_part) if int_part != "0" else "零"
            dec_cn = "点" + "".join(_NUMBER_MAP.get(c, c) for c in dec_part)
            return int_cn + dec_cn
        return _small_number_to_cn(num_str)

    return re.sub(r"\d+(\.\d+)?", _replace_num, text)


def preprocess_text(text: str) -> str:
    """TTS 文本预处理"""
    text = number_to_chinese(text)
    text = text.replace("%", "百分之")
    text = text.replace("℃", "度")
    text = text.replace("km", "公里")
    text = text.replace("m", "米")
    text = text.replace("cm", "厘米")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_into_sentences(text: str) -> list:
    """按标点分割句子（用于流式合成）"""
    parts = re.split(r"([。！？，\n])", text)
    sentences = []
    buffer = ""
    for part in parts:
        buffer += part
        if part in ("。", "！", "？", "\n"):
            if buffer.strip():
                sentences.append(buffer.strip())
            buffer = ""
        elif part == "，":
            if buffer.strip():
                sentences.append(buffer.strip())
            buffer = ""
    if buffer.strip():
        sentences.append(buffer.strip())
    return sentences


def estimate_duration(text: str, speed: float = 1.0) -> float:
    """估算TTS合成时长（秒），用于流式调度"""
    char_count = len(text)
    base_duration = char_count * 0.12
    return base_duration / speed
