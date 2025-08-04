from referee.game import PlayerColor, PlaceAction, Coord, constants, coord, pieces
from .pieces import _TEMPLATES
import random

EXPAND_LIMIT = 25

# internal board representation class
class Selfboard:

    # initiating the board
    def __init__(
        self,
        initial_player: PlayerColor = PlayerColor.RED
    ):
        self.turn_color = initial_player
        self.state = {}
        for r in range(constants.BOARD_N):
            for c in range(constants.BOARD_N):

                self.state[Coord(r,c)] = None
        self.turn_count = 0

    # visual representation of the board
    def render(self, use_color: bool=False, use_unicode: bool=False):

        def apply_ansi(str, bold=True, color=None):
            bold_code = "\033[1m" if bold else ""
            color_code = ""
            if color == "r":
                color_code = "\033[31m"
            if color == "b":
                color_code = "\033[34m"
            return f"{bold_code}{color_code}{str}\033[0m"

        output = ""
        for r in range(constants.BOARD_N):
            for c in range(constants.BOARD_N):

                if self.state[Coord(r, c)] != None:
                    color = self.state[Coord(r, c)]
                    color = "r" if color == PlayerColor.RED else "b"
                    text = f"{color}"
                    if use_color:
                        output += apply_ansi(text, color=color, bold=False)
                    else:
                        output += text
                else:
                    output += "."

                output += " "
            output += "\n"
        return output
    
    # changing the board based on an applied action
    def apply_action(self, action: PlaceAction):

        for coords in action.coords:

            self.state[coords] = self.turn_color

        self._resolve_place_action(action)

        if self.turn_color == PlayerColor.RED:
            self.turn_color = PlayerColor.BLUE
        else:
            self.turn_color = PlayerColor.RED

        self.turn_count += 1

    # clears a full column
    def _resolve_place_action(self, action: PlaceAction):

        coords_with_piece = action.coords
        min_r = min(c.r for c in action.coords)
        max_r = max(c.r for c in action.coords)
        min_c = min(c.c for c in action.coords)
        max_c = max(c.c for c in action.coords)

        remove_r_coords = [
            Coord(r, c)
            for r in range(min_r, max_r + 1)
            for c in range(constants.BOARD_N)
            if all(self.state[Coord(r, c)] != None for c in range(constants.BOARD_N))
        ]
        remove_c_coords = [
            Coord(r, c)
            for r in range(constants.BOARD_N)
            for c in range(min_c, max_c + 1)
            if all(self.state[Coord(r, c)] != None for r in range(constants.BOARD_N))

        ]

        for coords in remove_r_coords + remove_c_coords:
            self.state[coords] = None

# places a specific piece with the argument as its topleft origin
def vecpiece_to_action(origin: Coord, piece: pieces.PieceType):
    ac = []
    for vec in _TEMPLATES[piece]:
       ac.append(origin + vec)
       
    return PlaceAction(ac[0], ac[1], ac[2], ac[3])

# returns list of every coordinate with the same color as the argument passed
def find_color_cell(board: Selfboard, color: PlayerColor):

    color_list = []

    for i in range(constants.BOARD_N):
        for j in range(constants.BOARD_N):
            cell = board.state[Coord(i,j)]      
            if cell == color:
                color_list.append(Coord(i,j))

    return color_list

# returns list of every empty coordinate on the board
def find_empty_cells(board: Selfboard):

    empty_list = []

    for i in range(constants.BOARD_N):
        for j in range(constants.BOARD_N):
            cell = board.state[Coord(i,j)]     
            if cell == None:
                empty_list.append(Coord(i,j))

    return empty_list

# checks if all coordinates of the target action are empty
def check_empty_action(board: Selfboard, action: PlaceAction):

    for coord in action.coords:
        cell = board.state[coord]
        if cell != None:
            return False
        
    return True

# returns list of directly adjacent empty coordinates from the passed argument
def find_free_adj(board: Selfboard, origin: Coord):

    directions = [coord.Direction.Down.value,
                 coord.Direction.Up.value,
                 coord.Direction.Left.value,
                 coord.Direction.Right.value]

    freeadj = []
    for dir in directions:
        cell = board.state[(origin.__add__(dir))]
        if cell == None:
            freeadj.append(origin.__add__(dir))

    return freeadj

# returns list of empty cells that are directly adjacent to color cells
def find_free_adj_color(board: Selfboard, color: PlayerColor):

    color_list = find_color_cell(board, color)

    free_adj_color = []
    for origin in color_list:
        free_adj_color = free_adj_color + find_free_adj(board, origin)

    return free_adj_color

# checks if the down and right coordinates from the origin are colored
# if they are, it is an impossible topleft origin
def check_botright(board: Selfboard, origin: Coord):

    bot = board.state[(origin.__add__(coord.Direction.Down.value))]
    right = board.state[(origin.__add__(coord.Direction.Right.value))]

    if bot != None and right != None:
        return False  
    return True

# simplified version of find_all_actions that terminates after finding a single random action
def find_random_action(board: Selfboard, color: PlayerColor):

    cell2check = find_empty_cells(board)
    freeadj_cells = find_free_adj_color(board, color)
    piece_list = list(_TEMPLATES)

    len_piece = len(piece_list)
    len_cell = len(cell2check)

    # a 2d array for each possible origin and its list of possible pieces
    cellsexpand =  [[piece for piece in piece_list] for y in range(len_cell)]
    max_no_moves = len_piece * len_cell

    i = 0
    actions = []

    while i != max_no_moves and len(actions) < EXPAND_LIMIT and len_cell:
        
        index = random.choice(range(len_cell))
        cell = cell2check[index]
        cell_pieces = cellsexpand[index]

        # all pieces of this array have been tried
        # or it is an impossible origin
        if not cell_pieces or check_botright(board, cell) == False:
            cellsexpand.remove(cell_pieces)
            cell2check.remove(cell)
            len_cell -= 1
            continue

        piece = random.choice(cell_pieces)
        test_action = vecpiece_to_action(cell, piece)

        if not check_empty_action(board, test_action) or ((board.turn_count > 1) and not check_action(freeadj_cells, test_action)):
            # impossible, won't try it again
            cell_pieces.remove(piece)
            i += 1
            continue
        else:
           return test_action
    
    return None

# checks if the target action is connected to a current color cell on the board
def check_action(cell2check, action: PlaceAction):

    coords = action.coords
    for coord in coords:
        if coord in cell2check:
            return True
        
    return False

# returns a list of every possible action
def find_all_actions(board: Selfboard, color: PlayerColor):

    cell2check = find_empty_cells(board)
    freeadj_cells = find_free_adj_color(board, color)
    piece_list = list(_TEMPLATES)

    len_piece = len(piece_list)
    len_cell = len(cell2check)

    # a 2d array for each possible origin and its list of possible pieces
    cellsexpand =  [[piece for piece in piece_list] for y in range(len_cell)]
    max_no_moves = len_piece * len_cell

    i = 0
    actions = []
    while i != max_no_moves and len(actions) < EXPAND_LIMIT and len_cell:
        
        index = random.choice(range(len_cell))
        cell = cell2check[index]
        cell_pieces = cellsexpand[index]

        # all pieces of this array have been tried
        # or it is an impossible origin
        if not cell_pieces or check_botright(board, cell) == False:
            cellsexpand.remove(cell_pieces)
            cell2check.remove(cell)
            len_cell -= 1
            continue

        # remove the piece after trying
        piece = random.choice(cell_pieces)
        cell_pieces.remove(piece)
        i += 1

        test_action =  vecpiece_to_action(cell, piece)
        if not check_empty_action(board, test_action) or ((board.turn_count > 1) and not check_action(freeadj_cells, test_action)):
            continue
        actions.append(test_action)

    return actions