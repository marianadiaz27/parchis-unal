import threading
import tkinter as tk
import time
import random

# =============================================================================
# CONFIGURACIÓN Y CONSTANTES
# =============================================================================

BOARD_SIZE = 68
FINISH_TRACK_LENGTH = 8   # Casillas internas: índices 0 a 7; la posición 7 es “la llegada”
HOME_SIZE = 4             # Para ganar, todas las fichas deben llegar a la casa

COLORS = ["amarillas", "verdes", "rojas", "azules"]

SALIDAS = {
    "amarillas": 4,
    "verdes": 21,
    "rojas": 38,
    "azules": 55
}

SEGUROS = {
    "amarillas": [4, 11],
    "verdes": [21, 28],
    "rojas": [38, 45],
    "azules": [55, 62]
}
SAFE_CELLS = set([4, 11, 21, 28, 38, 45, 55, 62])

SEGURO_LLEGADA = {
    "amarillas": 67,
    "verdes": 16,
    "rojas": 33,
    "azules": 50
}

# =============================================================================
# CLASES DEL JUEGO
# =============================================================================

class Piece:
    def __init__(self, team, id):
        self.team = team      # Color del equipo
        self.id = id          # Identificador (0 a 3)
        self.state = "carcel" # "carcel", "externo", "interno", "casa"
        self.position = None  # Número de casilla (para externo) o índice (para interno)

    def __repr__(self):
        return f"{self.team[0].upper()}{self.id}"

class Team:
    def __init__(self, color):
        self.color = color
        self.pieces = [Piece(color, i) for i in range(HOME_SIZE)]
        self.internal = [None] * FINISH_TRACK_LENGTH
        self.home = []

    def fichas_en_carcel(self):
        return [p for p in self.pieces if p.state == "carcel"]

    def fichas_en_tablero(self):
        return [p for p in self.pieces if p.state == "externo"]

    def fichas_internas(self):
        return [p for p in self.pieces if p.state == "interno"]

    def fichas_movibles(self):
        return self.fichas_en_tablero() + self.fichas_internas()

    def todas_en_casa(self):
        return len(self.home) == HOME_SIZE

    def __repr__(self):
        return f"Equipo {self.color}"

class Board:
    def __init__(self):
        self.cells = {i: [] for i in range(1, BOARD_SIZE+1)}

    def is_cell_available(self, cell):
        return len(self.cells[cell]) < 2

    def add_piece(self, cell, piece):
        if self.is_cell_available(cell):
            self.cells[cell].append(piece)
        else:
            raise Exception(f"La casilla {cell} ya tiene 2 fichas.")

    def remove_piece(self, cell, piece):
        if piece in self.cells[cell]:
            self.cells[cell].remove(piece)

    def get_pieces(self, cell):
        return self.cells[cell]

    def move_piece(self, from_cell, to_cell, piece):
        self.remove_piece(from_cell, piece)
        self.add_piece(to_cell, piece)

    def __repr__(self):
        board_str = ""
        for i in range(1, BOARD_SIZE+1):
            if self.cells[i]:
                board_str += f"{i}:{self.cells[i]}  "
        return board_str

# =============================================================================
# CLASE PRINCIPAL DEL JUEGO
# =============================================================================

class Game:
    def __init__(self, turn_order):
        self.turn_order = []
        mapping = {"R": "rojas", "B": "azules", "G": "verdes", "Y": "amarillas"}
        for ch in turn_order.upper():
            if ch in mapping:
                self.turn_order.append(mapping[ch])
        for color in COLORS:
            if color not in self.turn_order:
                self.turn_order.append(color)
        self.teams = {color: Team(color) for color in COLORS}
        self.board = Board()
        self.turn_index = 0
        self.bonus_moves = {}
        self.doubles_count = {color: 0 for color in COLORS}
        # Función de callback para actualizar la UI (se asigna desde el hilo principal)
        self.update_callback = lambda: None

    def roll_dice(self):
        d1 = random.randint(1,6)
        d2 = random.randint(1,6)
        print(f"Dados: {d1} y {d2}")
        return d1, d2

    def start_turn(self, team_color):
        print(f"\nTurno de {team_color.upper()}")
        input_cmd = input("Escribe 'GO' para tirar los dados: ").strip().upper()
        if input_cmd != "GO":
            print("Comando no reconocido. Se omite el turno.")
            return None
        return self.roll_dice()

    def can_salir_de_carcel(self, dice):
        return 5 in dice

    def sacar_ficha_de_carcel(self, team):
        if not team.fichas_en_carcel():
            return None
        salida = SALIDAS[team.color]
        if not self.board.is_cell_available(salida):
            print(f"La salida ({salida}) del equipo {team.color} está llena.")
            return None
        ficha = team.fichas_en_carcel()[0]
        ficha.state = "externo"
        ficha.position = salida
        self.board.add_piece(salida, ficha)
        print(f"{ficha} sale de la cárcel a la casilla {salida}.")
        self.update_callback()
        return ficha

    def mover_ficha_externa(self, team, ficha, pasos):
        pos_inicial = ficha.position
        nueva_pos = pos_inicial + pasos
        if nueva_pos > BOARD_SIZE:
            nueva_pos = nueva_pos - BOARD_SIZE
        seguro_llegada = SEGURO_LLEGADA[team.color]
        if self._pasa_seguro(pos_inicial, nueva_pos, seguro_llegada, pasos):
            pasos_internos = nueva_pos - seguro_llegada if nueva_pos > seguro_llegada else (pasos - (BOARD_SIZE - pos_inicial + seguro_llegada))
            if pasos_internos < FINISH_TRACK_LENGTH:
                ficha.state = "interno"
                ficha.position = pasos_internos
                self.board.remove_piece(pos_inicial, ficha)
                print(f"{ficha} entra a la pista interna en la posición {pasos_internos}.")
            elif pasos_internos == FINISH_TRACK_LENGTH - 1:
                ficha.state = "casa"
                ficha.position = None
                self.board.remove_piece(pos_inicial, ficha)
                team.home.append(ficha)
                print(f"{ficha} ha llegado a la casa.")
                self.agregar_bonus(team.color, 10)
            else:
                print("Movimiento excede la pista interna; movimiento no permitido.")
                return False
        else:
            if not self.board.is_cell_available(nueva_pos):
                print(f"La casilla {nueva_pos} está llena. No se puede mover {ficha}.")
                return False
            piezas_destino = self.board.get_pieces(nueva_pos)
            if piezas_destino:
                if all(p.team == team.color for p in piezas_destino):
                    print(f"Casilla {nueva_pos} tiene bloqueo propio. No se permite mover {ficha}.")
                    return False
                else:
                    if nueva_pos in SAFE_CELLS:
                        print(f"La casilla {nueva_pos} es segura; no se puede capturar. Movimiento no permitido.")
                        return False
                    else:
                        for p in piezas_destino.copy():
                            if p.team != team.color:
                                self.capturar_ficha(p)
                                print(f"{ficha} captura a {p} en la casilla {nueva_pos}.")
                                self.agregar_bonus(team.color, 20)
            self.board.remove_piece(pos_inicial, ficha)
            self.board.add_piece(nueva_pos, ficha)
            ficha.position = nueva_pos
            print(f"{ficha} se mueve de la casilla {pos_inicial} a la {nueva_pos}.")
        self.update_callback()  # Notifica la actualización a la UI
        return True

    def mover_ficha_interna(self, team, ficha, pasos):
        pos_inicial = ficha.position
        nueva_pos = pos_inicial + pasos
        if nueva_pos < FINISH_TRACK_LENGTH:
            ficha.position = nueva_pos
            print(f"{ficha} avanza en pista interna de {pos_inicial} a {nueva_pos}.")
        elif nueva_pos == FINISH_TRACK_LENGTH - 1:
            ficha.state = "casa"
            ficha.position = None
            team.home.append(ficha)
            print(f"{ficha} ha llegado a la casa desde la pista interna.")
            self.agregar_bonus(team.color, 10)
        else:
            print("Movimiento excede la pista interna; movimiento no permitido.")
            return False
        self.update_callback()  # Notifica la actualización
        return True

    def _pasa_seguro(self, pos_inicial, nueva_pos, seguro, pasos):
        if pos_inicial <= nueva_pos:
            return pos_inicial < seguro <= nueva_pos
        else:
            return pos_inicial < seguro + BOARD_SIZE or seguro <= nueva_pos

    def capturar_ficha(self, ficha):
        team = self.teams[ficha.team]
        if ficha.state == "externo":
            self.board.remove_piece(ficha.position, ficha)
        ficha.state = "carcel"
        ficha.position = None
        print(f"{ficha} es capturada y regresa a la cárcel de {ficha.team}.")
        self.update_callback()

    def agregar_bonus(self, team_color, movimientos):
        if team_color in self.bonus_moves:
            self.bonus_moves[team_color] += movimientos
        else:
            self.bonus_moves[team_color] = movimientos
        print(f"Se otorgan {movimientos} movimientos extra para el equipo {team_color}.")
        self.update_callback()

    def aplicar_bonus(self, team):
        if self.bonus_moves.get(team.color, 0) > 0:
            print(f"El equipo {team.color} tiene {self.bonus_moves[team.color]} movimientos extra pendientes.")
            while self.bonus_moves[team.color] > 0:
                print(f"Movimientos bonus restantes: {self.bonus_moves[team.color]}")
                movibles = team.fichas_movibles()
                if not movibles:
                    print("No hay fichas que se puedan mover con bonus.")
                    break
                print("Fichas disponibles para bonus:", movibles)
                try:
                    ficha_id = int(input("Selecciona el id de la ficha a mover (número entero): "))
                except:
                    print("Entrada inválida. Se omite bonus.")
                    break
                ficha = next((p for p in movibles if p.id == ficha_id), None)
                if ficha is None:
                    print("Ficha no encontrada.")
                    continue
                try:
                    pasos = int(input("¿Cuántos pasos mover? (1 o más): "))
                except:
                    print("Entrada inválida.")
                    continue
                if pasos > self.bonus_moves[team.color]:
                    print("No puede mover más pasos de los bonus disponibles.")
                    continue
                if ficha.state == "externo":
                    if self.mover_ficha_externa(team, ficha, pasos):
                        self.bonus_moves[team.color] -= pasos
                elif ficha.state == "interno":
                    if self.mover_ficha_interna(team, ficha, pasos):
                        self.bonus_moves[team.color] -= pasos
                else:
                    print("La ficha no se puede mover.")
            if self.bonus_moves.get(team.color, 0) == 0:
                del self.bonus_moves[team.color]
        self.update_callback()

    def turno(self):
        equipo_actual = self.teams[self.turn_order[self.turn_index]]
        if self.bonus_moves.get(equipo_actual.color, 0) > 0:
            self.aplicar_bonus(equipo_actual)
        dados = self.start_turn(equipo_actual.color)
        if dados is None:
            self.siguiente_turno()
            return

        d1, d2 = dados
        total = d1 + d2

        if d1 == d2:
            self.doubles_count[equipo_actual.color] += 1
            extra_turn = True
            print("¡Dados dobles! Obtienes un turno extra.")
        else:
            self.doubles_count[equipo_actual.color] = 0
            extra_turn = False

        if self.doubles_count[equipo_actual.color] == 3:
            movibles = equipo_actual.fichas_movibles()
            if movibles:
                ficha_castigo = movibles[0]
                print(f"Tres dobles consecutivos. {ficha_castigo} es enviada a la cárcel.")
                self.capturar_ficha(ficha_castigo)
            self.doubles_count[equipo_actual.color] = 0
            self.siguiente_turno()
            return

        if (len(equipo_actual.fichas_en_carcel()) == HOME_SIZE and not self.can_salir_de_carcel((d1, d2))) or \
           (not equipo_actual.fichas_movibles() and not self.can_salir_de_carcel((d1, d2))):
            print(f"No hay movimientos posibles para el equipo {equipo_actual.color}. Se salta el turno.")
            self.siguiente_turno(extra_turn)
            return

        if self.can_salir_de_carcel((d1, d2)) and equipo_actual.fichas_en_carcel():
            opcion = input("¿Deseas sacar una ficha de la cárcel? (s/n): ").strip().lower()
            if opcion == "s":
                self.sacar_ficha_de_carcel(equipo_actual)
                otro_valor = d2 if d1 == 5 else d1
                mover = input(f"¿Deseas mover otra ficha {otro_valor} pasos? (s/n): ").strip().lower()
                if mover == "s":
                    self.seleccionar_y_mover(equipo_actual, otro_valor)
                self.siguiente_turno(extra_turn)
                return

        self.seleccionar_y_mover(equipo_actual, total)
        self.siguiente_turno(extra_turn)

    def seleccionar_y_mover(self, team, pasos):
        movibles = team.fichas_movibles()
        if not movibles:
            print("No hay fichas movibles.")
            return
        print("Fichas movibles:", movibles)
        try:
            ficha_id = int(input("Selecciona el id de la ficha a mover: "))
        except:
            print("Entrada inválida. Se omite movimiento.")
            return
        ficha = next((p for p in movibles if p.id == ficha_id), None)
        if ficha is None:
            print("Ficha no encontrada.")
            return
        if ficha.state == "externo":
            self.mover_ficha_externa(team, ficha, pasos)
        elif ficha.state == "interno":
            self.mover_ficha_interna(team, ficha, pasos)

    def siguiente_turno(self, turno_extra=False):
        if not turno_extra:
            self.turn_index = (self.turn_index + 1) % len(self.turn_order)
        self.update_callback()

    def juego_terminado(self):
        for color, team in self.teams.items():
            if team.todas_en_casa():
                print(f"\n¡El equipo {color.upper()} ha ganado!")
                return True
        return False

    def estado_tablero(self):
        print("\nEstado del tablero externo:")
        print(self.board)
        for color, team in self.teams.items():
            print(f"{color.upper()} - Carcel: {team.fichas_en_carcel()}, En tablero: {team.fichas_en_tablero()}, Pista interna: {team.fichas_internas()}, Casa: {team.home}")

    def run(self):
        print("Bienvenido al juego de Parqués")
        while not self.juego_terminado():
            self.estado_tablero()
            self.turno()
        print("¡Fin del juego!")
        self.update_callback()

# =============================================================================
# INTERFAZ
# =============================================================================

# Mapeo de posiciones (para el tablero externo)
CELL_SIZE = 30
color_map = {
    "W": "#D3D3D3",
    "HW": "#A9A9A9",
    "Y": "#FFFF00",
    "BR": "#FF00FF",
    "B": "#0000FF",
    "GO": "#800080",
    "HY": "#FFFF66",
    "HG": "#66FF66",
    "HB": "#66CCFF",
    "HR": "#FF6666",
    "G": "#008000",
    "R": "#FF0000"
}

grid_str = """
W	W	W	W	W	W	HW	Y	Y	Y	BR	BR	BR	B	B	B	HW	W	W	W	W	W	W
W	W	W	W	W	W	HW	Y	Y	Y	HY	HY	HY	B	B	B	HW	W	W	W	W	W	W
W	W	W	W	W	W	HW	Y	Y	Y	HY	HY	HY	B	B	B	HW	W	W	W	W	W	W
W	W	W	W	W	W	HW	Y	Y	Y	HY	HY	HY	B	B	B	HW	W	W	W	W	W	W
W	W	W	W	W	W	HW	GO	GO	GO	HY	HY	HY	BR	BR	BR	HW	W	W	W	W	W	W
W	W	W	W	W	W	HW	Y	Y	Y	HY	HY	HY	B	B	B	HW	W	W	W	W	W	W
HW	HW	HW	HW	HW	HW	HW	Y	Y	Y	HY	HY	HY	B	B	B	HW	HW	HW	HW	HW	HW	HW
Y	Y	Y	Y	BR	Y	Y	Y	Y	Y	HY	HY	HY	B	B	B	B	B	GO	B	B	B	B
Y	Y	Y	Y	BR	Y	Y	Y	Y	HW	Y	Y	Y	HW	B	B	B	B	GO	B	B	B	B
Y	Y	Y	Y	BR	Y	Y	Y	HW	W	W	W	W	W	HW	B	B	B	GO	B	B	B	B
BR	HG	HG	HG	HG	HG	HG	HG	G	W	HW	HW	HW	W	B	HB	HB	HB	HB	HB	HB	HB	BR
BR	HG	HG	HG	HG	HG	HG	HG	G	W	HW	W	HW	W	B	HB	HB	HB	HB	HB	HB	HB	BR
BR	HG	HG	HG	HG	HG	HG	HG	G	W	HW	HW	HW	W	B	HB	HB	HB	HB	HB	HB	HB	BR
G	G	G	G	GO	G	G	G	HW	W	W	W	W	W	HW	R	R	R	BR	R	R	R	R
G	G	G	G	GO	G	G	G	G	HW	R	R	R	HW	R	R	R	R	BR	R	R	R	R
G	G	G	G	GO	G	G	G	G	G	HR	HR	HR	R	R	R	R	R	BR	R	R	R	R
HW	HW	HW	HW	HW	HW	HW	G	G	G	HR	HR	HR	R	R	R	HW	HW	HW	HW	HW	HW	HW
W	W	W	W	W	W	HW	G	G	G	HR	HR	HR	R	R	R	HW	W	W	W	W	W	W
W	W	W	W	W	W	HW	BR	BR	BR	HR	HR	HR	GO	GO	GO	HW	W	W	W	W	W	W
W	W	W	W	W	W	HW	G	G	G	HR	HR	HR	R	R	R	HW	W	W	W	W	W	W
W	W	W	W	W	W	HW	G	G	G	HR	HR	HR	R	R	R	HW	W	W	W	W	W	W
W	W	W	W	W	W	HW	G	G	G	HR	HR	HR	R   R   R   HW  W   W   W   W   W   W
W	W	W	W	W	W	HW	G	G	G	BR	BR	BR	R	R	R	HW	W	W	W	W	W	W
"""  # La cuadrícula puede ajustarse según tus necesidades

def parse_grid(grid_str):
    grid = []
    for line in grid_str.strip().splitlines():
        row = [cell for cell in line.split() if cell]
        grid.append(row)
    return grid

board_grid = parse_grid(grid_str)

external_positions = {
    0: (0,8), 1: (1,8), 2: (2,8), 3: (3,8), 4: (4,8), 5: (5,8), 6: (6,8), 7: (7,8),
    8: (8,7), 9: (8,6), 10: (8,5), 11: (8,4), 12: (8,3), 13: (8,2), 14: (8,1), 15: (8,0),
    16: (11,0), 17: (14,0), 18: (14,1), 19: (14,2), 20: (14,3), 21: (14,4), 22: (14,5),
    23: (14,6), 24: (14,7), 25: (15,8), 26: (16,8), 27: (17,8), 28: (18,8), 29: (19,8),
    30: (20,8), 31: (21,8), 32: (22,8), 33: (22,11), 34: (22,14), 35: (21,14), 36: (20,14),
    37: (19,14), 38: (18,14), 39: (17,14), 40: (16,14), 41: (15,14), 42: (14,15), 43: (14,16),
    44: (14,17), 45: (14,18), 46: (14,19), 47: (14,20), 48: (14,21), 49: (14,22), 50: (11,22),
    51: (8,22), 52: (8,21), 53: (8,20), 54: (8,19), 55: (8,18), 56: (8,17), 57: (8,16),
    58: (8,15), 59: (7,14), 60: (6,14), 61: (5,14), 62: (4,14), 63: (3,14), 64: (2,14),
    65: (1,14), 66: (0,14), 67: (0,11)
}

internal_positions = {
    "amarillas": [(11,1), (11,2), (11,3), (11,4), (11,5), (11,6), (11,7), (11,8)],
    "verdes":    [(1,11), (2,11), (3,11), (4,11), (5,11), (6,11), (7,11), (8,11)],
    "rojas":     [(11,21), (11,20), (11,19), (11,18), (11,17), (11,16), (11,15), (11,14)],
    "azules":    [(21,11), (20,11), (19,11), (18,11), (17,11), (16,11), (15,11), (14,11)]
}

jail_positions = {
    "amarillas": [(2,2), (3,2), (2,3), (3,3)],
    "verdes":    [(19,2), (20,2), (19,3), (20,3)],
    "rojas":     [(19,19), (20,19), (19,20), (20,20)],
    "azules":    [(2,19), (3,19), (2,20), (3,20)]
}

team_token_colors = {
    "amarillas": "#FFFF00",
    "verdes": "#008000",
    "rojas": "#FF0000",
    "azules": "#0000FF"
}

def draw_board(canvas, grid):
    for i, row in enumerate(grid):
        for j, cell in enumerate(row):
            x1 = j * CELL_SIZE
            y1 = i * CELL_SIZE
            x2 = x1 + CELL_SIZE
            y2 = y1 + CELL_SIZE
            fill_color = color_map.get(cell, "#FFFFFF")
            canvas.create_rectangle(x1, y1, x2, y2, fill=fill_color, outline="black")

def draw_token(canvas, row, col, token_color, text=""):
    pad = 4
    x1 = col * CELL_SIZE + pad
    y1 = row * CELL_SIZE + pad
    x2 = (col + 1) * CELL_SIZE - pad
    y2 = (row + 1) * CELL_SIZE - pad
    canvas.create_oval(x1, y1, x2, y2, fill=token_color, outline="black")
    if text:
        canvas.create_text((x1+x2)//2, (y1+y2)//2, text=text, fill="white", font=("Arial", 10, "bold"))

# Función de refresco de la interfaz; se llama periódicamente
def run_interface(game_state_updater):
    root = tk.Tk()
    root.title("Tablero de Parqués")
    canvas_width = len(board_grid[0]) * CELL_SIZE
    canvas_height = len(board_grid) * CELL_SIZE
    canvas = tk.Canvas(root, width=canvas_width, height=canvas_height)
    canvas.pack()

    def refresh():
        canvas.delete("all")
        draw_board(canvas, board_grid)
        state = game_state_updater()
        for token in state.get("external", []):
            row, col, team, label = token
            draw_token(canvas, row, col, team_token_colors[team], text=label)
        for token in state.get("internal", []):
            row, col, team, label = token
            draw_token(canvas, row, col, team_token_colors[team], text=label)
        for token in state.get("jail", []):
            row, col, team, label = token
            draw_token(canvas, row, col, team_token_colors[team], text=label)
        root.after(100, refresh)

    refresh()

    # Configuramos la función de callback para actualización desde el hilo del juego.
    global update_ui_callback
    update_ui_callback = lambda: root.event_generate("<<Refresh>>")
    root.bind("<<Refresh>>", lambda e: refresh())

    root.mainloop()

def run_game():
    print("Bienvenido al juego de Parqués (consola)")
    orden = input("Orden de turnos (ejemplo: RBGY): ")
    juego = Game(orden)
    global game_instance
    game_instance = juego
    # Asignamos el callback de actualización para que se llame en cada movimiento.
    juego.update_callback = lambda: None  # Lo actualizará la interfaz a través de update_ui_callback
    while not juego.juego_terminado():
        juego.estado_tablero()
        juego.turno()
        time.sleep(0.1)
    print("¡Fin del juego!")
    update_ui_callback()

def game_state_updater():
    if game_instance is None:
        return {"external": [], "internal": [], "jail": []}
    state = {"external": [], "internal": [], "jail": []}
    for color, team in game_instance.teams.items():
        for ficha in team.fichas_en_tablero():
            pos = ficha.position
            if pos in external_positions:
                row, col = external_positions[pos]
                state["external"].append((row, col, color, ficha.__repr__()))
        for ficha in team.fichas_internas():
            idx = ficha.position
            row, col = internal_positions[color][idx]
            state["internal"].append((row, col, color, ficha.__repr__()))
        for ficha in team.fichas_en_carcel():
            pos = jail_positions[color][0]
            state["jail"].append((pos[0], pos[1], color, ficha.__repr__()))
    return state

# Variables globales
game_instance = None
update_ui_callback = lambda: None

if __name__ == "__main__":
    # Se ejecuta la lógica del juego en un hilo separado (usa input() en consola)
    def game_thread():
        global game_instance
        orden = input("Orden de turnos (ejemplo: RBGY): ")
        game_instance = Game(orden)
        # Configuramos el callback para actualizar la UI; aquí se invoca la función global
        game_instance.update_callback = lambda: update_ui_callback()
        game_instance.run()
    t = threading.Thread(target=game_thread)
    t.daemon = True
    t.start()

    run_interface(game_state_updater)
