"""Analizador de español controlado para Elsy: léxico y descenso recursivo.
Admite conjunciones, disyunciones, negación y condicionales de varias formas.
No usa servicios de IA.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
@dataclass(frozen=True)
class Nodo:
    op: str
    hijos: tuple=()
def negar(n): return Nodo('¬',(n,))

class AnalizadorRecursivo:
    """Analizador descendente para español controlado, sin IA.

    Precedencia, de mayor a menor: ¬, ∧, ∨, →, ↔. Los condicionales
    escritos al inicio usan «si A, entonces B» o «si A, B».
    Las comillas dobles preservan proposiciones con conectores literales.
    """
    ALIASES = (
        ('si y solo si', '↔'), ('si, y solo si', '↔'),
        ('si y solamente si', '↔'), ('si y únicamente si', '↔'),
        ('es equivalente a', '↔'), ('equivale a', '↔'),
        ('siempre y cuando', 'COND'), ('en caso de que', 'COND'),
        ('siempre que', 'COND'), ('cuando', 'COND'),
        ('a menos que', '∨'), ('salvo que', '∨'),
        ('únicamente si', 'SOLO_SI'), ('solamente si', 'SOLO_SI'),
        ('solo si', 'SOLO_SI'), ('sólo si', 'SOLO_SI'),
        ('por lo tanto', '→'), ('por tanto', '→'),
        ('implica que', '→'), ('implica', '→'),
        ('es falso que', '¬'), ('no es cierto que', '¬'),
        ('no es verdad que', '¬'), ('es mentira que', '¬'),
        ('y además', '∧'), ('así como', '∧'),
        ('además', '∧'), ('pero', '∧'), ('también', '∧'),
        ('asimismo', '∧'), ('aunque', '∧'), ('ni', 'NI'),
        ('o bien', '∨'), ('o', '∨'), ('u', '∨'), ('y', '∧'), ('e', '∧'),
        ('tampoco', '¬'), ('entonces', 'ENTONCES'),
        ('si', 'SI'), ('no', '¬'),
    )
    _alternativas = sorted(ALIASES, key=lambda p: len(p[0]), reverse=True)
    _patron_es = re.compile(
        r'"(?:\\.|[^"\\])*"|[()¬∧∨→↔]|,|(?<!\w)(?:' +
        '|'.join(re.escape(k).replace(r'\ ', r'\s+') for k, _ in _alternativas) +
        r')(?!\w)', re.IGNORECASE)
    _patron_sim = re.compile(r'[()¬∧∨→↔]')
    _op = {'∧','∨','→','↔','¬','SI','COND','SOLO_SI','ENTONCES','NI','(',')',','}

    def __init__(self, texto, simbolica=False):
        if len(texto)>15000:
            raise ValueError('La regla es demasiado larga; divídela en reglas menores.')
        self.simbolica = simbolica
        self.tokens = []
        patron = self._patron_sim if simbolica else self._patron_es
        pos = 0
        for m in patron.finditer(texto):
            self._agregar_atomo(texto[pos:m.start()])
            raw = m.group()
            if not simbolica and raw.startswith('"'):
                # Una proposición entre comillas no se separa aunque contenga «y», «o», etc.
                self.tokens.append(('ATOMO', raw[1:-1].replace(r'\"', '"')))
            elif raw == ',':
                self.tokens.append((',', ','))
            elif raw in '()¬∧∨→↔':
                self.tokens.append((raw, raw))
            else:
                token = raw if simbolica else next(
                    v for k,v in self._alternativas if re.fullmatch(k.replace(' ', r'\s+'), raw, re.I)
                )
                self.tokens.append((token,raw))
            pos=m.end()
        self._agregar_atomo(texto[pos:])
        # Comas de estilo antes de «entonces», «y», etc., no significan implicación.
        self.pos=0

    def _agregar_atomo(self, texto):
        texto=' '.join(texto.strip(' \t\n\r.;:¡!¿?').split())
        if texto:
            self.tokens.append(('ATOMO',texto))

    def actual(self):
        return self.tokens[self.pos][0] if self.pos<len(self.tokens) else None

    def tomar(self, esperado=None):
        t=self.actual()
        if t is None or (esperado is not None and t!=esperado):
            raise ValueError(f"Se esperaba {esperado or 'una proposición'}; apareció {t or 'fin de la regla'}.")
        self.pos+=1
        return self.tokens[self.pos-1][1]

    def _comas_estilo(self):
        # La coma antes del conector explícito «entonces» o «y» es puntuación.
        while self.actual()==',' and self.pos+1<len(self.tokens) and self.tokens[self.pos+1][0] in {'ENTONCES','∧','∨','→','↔'}:
            self.tomar(',')

    def _expresion_desde_tokens(self, tokens):
        """Analiza una subexpresión conservando los tokens originales y sus comillas."""
        if not tokens:
            raise ValueError('Falta una proposición en la regla.')
        otro=self.__class__.__new__(self.__class__)
        otro.tokens=list(tokens)
        otro.pos=0
        otro.simbolica=self.simbolica
        return otro.analizar()

    def _conector_inicial(self):
        """Soporta «Solo si, A, B»: B → A y «Si y solo si, A, B»: A ↔ B.

        La coma anterior a A es opcional; la coma entre A y B es obligatoria.
        Solo se separa en comas fuera de paréntesis.
        """
        tipo=self.tokens[0][0]
        inicio=1
        if inicio < len(self.tokens) and self.tokens[inicio][0]==',':
            inicio+=1
        profundidad=0
        separador=None
        for indice in range(inicio,len(self.tokens)):
            token=self.tokens[indice][0]
            if token=='(':
                profundidad+=1
            elif token==')':
                profundidad-=1
                if profundidad<0:raise ValueError('Paréntesis de cierre sin apertura.')
            elif token==',' and profundidad==0:
                if separador is not None:
                    raise ValueError('El conector inicial requiere dos proposiciones, separadas por una coma.')
                separador=indice
        if profundidad!=0:raise ValueError('Paréntesis sin cerrar.')
        if separador is None:
            raise ValueError('Escribe «Solo si, condición, consecuencia» o «consecuencia solo si condición».')
        condicion=self._expresion_desde_tokens(self.tokens[inicio:separador])
        consecuencia=self._expresion_desde_tokens(self.tokens[separador+1:])
        if tipo=='SOLO_SI':
            return Nodo('→',(consecuencia,condicion))
        return Nodo('↔',(condicion,consecuencia))

    def analizar(self):
        try:
            if not self.simbolica and self.tokens and self.tokens[0][0] in {'SOLO_SI','↔'}:
                return self._conector_inicial()
            resultado=self.equivalencia()
            self._comas_estilo()
        except RecursionError:
            raise ValueError('Demasiados paréntesis o negaciones anidados.') from None
        if self.actual() is not None:
            raise ValueError(f'Conector sin completar o texto inesperado: {self.actual()}.')
        return resultado

    def equivalencia(self):
        a=self.implicacion()
        while True:
            self._comas_estilo()
            if self.actual()!='↔': break
            self.tomar('↔')
            a=Nodo('↔',(a,self.implicacion()))
        return a

    def implicacion(self):
        a=self.disyuncion()
        self._comas_estilo()
        t=self.actual()
        if t in {'→','SOLO_SI','SI','COND'}:
            self.tomar()
            b=self.implicacion()  # Asociatividad derecha.
            if t in {'SI','COND'}:
                return Nodo('→',(b,a))  # «A si B» significa B → A.
            return Nodo('→',(a,b))
        return a

    def disyuncion(self):
        a=self.conjuncion()
        while True:
            self._comas_estilo()
            if self.actual()!='∨':break
            self.tomar('∨')
            a=Nodo('∨',(a,self.conjuncion()))
        return a

    def conjuncion(self):
        a=self.termino()
        while True:
            self._comas_estilo()
            if self.actual() not in {'∧','NI'}:break
            t=self.actual();self.tomar()
            b=self.termino()
            a=Nodo('∧',(a,negar(b) if t=='NI' else b))
        return a

    def termino(self):
        t=self.actual()
        if t is None:
            raise ValueError('Falta una proposición al final de la regla.')
        if t in {'¬','NI'}:
            self.tomar()
            return negar(self.termino())
        if t in {'SI','COND'}:
            self.tomar()
            antecedente=self.equivalencia()
            # Antecedente termina ante «entonces» o la coma separadora.
            if self.actual()=='ENTONCES':
                self.tomar('ENTONCES')
            elif self.actual()==',':
                self.tomar(',')
                if self.actual()=='ENTONCES':self.tomar('ENTONCES')
            else:
                raise ValueError('En «si/cuando ...» separa condición y resultado con «entonces» o una coma.')
            consecuencia=self.equivalencia()
            return Nodo('→',(antecedente,consecuencia))
        if t=='(':
            self.tomar('(')
            a=self.equivalencia()
            self.tomar(')')
            return a
        if t!='ATOMO':
            raise ValueError('Conector sin proposición: '+str(t))
        nombre=self.tomar('ATOMO')
        if self.simbolica:
            if not re.fullmatch(r'[a-z]\d*|X\d+',nombre):
                raise ValueError('Identificador simbólico inválido: '+nombre)
            return Nodo(nombre)
        # «Juan no estudia» equivale a ¬(Juan estudia).
        if self.actual()=='¬':
            self.tomar('¬')
            if self.actual()!='ATOMO':
                raise ValueError('Después de una negación interna falta una acción.')
            accion=self.tomar('ATOMO')
            return negar(Nodo(' '.join((nombre+' '+accion).split())))
        return Nodo(nombre)

