"""Conservative additional query view; never a filter or a replacement query."""

import re


def focus_query(query):
    """Remove retrieval framing, preserving topic/action and uncertain wording.

    The original query remains the scope authority and a semantic search view.
    Quotation and negation are kept untouched rather than risk shifting their
    scope. Rules describe request syntax, never a user's topics or synonyms.
    """
    text = query.strip()
    if re.search(r'["\'“”「」]|말고|아니|제외|빼고|않|없는|없이|못|\b(?:not|without|except|excluding)\b', text, re.I):
        return text
    value = re.sub(
        r'^(?:(?:내가|제가|우리가|저희가)\s+)?'
        r'(?:(?:최근에|예전에|이전에|전에)\s+)?'
        r'(?:(?:작업하던|진행하던|검토하던)\s+)?', '', text)
    value = re.sub(
        r'\s*(?:찾아(?:줘|주세요|줄래요?|봐)|보여(?:줘|주세요|줄래요?)|'
        r'검색해(?:줘|주세요)|알려(?:줘|주세요))[.!?~\s]*$', '', value)
    value = re.sub(r'\s+(?:세션|문서|자료|기록|내용)(?:들)?(?:만|을|를)?$', '', value)
    value = re.sub(r'\s*(?:(?:과|와|에)\s+)?(?:관련(?:된|한)?|관한)$', '', value)
    value = re.sub(
        r'^(?:find|show|search for)\s+(?:(?:me|my)\s+)?'
        r'(?:(?:work|sessions?|documents?|records?)\s+(?:about|on|related to)\s+)?',
        '', value, flags=re.I)
    value = value.strip()
    # A single Hangul syllable (for example 앱) can be the complete topic.
    return value if value else text
