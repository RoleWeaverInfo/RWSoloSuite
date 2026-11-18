"""Gameplay-only local dialogue guards adapted from the Role Weaver Server Addon."""
import copy
import json
import re
import threading
import unicodedata
from .storage import write_json

FALLBACK='Let us keep to matters of this world. What do you need?'
NONVERBAL='Pauses, then offers an attentive, wordless acknowledgment.'
DEFAULTS=dict(sdk_enabled=True,block_overrides=True,keep_in_character=True,redact_private=True,
    blocked_terms='',input_char_limit=60000,output_char_limit=1200,max_output_tokens=1400,
    requests_per_minute=12,requests_per_hour=60,daily_token_limit=0,ambient_enabled=True)
INPUT_PATTERNS=[
    r'\b(?:ignore|discard|abandon|forget)\b.{0,30}\b(?:your|the)\s+(?:persona|character|roleplay|role-playing)\b',
    r'\b(?:ignore|disregard|override|forget)\b.{0,60}\b(?:system|developer|previous|prior|above|all)\b.{0,35}\b(?:instructions?|prompts?|rules)\b',
    r'\b(?:reveal|print|repeat|show|quote|output)\b.{0,65}\b(?:system|developer|hidden|internal)\s+(?:prompt|instructions?)\b',
    r'\b(?:reveal|print|show|output)\b.{0,50}\b(?:api[ _-]?keys?|environment variables|provider\.env)\b',
    r'\b(?:you are now|act as|answer as|become)\s+(?:chatgpt|an? ai|an? language model|an? assistant|dan)\b',
    r'\b(?:i am|i.m)\s+(?:the\s+)?(?:dm|developer|administrator)\b.{0,80}\b(?:override|instructions?|prompt|ignore|reveal)\b',
    r'(?:<\|(?:im_start|system|developer)\|>|\[/?inst\]|</?(?:system|developer)>)',
    r'\b(?:decode|decrypt)\b.{0,60}\b(?:base64|rot13)\b.{0,60}\b(?:follow|obey|execute)\b']
OUTPUT_PATTERNS=[
    r'\b(?:video game|game engine|native receipt|game-confirmed receipt)\b',
    r'\b(?:the game|game scripts?)\b.{0,45}\b(?:confirm|verify|validate|transfer|receipt|failed|open)\w*\b',
    r'\b(?:as (?:an? )?(?:ai|language model|chatgpt)|i am an? (?:ai|language model))\b',
    r'\b(?:my|the|your)\s+(?:system|developer)\s+(?:prompt|instructions?)\b',
    r'```(?:python|javascript|bash|powershell|json)\b',
    r'(?:<\|im_start\|>|</?(?:system|developer)>|\[/?inst\])']
SECRET=re.compile(r'\b(?:sk-(?:proj-)?[a-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{30,})\b',re.I)
EMAIL=re.compile(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b',re.I)
PHONE=re.compile(r'(?<!\d)(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3}[-. ])[-.\s]?\d{3}[-. ]\d{4}(?!\d)')


def normalized(text):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKC',text) if unicodedata.category(c)!='Cf').lower().split())


def text_content(value):
    if isinstance(value,str):return value
    if isinstance(value,dict):return '\n'.join(text_content(v) for v in value.values())
    if isinstance(value,list):return '\n'.join(text_content(v) for v in value)
    return ''


def validate_settings(value):
    if not isinstance(value,dict) or set(value)!=set(DEFAULTS):raise ValueError('Invalid gameplay guardrail settings')
    value=copy.deepcopy(value)
    for key in ('sdk_enabled','block_overrides','keep_in_character','redact_private','ambient_enabled'):
        if type(value[key]) is not bool:raise ValueError('Invalid guardrail switch: '+key)
    for key,low,high in (('input_char_limit',2000,200000),('output_char_limit',100,2000),('max_output_tokens',256,4000),('requests_per_minute',1,120),('requests_per_hour',1,2000),('daily_token_limit',0,100000000)):
        if type(value[key]) is not int or not low<=value[key]<=high:raise ValueError(f'{key} must be an integer from {low} to {high}')
    if not isinstance(value['blocked_terms'],str) or len(value['blocked_terms'])>5000:raise ValueError('Blocked terms must be at most 5,000 characters')
    terms=[t.strip() for t in value['blocked_terms'].splitlines() if t.strip()]
    if len(terms)>50 or any(len(t)>100 for t in terms):raise ValueError('Use up to 50 blocked terms, at most 100 characters each')
    value['blocked_terms']='\n'.join(terms);return value


def reason(text,direction,settings,instructions=''):
    limit=settings['input_char_limit'] if direction=='input' else settings['output_char_limit']
    if not text.strip() or len(text)>limit:return 'text_size'
    if re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]',text):return 'text_format'
    value=normalized(text)
    if SECRET.search(value):return 'credential_text'
    if direction=='output' and settings['redact_private'] and (EMAIL.search(text) or PHONE.search(text)):return 'private_information'
    if direction=='input' and settings['block_overrides'] and any(re.search(p,value) for p in INPUT_PATTERNS):return 'instruction_override'
    if direction=='output' and settings['keep_in_character']:
        if any(re.search(p,value) for p in OUTPUT_PATTERNS):return 'out_of_character'
        protected=normalized(instructions)
        if len(protected)>=60 and protected[:60] in value:return 'instruction_leak'
    if any(normalized(term) in value for term in settings['blocked_terms'].splitlines() if term.strip()):return 'blocked_term'
    return ''


def safe_result(schema,context):
    """Replace the entire response, including all proposed actions."""
    def blank(spec):
        choices=spec.get('enum')
        if choices:return 'none' if 'none' in choices else '' if '' in choices else choices[0]
        kind=spec.get('type')
        if kind=='object':return {k:blank(v) for k,v in spec['properties'].items()}
        if kind=='array':return []
        if kind=='boolean':return False
        if kind in ('integer','number'):return spec.get('minimum',0)
        return ''
    result=blank(schema)
    nonverbal=context.get('communication')=='nonverbal' or (context.get('companion') or {}).get('communication')=='nonverbal'
    for key in ('reply','line','line_a','line_b'):
        if key in result:result[key]=NONVERBAL if nonverbal else FALLBACK
    return result


class GameplayGuardrails:
    def __init__(self,path):
        self.path=path;self.lock=threading.RLock();self.backend=None;self.error='';self.version=''
        self.settings=validate_settings(json.loads(path.read_text(encoding='utf-8'))) if path.is_file() else copy.deepcopy(DEFAULTS)
        self._initialize()

    def _initialize(self):
        if not self.settings['sdk_enabled']:return
        try:
            from .guardrails_sdk import LocalValidation
            self.backend=LocalValidation()
            # Installation health must not depend on the owner's blocked terms.
            if self.backend.validate('Greetings, traveler.','output',DEFAULTS,''):raise ValueError('Validator self-check failed')
            self.version=self.backend.version;self.error=''
        except Exception:
            self.backend=None;self.error='Guardrails AI is unavailable. Gameplay AI is blocked while its SDK checks are enabled. Install the bundled dependencies or use built-in checks in Guardrails settings.'

    def configure(self,value):
        value=validate_settings(value)
        with self.lock:
            write_json(self.path,value);self.settings=value
            if value['sdk_enabled'] and self.backend is None:self._initialize()
        return self.status()

    def snapshot(self):
        with self.lock:return copy.deepcopy(self.settings)

    def status(self):
        with self.lock:return dict(settings=copy.deepcopy(self.settings),active=bool(self.settings['sdk_enabled'] and self.backend and not self.error),
            backend='Guardrails AI' if self.settings['sdk_enabled'] else 'Built-in checks',version=self.version,
            error=self.error if self.settings['sdk_enabled'] else '',local_only=True)

    def check(self,text,direction,settings,instructions=''):
        if settings['sdk_enabled']:
            if self.backend is None:raise ValueError('Guardrails AI is unavailable; gameplay AI is paused. See Guardrails settings.')
            try:
                found=self.backend.validate(text,direction,settings,instructions)
                with self.lock:self.error=''
                return found
            except Exception:
                with self.lock:self.error='Guardrails AI validation failed. Gameplay AI is paused; check the local installation.'
                raise ValueError(self.error) from None
        return reason(text,direction,settings,instructions)

    def prepare(self,context,settings):
        def clean(value,key=''):
            if isinstance(value,dict):return {k:clean(v,k) for k,v in value.items()}
            if isinstance(value,list):return [clean(v,key) for v in value]
            if not isinstance(value,str):return value
            if key in ('history','conversation'):
                value='\n'.join(line for line in value.splitlines() if not reason(line,'input',settings) and not reason(line,'output',settings))
            if settings['redact_private']:value=PHONE.sub('[private phone]',EMAIL.sub('[private email]',value))
            return value
        return clean(context)
