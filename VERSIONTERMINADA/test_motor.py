import unittest,itertools
from motor import *
def evaluar(n,m):
 if not n.hijos:return m[n.op]
 if n.op=='¬':return not evaluar(n.hijos[0],m)
 a,b=[evaluar(h,m) for h in n.hijos]
 return {'∧':a and b,'∨':a or b,'→':not a or b,'↔':a==b}[n.op]
class Pruebas(unittest.TestCase):
 def test_expansiones(self):
  for s in ['A y B','A o B','Si A entonces B','A si y solo si B','no (A y B)','no (A o B)','no (Si A entonces B)','no (A si y solo si B)','no no A']:
   atoms={};n=parse(s,atoms);branches=abiertas(tableau([n]));keys=[v[0] for v in atoms.values()]
   for vals in itertools.product([False,True],repeat=len(keys)):
    m=dict(zip(keys,vals));self.assertEqual(evaluar(n,m),any(all(m[k]==v for k,v in branch.items()) for branch in branches),s)
 def test_contradiccion(self):
  a={};self.assertFalse(abiertas(tableau([parse(s,a) for s in ['Si es de día entonces voy a trabajar','es de día','no voy a trabajar']])))
 def test_atomos(self):
  a={};parse('Juan estudia',a);parse('Juan no estudia',a);self.assertEqual(len(a),1)
 def test_letras_como_conectores(self):
  for s in ['(y → o)', '(p ∧ y)', '¬o', '(y ↔ q)']:
   self.assertEqual(fmt(leer_formula(s)),s if s.startswith('(') or s=='¬o' else s)
 def test_invalidas(self):
  for s in ['A y','(A o B','A o o B']:
   with self.assertRaises(ValueError):parse(s,{})
if __name__=='__main__':unittest.main()
