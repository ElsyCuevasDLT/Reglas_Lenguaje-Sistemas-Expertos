import re
from dataclasses import dataclass
@dataclass(frozen=True)
class N:
    op:str
    hijos:tuple=()
def fmt(n):
    if not n.hijos:return n.op
    if n.op=='¬':return '¬'+fmt(n.hijos[0]) if not n.hijos[0].hijos else '¬('+fmt(n.hijos[0])+')'
    return '('+fmt(n.hijos[0])+' '+n.op+' '+fmt(n.hijos[1])+')'
def neg(n):return N('¬',(n,))
def parse(text, atomos, transformar=None):
    """Analiza varios conectores y convierte las proposiciones a letras.
    Preserva la estructura original de motor/tableau de Elsy.
    """
    from lenguaje_espanol import AnalizadorRecursivo
    analizador=AnalizadorRecursivo(text)
    arbol=analizador.analizar()
    # Se asignan letras según primera aparición en el TEXTO, no según el
    # orden interno del árbol (que se invierte en «A si B»).
    tks=analizador.tokens
    i=0
    while i<len(tks):
        if tks[i][0]=='ATOMO':
            frase=tks[i][1]
            if i+2<len(tks) and tks[i+1][0]=='¬' and tks[i+2][0]=='ATOMO':
                frase+=' '+tks[i+2][1]
                i+=2
            frase=transformar(frase) if transformar else frase
            clave=' '.join(frase.casefold().split())
            if clave not in atomos:atomos[clave]=(letra(len(atomos)),frase)
        i+=1
    def convertir(n):
        if n.hijos:return N(n.op,tuple(convertir(h) for h in n.hijos))
        t=transformar(n.op) if transformar else n.op
        key=' '.join(t.casefold().split())
        if key not in atomos:atomos[key]=(letra(len(atomos)),t)
        return N(atomos[key][0])
    return convertir(arbol)

def letra(i):
    abc='pqrstuvwxyzabcdefghijklmno';return abc[i%26]+(str(i//26+1) if i>=26 else '')
def expand(n):
    op=n.op;h=n.hijos
    if op=='¬':
        a=h[0]
        if not a.hijos:return None
        if a.op=='¬':return [[a.hijos[0]]]
        x,y=a.hijos
        return {'∧':[[neg(x)],[neg(y)]],'∨':[[neg(x),neg(y)]],'→':[[x,neg(y)]],'↔':[[x,neg(y)],[neg(x),y]]}[a.op]
    if not h:return None
    x,y=h
    return {'∧':[[x,y]],'∨':[[x],[y]],'→':[[neg(x)],[y]],'↔':[[x,y],[neg(x),neg(y)]]}[op]
class LimiteAnalisis(Exception):
    pass

def tableau(formulas, max_nodos=6000, segundos=8, cancelar=None):
    """Expande primero reglas sin bifurcación y cierra contradicciones pronto.
    Límites explícitos: un análisis incompleto nunca se presenta como insatisfacible.
    """
    import time
    inicio=time.monotonic(); contador=0
    def rama(fs,aplicadas,agregadas):
        nonlocal contador
        contador+=1
        if contador>max_nodos or time.monotonic()-inicio>segundos:
            raise LimiteAnalisis('Se alcanzó el límite de tiempo o nodos. No hay una conclusión completa. Reduce el lote o separa la base.')
        if cancelar is not None and cancelar.is_set():
            raise LimiteAnalisis('Análisis cancelado. No se emitió una conclusión.')
        conjunto=set(fs);lits={}
        closed=any(neg(f) in conjunto for f in fs)
        for n in fs:
            if not n.hijos:lits[n.op]=True
            elif n.op=='¬' and not n.hijos[0].hijos:lits[n.hijos[0].op]=False
        node={'formulas':[fmt(n) for n in agregadas], 'aplicada':None,
              'estado':'cerrada ✕' if closed else 'abierta', 'valores':lits, 'hijos':[]}
        if closed:return node
        pendientes=[(n,expand(n)) for n in fs if n not in aplicadas and expand(n) is not None]
        if pendientes:
            # Las expansiones alfa no crean alternativas; se resuelven antes.
            def prioridad(par):
                opciones=par[1]
                cerrables=sum(any(neg(f) in conjunto or (f.op=='¬' and f.hijos[0] in conjunto) for f in extra) for extra in opciones)
                return (0 if len(opciones)==1 else 1, -cerrables)
            n,ex=min(pendientes,key=prioridad)
            node['aplicada']=fmt(n)+' ✓';node['estado']='expansión'
            node['hijos']=[rama(fs+[f for f in extra if f not in conjunto],aplicadas|{n},extra) for extra in ex]
        return node
    try:return rama(list(dict.fromkeys(formulas)),set(),list(dict.fromkeys(formulas)))
    except RecursionError:raise LimiteAnalisis('Se alcanzó el límite de profundidad. No hay una conclusión completa.') from None

def abiertas(t):
    salida=[];pila=[t]
    while pila:
        n=pila.pop()
        if n['hijos']:pila.extend(reversed(n['hijos']))
        elif n['estado']=='abierta':salida.append(n['valores'])
    return salida

def leer_formula(text):
    """Lee una fórmula ya almacenada, conservando sus letras."""
    protegido=re.sub(r'\b[a-z][0-9]*\b',lambda m:'ATOM_'+m.group(),text)
    tabla={};root=parse(protegido,tabla);ids={v[0]:v[1].removeprefix('ATOM_') for v in tabla.values()}
    def convertir(n):
        return N(ids[n.op]) if not n.hijos else N(n.op,tuple(convertir(h) for h in n.hijos))
    return convertir(root)
