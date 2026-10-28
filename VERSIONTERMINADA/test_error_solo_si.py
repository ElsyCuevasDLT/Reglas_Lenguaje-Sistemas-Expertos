"""Regresión de la captura: SOLO SI al comienzo, orden semántico y guardado."""
import tempfile,unittest
from pathlib import Path
from motor import parse,fmt,tableau,abiertas,leer_formula
from analizador_grafico import RegistroReglas

class TestSoloSi(unittest.TestCase):
 def test_captura(self):
  tabla={}
  arbol=parse('Solo si, estudio para el examen, apruebo',tabla)
  self.assertEqual(fmt(arbol),'(q → p)')
  self.assertEqual(tabla['estudio para el examen'][0],'p')
  self.assertEqual(tabla['apruebo'][0],'q')
 def test_variantes(self):
  casos={
   'Solo si, A, B':'(q → p)',
   'Solo si A, B':'(q → p)',
   'B solo si A':'(p → q)',
   'Si A, entonces B':'(p → q)',
   'Si y solo si, A, B':'(p ↔ q)',
   'Solo si, (A y C), B':'(r → (p ∧ q))',
   'A si y solo si B':'(p ↔ q)',
   'No A o B':'(¬p ∨ q)'
  }
  for texto,formula in casos.items():
   with self.subTest(texto=texto):self.assertEqual(fmt(parse(texto,{})),formula)
 def test_persistencia_y_consistencia(self):
  with tempfile.TemporaryDirectory() as carpeta:
   r=RegistroReglas(Path(carpeta)/'reglas.json')
   reglas=r.registrar_lote(['Solo si, estudio para el examen, apruebo','Apruebo solo si estudio para el examen'])
   self.assertEqual(len(r.atomos),2)
   self.assertEqual([x['formula'] for x in reglas],['(q → p)','(q → p)'])
   # Agregar estudiar y no estudiar debe producir cierre.
   r.registrar_lote(['estudio para el examen','no estudio para el examen'])
   self.assertEqual(abiertas(tableau([leer_formula(a['formula']) for a in r.reglas])),[])

if __name__=='__main__':unittest.main()
