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
        ttk.Label(margen, text="Elsy Valeria Cuevas de la Torre · Registro 23310379 · Primera entrega · Sin IA").pack(anchor="w", pady=(4, 12))
        ttk.Label(margen, text="Escribe una regla por línea. Estructura: Si [condición], entonces [resultado].").pack(anchor="w")
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


if __name__ == "__main__":
    VentanaElsy().mainloop()
