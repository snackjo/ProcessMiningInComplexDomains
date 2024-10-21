# Define the position representation as a dictionary in Python
pos = {
    'b': [["r", "-", "-", "p", "-", "-", "P", "-"],
          ["n", "-", "p", "-", "-", "-", "P", "-"],
          ["b", "-", "p", "-", "B", "P", "Q", "-"],
          ["q", "-", "p", "-", "P", "-", "-", "R"],
          ["-", "n", "p", "-", "P", "B", "-", "R"],
          ["r", "-", "p", "-", "P", "N", "-", "-"],
          ["k", "b", "p", "-", "-", "N", "P", "K"],
          ["-", "-", "p", "-", "-", "-", "P", "-"]],

    # Castling rights
    'c': [True, True, True, True],

    # En passant target square (None if not applicable)
    'e': None,

    # Side to move (True for white, False for black)
    'w': True,

    # Move counts (halfmove clock and fullmove number)
    'm': [2, 3]
}


# Function to get the board position at (x, y)
def board(position, x, y):
    if 0 <= x <= 7 and 0 <= y <= 7:
        return position['b'][x][y]
    return "x"


def colorflip(position):
    flipped_board = [["" for _ in range(8)] for _ in range(8)]
    for x in range(8):
        for y in range(8):
            flipped_piece = position['b'][7 - x][y]  # Flip ranks (x-axis), keep files (y-axis)
            color = flipped_piece.isupper()
            flipped_board[x][y] = flipped_piece.lower() if color else flipped_piece.upper()

    # Update castling rights (swap kingside/queenside for both sides)
    flipped_castling = [position['c'][2], position['c'][3], position['c'][0], position['c'][1]]

    # Update en passant (flip rank if en passant is available)
    flipped_en_passant = None if position['e'] is None else [7 - position['e'][0], position['e'][1]]

    # Flip the side to move
    flipped_side_to_move = not position['w']

    # Preserve move counts
    flipped_move_counts = [position['m'][0], position['m'][1]]

    return {
        'b': flipped_board,
        'c': flipped_castling,
        'e': flipped_en_passant,
        'w': flipped_side_to_move,
        'm': flipped_move_counts
    }




# Function to sum the result of applying a function to each board square
def sum_function(position, func, param=None):
    total_sum = 0
    for x in range(8):
        for y in range(8):
            total_sum += func(position, {'x': x, 'y': y}, param)
    return total_sum


def all_squares():
    return [{'x': x, 'y': y} for x in range(8) for y in range(8)]


import chess


def board_to_position(board_to_convert: chess.Board):
    # Initialize an empty 8x8 board representation
    pos_board = [["-" for _ in range(8)] for _ in range(8)]

    # Fill the board with pieces from the python-chess board
    for square in chess.SQUARES:
        piece = board_to_convert.piece_at(square)
        if piece:
            rank = 7 - (square // 8)  # Convert to rank in your format (0-indexed)
            file = square % 8  # Convert to file in your format (0-indexed)
            pos_board[rank][file] = piece.symbol()

    # Castling rights
    castling_rights = [
        board_to_convert.has_kingside_castling_rights(chess.WHITE),  # White kingside
        board_to_convert.has_queenside_castling_rights(chess.WHITE),  # White queenside
        board_to_convert.has_kingside_castling_rights(chess.BLACK),  # Black kingside
        board_to_convert.has_queenside_castling_rights(chess.BLACK)  # Black queenside
    ]

    # En passant target square (convert to None if not applicable)
    ep_square = board_to_convert.ep_square
    ep_square_pos = None if ep_square is None else (7 - (ep_square // 8), ep_square % 8)

    # Side to move (True for white, False for black)
    side_to_move = board_to_convert.turn

    # Move counts
    move_counts = [board_to_convert.halfmove_clock, board_to_convert.fullmove_number]

    # Construct the final pos dictionary
    position = {
        'b': pos_board,
        'c': castling_rights,
        'e': ep_square_pos,
        'w': side_to_move,
        'm': move_counts
    }

    return position


'''Helpers'''


def rank(position, square=None, param=None):
    if square is None:
        return sum_function(position, rank)
    return 8 - square['x']


'''King'''


def blockers_for_king(position, square=None, param=None):
    if square is None:
        return sum_function(position, blockers_for_king)

    if pinned_direction(colorflip(position), {'x': square['x'], 'y': 7 - square['y']}):
        return 1

    return 0


'''Attack'''


def pinned_direction(position, square=None):
    if square is None:
        return sum_function(position, pinned_direction)

    if "PNBRQK".find(board(position, square['x'], square['y']).upper()) < 0:
        return 0

    color = 1 if "PNBRQK".find(board(position, square['x'], square['y'])) >= 0 else -1

    for i in range(8):
        ix = (i + (i > 3)) % 3 - 1
        iy = ((i + (i > 3)) // 3) - 1
        king = False
        for d in range(1, 8):
            b = board(position, square['x'] + d * ix, square['y'] + d * iy)
            if b == "K":
                king = True
            if b != "-":
                break
        if king:
            for d in range(1, 8):
                b = board(position, square['x'] - d * ix, square['y'] - d * iy)
                if b == "q" or (b == "b" and ix * iy != 0) or (b == "r" and ix * iy == 0):
                    return abs(ix + iy * 3) * color
                if b != "-":
                    break
    return 0
