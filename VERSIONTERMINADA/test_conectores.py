import tempfile,unittest
from pathlib import Path
from motor import parse,fmt,leer_formula,tableau,abiertas
from analizador_grafico import RegistroReglas

class PruebasNuevas(unittest.TestCase):
    def test_variantes(self):
        casos={
            'A y B':'(p ∧ q)',
            'A o B':'(p ∨ q)',
            'No A':'¬p',
            'A si B':'(q → p)',
            'A solo si B':'(p → q)',
            'Si A entonces B':'(p → q)',
            'Si A, B':'(p → q)',
            'Cuando A, B':'(p → q)',
            'A implica B':'(p → q)',
            'A si y solo si B':'(p ↔ q)',
            'A equivale a B':'(p ↔ q)',
            'A o bien B':'(p ∨ q)',
            'A además B':'(p ∧ q)',
            'A a menos que B':'(p ∨ q)',
            'ni A ni B':'(¬p ∧ ¬q)',
            'es falso que A':'¬p',
        }
        for texto,esperado in casos.items():
            with self.subTest(texto=texto):
                self.assertEqual(fmt(parse(texto,{})),esperado)

    def test_reutilizacion_y_tableau(self):
        with tempfile.TemporaryDirectory() as d:
            reg=RegistroReglas(Path(d)/'datos.json')
            reg.registrar_lote(['Juan no estudia','Juan estudia','Juan estudia si y solo si Juan prepara su mochila'])
            self.assertEqual(list(reg.atomos.values()),['Juan estudia','Juan prepara su mochila'])
            self.assertFalse(abiertas(tableau([leer_formula(r['formula']) for r in reg.reglas])))

    def test_condicional_inverso(self):
        with tempfile.TemporaryDirectory() as d:
            reg=RegistroReglas(Path(d)/'datos.json')
            reg.registrar_lote(['Trabajo si estudio','estudio','no trabajo'])
            self.assertFalse(abiertas(tableau([leer_formula(r['formula']) for r in reg.reglas])))

if __name__=='__main__':unittest.main()
