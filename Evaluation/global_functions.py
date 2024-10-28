# Define the position representation as a dictionary in Python
pos = {
    'b': [["r", "-", "b", "-", "p", "-", "P", "R"],
          ["n", "-", "p", "-", "-", "P", "B", "N"],
          ["-", "-", "p", "-", "-", "-", "P", "-"],
          ["q", "-", "-", "p", "P", "B", "-", "Q"],
          ["k", "p", "-", "-", "P", "-", "-", "K"],
          ["b", "p", "-", "-", "-", "P", "-", "-"],
          ["n", "p", "-", "-", "-", "-", "P", "N"],
          ["r", "p", "-", "-", "-", "-", "P", "R"]],

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
    # Initialize an empty 8x8 board for the flipped position
    flipped_board = [["" for _ in range(8)] for _ in range(8)]

    # Flip the pieces by changing case and swapping files only
    for y in range(8):
        for x in range(8):
            piece = position['b'][y][x]  # Get the piece at (x, y)
            if piece != "-":  # Ignore empty squares
                if piece.isupper():
                    # Convert white to black and flip the file (x-axis)
                    flipped_board[y][7 - x] = piece.lower()
                else:
                    # Convert black to white and flip the file (x-axis)
                    flipped_board[y][7 - x] = piece.upper()
            else:
                flipped_board[y][7 - x] = "-"

    # Update castling rights (swap kingside/queenside for both sides)
    flipped_castling = [position['c'][2], position['c'][3], position['c'][0], position['c'][1]]

    # En passant remains unchanged (no need to flip horizontally)
    flipped_en_passant = position['e']

    # Flip the side to move
    flipped_side_to_move = not position['w']

    # Preserve move counts (these remain the same)
    flipped_move_counts = [position['m'][0], position['m'][1]]

    # Construct the flipped position dictionary
    flipped_position = {
        'b': flipped_board,
        'c': flipped_castling,
        'e': flipped_en_passant,
        'w': flipped_side_to_move,
        'm': flipped_move_counts
    }

    return flipped_position



def zero(*args):
    return 0


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


import chess

# Function to convert python-chess board into a flipped custom position dictionary
def board_to_position(board_to_convert: chess.Board):
    # Initialize an empty 8x8 board representation
    pos_board = [["-" for _ in range(8)] for _ in range(8)]

    # Fill the board with pieces from the python-chess board
    for square in chess.SQUARES:
        piece = board_to_convert.piece_at(square)
        if piece:
            rank = square % 8  # Flipping the rank
            file = 7 - (square // 8)  # Keeping the file the same
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
    return 8 - square['y']


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

    piece = board(position, square['x'], square['y']).upper()
    if "PNBRQK".find(piece) < 0:
        return 0


    color = 1
    if "PNBRQK".find(board(position, square['x'], square['y'])) < 0:
        color = -1

    for i in range(8):
        ix = (i + (i > 3)) % 3 - 1
        iy = int((i + (i > 3)) / 3) - 1
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
                if b == "q" \
                        or (b == "b" and ix * iy != 0) \
                        or (b == "r" and ix * iy == 0):
                    return abs(ix + iy * 3) * color
                if b != "-":
                    break
    return 0
