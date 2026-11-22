"""Static NWScript bytecode inspection; never executes or recompiles scripts.

Instruction layout reference: niv/neverwinter.nim, nwasm.nim (NCS V1.0).
Constant arguments are only reported when locally traceable within one block;
they do not establish reachability, quest prerequisites or execution order.
"""
import collections
import json
import math
import re
import struct
from .analysis_formats import decode

OPS=('','CPDOWNSP','RSADD','CPTOPSP','CONST','ACTION','LOGAND','LOGOR','INCOR','EXCOR','BOOLAND','EQUAL','NEQUAL','GEQ','GT','LT','LEQ','SHLEFT','SHRIGHT','USHRIGHT','ADD','SUB','MUL','DIV','MOD','NEG','COMP','MOVSP','STOREIP','JMP','JSR','JZ','RETN','DESTRUCT','NOT','DECSP','INCSP','JNZ','CPDOWNBP','CPTOPBP','DECBP','INCBP','SAVEBP','RESTOREBP','STORESTATE','NOP')
CATEGORIES={
 'journal':{'AddJournalQuestEntry','RemoveJournalQuestEntry','GetJournalQuestExperience'},
 'state':{'GetLocalInt','SetLocalInt','GetLocalString','SetLocalString','DeleteLocalInt','DeleteLocalString','GetCampaignInt','SetCampaignInt','GetCampaignString','SetCampaignString'},
 'inventory':{'GetItemPossessedBy','GetItemInSlot','CreateItemOnObject','DestroyObject','ActionGiveItem','ActionTakeItem'},
 'rewards':{'GiveGoldToCreature','GiveXPToCreature','TakeGoldFromCreature'},
 'spawns':{'CreateObject','CreateTrapAtLocation','CreateTrapOnObject'},
 'travel':{'JumpToLocation','JumpToObject','ActionJumpToLocation','ActionJumpToObject','SetTransitionTarget'},
 'dialogue':{'ActionStartConversation','BeginConversation','SpeakString','SpeakOneLiner','GetPCSpeaker'},
 'scripts':{'ExecuteScript','ExecuteScriptEnhanced','DelayCommand','AssignCommand'},
 'companions':{'AddHenchman','RemoveHenchman','GetAssociate','GetMaster','SummonAssociate','GetAssociateType'},
 'external':{'GetCampaignInt','SetCampaignInt','GetCampaignString','SetCampaignString','SqlPrepareQueryCampaign','StoreCampaignObject','RetrieveCampaignObject'},
}

def prototypes(source):
    """Engine action numbers follow prototype declaration order in nwscript.nss."""
    text=decode(source);text=re.sub(r'/\*.*?\*/|//[^\n]*','',text,flags=re.S)
    matches=re.findall(r'^\s*(\w+)\s+(\w+)\s*\(([^;{}]*)\)\s*;',text,re.M)
    result={}
    for i,(ret,name,args) in enumerate(matches):
        types=[];names=[]
        for arg in args.split(','):
            m=re.match(r'\s*(\w+)\s+(\w+)',arg)
            if m:types.append(m[1]);names.append(m[2])
        result[i]={'name':name,'return':ret,'types':types,'params':names}
    if len(result)<100:raise ValueError('Engine function definitions are incomplete.')
    return result

def analyse(raw,actions=None):
    actions=actions or {};warnings=[];instructions=[];offset=13
    if len(raw)<13 or raw[:8]!=b'NCS V1.0' or raw[8]!=0x42:raise ValueError('Not a supported NCS V1.0 compiled script.')
    if struct.unpack_from('>I',raw,9)[0]!=len(raw):raise ValueError('Compiled script size does not match its header.')
    while offset<len(raw):
        if len(instructions)>=250000:warnings.append('Instruction budget reached; remaining bytecode was not decoded.');break
        start=offset
        try:
            if offset+2>len(raw):raise ValueError('Truncated opcode')
            op,aux=raw[offset:offset+2];offset+=2
            if not 1<=op<len(OPS) or op==0x1c:raise ValueError('Unsupported opcode '+hex(op))
            size=0;operand=None
            if op==4:
                if aux in (3,4,6,0x12):size=4
                elif aux in (5,0x17):
                    if offset+2>len(raw):raise ValueError('Truncated string length')
                    size=2+struct.unpack_from('>H',raw,offset)[0]
                else:raise ValueError('Unsupported constant type '+hex(aux))
            elif op in (1,3,0x26,0x27,0x21):size=6
            elif op in (0x1b,0x1d,0x1e,0x1f,0x25,0x23,0x24,0x28,0x29):size=4
            elif op==5:size=3
            elif op==0x2c:size=8
            elif op in (0xb,0xc) and aux==0x24:size=2
            if offset+size>len(raw):raise ValueError('Truncated operand')
            data=raw[offset:offset+size];offset+=size
            if op==4:
                operand=decode(data[2:]) if aux in (5,0x17) else struct.unpack('>f' if aux==4 else '>i' if aux==3 else '>I',data)[0]
                if isinstance(operand,float) and not math.isfinite(operand):operand=str(operand)
            elif op==5:operand=list(struct.unpack('>HB',data))
            elif op in (1,3,0x26,0x27):operand=list(struct.unpack('>iH',data))
            elif op==0x21:operand=list(struct.unpack('>HHH',data))
            elif op==0x2c:operand=list(struct.unpack('>II',data))
            elif size==4:operand=struct.unpack('>i',data)[0]
            elif size==2:operand=struct.unpack('>H',data)[0]
            row={'offset':start,'op':OPS[op],'aux':aux,'operand':operand,'end':offset}
            if op in (0x1d,0x1e,0x1f,0x25):row['target']=start+operand
            instructions.append(row)
        except (ValueError,struct.error) as exc:
            warnings.append('Stopped at 0x%08X: %s. Later instructions were not analysed.'%(start,exc));break
    offsets={r['offset'] for r in instructions};targets={r['target'] for r in instructions if 'target' in r}
    for target in sorted(targets-offsets):warnings.append('Branch target 0x%08X is not a decoded instruction.'%target)
    calls=[];stack=[];strings=[];branches=[];listing=[];counts=collections.Counter()
    # A fresh abstract stack at each branch/join prevents cross-branch guesses.
    for r in instructions:
        op=r['op'];arg=r['operand'];at=r['offset']
        if at in targets:stack=[]
        display=json.dumps(arg,ensure_ascii=False) if arg is not None else ''
        if op=='CONST':
            stack.append({'literal':arg})
            if r['aux'] in (5,0x17):strings.append({'offset':at,'value':arg})
        elif op=='RSADD':stack.extend([None]*(3 if r['aux']==0x3a else 1))
        elif op=='CPTOPSP':
            delta,size=arg;n=size//4;start=len(stack)+delta//4
            stack.extend(stack[start:start+n] if size%4==0 and delta%4==0 and 0<=start and start+n<=len(stack) else [None]*min(n,4096))
        elif op=='CPDOWNSP':
            delta,size=arg;n=size//4;start=len(stack)+delta//4
            if n and size%4==0 and delta%4==0 and 0<=start and start+n<=len(stack) and n<=len(stack):stack[start:start+n]=stack[-n:]
            else:stack=[]
        elif op=='MOVSP':
            if arg<=0 and arg%4==0 and -arg//4<=len(stack):
                if arg:del stack[len(stack)+arg//4:]
            else:stack=[]
        elif op=='ACTION':
            ident,argc=arg;definition=actions.get(ident);name=definition['name'] if definition else 'ACTION_'+str(ident)
            values=[]
            for i in range(argc):
                typ=definition['types'][i] if definition and i<len(definition['types']) else '?'
                slots=3 if typ=='vector' else 0 if typ=='action' else 1
                value=stack[-1] if definition and slots==1 and stack else None
                values.append(value.get('literal') if isinstance(value,dict) else None)
                if slots:
                    if len(stack)>=slots:del stack[-slots:]
                    else:stack=[]
            categories=[key for key,names in CATEGORIES.items() if name in names]
            calls.append({'offset':at,'name':name,'arguments':values,'parameters':definition['params'][:argc] if definition else [],'categories':categories})
            counts[name]+=1;display=name+' '+json.dumps(values,ensure_ascii=False)
            if not definition:stack=[]
            elif definition['return']!='void':stack.extend([None]*(3 if definition['return']=='vector' else 1))
        elif op=='ADD' and r['aux'] in (0x20,0x23):
            b=stack.pop() if stack else None;a=stack.pop() if stack else None
            if isinstance(a,dict) and isinstance(b,dict) and type(a['literal']) is type(b['literal']) and isinstance(a['literal'],(str,int)):
                v=a['literal']+b['literal'];stack.append({'literal':v} if not isinstance(v,str) or len(v)<100000 else None)
            else:stack.append(None)
        elif op in ('JMP','JSR','JZ','JNZ','RETN','STORESTATE','SAVEBP','RESTOREBP'):
            if 'target' in r:branches.append({'offset':at,'kind':op,'target':r['target']});display='0x%08X'%r['target']
            stack=[]
        else:stack=[]
        if len(stack)>4096:stack=[]
        listing.append('%08X  %-12s %02X  %s'%(at,op,r['aux'],display))
    categories={key:sum(c['name'] in names for c in calls) for key,names in CATEGORIES.items()}
    return {'status':'partial' if warnings else 'decoded','bytes':len(raw),'instructions':len(instructions),'decoded_bytes':offset,'warnings':warnings[:80],
            'functions':dict(counts),'categories':{k:v for k,v in categories.items() if v},'calls':calls,'strings':strings,'branches':branches,'disassembly':'\n'.join(listing),
            'interpretation':'Static call sites and locally traceable constants. Calls may be conditional or unreachable; null arguments are unresolved. No execution or complete source recovery.'}
