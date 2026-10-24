# Sistemas expertos — Elsy Valeria Cuevas de la Torre, 23310379

Versión corregida: conserva la interfaz de la primera entrega y agrega árbol semántico y modelos.

## Abrir
Descomprime TODO el ZIP. Abre START_Program.bat en Windows con Python 3.10 o posterior y Tkinter instalado. Mantén motor.py, analizador_grafico.py y conocimiento_elsy.json juntos.

## Funciones originales conservadas
Analizar y guardar varias líneas, cargar ejemplos, vaciar entrada, tabla de átomos, tabla de reglas, exportar base JSON y reiniciar con confirmación. La base previa se carga automáticamente; se conservan las proposiciones y reglas, cambiando X1, X2… por p, q… en memoria y al guardar. original.py conserva el código anterior como respaldo.

## Funciones nuevas
Cinco conectivos: y (∧), o (∨), no (¬), si… entonces (→), si y solo si (↔). Paréntesis anidados; análisis y expansión recursivos. Precedencia: ¬, ∧, ∨, →, ↔. La implicación se asocia a derecha.

1. Escribe reglas, una por línea, y pulsa Analizar y guardar.
2. Pulsa Construir árbol y modelos de la base. Usa TODAS las reglas guardadas.
3. El cálculo se ejecuta en segundo plano y puede cancelarse.
4. Se dibuja el árbol con ramas y colores: rojo cerrado, verde abierto, azul expansión. Usa las barras de desplazamiento.
5. ✓ indica la fórmula aplicada. Cada nodo muestra las fórmulas nuevas; el botón de detalle muestra todas sin truncar. La raíz parte de todas las reglas verdaderas.
6. Las ramas abiertas muestran modelos parciales: letras ausentes son libres. Todas cerradas significa base insatisfacible.
7. Exportar árbol y modelos guarda un JSON separado; Exportar JSON conserva su función de exportar la base.

## Límites y correcciones
Se priorizan las expansiones sin bifurcación y las alternativas con contradicciones evidentes. El árbol tiene límites de 6000 nodos y 8 segundos; si se alcanzan, se informa análisis incompleto, sin declarar satisfacibilidad ni insatisfacibilidad. No se pretende interpretar español libre: no se reconocen sinónimos ni conectivos fuera de los cinco indicados. Se conserva la heurística original para heredar nombres; escribe sujetos completos cuando haya ambigüedad.
Las letras y/o usadas como identificadores en fórmulas almacenadas ya no se confunden con conectivos del español.

## Validación
python -m unittest -v
Pruebas de los conectivos y expansiones comparadas contra valores de verdad, contradicciones, límite controlado, errores de sintaxis, conservación y recarga de la base anterior, guardado transaccional y caso largo de 32 líneas (Prueba_larga.txt). Agregar «no el ciclo está autorizado» cierra todas las ramas del caso largo.
La interfaz no pudo comprobarse visualmente en el entorno de entrega; sí se comprobó compilación y ejecución del motor y de la integración con la base.

## Navegación del árbol
Botones Acercar, Alejar, Ver árbol completo y 100%. La rueda del mouse hace zoom sobre el cursor. Arrastra con el botón izquierdo para mover el árbol. Se abre ajustado a la ventana; mientras esté en ese modo, se reajusta al cambiar su tamaño.
