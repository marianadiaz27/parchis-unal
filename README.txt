Hi!
--------------------------------------------------
Introducción
--------------------------------------------------
Este documento describe detalladamente el proceso de desarrollo de un juego de Parqués, abarcando desde la concepción de la lógica del tablero hasta su integración con una interfaz gráfica mediante la biblioteca tkinter en Python. El objetivo es presentar una explicación minuciosa de cada parte del código, justificando las decisiones de diseño y las implementaciones realizadas. 

El juego se basa en:
   • Un tablero con 68 casillas externas.
   • Reglas para el movimiento de fichas.
   • Una pista interna de 8 casillas que marca el avance hacia la meta.
   • Reglas especiales como la salida de la cárcel (al obtener un 5 en el dado), la captura de fichas y la asignación de movimientos extra.

La integración con tkinter permite visualizar de forma gráfica los movimientos y el estado del juego, lo que resulta esencial para comprender el funcionamiento completo del sistema.

--------------------------------------------------
Configuración y Definición de Constantes
--------------------------------------------------
La primera etapa del proyecto consistió en definir las constantes utilizadas en todo el código, estableciendo los parámetros del juego y la estructura del tablero.

Dimensiones y Parámetros del Tablero:
   • BOARD_SIZE = 68  
     Indica el número total de casillas en el tablero externo, definiendo el recorrido circular de las fichas.
     
   • FINISH_TRACK_LENGTH = 8  
     Establece el número de casillas en la pista interna (índices 0 a 7), donde la casilla 7 representa la meta.

   • HOME_SIZE = 4  
     Cada equipo dispone de 4 fichas. El objetivo del juego es que todas las fichas lleguen a “casa” para ganar.

Definición de Equipos y Posiciones Especiales:
   • COLORS:  
     Los equipos se identifican por los colores: ["amarillas", "verdes", "rojas", "azules"].

   • SALIDAS:  
     Un diccionario que asocia cada color con la casilla de salida correspondiente (por ejemplo, para “amarillas” la salida es la casilla 4).

   • SEGUROS y SAFE_CELLS:  
     Se definen las casillas en las que las fichas están protegidas de ser capturadas.

   • SEGURO_LLEGADA:  
     Mapea cada color a la casilla que sirve como punto de transición hacia la pista interna.

Estas constantes son fundamentales para simular fielmente las reglas del Parqués y asegurar que la lógica del juego se comporte de forma coherente.

--------------------------------------------------
Modelado de la Lógica
--------------------------------------------------
La lógica del juego se organiza mediante clases que separan la representación del estado del juego de la interfaz gráfica.

1. Clase Piece:
   • Representa una ficha individual.
   • Cada ficha tiene un color, un identificador único, un estado (carcel, externo, interno, casa) y una posición.
   • Se implementa el método __repr__ para mostrar una representación sencilla (por ejemplo, “A0” para la primera ficha de un equipo).

2. Clase Team:
   • Agrupa todas las fichas de un equipo.
   • Métodos clave:
         - fichas_en_carcel(): Devuelve las fichas que están en la cárcel.
         - fichas_en_tablero(): Retorna las fichas en el tablero externo.
         - fichas_internas(): Obtiene las fichas en la pista interna.
         - fichas_movibles(): Une las fichas que se pueden mover en un turno.
         - todas_en_casa(): Verifica si el equipo ha ganado (todas las fichas en casa).

3. Clase Board:
   • Modela el tablero externo de 68 casillas, utilizando un diccionario donde cada clave es un número de casilla y el valor es una lista de fichas.
   • Métodos principales:
         - is_cell_available(cell): Verifica que la casilla no tenga más de 2 fichas.
         - add_piece(cell, piece): Agrega una ficha a la casilla, comprobando la disponibilidad.
         - remove_piece(cell, piece): Elimina una ficha de la casilla.
         - get_pieces(cell): Retorna la lista de fichas en una casilla determinada.
         - move_piece(from_cell, to_cell, piece): Mueve una ficha de una casilla a otra.

4. Clase Game:
   • Es el núcleo de la lógica del juego, coordinando todas las acciones: turnos, lanzamiento de dados, movimientos, capturas y asignación de movimientos extra.
   • Aspectos destacados:
         - Turnos y Orden: El orden se define a partir de una cadena (por ejemplo, “RBGY”), mapeada a los colores de los equipos; si falta alguno, se añade automáticamente.
         - Lanzamiento de Dados: Inicialmente se usaba roll_dice() para generar dos valores aleatorios (random.randint(1,6)), pero se ha modificado para permitir la entrada manual en modo desarrollador.
         - Movimiento de Fichas: Se implementan mover_ficha_externa() y mover_ficha_interna() para mover las fichas a lo largo del tablero y la pista interna.
         - Captura y Bonus: El método capturar_ficha() gestiona la captura de fichas, y agregar_bonus() junto a aplicar_bonus() asignan movimientos extra.
         - Gestión de Turnos: El método turno() coordina todo el proceso de un turno, incluyendo el manejo de dados, selección y movimiento de fichas, y la actualización de turnos.
         - Callback para Actualización de la UI: Permite notificar a la interfaz gráfica cada vez que se produce un cambio en el estado del juego.

--------------------------------------------------
Justificación y Desarrollo
--------------------------------------------------
El desafío principal fue integrar la lógica de consola con una interfaz gráfica en tiempo real. Para lograrlo se utilizaron hilos (threading), permitiendo que la lógica del juego se ejecute en un hilo separado y pueda usar input() sin bloquear la actualización de la interfaz.

La implementación de callbacks para actualizar la UI en cada cambio significativo (movimiento, captura, bonus, cambio de turno) fue crucial para mantener la representación gráfica actualizada.

La división del código en clases modulares (Piece, Team, Board, Game) facilita la depuración y el mantenimiento, garantizando que cada componente cumpla una función específica.

--------------------------------------------------
Integración con la Interfaz Gráfica
--------------------------------------------------
La interfaz se implementa con tkinter, utilizando un Canvas para dibujar el tablero y las fichas.

Aspectos clave:
   • Diseño del Tablero:  
     Se dibuja un tablero de 23x23 celdas, donde cada celda tiene un tamaño fijo (CELL_SIZE = 30 píxeles). La disposición se define mediante una cadena (grid_str) que, mediante un mapeo de colores (color_map), configura el fondo del tablero.

   • Funciones de Dibujo:
         - draw_board(canvas, grid): Dibuja el fondo del tablero.
         - draw_token(canvas, row, col, token_color, text=""): Dibuja las fichas en las posiciones adecuadas.

   • Actualización Continua:
     La función refresh() actualiza el Canvas cada 100 milisegundos, redibujando el tablero y las fichas según el estado actual del juego obtenido mediante game_state_updater().

   • Callback para Actualización:
     Se utiliza un callback (update_ui_callback) para notificar a la interfaz cuando la lógica del juego sufre cambios, permitiendo una actualización casi instantánea de la UI.

--------------------------------------------------
Comunicación entre Hilos y Ejecución Concurrente
--------------------------------------------------
Debido al uso de input() en la lógica del juego, esta se ejecuta en un hilo separado para evitar bloquear la interfaz gráfica. La sincronización entre el hilo de la lógica y el de la UI se gestiona mediante variables globales (por ejemplo, game_instance) y callbacks que actualizan el Canvas, garantizando que ambas partes trabajen de manera concurrente sin interferencias.

--------------------------------------------------
Modo Desarrollador
--------------------------------------------------
Para facilitar el proceso de depuración y prueba, se ha implementado un modo desarrollador que modifica el método de lanzamiento de dados. 

En el código original, el método roll_dice() utilizaba:
   d1 = random.randint(1,6)
   d2 = random.randint(1,6)

En modo desarrollador, estas líneas se comentan y se reemplazan por:
   d1 = int(input("Ingresa el valor del dado 1 (1-6): "))
   d2 = int(input("Ingresa el valor del dado 2 (1-6): "))

Este cambio permite que el usuario ingrese manualmente los valores de los dados, facilitando la simulación de situaciones específicas y la realización de pruebas.

--------------------------------------------------
Repositorio en GitHub
--------------------------------------------------
El código completo del juego se encuentra en el siguiente repositorio de GitHub:

   https://github.com/marianadiaz27/parchis-unal

--------------------------------------------------
Conclusiones
--------------------------------------------------
El desarrollo de este juego de Parqués representó un reto considerable al combinar una lógica basada en consola con una interfaz gráfica en tiempo real. Los aspectos más relevantes del proyecto incluyen:

1. La definición precisa de constantes y la configuración básica del tablero.
2. La creación de una arquitectura orientada a objetos (Piece, Team, Board, Game) que facilita la modularidad y el mantenimiento.
3. La implementación cuidadosa de las reglas de movimiento, capturas y bonus.
4. La integración de la lógica con tkinter mediante un Canvas y el uso de callbacks para actualizaciones en tiempo real.
5. La utilización de hilos para permitir que la lógica y la interfaz operen concurrentemente sin interferencias.

Este proyecto demuestra la viabilidad de combinar métodos tradicionales de entrada por consola con una interfaz gráfica interactiva, ofreciendo una experiencia visual que refleja fielmente el estado del juego.

-I'm dying.