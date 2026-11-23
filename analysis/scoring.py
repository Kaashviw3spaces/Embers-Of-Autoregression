"""Explicit scoring rules. Extraction never receives or searches for an answer key."""
import re

SCORING_VERSION = "completed-stored-exact-v1"


def final_text(content):
    text = content or ""
    if "</think>" in text:
        text = text.rsplit("</think>", 1)[1]
    elif "<think>" in text:
        return ""
    return text.strip()


def normalized_answer(content, task):
    """A conservative secondary rule, not a search through reasoning."""
    text = final_text(content)
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1]).strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        text = text[1:-1].strip()
    if "acronym" in task and re.fullmatch(r"[A-Za-z\s-]+", text):
        text = re.sub(r"[\s-]", "", text).upper()
    return text


def evaluate(content, expected, finish_reason, task, api_error=False, quality="usable"):
    text = final_text(content)
    if api_error:
        return {"strict_correct": None, "normalized_correct": None, "status": "api_error", "category": "Request error", "final_text": text}
    if quality == "quarantined_excerpt":
        return {"strict_correct": None, "normalized_correct": None, "status": "quarantined", "category": "Insufficient source output", "final_text": text}
    expected = expected.strip()
    strict = finish_reason == "stop" and bool(text) and text == expected
    normal = finish_reason == "stop" and bool(text) and normalized_answer(content, task) == expected
    if finish_reason == "length":
        status, category = "truncated", "Output-token limit reached"
    elif finish_reason != "stop":
        status, category = "incomplete", "Completion state missing or incomplete"
    elif not text:
        status, category = "empty", "No final answer"
    elif strict:
        status, category = "correct", "Correct"
    elif normal:
        status, category = "formatting", "Formatting differs under strict scoring"
    elif "acronym" in task and len(text) == len(expected) and sorted(text) == sorted(expected):
        status, category = "incorrect", "Letter-order error"
    elif "acronym" in task and len(text) < len(expected) and expected.startswith(text):
        status, category = "incorrect", "Incomplete letter sequence"
    elif expected in text:
        # Classification only: never use a substring to manufacture a prediction
        # or award success. It may be quoted, contradicted, or wrapped in prose.
        status, category = "formatting", "Extra text; target present (verify final choice)"
    else:
        status, category = "incorrect", "Incorrect answer or extra explanation"
    return {"strict_correct": strict, "normalized_correct": normal, "status": status, "category": category, "final_text": text}


def transform_cipher(text, shift):
    result = []
    for char in text:
        base = ord("a") if "a" <= char <= "z" else ord("A") if "A" <= char <= "Z" else None
        result.append(chr((ord(char) - base + shift) % 26 + base) if base is not None else char)
    return "".join(result)


def oracle_answer(task, text):
    if task.startswith("acronym1"):
        return "".join(word[0] for word in text.split()).upper()
    match = re.match(r"rot(\d+)(dec|enc)", task)
    if match:
        shift = int(match[1]) * (-1 if match[2] == "dec" else 1)
        return transform_cipher(text, shift)
    if task=='word_reverse':
        return ' '.join(reversed(text.split()))
    if task=='count_words':
        return str(len(text.split()))
    if task=='word_multiply':
        parts=text.split(' times ')
        if len(parts)!=2:raise ValueError('Expected two written numbers separated by times')
        return str(english_integer(parts[0])*english_integer(parts[1]))
    if task in {'sort_alphabetical','sort_reversealphabetical'}:
        return ', '.join(sorted((word.strip() for word in text.split(',')),reverse=task=='sort_reversealphabetical'))
    if task in {'sort_ascending','sort_descending'}:
        return ', '.join(str(n) for n in sorted((int(word.strip()) for word in text.split(',')),reverse=task=='sort_descending'))
    if task in {'conversion_actual','conversion_fake'}:
        from decimal import Decimal
        slope,offset=(Decimal(9)/5,32) if task=='conversion_actual' else (Decimal(7)/5,31)
        return str(Decimal(text)*slope+offset)
    if task=='article_swap_prev':
        pieces=re.split(r"([A-Za-z]+(?:['’][A-Za-z]+)*)",text)
        word_positions=[i for i in range(1,len(pieces),2)]
        # Move words; punctuation stays in its original textual position.
        for j in range(len(word_positions)):
            i=word_positions[j]
            if j and pieces[i].lower() in {'a','an','the'}:
                previous=word_positions[j-1]
                pieces[previous],pieces[i]=pieces[i],pieces[previous]
        return ''.join(pieces)
    raise ValueError(f"Unsupported oracle task: {task}")


def english_integer(text):
    small=dict(zip('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split(),range(20)))
    small.update(dict(zip('twenty thirty forty fifty sixty seventy eighty ninety'.split(),range(20,100,10))))
    total,current=0,0
    for word in text.lower().replace('-',' ').split():
        if word=='and':continue
        if word in small:current+=small[word]
        elif word=='hundred':current*=100
        elif word=='thousand':total+=current*1000;current=0
        else:raise ValueError('Unknown written-number word')
    return total+current


def pig_latin_encode(text,vowel_suffix):
    def convert(match):
        word=match.group()
        prefix=re.match(r'[^aeiouAEIOU]+',word)
        if prefix:
            n=len(prefix.group());return word[n:]+word[:n]+'ay'
        return word+vowel_suffix
    return re.sub(r"[A-Za-z]+(?:['’][A-Za-z]+)*",convert,text)
