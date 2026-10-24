import unittest,tempfile,shutil,json,time
from pathlib import Path
from analizador_grafico import RegistroReglas
from motor import *
class Integracion(unittest.TestCase):
 def test_caso_largo(self):
  with tempfile.TemporaryDirectory() as d:
   r=RegistroReglas(Path(d)/'base.json');r.registrar_lote(Path(__file__).with_name('Prueba_larga.txt').read_text().splitlines())
   t=time.monotonic();tree=tableau([leer_formula(x['formula']) for x in r.reglas]);models=abiertas(tree)
   self.assertTrue(models)
   for frase in ['el ciclo está autorizado','el indicador verde está encendido','el historial está actualizado']:
    k=next(k for k,v in r.atomos.items() if v==frase)
    self.assertTrue(all(m.get(k) is True for m in models))
   r.registrar_lote(['no el ciclo está autorizado'])
   self.assertFalse(abiertas(tableau([leer_formula(x['formula']) for x in r.reglas])))
   print('Caso largo completo en',round(time.monotonic()-t,3),'s')
 def test_base_previa_y_guardado(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'base.json';shutil.copy(Path(__file__).with_name('conocimiento_elsy.json'),p)
   original=json.loads(p.read_text());r=RegistroReglas(p)
   self.assertEqual(len(r.reglas),len(original['reglas']));self.assertEqual(list(r.atomos.values()),list(original['atomos'].values()))
   r.registrar_lote(['Si Juan estudia y entrega la tarea, entonces aprueba el examen'])
   self.assertEqual(len(r.atomos),len(original['atomos']))
   reread=RegistroReglas(p);self.assertEqual(r.atomos,reread.atomos)
   before=p.read_bytes()
   with self.assertRaises(ValueError):r.registrar_lote(['hecho nuevo','algo y'])
   self.assertEqual(p.read_bytes(),before)
 def test_limite(self):
  with self.assertRaises(LimiteAnalisis):tableau([parse('A o B',{})],max_nodos=1)
if __name__=='__main__':unittest.main()
