"""Prueba de humo en pantalla virtual sin modificar conocimiento_elsy.json."""
import tempfile,time
from pathlib import Path
import analizador_grafico as mod
with tempfile.TemporaryDirectory() as d:
    init=mod.RegistroReglas.__init__
    def init_prueba(self,archivo=None):
        init(self,Path(d)/'prueba.json')
    mod.RegistroReglas.__init__=init_prueba
    mod.messagebox.showinfo=lambda *a,**k:None
    app=mod.VentanaElsy()
    app.withdraw()
    app.caja.insert('1.0','Solo si, estudio para el examen, apruebo\nestudio para el examen\napruebo si y solo si tengo el certificado')
    app.analizar()
    assert len(app.registro.reglas)==3
    assert app.registro.reglas[0]['formula']=='(q → p)', app.registro.reglas[0]['formula']
    app.construir()
    t=time.monotonic()+8
    while app.trabajando and time.monotonic()<t:
        app.update();time.sleep(.03)
    assert not app.trabajando
    assert app.resultado is not None
    assert app.resultado['modelos_parciales']
    print('Interfaz Elsy OK: entrada, árbol y modelos.')
    app.destroy()
