"""Resolve representative item-class icons from installed resources, without guessed paths."""
import shlex


def icon_catalog(game):
    lines=game.get('baseitems',2017).decode('latin1').splitlines()
    header=shlex.split(lines[2]);column=header.index('DefaultIcon')
    images={name for name,kind in game.index if kind in (3,2033)}
    result={}
    for line in lines[3:]:
        parts=shlex.split(line)
        if not parts or not parts[0].isdigit() or len(parts)<=column+1:continue
        prefix=parts[column+1].lower()
        if prefix=='****':continue
        matches=sorted(n for n in images if n==prefix or n.startswith(prefix+'_'))
        if matches:result[int(parts[0])]=prefix if prefix in images else matches[0]
    return result


def native_icons(game,literal):
    icons=icon_catalog(game)
    fallback=''  # Unknown custom types keep their name; never pretend to be a potion.
    return 'string AWGIcon(int base){'+''.join(f'if(base=={base})return {literal(icon)};' for base,icon in icons.items())+'return '+literal(fallback)+';}'
