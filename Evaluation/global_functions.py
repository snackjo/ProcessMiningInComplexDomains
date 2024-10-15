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
def board(pos, x, y):
    if 0 <= x <= 7 and 0 <= y <= 7:
        return pos['b'][x][y]
    return "x"


# Function to colorflip the board (flip the board and pieces for the other side)
def colorflip(pos):
    flipped_board = [["" for _ in range(8)] for _ in range(8)]
    for x in range(8):
        for y in range(8):
            flipped_piece = pos['b'][x][7 - y]
            color = flipped_piece.isupper()
            flipped_board[x][y] = flipped_piece.lower() if color else flipped_piece.upper()

    # Update castling rights, en passant, and side to move
    return {
        'b': flipped_board,
        'c': [pos['c'][2], pos['c'][3], pos['c'][0], pos['c'][1]],
        'e': None if pos['e'] is None else [pos['e'][0], 7 - pos['e'][1]],
        'w': not pos['w'],
        'm': [pos['m'][0], pos['m'][1]]
    }


# Function to sum the result of applying a function to each board square
def sum_function(pos, func, param=None):
    total_sum = 0
    for x in range(8):
        for y in range(8):
            total_sum += func(pos, {'x': x, 'y': y}, param)
    return total_sum


def all_squares(position):
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
    pos = {
        'b': pos_board,
        'c': castling_rights,
        'e': ep_square_pos,
        'w': side_to_move,
        'm': move_counts
    }

    return pos