"""Creator-owned stock definitions and game-observed merchant context."""
import re
from .content import _obj,array,enum,I,B

CATALOG={
 'dagger':dict(name='Dagger',resref='nw_wswdg001',price=2),
 'shortsword':dict(name='Short sword',resref='nw_wswss001',price=10),
 'longsword':dict(name='Longsword',resref='nw_wswls001',price=15),
 'quarterstaff':dict(name='Quarterstaff',resref='nw_wdbqs001',price=1),
 'shortbow':dict(name='Shortbow',resref='nw_wbwsh001',price=30),
 'leather_armor':dict(name='Leather armour',resref='nw_aarcl001',price=10),
 'small_shield':dict(name='Small shield',resref='nw_ashsw001',price=3),
 'healing_potion':dict(name='Potion of Cure Light Wounds',resref='nw_it_mpotion001',price=50),
}
SCHEMA=_obj({'interface':enum('native','list'),'enabled':B,'haggle_enabled':B,'haggle_chance':dict(I,minimum=0,maximum=100),'discount_percent':dict(I,minimum=0,maximum=10),'offer_seconds':dict(I,minimum=60,maximum=3600),
             'stock':dict(array(_obj({'item':enum(*CATALOG),'quantity':dict(I,minimum=1,maximum=20),'price':dict(I,minimum=1,maximum=100000)})),maxItems=8)})

def defaults():
    return dict(interface='native',enabled=False,haggle_enabled=True,haggle_chance=50,discount_percent=5,offer_seconds=600,stock=[])

def validate(npc):
    m=npc['merchant'];seen=set()
    if not 0<=m['haggle_chance']<=100 or not 0<=m['discount_percent']<=10:raise ValueError(npc['name']+': use haggle chance 0–100% and discount 0–10%')
    if not 60<=m['offer_seconds']<=3600:raise ValueError('Merchant offers must last 60–3600 active game seconds')
    if len(m['stock'])>8 or sum(s['quantity'] for s in m['stock'])>80:raise ValueError('Use at most 8 merchant stock lines and 80 individual goods')
    for s in m['stock']:
        if s['item'] in seen:raise ValueError('A merchant stock item may appear only once')
        seen.add(s['item'])
        if not 1<=s['quantity']<=20 or not 1<=s['price']<=100000:raise ValueError('Merchant quantities must be 1–20 and prices 1–100000 gold')

def context(npc,snapshot):
    """Never substitute creator stock for missing live inventory observations."""
    observed=snapshot.get('merchant',{})
    if not isinstance(observed,dict) or observed.get('npc')!=npc['id'] or observed.get('available')!=1:
        return dict(available=False,items=[])
    if observed.get('price_mode')=='native':
        if npc['merchant'].get('interface')!='native':return dict(available=False,items=[])
        grouped={}
        for item in observed.get('items',[])[:32]:
            if not isinstance(item,dict):continue
            name=item.get('name');qty=item.get('quantity')
            if not isinstance(name,str) or not 1<=len(name)<=100 or type(qty) is not int or not 0<qty<=1000000:continue
            grouped[name]=grouped.get(name,0)+qty
        return dict(available=True,price_mode='native',items=[dict(name=n,quantity=q) for n,q in grouped.items()],more_items=observed.get('more_items')==1,haggle_available=observed.get('haggle_available')==1)
    items=[]
    for item in observed.get('items',[])[:8]:
        if not isinstance(item,dict) or item.get('item') not in CATALOG:continue
        qty=item.get('quantity');price=item.get('price')
        if type(qty) is not int or type(price) is not int or not 0<=qty<=80 or not 1<=price<=100000:continue
        items.append(dict(item=item['item'],name=CATALOG[item['item']]['name'],quantity=qty,price=price))
    return dict(available=True,items=items,haggle_available=observed.get('haggle_available')==1)

PRICE_QUESTION=re.compile(r'\b(how much|prices?|costs?|wares|stock|sell|selling|available)\b',re.I)

def ground_quote(reply,message,shop):
    if not PRICE_QUESTION.search(message) and not (shop.get('price_mode')=='native' and re.search(r'\d+\s*(gold|gp|coins?)',reply,re.I)):return reply
    if not shop['available']:return 'Please open my goods panel so we can check my current stock and prices.'
    items=[i for i in shop['items'] if i['quantity']>0]
    if not items:return 'My stock is sold out for now.'
    if shop.get('price_mode')=='native':
        goods='; '.join(f'{i["name"]} ({i["quantity"]} available)' for i in items[:8])
        more=' There are more goods to browse.' if shop.get('more_items') or len(items)>8 else ''
        return 'On my shelves: '+goods+'.'+more+' Browse my goods for your exact buying and selling prices before confirming a trade.'
    return 'My current stock: '+ '; '.join(f'{i["name"]}: {i["price"]} gold each ({i["quantity"]} available)' for i in items)+'. Confirm any purchase in the goods panel.'

def example():
    from .authoring import seed,npc,validate as validate_project
    p=seed();p.update(id='ai_market',module_name='rw_ai_market',title='The Silent Bell — AI & Merchant Trial',ai_conversations=True)
    bram=npc('bram','Bram Ironstock','guest_hall')
    bram.update(appearance='innkeeper',role='Travelling equipment merchant',personality='Dry wit, honest prices, and a soft spot for nervous adventurers.',knowledge='The abbey elder needs help. Rowan scouts the old road. My goods panel shows my real current stock and prices.',motivation='Earn a fair living and help travelers survive.',greeting='Welcome. Ask about my goods or browse them from this menu. A fair offer costs nothing to ask for.')
    bram['merchant']=defaults();bram['merchant'].update(interface='list',enabled=True,stock=[dict(item=k,quantity=q,price=CATALOG[k]['price']) for k,q in [('dagger',2),('shortsword',2),('shortbow',1),('small_shield',2),('healing_potion',4)]])
    p['npcs'].append(bram)
    return validate_project(p,True)
