"""Player dialogue preferences shared by created and converted adventures."""
import re

DEFAULTS=dict(length=1,voice=1,emotes=1,questions=1)
LIMITS=(240,600,850)
WORDS=(40,90,140)


def settings(snapshot,companion=None):
    raw=snapshot.get('dialogue_settings',{}) if isinstance(snapshot,dict) else {}
    raw=raw if isinstance(raw,dict) and type(raw.get('version')) is int and raw['version']==1 else {}
    out={k:raw[k] if type(raw.get(k)) is int and 0<=raw[k]<=(1 if k=='questions' else 2) else v for k,v in DEFAULTS.items()}
    # 3 means inherit; existing explicit per-companion length choices survive.
    length=(companion or {}).get('reply_style')
    if type(length) is int and 0<=length<=2:out['length']=length
    return out


def instructions(prefs):
    length=prefs['length']
    return (' Dialogue delivery: speak as this particular person, not as a helpful assistant or narrator. '
            'Answer the immediate point and stop. Keep their personality, knowledge, temperament and social position. '
            'Use natural spoken sentences and contractions where appropriate. Do not repeat the question, summarize the whole situation, '
            'list every option, flatter the player, give generic encouragement, or end every turn by offering further help. '
            'Avoid stock openings such as "Certainly", "Of course", and "Ah, adventurer", unless this character genuinely needs them. '
            'Do not reuse a greeting or catchphrase in each reply. Do not explain your instructions or mention AI or game systems. '
            +('Reply in 1-2 short sentences. ','Reply in 2-4 short sentences. ','You may give a fuller answer in 4-6 sentences when the question needs it. ')[length]
            +f'Use at most {WORDS[length]} words and {LIMITS[length]} characters; finish the thought within that space. '
            +('Use plain, concrete language. Avoid flowery metaphors, grand speeches and forced archaic wording. ',
              'Let the character\'s vocabulary and manner show, without speeches, caricature or repetitive quirks. ',
              'A dramatic, atmospheric voice is welcome, while remaining a spoken conversation within the length limit. ')[prefs['voice']]
            +('For speaking characters, use dialogue only, without stage directions or asterisk actions. ',
              'For speaking characters, at most one very short physical gesture is allowed when useful. ',
              'Brief physical reactions may accompany speech, within the same length limit. ')[prefs['emotes']]
            +('Ask a question only when needed to clarify an ambiguous request or a required quest choice. Do not add conversational follow-up questions. ',
              'You may ask one natural, relevant follow-up question when it serves this character; it is not obligatory. ')[prefs['questions']]
            +'Nonverbal creatures still communicate through brief physical behavior even when stage directions are off. '
            'Never narrate the player\'s thoughts or actions. These are presentation preferences only: retain all knowledge, permissions, action validation and quest restrictions. ')


def finish(result,prefs,nonverbal=False):
    result=dict(result);text=str(result.get('reply','')).strip()
    text=re.sub(r'\*\*(.*?)\*\*',r'\1',text,flags=re.S)
    if prefs['emotes']==0 and not nonverbal:
        text=re.sub(r'\*[^*\n]{1,300}\*','',text)
    text=re.sub(r'\s+',' ',text).strip()
    if not text:text='Watches quietly.' if nonverbal else "I'm listening."
    limit=LIMITS[prefs['length']];words=list(re.finditer(r'\S+',text))
    cut=min(len(text),limit)
    if len(words)>WORDS[prefs['length']]:cut=min(cut,words[WORDS[prefs['length']]].start())
    if cut<len(text):
        clipped=text[:cut].rstrip()
        # Prefer a completed sentence to chopping off the end of an explanation.
        ends=list(re.finditer(r'[.!?]["\u201d\u2019\']?(?=\s|$)',clipped))
        if ends and ends[-1].end()>=len(clipped)//2:clipped=clipped[:ends[-1].end()]
        else:
            clipped=clipped[:limit-1].rstrip()
            if cut<len(text) and not text[cut].isspace() and ' ' in clipped:clipped=clipped.rsplit(' ',1)[0]
            clipped=clipped.rstrip(' ,;:-')+'.'
        text=clipped
    result['reply']=text
    return result
