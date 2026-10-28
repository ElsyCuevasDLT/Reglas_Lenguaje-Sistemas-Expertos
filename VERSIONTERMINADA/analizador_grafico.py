"""Sistemas Expertos, etapa 1: editor gráfico de reglas en español.
Autora: Elsy Valeria Cuevas de la Torre | Registro: 23310379.
Análisis con notación posfija (shunting-yard). Biblioteca estándar, sin IA.
"""
from __future__ import annotations

import json
import os
import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

BASE = Path(__file__).with_name("conocimiento_elsy.json")
CONEXIONES = {"y": ("∧", 2), "o": ("∨", 1)}
NO_ES_NOMBRE = {
    "si", "es", "no", "hay", "voy", "soy", "estoy", "aprueba", "entrega",
    "estudia", "reprueba", "trabaja", "duerme", "tiene", "tenemos", "puede",
    "enciende", "apaga", "el", "la", "los", "las", "un", "una", "este",
    "esta", "hoy", "mañana", "cuando", "llueve", "nieva",
}
NO_HEREDAR = {"es", "hay", "voy", "estoy", "soy", "llueve", "nieva", "el", "la", "los", "las", "un", "una", "este", "esta", "hoy"}
EXP_REG = re.compile(r"\(|\)|\b(?:y|o)\b", re.IGNORECASE)
EXP_IF = re.compile(r"^si\s+(.+?)\s*,?\s+entonces\s+(.+)$", re.IGNORECASE)


def limpiar(cadena: str) -> str:
    return " ".join(cadena.strip(" \t\n\r.;,:¡!¿?").split())


def dividir_regla(linea: str) -> tuple[str, str | None]:
    linea = limpiar(linea)
    if not linea:
        raise ValueError("La regla está vacía.")
    if re.match(r"^si\s+", linea, re.I):
        match = EXP_IF.fullmatch(linea)
        if not match:
            raise ValueError("Se necesita 'Si [condición], entonces [consecuencia]'.")
        return limpiar(match.group(1)), limpiar(match.group(2))
    return linea, None  # Permite registrar hechos.


def separar_tokens(cadena: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    comienzo = 0
    for m in EXP_REG.finditer(cadena):
        frase = limpiar(cadena[comienzo:m.start()])
        if frase:
            tokens.append(("A", frase))
        op = m.group().casefold()
        tokens.append(("(" if op == "(" else ")" if op == ")" else "OP", op))
        comienzo = m.end()
    frase = limpiar(cadena[comienzo:])
    if frase:
        tokens.append(("A", frase))
    return tokens


def posfija(tokens: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Algoritmo de patio de maniobras con revisión estricta de sintaxis."""
    pila: list[str] = []
    salida: list[tuple[str, str]] = []
    espera_atomo = True
    for tipo, valor in tokens:
        if tipo == "A":
            if not espera_atomo:
                raise ValueError(f"Falta operador lógico antes de '{valor}'.")
            salida.append((tipo, valor))
            espera_atomo = False
        elif tipo == "(":
            if not espera_atomo:
                raise ValueError("Falta operador antes del paréntesis.")
            pila.append("(")
        elif tipo == ")":
            if espera_atomo:
                raise ValueError("Paréntesis vacío u operador sin término.")
            while pila and pila[-1] != "(":
                salida.append(("OP", pila.pop()))
            if not pila:
                raise ValueError("Hay un paréntesis de cierre sin apertura.")
            pila.pop()
            espera_atomo = False
        else:
            if espera_atomo:
                raise ValueError(f"El operador '{valor}' no tiene un átomo a la izquierda.")
            while pila and pila[-1] != "(" and CONEXIONES[pila[-1]][1] >= CONEXIONES[valor][1]:
                salida.append(("OP", pila.pop()))
            pila.append(valor)
            espera_atomo = True
    if espera_atomo:
        raise ValueError("La expresión está incompleta.")
    while pila:
        operador = pila.pop()
        if operador == "(":
            raise ValueError("Hay un paréntesis sin cerrar.")
        salida.append(("OP", operador))
    profundidad = 0
    for tipo, _ in salida:
        profundidad += 1 if tipo == "A" else -1
        if profundidad < 1:
            raise ValueError("Los operadores no tienen suficientes argumentos.")
    if profundidad != 1:
        raise ValueError("No se pudo construir una expresión lógica única.")
    return salida


def separar_no(frase: str) -> tuple[bool, str]:
    texto = limpiar(frase)
    if texto.casefold().startswith("no "):
        texto = limpiar(texto[3:])
        return True, texto
    encontrado = re.search(r"\s+no\s+", texto, re.I)
    if encontrado:
        texto = limpiar(texto[:encontrado.start()] + " " + texto[encontrado.end():])
        return True, texto
    return False, texto


def nombre_sujeto(frase: str) -> str | None:
    palabras = frase.split()
    if len(palabras) < 2 or palabras[0].casefold() in NO_ES_NOMBRE:
        return None
    if not (palabras[0][0].isupper() and palabras[0][1:].islower()):
        return None
    cantidad = 1
    while cantidad < min(len(palabras) - 1, 3):
        p = palabras[cantidad]
        if len(p) < 2 or not (p[0].isupper() and p[1:].islower()):
            break
        cantidad += 1
    return " ".join(palabras[:cantidad])


def completar(tokens: list[tuple[str, str]], protagonista: str | None) -> list[tuple[str, str]]:
    resultado = []
    for tipo, frase in tokens:
        if tipo != "A":
            resultado.append((tipo, frase))
            continue
        negado, proposicion = separar_no(frase)
        if not proposicion:
            raise ValueError("Falta proposición después de 'no'.")
        palabra_inicial = proposicion.split()[0].casefold()
        if (protagonista and not nombre_sujeto(proposicion)
                and proposicion[0].islower() and palabra_inicial not in NO_HEREDAR):
            proposicion = protagonista + " " + proposicion
        resultado.append(("A", ("¬" if negado else "") + proposicion))
    return resultado


def extraer_protagonista(tokens: list[tuple[str, str]]) -> str | None:
    personas: dict[str, str] = {}
    for tipo, frase in tokens:
        if tipo != "A":
            continue
        _, proposicion = separar_no(frase)
        nombre = nombre_sujeto(proposicion)
        if nombre:
            personas[nombre.casefold()] = nombre
    return list(personas.values())[0] if len(personas) == 1 else None


def renderizar(rpn: list[tuple[str, str]], equivalencias: dict[str, str]) -> tuple[str, list[str]]:
    """Interpreta la notación posfija y da prioridad a ∧ sobre ∨."""
    pila: list[tuple[str, int]] = []
    mencionados: list[str] = []
    for tipo, valor in rpn:
        if tipo == "A":
            negativo = valor.startswith("¬")
            frase = valor[1:] if negativo else valor
            id_atomo = equivalencias[frase.casefold()]
            mencionados.append(id_atomo)
            pila.append((("¬" if negativo else "") + id_atomo, 3))
        else:
            derecha, prio_der = pila.pop()
            izquierda, prio_izq = pila.pop()
            operador, prioridad = CONEXIONES[valor]
            if prio_izq < prioridad:
                izquierda = f"({izquierda})"
            if prio_der < prioridad:
                derecha = f"({derecha})"
            pila.append((f"{izquierda} {operador} {derecha}", prioridad))
    return pila[0][0], mencionados


class RegistroReglas:
    """Base de reglas con guardado transaccional de líneas múltiples."""
    def __init__(self, archivo: Path = BASE):
        self.archivo = Path(archivo)
        self.atomos: dict[str, str] = {}
        self.reglas: list[dict] = []
        if self.archivo.is_file():
            contenido = json.loads(self.archivo.read_text(encoding="utf-8"))
            self.atomos = contenido["atomos"]
            self.reglas = contenido["reglas"]

    def registrar_lote(self, oraciones: list[str]) -> list[dict]:
        nueva_tabla = self.atomos.copy()
        reglas_nuevas = []
        catalogo = {v.casefold(): k for k, v in nueva_tabla.items()}
        for linea in oraciones:
            antecedente, consecuente = dividir_regla(linea)
            tokens_a = separar_tokens(antecedente)
            sujeto = extraer_protagonista(tokens_a)
            tokens_a = completar(tokens_a, sujeto)
            rpn_a = posfija(tokens_a)
            rpn_b = None
            if consecuente:
                rpn_b = posfija(completar(separar_tokens(consecuente), sujeto))
            # Se registran las proposiciones una vez VALIDADA cada estructura.
            for rpn in [rpn_a, rpn_b]:
                for tipo, valor in rpn or []:
                    if tipo == "A":
                        frase = valor.removeprefix("¬")
                        if frase.casefold() not in catalogo:
                            nuevo_id = f"X{len(nueva_tabla) + 1}"
                            nueva_tabla[nuevo_id] = frase
                            catalogo[frase.casefold()] = nuevo_id
            formula_a, usados_a = renderizar(rpn_a, catalogo)
            referenciados = usados_a
            if rpn_b:
                formula_b, usados_b = renderizar(rpn_b, catalogo)
                # Cuando hay varios operadores se agrupan las dos partes.
                if any(tipo == "OP" for tipo, _ in rpn_a):
                    formula_a = "(" + formula_a + ")"
                if any(tipo == "OP" for tipo, _ in rpn_b):
                    formula_b = "(" + formula_b + ")"
                formula_a = formula_a + " → " + formula_b
                referenciados += usados_b
            reglas_nuevas.append({"id": f"R{len(self.reglas) + len(reglas_nuevas) + 1}",
                                  "original": limpiar(linea), "formula": formula_a,
                                  "atomos": list(dict.fromkeys(referenciados))})
        # Si cualquier línea falla, NO se cambia ningún dato previo.
        self.atomos = nueva_tabla
        self.reglas.extend(reglas_nuevas)
        self.guardar()
        return reglas_nuevas

    def guardar(self) -> None:
        datos = json.dumps({"atomos": self.atomos, "reglas": self.reglas},
                           indent=2, ensure_ascii=False)
        temporal = self.archivo.with_suffix(".tmp")
        temporal.write_text(datos, encoding="utf-8")
        os.replace(temporal, self.archivo)

    def exportar(self, archivo: Path) -> None:
        archivo.write_text(json.dumps({"atomos": self.atomos, "reglas": self.reglas},
                                      indent=2, ensure_ascii=False), encoding="utf-8")


class VentanaElsy(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistemas Expertos | Elsy Cuevas de la Torre | 23310379")
        self.geometry("1040x690")
        self.minsize(800, 550)
        self.registro = RegistroReglas()
        self.crear_interfaz()
        self.actualizar_tablas()

    def crear_interfaz(self) -> None:
        margen = ttk.Frame(self, padding=15)
        margen.pack(fill="both", expand=True)
        ttk.Label(margen, text="ANALIZADOR DE REGLAS LÓGICAS", font=("Arial", 17, "bold")).pack(anchor="w")
        ttk.Label(margen, text="Elsy Valeria Cuevas de la Torre · Registro 23310379 · Árbol semántico y modelos · Sin IA").pack(anchor="w", pady=(4, 12))
        ttk.Label(margen, text="Escribe hechos o reglas. Admite Y, O, NO, SI, CUANDO, SOLO SI, IMPLICA y SI Y SOLO SI.").pack(anchor="w")
        self.caja = scrolledtext.ScrolledText(margen, height=6, wrap="word", font=("Arial", 11))
        self.caja.pack(fill="x", pady=(5, 9))
        acciones = ttk.Frame(margen)
        acciones.pack(fill="x")
        ttk.Button(acciones, text="Analizar y guardar", command=self.analizar).pack(side="left", padx=(0, 7))
        ttk.Button(acciones, text="Cargar ejemplos", command=self.ejemplos).pack(side="left", padx=(0, 7))
        ttk.Button(acciones, text="Vaciar entrada", command=lambda: self.caja.delete("1.0", "end")).pack(side="left", padx=(0, 7))
        ttk.Button(acciones, text="Exportar JSON", command=self.exportar).pack(side="left", padx=(0, 7))
        ttk.Button(acciones, text="Reiniciar base", command=self.reiniciar).pack(side="right")
        separador = ttk.PanedWindow(margen, orient="vertical")
        separador.pack(fill="both", expand=True, pady=(14, 5))
        marco_atomos = ttk.LabelFrame(separador, text="ÁTOMOS IDENTIFICADOS", padding=6)
        self.tabla_atomos = ttk.Treeview(marco_atomos, columns=("id", "proposicion"), show="headings", height=7)
        self.tabla_atomos.heading("id", text="Átomo")
        self.tabla_atomos.heading("proposicion", text="Proposición")
        self.tabla_atomos.column("id", width=85, stretch=False, anchor="center")
        self.tabla_atomos.column("proposicion", width=820)
        self.tabla_atomos.pack(fill="both", expand=True)
        separador.add(marco_atomos, weight=1)
        marco_reglas = ttk.LabelFrame(separador, text="REGLAS Y FÓRMULAS", padding=6)
        self.tabla_reglas = ttk.Treeview(marco_reglas, columns=("id", "formula", "texto"), show="headings", height=7)
        self.tabla_reglas.heading("id", text="Regla")
        self.tabla_reglas.heading("formula", text="Lógica proposicional")
        self.tabla_reglas.heading("texto", text="Oración original")
        self.tabla_reglas.column("id", width=65, stretch=False, anchor="center")
        self.tabla_reglas.column("formula", width=300)
        self.tabla_reglas.column("texto", width=580)
        self.tabla_reglas.pack(fill="both", expand=True)
        separador.add(marco_reglas, weight=1)
        self.estado = tk.StringVar(value="Preparada para recibir reglas")
        ttk.Label(margen, textvariable=self.estado).pack(anchor="w", pady=(3, 0))

    def actualizar_tablas(self) -> None:
        for tabla in (self.tabla_atomos, self.tabla_reglas):
            for linea in tabla.get_children():
                tabla.delete(linea)
        for numero, frase in self.registro.atomos.items():
            self.tabla_atomos.insert("", "end", values=(numero, frase))
        for regla in self.registro.reglas:
            self.tabla_reglas.insert("", "end", values=(regla["id"], regla["formula"], regla["original"]))
        self.estado.set(f"{len(self.registro.atomos)} átomos únicos | {len(self.registro.reglas)} reglas guardadas")

    def analizar(self) -> None:
        lineas = [fila.strip() for fila in self.caja.get("1.0", "end").splitlines() if fila.strip()]
        if not lineas:
            messagebox.showwarning("Sin datos", "Escribe al menos una oración.")
            return
        try:
            nuevas = self.registro.registrar_lote(lineas)
        except (ValueError, OSError) as exc:
            messagebox.showerror("Regla no admitida", f"No se guardó ninguna regla del lote.\n\n{exc}")
            return
        self.actualizar_tablas()
        self.caja.delete("1.0", "end")
        messagebox.showinfo("Registro correcto", "\n".join(f"{r['id']} = {r['formula']}" for r in nuevas))

    def ejemplos(self) -> None:
        self.caja.delete("1.0", "end")
        self.caja.insert("1.0", "Si Juan estudia y entrega la tarea, entonces aprueba el examen\n"
                                 "Si Juan aprueba el examen, entonces obtiene su certificado\n"
                                 "Si no hay energía, entonces la máquina no funciona")

    def exportar(self) -> None:
        destino = filedialog.asksaveasfilename(title="Guardar base", defaultextension=".json",
                                               filetypes=[("Datos JSON", "*.json")])
        if destino:
            try:
                self.registro.exportar(Path(destino))
                messagebox.showinfo("Exportación", "Archivo JSON exportado correctamente.")
            except OSError as exc:
                messagebox.showerror("Error al exportar", str(exc))

    def reiniciar(self) -> None:
        if messagebox.askyesno("Confirmar", "¿Eliminar permanentemente todos los átomos y las reglas guardadas?"):
            self.registro.atomos = {}
            self.registro.reglas = []
            self.registro.guardar()
            self.actualizar_tablas()



# Extensiones: se conserva la interfaz y el flujo de la primera entrega.
from motor import N, parse, fmt, letra, leer_formula, tableau, abiertas, LimiteAnalisis
import threading
import queue
import copy

RegistroAnterior = RegistroReglas
class RegistroReglas(RegistroAnterior):
    def __init__(self, archivo=BASE):
        super().__init__(archivo)
        # Migración en memoria: conserva el significado y las reglas originales.
        cambios={k:letra(i) for i,k in enumerate(self.atomos)}
        self.atomos={cambios[k]:v for k,v in self.atomos.items()}
        for r in self.reglas:
            r['formula']=re.sub(r'\bX\d+\b',lambda m:cambios[m.group()],r['formula'])
            r['atomos']=[cambios.get(a,a) for a in r['atomos']]
    def registrar_lote(self, oraciones):
        tabla={v.casefold():(k,v) for k,v in self.atomos.items()}; nuevas=[]
        for numero,linea in enumerate(oraciones,1):
            try:
                temporal={};parse(linea,temporal)
                nombres={nombre_sujeto(v[1]) for v in temporal.values() if nombre_sujeto(v[1])}
                sujeto=next(iter(nombres)) if len(nombres)==1 else None
                def completar_frase(t):
                    if (sujeto and t and t[0].islower() and not nombre_sujeto(t)
                            and t.split()[0].casefold() not in NO_HEREDAR):
                        return sujeto+' '+t
                    return t
                root=parse(linea,tabla,completar_frase)
                usados=[]
                def visitar(n):
                    if not n.hijos:
                        if n.op not in usados:usados.append(n.op)
                    for h in n.hijos:visitar(h)
                visitar(root)
                nuevas.append({'id':f'R{len(self.reglas)+len(nuevas)+1}',
                               'original':limpiar(linea),'formula':fmt(root),'atomos':usados})
            except (ValueError,RecursionError) as e:
                raise ValueError(f'Línea {numero}: {e}') from None
        anteriores=self.atomos,self.reglas
        self.atomos={k:v for k,v in tabla.values()};self.reglas=self.reglas+nuevas
        try:self.guardar()
        except OSError:
            self.atomos,self.reglas=anteriores
            raise
        return nuevas

VentanaAnterior=VentanaElsy
class VentanaElsy(VentanaAnterior):
    def __init__(self):
        self.trabajando=False;self.resultado=None;self.cancelar_evento=threading.Event()
        super().__init__()
    def crear_interfaz(self):
        super().crear_interfaz()
        extra=ttk.Frame(self,padding=(15,4,15,10));extra.pack(fill='x')
        self.boton_arbol=ttk.Button(extra,text='Construir árbol y modelos de la base',command=self.construir)
        self.boton_arbol.pack(side='left')
        ttk.Button(extra,text='Cancelar análisis',command=lambda:self.cancelar_evento.set()).pack(side='left',padx=8)
        ttk.Button(extra,text='Exportar árbol y modelos',command=self.exportar_analisis).pack(side='left')
        ttk.Button(extra,text='Guía de conectores',command=self.guia_conectores).pack(side='left',padx=7)
        ttk.Label(extra,text='Incluye todas las reglas guardadas.').pack(side='left',padx=10)
    def guia_conectores(self):
        messagebox.showinfo('Conectores admitidos',
            'Y / ∧: y, e, además, pero, aunque.\n'
            'O / ∨: o, u, o bien, a menos que.\n'
            'NO / ¬: no, tampoco, es falso que.\n\n'
            'SI A ENTONCES B = A → B\n'
            'SI A, B = A → B\n'
            'CUANDO A, B = A → B\n'
            'A IMPLICA B = A → B\n'
            'A SI B = B → A\n'
            'A SOLO SI B = A → B\n'
            'SOLO SI, A, B = B → A\n'
            'SOLO SI A, B = B → A\n'
            'A SI Y SOLO SI B = A ↔ B\n'
            'A EQUIVALE A B = A ↔ B\n\n'
            'Una oración por línea, paréntesis para agrupar.\n'
            'Pon entre comillas un átomo que contenga Y u O literales.\n'
            'El analizador reconoce español controlado, no lenguaje libre ilimitado.')

    def ejemplos(self):
        self.caja.delete('1.0','end')
        self.caja.insert('1.0',
            'Si Juan estudia y entrega la tarea, entonces aprueba el examen\n'
            'Cuando Juan estudia, Juan aprende\n'
            'Juan aprueba el examen si y solo si Juan tiene calificación aprobatoria\n'
            'Juan recibe certificado solo si Juan aprueba el examen\n'
            'no Juan reprueba el examen\n'
            'Juan se concentra o bien Juan se distrae')

    def analizar(self):
        if self.trabajando:return
        super().analizar();self.resultado=None
    def reiniciar(self):
        if self.trabajando:return
        super().reiniciar();self.resultado=None
    def construir(self):
        if self.trabajando:return
        if not self.registro.reglas:
            messagebox.showwarning('Base vacía','Primero analiza y guarda las reglas.');return
        if self.caja.get('1.0','end').strip():
            messagebox.showwarning('Entrada pendiente','Pulsa Analizar y guardar para incluir el texto de entrada.');return
        self.trabajando=True;self.resultado=None;self.cancelar_evento.clear();self.boton_arbol.state(['disabled'])
        self.estado.set('Construyendo árbol en segundo plano… Puedes cancelar el análisis.')
        datos=copy.deepcopy(self.registro.reglas);cola=queue.Queue()
        def worker():
            try:
                tree=tableau([leer_formula(r['formula']) for r in datos],cancelar=self.cancelar_evento)
                cola.put(('ok',{'reglas':datos,'atomos':self.registro.atomos.copy(),'arbol':tree,'modelos_parciales':abiertas(tree)}))
            except Exception as e:cola.put(('error',str(e)))
        threading.Thread(target=worker,daemon=True).start()
        def revisar():
            try:tipo,valor=cola.get_nowait()
            except queue.Empty:self.after(80,revisar);return
            self.trabajando=False;self.boton_arbol.state(['!disabled'])
            if tipo=='error':
                self.estado.set('Análisis incompleto: no se emitió conclusión.')
                messagebox.showwarning('Análisis detenido',valor);return
            self.resultado=valor
            self.estado.set(f"Análisis completo: {len(valor['modelos_parciales'])} ramas abiertas")
            self.mostrar_resultado()
        self.after(80,revisar)
    def mostrar_resultado(self):
        d=self.resultado;w=tk.Toplevel(self);w.title('Árbol semántico y modelos');w.geometry('1100x750')
        modelos=d['modelos_parciales']
        ttk.Label(w,text='Base satisfacible' if modelos else 'Base insatisfacible: todas las ramas están cerradas',font=('Arial',13,'bold')).pack(anchor='w',padx=10,pady=8)
        nota='✓ = fórmula aplicada; ✕ = contradicción. Se muestran las fórmulas añadidas en cada paso.'
        ttk.Label(w,text=nota).pack(anchor='w',padx=10)
        resumen=scrolledtext.ScrolledText(w,height=6,wrap='word');resumen.pack(fill='x',padx=10,pady=5)
        for i,m in enumerate(modelos):
            resumen.insert('end',f"Rama {i+1}: "+', '.join(f"{a} = {'V' if v else 'F'}" for a,v in m.items())+'\n')
        resumen.insert('end','Las letras ausentes en una rama son libres: pueden valer V o F.');resumen.configure(state='disabled')
        controles=ttk.Frame(w,padding=(10,5));controles.pack(fill='x')
        frame=ttk.Frame(w);frame.pack(fill='both',expand=True)
        c=tk.Canvas(frame,bg='#f8fafc');ys=ttk.Scrollbar(frame,orient='vertical',command=c.yview);xs=ttk.Scrollbar(frame,orient='horizontal',command=c.xview)
        c.configure(yscrollcommand=ys.set,xscrollcommand=xs.set);ys.pack(side='right',fill='y');xs.pack(side='bottom',fill='x');c.pack(fill='both',expand=True)
        # Una etiqueta por paso; la raíz con todas las reglas se consulta arriba.
        nodos=[];pila=[(d['arbol'],0,None)];hoja=0
        while pila:
            n,depth,parent=pila.pop();idx=len(nodos);nodos.append([n,depth,parent,None])
            for h in reversed(n['hijos']):pila.append((h,depth+1,idx))
        hijos={}
        for i,(_,_,parent,_) in enumerate(nodos):hijos.setdefault(parent,[]).append(i)
        for i in range(len(nodos)-1,-1,-1):
            if i in hijos:nodos[i][3]=sum(nodos[j][3] for j in hijos[i])/len(hijos[i])
            else:nodos[i][3]=140+hoja*290;hoja+=1
        for i,(n,depth,parent,x) in enumerate(nodos):
            y=75+depth*135
            if parent is not None:
                pn,pd,pp,px=nodos[parent];c.create_line(px,75+pd*135+43,x,y-43,fill='#64748b',width=2)
            color='#fee2e2' if '✕' in n['estado'] else '#dcfce7' if n['estado']=='abierta' else '#dbeafe'
            c.create_rectangle(x-130,y-43,x+130,y+43,fill=color,outline='#64748b')
            texto=('Raíz: todas las reglas verdaderas' if parent is None else '; '.join(n['formulas']))
            if len(texto)>110:texto=texto[:107]+'…'
            texto+='\n'+(n['aplicada'] or n['estado'])
            c.create_text(x,y,text=texto,width=245,font=('Arial',9))
        # Zoom absoluto: se escalan geometría, tipografía y ancho de texto.
        escala=1.0
        ajuste_activo=True
        porcentaje=tk.StringVar(value='100%')
        def region():
            b=c.bbox('all')
            if b:
                r=(b[0]-25,b[1]-25,b[2]+25,b[3]+25)
                c.configure(scrollregion=r)
                return r
            return (0,0,1,1)
        def zoom(nueva,x=None,y=None):
            nonlocal escala
            nueva=max(0.00001,min(5.0,nueva))
            x=c.winfo_width()/2 if x is None else x
            y=c.winfo_height()/2 if y is None else y
            factor=nueva/escala
            objetivo_x=c.canvasx(x)*factor
            objetivo_y=c.canvasy(y)*factor
            c.scale('all',0,0,factor,factor)
            escala=nueva
            for item in c.find_all():
                if c.type(item)=='text':
                    c.itemconfigure(item,font=('Arial',max(1,round(9*escala))),width=max(1,245*escala))
            r=region()
            c.xview_moveto((objetivo_x-x-r[0])/max(1,r[2]-r[0]))
            c.yview_moveto((objetivo_y-y-r[1])/max(1,r[3]-r[1]))
            porcentaje.set(f'{escala*100:.2f}%')
        def ajustar():
            nonlocal ajuste_activo
            ajuste_activo=True
            w.update_idletasks()
            b=c.bbox('all')
            if not b:return
            factor=min(max(1,c.winfo_width()-70)/max(1,b[2]-b[0]),
                       max(1,c.winfo_height()-70)/max(1,b[3]-b[1]))
            zoom(escala*factor)
            c.xview_moveto(0);c.yview_moveto(0)
        def manual(factor,x=None,y=None):
            nonlocal ajuste_activo
            ajuste_activo=False
            zoom(escala*factor,x,y)
        def restaurar():
            nonlocal ajuste_activo
            ajuste_activo=False
            zoom(1.0)
        def rueda(e):
            direccion=1 if getattr(e,'num',None)==4 or getattr(e,'delta',0)>0 else -1
            manual(1.2 if direccion>0 else 1/1.2,e.x,e.y)
            return 'break'
        ttk.Button(controles,text='− Alejar',command=lambda:manual(1/1.2)).pack(side='left')
        ttk.Button(controles,text='+ Acercar',command=lambda:manual(1.2)).pack(side='left',padx=5)
        ttk.Button(controles,text='Ver árbol completo',command=ajustar).pack(side='left',padx=5)
        ttk.Button(controles,text='100%',command=restaurar).pack(side='left',padx=5)
        ttk.Label(controles,textvariable=porcentaje,width=10).pack(side='left',padx=5)
        ttk.Label(controles,text='Rueda: zoom · Arrastrar: mover').pack(side='left',padx=8)
        c.bind('<MouseWheel>',rueda)
        c.bind('<Button-4>',rueda);c.bind('<Button-5>',rueda)
        c.bind('<ButtonPress-1>',lambda e:c.scan_mark(e.x,e.y))
        c.bind('<B1-Motion>',lambda e:c.scan_dragto(e.x,e.y,gain=1))
        pendiente=[None]
        def redimensionar(e):
            if not ajuste_activo:return
            if pendiente[0] is not None:c.after_cancel(pendiente[0])
            pendiente[0]=c.after(120,ajustar)
        c.bind('<Configure>',redimensionar)
        region()
        w.after_idle(ajustar)
        # Detalle sin truncamiento de fórmulas; conserva relación padre/hijo.
        def detalle():
            v=tk.Toplevel(w);v.title('Detalle completo del árbol');v.geometry('1000x650')
            t=scrolledtext.ScrolledText(v,wrap='word');t.pack(fill='both',expand=True)
            for i,(n,depth,parent,x) in enumerate(nodos):
                t.insert('end',f"Nodo {i+1} | Padre {parent+1 if parent is not None else 'raíz'} | {n['estado']}\n"+'; '.join(n['formulas'])+'\n'+(n['aplicada'] or '')+'\n\n')
            t.configure(state='disabled')
        ttk.Button(w,text='Ver fórmulas completas de cada nodo',command=detalle).pack(pady=5)
    def exportar_analisis(self):
        if self.resultado is None:
            messagebox.showwarning('Sin análisis','Construye primero el árbol.');return
        p=filedialog.asksaveasfilename(defaultextension='.json',filetypes=[('Análisis JSON','*.json')])
        if p:
            try:Path(p).write_text(json.dumps(self.resultado,ensure_ascii=False,indent=2),encoding='utf-8')
            except (OSError,RecursionError) as e:messagebox.showerror('Error al exportar',str(e))


if __name__ == "__main__":
    VentanaElsy().mainloop()
