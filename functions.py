import inspect
import re
import time
from copy import copy
from typing import Any

import chess.engine
import chess.pgn
from chess import Board
from chess.pgn import GameNode

from Evaluation.attack import *
from Evaluation.global_functions import *
from Evaluation.helpers import *
from Evaluation.imbalance import *
from Evaluation.king import *
from Evaluation.main_evaluation import *
from Evaluation.material import *
from Evaluation.mobility import *
from Evaluation.passed_pawns import *
from Evaluation.pawns import *
from Evaluation.pieces import *
from Evaluation.space import *
from Evaluation.threats import *
from evaluation_code import get_dynamic_evaluation_code
import pm4py
import pandas as pd
from pm4py.objects.log.obj import EventLog, Trace, Event
from pm4py.objects.log.exporter.xes import exporter as xes_exporter
from pm4py.util.xes_constants import DEFAULT_NAME_KEY
from datetime import datetime
from HttpRequests.chess_api import ChessAPI
from pm4py.objects.log.importer.xes import importer as xes_importer
import zstandard as zstd

from tagger_module.mytagger import cook_positions
from tagger_module.tagger import read
import copy
import random

def extract_sample_from_csv(start = 0, end = 130000):
    input_file = 'lichess_db_puzzle.csv.zst'
    output_file = 'lichess_db_puzzle.csv'

    with open(input_file, 'rb') as f_in, open(output_file, 'wb') as f_out:
        dctx = zstd.ZstdDecompressor()
        with dctx.stream_reader(f_in) as reader:
            while True:
                chunk = reader.read(16384)
                if not chunk:
                    break
                f_out.write(chunk)

    df = pd.read_csv(output_file)

    sample = df.iloc[start:end]

    sample.to_csv(f'{start}_{end}_puzzles.csv', index=False)

def get_engine():
    return chess.engine.SimpleEngine.popen_uci(
        r"C:\Users\carlj\Documents\stockfish\stockfish\stockfish-windows-x86-64-avx2.exe")

# USE CASE 3
def generate_puzzle_move_log(file_path="Data/0_10000_puzzles.csv", existing_xes_path=None, elo_limit=0):
    puzzles = pd.read_csv(file_path)
    game_objects = []
    for _, row in puzzles.iterrows():
        if row["Rating"] < elo_limit:
            continue
        fen = row['FEN']
        moves_str = row['Moves']
        game = create_game_from_fen_and_moves(fen, moves_str)
        position_tags = cook_positions(read({
            "_id": row["PuzzleId"],
            "fen": row["FEN"],
            "line": row["Moves"],
            "cp": 999999998
        }))
        game.headers["PuzzleId"] = row['PuzzleId']
        game.headers["Rating"] = str(row['Rating'])
        game.headers["Themes"] = row['Themes']
        game.headers["GameUrl"] = row['GameUrl']

        game_objects.append((position_tags, game))

    output_path = "event_log_" + file_path[file_path.find("/") + 1:]
    output_path = output_path.replace(".csv", ".xes")
    data = get_dynamic_evaluation_code()

    if existing_xes_path is None:
        print("No existing XES file path provided. Creating a new event log.")
        event_log = EventLog()
    else:
        try:
            event_log = xes_importer.apply(existing_xes_path)
            print(f"Loaded existing event log with {len(event_log)} traces.")
        except FileNotFoundError:
            print(f"File {existing_xes_path} not found. Creating a new event log.")
            event_log = EventLog()
    case_id = len(event_log) + 1
    print(f'Processing {len(game_objects)} games')
    game_num = 0

    for position_tags, game in game_objects:
        print(f'Processing game {game_num}')
        game_num += 1
        start = time.time()
        result = []

        if position_tags:
            for move_to_find, type_of_move in position_tags:
                index = -1
                for i, move in enumerate(game.mainline_moves()):
                    if move == move_to_find:
                        index = i
                        break
                if index != -1:
                    result.append((index, type_of_move))

        if result:
            max_value = max(t[0] for t in result)
            unique_first_elements = {t[0] for t in result}
            move_count = len(list(game.mainline_moves()))
            if (move_count - 1) == max_value:
                move_count += 1
            if len(unique_first_elements) < ((move_count/2) - 1):
                end = time.time()
                print(f"Continuing Game {case_id} in {end - start:.2f} seconds")
                continue
        else:
            continue

        game_events = process_puzzle_without_piece_bonus(game, data)

        trace = Trace()
        trace.attributes[DEFAULT_NAME_KEY] = f'case_{case_id}'
        trace.attributes["puzzle_id"] = game.headers["PuzzleId"]
        trace.attributes["rating_50"] = round(int(game.headers["Rating"]) / 50) * 50
        trace.attributes["rating_100"] = round(int(game.headers["Rating"]) / 100) * 100
        trace.attributes["rating_200"] = round(int(game.headers["Rating"]) / 200) * 200
        trace.attributes["themes"] = game.headers["Themes"]
        trace.attributes["game_url"] = game.headers["GameUrl"]

        # print(result)
        end_index = 0
        for i, event in enumerate(game_events, start=1):
            if i % 2 == 0:
                end_index = i
                moves = [move for idx, move in result if idx == i - 1]
                if moves:
                    selected_move = random.choice(moves)
                    trace.append(Event({
                        DEFAULT_NAME_KEY: f"move: {i}, {selected_move}",
                        "time:timestamp": event["Timestamp"],
                    }))
            else:
                trace.append(Event({
                    DEFAULT_NAME_KEY: f"state: {i}, {event["Activity"]}",
                    "time:timestamp": event["Timestamp"],
                }))
                end_index = i
        end_index += 1
        if end_index % 2 == 0:
            moves = [move for idx, move in result if idx == end_index - 1]
            if moves:
                selected_move = random.choice(moves)
                trace.append(Event({
                    DEFAULT_NAME_KEY: f"move: {end_index}, {selected_move}",
                }))
        event_log.append(trace)

        end = time.time()
        print(f"Processed Game {case_id} in {end - start:.2f} seconds")
        case_id += 1

    xes_exporter.apply(event_log, output_path)


def process_puzzle_without_piece_bonus(game, data):
    current_board = game.board()
    color = "black"
    if not current_board.turn:
        color = "white"
    item_sums, group_list = get_item_sums_and_group_list_puzzle(game, current_board, data)
    elem_list = [entry['elem'] for entry in group_list]

    game_events = []

    for i, item in enumerate(item_sums, start=1):
        activity = max(
            ((value, key) for value, key in zip(item, elem_list) if key not in {"piece_value_bonus", "psqt_bonus"}),
            key=lambda x: x[0]
        )
        if color == "black":
            activity = min(
                ((value, key) for value, key in zip(item, elem_list) if key not in {"piece_value_bonus", "psqt_bonus"}),
                key=lambda x: x[0]
            )

        activity_name = activity[1]
        if activity[0] != 0:
            game_events.append({
                'Timestamp': f'{datetime(2024, 1, 1, 12, i)}',
                'Activity': activity_name
            })

    return game_events


def create_game_from_fen_and_moves(fen, moves_str):
    board = chess.Board(fen)
    moves = moves_str.split()

    game = chess.pgn.Game()
    game.setup(board)
    node = game

    for move in moves:
        move_obj = board.parse_san(move)
        node = node.add_variation(move_obj)
        board.push(move_obj)

    return game


def call_with_param(func, position):
    sig = inspect.signature(func)

    kwargs = {}

    if 'replacement_func' in sig.parameters:
        kwargs['replacement_func'] = func

    return func(position, **kwargs)


def get_item_sums_and_group_list_puzzle(game, current_board, data):
    item_sums = []
    recent_items = []
    item_length = 50
    group_list = []

    for move_num, move in enumerate(list(game.mainline_moves())[:-1], start=1):
        current_board.push(move)

        group_list = get_group_list(board_to_position(current_board), data)

        item_third_elements = [{group['elem']: group['item'][2]} for group in group_list]
        recent_items.append(item_third_elements)
        item_length = len(item_third_elements)

        add_items(item_length, item_sums, recent_items)

    return item_sums, group_list


def get_group_list(position, data, king_danger_only=False):
    grouplist = []
    midindex = None
    endindex = None
    maincode = None

    for i, item in enumerate(data):
        if item['name'] == "Middle game evaluation":
            midindex = i
        elif item['name'] == "End game evaluation":
            endindex = i
        elif item['name'] == "Main evaluation":
            n = item['name'].lower().replace(" ", "_")
            maincode = globals().get(n)

    if midindex is None or endindex is None or maincode is None:
        return []

    for i, item in enumerate(data):
        n = item['name'].lower().replace(" ", "_")

        func = globals().get(n)
        if not func:
            print(f"Function {n} not found")
            continue

        if not (f"{n}(" in data[midindex]['code'] or f"{n}(" in data[endindex]['code']):
            continue

        code = item['code']
        list_items = []

        for j, item_j in enumerate(data):
            if not item_j.get('graph') or item_j.get('group') != item.get('group') or i == j:
                continue
            n2 = item_j['name'].lower().replace(" ", "_")
            code = re.sub(rf"\b{n2}\(", f"g-{n2}(", code)
            list_items.append(n2)

        if item.get('graph'):
            list_items.append(n)

        for n2 in list_items:
            if f"g-{n2}(" not in code and n2 != 'space':
                continue

            if king_danger_only and n2 != 'king_danger':
                continue

            try:
                eval_code = code.replace(f"g-{n2}(", f"{n2}(")
                eval_code = re.sub(r'g-[a-z_]+\(', "zero(", eval_code)

                local_vars = {"zero": zero, "colorflip": colorflip, "sum_function": sum_function}
                exec(eval_code, globals(), local_vars)
                eval_func = local_vars.get("eval_func")

                mw, mb, ew, eb = 0, 0, 0, 0
                if f"{n}(pos" in data[midindex]['code']:
                    mw = call_with_param(eval_func, position)
                if f"{n}(colorflip(pos)" in data[midindex]['code']:
                    mb = call_with_param(eval_func, colorflip(position))
                if f"{n}(pos" in data[endindex]['code']:
                    ew = call_with_param(eval_func, position)
                if f"{n}(colorflip(pos)" in data[endindex]['code']:
                    eb = call_with_param(eval_func, colorflip(position))

            except Exception as e:
                print(f"Error evaluating {n}: {e}")
                continue

            evals = [mw - mb, ew - eb]
            index = next((idx for idx, grp in enumerate(grouplist) if grp['elem'] == n2), -1)
            if index < 0:
                grouplist.append(
                    {"group": item['group'], "elem": n2, "item": evals, "hidden": False, "mc": position['m'][1]})
            else:
                grouplist[index]['item'][0] += evals[0]
                grouplist[index]['item'][1] += evals[1]

    grouplist.sort(key=lambda x: x['group'])

    for item in grouplist:
        item['item'].append(maincode(item['item'][0], item['item'][1], position) - maincode(0, 0, position))

    grouplist.append({
        "group": "Tempo",
        "elem": "tempo",
        "item": [maincode(0, 0, position), maincode(0, 0, position), maincode(0, 0, position)],
        "hidden": False,
        "mc": position['m'][1]
    })

    return grouplist


def add_items(item_length, item_sums, recent_items):
    if recent_items:
        elem_sum = [0] * len(recent_items[0])
        for item in recent_items:
            for i, elem in enumerate(item):
                elem_sum[i] += list(elem.values())[0]

        item_sums.append([sum_value / len(recent_items) for sum_value in elem_sum])
        recent_items.clear()
    else:
        item_sums.append([0] * item_length)


# USE CASE 1
def generate_fine_grained_event_log(pgn_path="Data/2017_May_italian_game_filtered_high_elo.pgn"):
    output_path = "event_log_" + pgn_path[pgn_path.find("/") + 1:]
    output_path = output_path.replace(".pgn", ".xes")
    event_log = EventLog()
    engine = get_engine()
    case_id = 0

    with open(pgn_path) as pgn:
        while True:
            game = chess.pgn.read_game(pgn)
            if game is None:
                break
            outcome, ending, game_events = process_game_fine_grained(game, case_id, 7, engine)
            trace = Trace()
            trace.attributes[DEFAULT_NAME_KEY] = f'case_{case_id}'
            trace.attributes["outcome"] = outcome
            if ending: trace.attributes["ending"] = ending
            for event in game_events:
                pm_event = Event({
                    DEFAULT_NAME_KEY: event["Activity"],
                    "time:timestamp": event["Timestamp"],
                })
                trace.append(pm_event)
            event_log.append(trace)

            case_id += 1

    xes_exporter.apply(event_log, output_path)
    engine.quit()



def process_game_fine_grained(game, case_id, start, engine):
    print(f"Processing Game {case_id}")
    current_board = game.board()
    result = game.headers['Result']
    ending = None
    if result == '1-0':
        outcome = 'White won'
    elif result == '0-1':
        outcome = 'Black won'
    else:
        outcome = 'Draw'
    moves = []
    for move in game.mainline():
        moves.append(move.move)
    for i in range(start):
        current_board.push(moves[i])
    moves = moves[start:len(moves)]

    game_events = []
    for move_num, move in enumerate(moves, start=start + 1):
        turn_str = "White_" if current_board.turn else "Black_"
        move_str = current_board.san(move)
        current_board.push(move)

        game_events.append({
            "Timestamp": f"move_{move_num}",
            "Activity": turn_str + move_str
        })

        info = engine.analyse(current_board, chess.engine.Limit(depth=16))
        overall_score = info['score'].white()
        if overall_score.is_mate() or abs(overall_score.score()) > 100 or abs(overall_score.score() < 10):
            break

    if outcome != 'Draw':
        if current_board.is_checkmate():
            ending = "Checkmate"
        else:
            ending = "Time/Forfeit"

    return outcome, ending, game_events

# USE CASE 2
def generate_coarse_event_log_xes(pgn_path="Data/2014_March_filtered_high_elo.pgn"):
    output_path = "event_log_" + pgn_path[pgn_path.find("/") + 1:]

    eco_mapping = get_eco_mapping()
    event_log = EventLog()
    case_id = 0

    with open(pgn_path) as pgn:
        while True:
            game = chess.pgn.read_game(pgn)
            if game is None or case_id == 10916:
                break
            outcome, opening, game_events, ending = create_game_event(game, case_id, eco_mapping)

            trace = Trace()
            trace.attributes[DEFAULT_NAME_KEY] = f'case_{case_id}'
            trace.attributes["outcome"] = outcome
            trace.attributes["opening"] = opening
            if ending: trace.attributes["ending"] = ending

            for event in game_events:
                pm_event = Event()
                pm_event[DEFAULT_NAME_KEY] = event['Activity']
                pm_event['time:timestamp'] = event['Timestamp']
                trace.append(pm_event)

            event_log.append(trace)
            case_id += 1

    xes_exporter.apply(event_log, output_path)


def create_game_event(game, case_id, eco_mapping):
    result = game.headers['Result']
    ending = None
    if result == '1-0':
        outcome = 'White won'
    elif result == '0-1':
        outcome = 'Black won'
    else:
        outcome = 'Draw'

    print(f"Processing game event {case_id}")
    eco = aggregate_eco(eco_mapping, game.headers['ECO'])
    game_events = [{
        'Timestamp': f'{datetime(2024, 1, 1, 12, 0)}',
        'Activity': eco,
    }]

    pawn_structures = []
    endgame_classifications = []
    current_board = game.board()
    for move in game.mainline_moves():
        current_board.push(move)

        current_structure = get_pawn_structure(current_board)
        if current_structure not in pawn_structures:
            pawn_structures.append(current_structure)

        current_endgame = get_endgame_classification(current_board)
        if current_endgame:
            if current_endgame not in endgame_classifications:
                endgame_classifications.append(current_endgame)

    if len(pawn_structures) > 1 and 'Other' in pawn_structures:
        pawn_structures.remove('Other')

    end_structure = 1
    for i, structure in enumerate(pawn_structures, start=1):
        if structure:
            game_events.append({
                'Timestamp': f'{datetime(2024, 1, 1, 12, i)}',
                'Activity': structure
            })
            end_structure = i + 1

    for i, classification in enumerate(endgame_classifications, start=end_structure):
        game_events.append({
            'Timestamp': f'{datetime(2024, 1, 1, 12, i)}',
            'Activity': classification
        })

    if outcome != 'Draw':
        if current_board.is_checkmate():
            ending = "Checkmate"
        else:
            ending = "Time/Forfeit"

    return outcome, game.headers['Opening'], game_events, ending


# OPENING
def aggregate_eco(eco_mapping, eco_code):
    for key in reversed(eco_mapping):
        if key <= eco_code:
            return key
    return "Unknown"


def get_eco_mapping():
    """
    From https://www.365chess.com/eco.php
    :return:
    eco mapping
    """
    return {
        "A00": "Polish (Sokolsky) opening",
        "A01": "Nimzovich-Larsen attack",
        "A02": "Bird's opening",
        "A04": "Reti opening",
        "A10": "English opening",
        "A40": "Queen's pawn",
        "A42": "Modern defence, Averbakh system",
        "A43": "Old Benoni defence",
        "A45": "Queen's pawn game",
        "A47": "Queen's Indian defence",
        "A48": "King's Indian, East Indian defence",
        "A50": "Queen's pawn game",
        "A51": "Budapest defence",
        "A53": "Old Indian defence",
        "A56": "Benoni defence",
        "A57": "Benko gambit",
        "A60": "Benoni defence",
        "A80": "Dutch",
        "B00": "King's pawn opening",
        "B01": "Scandinavian (centre counter) defence",
        "B02": "Alekhine's defence",
        "B06": "Robatsch (modern) defence",
        "B07": "Pirc defence",
        "B10": "Caro-Kann defence",
        "B20": "Sicilian defence",
        "C00": "French defence",
        "C20": "King's pawn game",
        "C21": "Centre game",
        "C23": "Bishop's opening",
        "C25": "Vienna game",
        "C30": "King's gambit",
        "C40": "King's knight opening",
        "C41": "Philidor's defence",
        "C42": "Petrov's defence",
        "C44": "King's pawn game",
        "C45": "Scotch game",
        "C46": "Three knights game",
        "C47": "Four knights, Scotch variation",
        "C50": "Italian Game",
        "C51": "Evans gambit",
        "C53": "Giuoco Piano",
        "C55": "Two knights defence",
        "C60": "Ruy Lopez (Spanish opening)",
        "D00": "Queen's pawn game",
        "D01": "Richter-Veresov attack",
        "D02": "Queen's pawn game",
        "D03": "Torre attack (Tartakower variation)",
        "D04": "Queen's pawn game",
        "D06": "Queen's Gambit",
        "D07": "Queen's Gambit Declined, Chigorin defence",
        "D10": "Queen's Gambit Declined Slav defence",
        "D16": "Queen's Gambit Declined Slav accepted, Alapin variation",
        "D17": "Queen's Gambit Declined Slav, Czech defence",
        "D20": "Queen's gambit accepted",
        "D30": "Queen's gambit declined",
        "D43": "Queen's Gambit Declined semi-Slav",
        "D50": "Queen's Gambit Declined, 4.Bg5",
        "D70": "Neo-Gruenfeld defence",
        "D80": "Gruenfeld defence",
        "E00": "Queen's pawn game",
        "E01": "Catalan, closed",
        "E10": "Queen's pawn game",
        "E11": "Bogo-Indian defence",
        "E12": "Queen's Indian defence",
        "E20": "Nimzo-Indian defence",
        "E60": "King's Indian defence",
    }


# MIDDLE GAME
def get_pawn_structure(current_board) -> str | None:
    fen = replace_numbers_with_dots(current_board.fen()).split(' ')[0]
    if has_caro_pawn_structure(fen):
        return "Caro Formation"
    elif has_slav_formation(fen):
        return "Slav Formation"
    elif has_sicilian_scheveningen(fen):
        return "Sicilian Scheveningen"
    elif has_sicilian_dragon(fen):
        return "Sicilian Dragon"
    elif has_boleslavsky_hole(fen):
        return "Boleslavsky Hole"
    elif has_maroczy_bind(fen):
        return "Maróczy Bind"
    elif has_hedgehog(fen):
        return "Hedgehog"
    elif has_rauzer_formation(fen):
        return "Rauzer Formation"
    elif has_boleslavsky_wall(fen):
        return "Boleslavsky Wall"
    elif has_d5_chain(fen):
        return "D5-Chain"
    elif has_e5_chain(fen):
        return "E5-chain"
    elif has_modern_benoni(fen):
        return "Modern Benoni Formation"
    elif has_giuoco_piano_isolani(fen):
        return "Giuoco Piano Isolani Formation"
    elif has_queens_gambit_isolani(fen):
        return "Queen's Gambit Isolani Formation"
    elif has_hanging_pawns(fen):
        return "Hanging Pawns"
    elif has_carlsbad_formation(fen):
        return "Carlsbad Formation"
    elif has_panov_formation(fen):
        return "Panov Formation"
    elif has_stonewall_formation(fen):
        return "Stonewall Formation"
    elif has_botvinnik_system(fen):
        return "Botvinnik System"
    elif has_closed_sicilian_formation(fen):
        return "Closed Sicilian Formation"
    else:
        return None


def replace_numbers_with_dots(fen):
    return ''.join('.' * int(char) if char.isdigit() else char for char in fen)


# END GAME
def get_endgame_classification(current_board) -> str | None:
    fen = current_board.fen()
    fen_pos = fen.split(' ')[0]
    fen_piece_count = len([char for char in fen_pos if char.isalpha()])
    material_points = calculate_material_from_fen(fen)
    if material_points['w'] <= 13 and material_points['b'] <= 13 and fen_piece_count == 7:
        return aggregate_endgame(classify_endgame(fen))
    return None


def calculate_material_from_fen(fen):
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9}
    material_points = {'w': 0, 'b': 0}

    for char in fen:
        if char.isalpha():
            piece_type = char.upper()
            color = 'w' if char.isupper() else 'b'
            if piece_type != 'K':
                material_points[color] += piece_values.get(piece_type, 0)

    return material_points


def aggregate_endgame(classification):
    split_index = classification.find('K', 1)
    end_string = classification.find('_')
    if end_string == -1:
        end_string = len(classification)
    white_string = classification[:split_index]
    black_string = classification[split_index:end_string]
    bishop_signature = classification[end_string + 1:]
    white_count = {piece: white_string.count(piece) for piece in "KQBNRP"}
    black_count = {piece: black_string.count(piece) for piece in "KQBNRP"}
    if bishop_signature:
        w_light = int(bishop_signature[0])
        w_dark = int(bishop_signature[1])
        b_light = int(bishop_signature[2])
        b_dark = int(bishop_signature[3])
    else:
        w_light = w_dark = b_light = b_dark = 0

    if classify_symmetric(white_count, black_count, is_rook_vs_rook):
        return "rook versus rook"

    if classify_symmetric(white_count, black_count, is_rook_bishop_vs_rook_knight):
        return "rook & bishop versus rook & knight"

    if classify_symmetric(white_count, black_count, is_two_rooks_vs_two_rooks):
        return "two rooks versus two rooks"

    if classify_symmetric(white_count, black_count, is_rook_bishop_vs_rook_bishop):
        if bishop_signature:
            if (w_light == 1 and b_dark == 1) or (w_dark == 1 and b_light == 1):
                return "rook & bishop versus rook & bishop (opposite color)"
            else:
                return "rook & bishop versus rook & bishop (same color)"

    if classify_symmetric(white_count, black_count, is_bishop_vs_knight):
        return "bishop versus knight"

    if classify_symmetric(white_count, black_count, is_rook_knight_vs_rook_knight):
        return "rook & knight versus rook & knight"

    if classify_symmetric(white_count, black_count, is_king_pawns_vs_king_pawns):
        return "king & pawns versus king & pawns"

    if classify_symmetric(white_count, black_count, is_queen_vs_queen):
        return "queen versus queen"

    if classify_symmetric(white_count, black_count, is_rook_bishop_vs_rook):
        return "rook & bishop versus rook"

    if classify_symmetric(white_count, black_count, is_bishop_vs_bishop):
        return "bishop versus bishop"

    if classify_symmetric(white_count, black_count, is_knight_vs_knight):
        return "knight versus knight"

    if classify_symmetric(white_count, black_count, is_rook_vs_bishop):
        return "rook versus bishop"

    if classify_symmetric(white_count, black_count, is_rook_vs_knight):
        return "rook versus knight"

    if classify_symmetric(white_count, black_count, is_bishop_vs_pawns):
        return "bishop versus pawns"

    if classify_symmetric(white_count, black_count, is_knight_vs_pawns):
        return "knight versus pawns"

    if classify_symmetric(white_count, black_count, is_queen_vs_minor_piece):
        return "queen versus minor piece"

    if classify_symmetric(white_count, black_count, is_rook_vs_two_minor_pieces):
        return "rook versus two minor pieces"

    if classify_symmetric(white_count, black_count, is_queen_vs_pawns):
        return "queen versus pawns"

    if classify_symmetric(white_count, black_count, is_queen_vs_rook):
        return "queen versus rook"

    if classify_symmetric(white_count, black_count, is_queen_vs_two_rooks):
        return "queen versus two rooks"

    if classify_symmetric(white_count, black_count, is_king_one_pawn_vs_king):
        return "king & one pawn versus king"

    if classify_symmetric(white_count, black_count, is_queen_vs_three_minor_pieces):
        return "queen versus three minor pieces"

    if classify_symmetric(white_count, black_count, is_queen_vs_rook_minor_piece):
        return "queen versus rook & minor piece"

    if classify_symmetric(white_count, black_count, is_rook_vs_pawns):
        return "rook versus pawns"

    return "Other endings"


def classify_endgame(fen):
    piece_order = ['K', 'Q', 'B', 'N', 'R', 'P']
    board_fen, _, castling, *_ = fen.split()

    white_count = {piece: 0 for piece in piece_order}
    black_count = {piece: 0 for piece in piece_order}

    white_light, white_dark = 0, 0
    black_light, black_dark = 0, 0

    ranks = board_fen.split('/')
    for rank_idx, rank in enumerate(ranks):
        file_idx = 0
        for char in rank:
            if char.isdigit():
                file_idx += int(char)
            elif char.isalpha():
                piece = char.upper()
                if char.isupper():
                    white_count[piece] += 1
                    if piece == 'B':
                        if (rank_idx % 2) == (file_idx % 2):
                            white_light += 1
                        else:
                            white_dark += 1
                else:
                    black_count[piece] += 1
                    if piece == 'B':
                        if (rank_idx % 2) == (file_idx % 2):
                            black_light += 1
                        else:
                            black_dark += 1
                file_idx += 1

    white_str = ''.join(piece * white_count[piece] for piece in piece_order)
    black_str = ''.join(piece * black_count[piece] for piece in piece_order)
    classification = white_str + black_str

    if white_light + white_dark > 0 and black_light + black_dark > 0:
        bishop_signature = f"_{white_light}{white_dark}{black_light}{black_dark}"
        classification += bishop_signature

    if castling != "-":
        classification += f"_{castling}"

    return classification


def classify_symmetric(white_count, black_count, condition):
    return condition(white_count, black_count) or condition(black_count, white_count)


# HELPERS USE CASE 3
def is_rook_vs_rook(wc, bc):
    return wc['R'] == 1 and bc['R'] == 1 and sum(wc[p] + bc[p] for p in "QBN") == 0


def is_rook_bishop_vs_rook_knight(wc, bc):
    return wc['R'] == 1 and wc['B'] == 1 and bc['R'] == 1 and bc['N'] == 1 and sum(wc[p] + bc[p] for p in "Q") == 0


def is_two_rooks_vs_two_rooks(wc, bc):
    return wc['R'] == 2 and bc['R'] == 2 and sum(wc[p] + bc[p] for p in "QBN") == 0


def is_rook_bishop_vs_rook_bishop(wc, bc):
    return wc['R'] == 1 and wc['B'] == 1 and bc['R'] == 1 and bc['B'] == 1 and sum(wc[p] + bc[p] for p in "QN") == 0


def is_bishop_vs_knight(wc, bc):
    return wc['B'] == 1 and bc['N'] == 1 and sum(wc[p] + bc[p] for p in "QR") == 0


def is_rook_knight_vs_rook_knight(wc, bc):
    return wc['R'] == 1 and wc['N'] == 1 and bc['R'] == 1 and bc['N'] == 1 and sum(wc[p] + bc[p] for p in "QB") == 0


def is_king_pawns_vs_king_pawns(wc, bc):
    total_pawns = wc['P'] + bc['P']
    return total_pawns > 0 and wc['K'] == 1 and bc['K'] == 1 and (
            sum(wc.values()) + sum(bc.values()) == 2 + total_pawns)


def is_queen_vs_queen(wc, bc):
    return wc['Q'] == 1 and bc['Q'] == 1 and sum(wc[p] + bc[p] for p in "RBN") == 0


def is_rook_bishop_vs_rook(wc, bc):
    return wc['R'] == 1 and wc['B'] == 1 and bc['R'] == 1 and sum(wc[p] + bc[p] for p in "QN") == 0


def is_bishop_vs_bishop(wc, bc):
    return wc['B'] == 1 and bc['B'] == 1 and sum(wc[p] + bc[p] for p in "QRN") == 0


def is_knight_vs_knight(wc, bc):
    return wc['N'] == 1 and bc['N'] == 1 and sum(wc[p] + bc[p] for p in "QRB") == 0


def is_rook_vs_bishop(wc, bc):
    return wc['R'] == 1 and bc['B'] == 1 and sum(wc[p] + bc[p] for p in "QN") == 0


def is_rook_vs_knight(wc, bc):
    return wc['R'] == 1 and bc['N'] == 1 and sum(wc[p] + bc[p] for p in "QB") == 0


def is_bishop_vs_pawns(wc, bc):
    return wc['B'] == 1 and bc['P'] > 0 and sum(wc[p] + bc[p] for p in "QRN") == 0


def is_knight_vs_pawns(wc, bc):
    return wc['N'] == 1 and bc['P'] > 0 and sum(wc[p] + bc[p] for p in "QRB") == 0


def is_queen_vs_minor_piece(wc, bc):
    return wc['Q'] == 1 and (bc['B'] + bc['N'] == 1) and sum(wc[p] + bc[p] for p in "R") == 0


def is_rook_vs_two_minor_pieces(wc, bc):
    return wc['R'] == 1 and (bc['B'] + bc['N'] == 2) and sum(wc[p] + bc[p] for p in "Q") == 0


def is_queen_vs_pawns(wc, bc):
    return wc['Q'] == 1 and bc['P'] > 0 and sum(wc[p] + bc[p] for p in "RBN") == 0


def is_queen_vs_rook(wc, bc):
    return wc['Q'] == 1 and bc['R'] == 1 and sum(wc[p] + bc[p] for p in "BN") == 0


def is_queen_vs_two_rooks(wc, bc):
    return wc['Q'] == 1 and bc['R'] == 2 and sum(wc[p] + bc[p] for p in "BN") == 0


def is_king_one_pawn_vs_king(wc, bc):
    return wc['K'] == 1 and wc['P'] == 1 and bc['K'] == 1 and sum(wc[p] + bc[p] for p in "QRBN") == 0


def is_queen_vs_three_minor_pieces(wc, bc):
    return wc['Q'] == 1 and bc['B'] + bc['N'] + bc['R'] == 3


def is_rook_vs_pawns(wc, bc):
    return wc['R'] == 1 and bc['P'] > 0 and sum(wc[p] + bc[p] for p in "QBN") == 0


def is_queen_vs_rook_minor_piece(wc, bc):
    return wc['Q'] == 1 and bc['R'] == 1 and bc['B'] + bc['N'] == 1


def has_caro_pawn_structure(fen: str):
    regex = r'[^pP]*\/pp[^pP][^pP][^pP]ppp\/[^pP][^pP]p[^pP]p[^pP][^pP][^pP]\/[^pP]*\/[^pP][^pP][^pP]P[^pP][^pP][^pP][^pP]\/[^pP]*\/PPP[^pP][^pP]PPP\/[^pP]*'
    return re.match(regex, fen) is not None


def has_slav_formation(fen):
    regex = r'[^pP]*\/pp[^pP][^pP][^pP]ppp\/[^pP][^pP]p[^pP]p[^pP][^pP][^pP]\/[^pP]*\/[^pP][^pP][^pP]P[^pP][^pP][^pP][^pP]\/[^pP][^pP][^pP][^pP]P[^pP][^pP][^pP]\/PP[^pP][^pP][^pP]PPP\/[^pP]*'
    return re.match(regex, fen) is not None


def has_sicilian_scheveningen(fen):
    regex = r'[^pP]*\/pp[^pP][^pP][^pP]ppp\/[^pP][^pP][^pP]pp[^pP][^pP][^pP]\/[^pP]*\/[^pP][^pP][^pP][^pP]P[^pP][^pP][^pP]\/[^pP]*\/PPP[^pP][^pP]PPP\/[^pP]*'
    return re.match(regex, fen) is not None


def has_sicilian_dragon(fen):
    regex = r'[^pP]*\/pp[^pP][^pP]pp[^pP]p\/[^pP][^pP][^pP]p[^pP][^pP]p[^pP]\/[^pP]*\/[^pP][^pP][^pP][^pP]P[^pP][^pP][^pP]\/[^pP]*\/PPP[^pP][^pP]PPP\/[^pP]*'
    return re.match(regex, fen) is not None


def has_boleslavsky_hole(fen):
    regex = r'[^pP]*\/pp[^pP][^pP][^pP]ppp\/[^pP][^pP][^pP]p[^pP][^pP][^pP][^pP]\/[^pP][^pP][^pP][^pP]p[^pP][^pP][^pP]\/[^pP][^pP][^pP][^pP]P[^pP][^pP][^pP]\/[^pP]*\/PPP[^pP][^pP]PPP\/[^pP]*'
    return re.match(regex, fen) is not None


def has_maroczy_bind(fen):
    regex1 = r'[^pP]*\/pp[^pP][^pP]pppp\/[^pP][^pP][^pP]p[^pP][^pP][^pP][^pP]\/[^pP]*\/[^pP][^pP]P[^pP]P[^pP][^pP][^pP]\/[^pP]*\/PP[^pP][^pP][^pP]PPP\/[^pP]*'
    regex2 = r'[^pP]*\/pp[^pP]p[^pP]ppp\/[^pP][^pP][^pP][^pP]p[^pP][^pP][^pP]\/[^pP]*\/[^pP][^pP]P[^pP]P[^pP][^pP][^pP]\/[^pP]*\/PP[^pP][^pP][^pP]PPP\/[^pP]*'
    return re.match(regex1, fen) is not None or re.match(regex2, fen) is not None


def has_hedgehog(fen):
    regex = r'[^pP]*\/[^pP][^pP][^pP][^pP][^pP]ppp\/pp[^pP]pp[^pP][^pP][^pP]\/[^pP]*\/[^pP][^pP]P[^pP]P[^pP][^pP][^pP]\/[^pP]*\/PP[^pP][^pP][^pP]PPP\/[^pP]*'
    return re.match(regex, fen) is not None


def has_rauzer_formation(fen):
    regex = r'[^pP]*\/pp[^pP][^pP][^pP]ppp\/[^pP][^pP]p[^pP][^pP][^pP][^pP][^pP]\/[^pP][^pP][^pP][^pP]p[^pP][^pP][^pP]\/[^pP][^pP]P[^pP]P[^pP][^pP][^pP]\/[^pP]*\/PP[^pP][^pP][^pP]PPP\/[^pP]*'
    return re.match(regex, fen) is not None


def has_boleslavsky_wall(fen):
    regex = r'[^pP]*\/pp[^pP][^pP][^pP]ppp\/[^pP][^pP]pp[^pP][^pP][^pP][^pP]\/[^pP]*\/[^pP][^pP]P[^pP]P[^pP][^pP][^pP]\/[^pP]*\/PP[^pP][^pP][^pP]PPP\/[^pP]*'
    return re.match(regex, fen) is not None


def has_d5_chain(fen):
    regex = r'[^pP]*\/ppp[^pP][^pP]ppp\/[^pP][^pP][^pP]p[^pP][^pP][^pP][^pP]\/[^pP][^pP][^pP]Pp[^pP][^pP][^pP]\/[^pP][^pP][^pP][^pP]P[^pP][^pP][^pP]\/[^pP]*\/PPP[^pP][^pP]PPP\/[^pP]*'
    return re.match(regex, fen) is not None


def has_e5_chain(fen):
    regex = r'[^pP]*\/ppp[^pP][^pP]ppp\/[^pP][^pP][^pP][^pP]p[^pP][^pP][^pP]\/[^pP][^pP][^pP]pP[^pP][^pP][^pP]\/[^pP][^pP][^pP]P[^pP][^pP][^pP][^pP]\/[^pP]*\/PPP[^pP][^pP]PPP\/[^pP]*'
    return re.match(regex, fen) is not None


def has_modern_benoni(fen):
    regex = r'[^pP]*\/pp[^pP][^pP][^pP]ppp\/[^pP][^pP][^pP]p[^pP][^pP][^pP][^pP]\/[^pP][^pP]pP[^pP][^pP][^pP][^pP]\/[^pP][^pP][^pP][^pP]P[^pP][^pP][^pP]\/[^pP]*\/PP[^pP][^pP][^pP]PPP\/[^pP]*'
    return re.match(regex, fen) is not None


def has_giuoco_piano_isolani(fen):
    regex = r'[^pP]*\/ppp[^pP][^pP]ppp\/[^pP]*\/[^pP]*\/[^pP][^pP][^pP]P[^pP][^pP][^pP][^pP]\/[^pP]*\/PP[^pP][^pP][^pP]PPP\/[^pP]*'
    return re.match(regex, fen) is not None


def has_queens_gambit_isolani(fen):
    regex = r'[^pP]*\/pp[^pP][^pP][^pP]ppp\/[^pP][^pP][^pP][^pP]p[^pP][^pP][^pP]\/[^pP]*\/[^pP][^pP][^pP]P[^pP][^pP][^pP][^pP]\/[^pP]*\/PP[^pP][^pP][^pP]PPP\/[^pP]*'
    return re.match(regex, fen) is not None


def has_hanging_pawns(fen):
    regex = r'[^pP]*\/pp[^pP][^pP][^pP]ppp\/[^pP][^pP][^pP][^pP]p[^pP][^pP][^pP]\/[^pP]*\/[^pP][^pP]PP[^pP][^pP][^pP][^pP]\/[^pP]*\/P[^pP][^pP][^pP][^pP]PPP\/[^pP]*'
    return re.match(regex, fen) is not None


def has_carlsbad_formation(fen):
    regex = r'[^pP]*\/pp[^pP][^pP][^pP]ppp\/[^pP][^pP]p[^pP][^pP][^pP][^pP][^pP]\/[^pP][^pP][^pP]p[^pP][^pP][^pP][^pP]\/[^pP][^pP][^pP]P[^pP][^pP][^pP][^pP]\/[^pP][^pP][^pP][^pP]P[^pP][^pP][^pP]\/PP[^pP][^pP][^pP]PPP\/[^pP]*'
    return re.match(regex, fen) is not None


def has_panov_formation(fen):
    regex = r'[^pP]*\/pp[^pP][^pP][^pP]ppp\/[^pP][^pP][^pP][^pP]p[^pP][^pP][^pP]\/[^pP][^pP]Pp[^pP][^pP][^pP][^pP]\/[^pP][^pP][^pP]P[^pP][^pP][^pP][^pP]\/[^pP]*\/PP[^pP][^pP][^pP]PPP\/[^pP]*'
    return re.match(regex, fen) is not None


def has_stonewall_formation(fen):
    regex = r'[^pP]*\/ppp[^pP][^pP][^pP]pp\/[^pP][^pP][^pP][^pP]p[^pP][^pP][^pP]\/[^pP][^pP][^pP]p[^pP]p[^pP][^pP]\/[^pP][^pP][^pP]P[^pP]P[^pP][^pP]\/[^pP][^pP][^pP][^pP]P[^pP][^pP][^pP]\/PPP[^pP][^pP][^pP]PP\/[^pP]*'
    return re.match(regex, fen) is not None


def has_botvinnik_system(fen):
    regex = r'[^pP]*\/pp[^pP][^pP][^pP]ppp\/[^pP][^pP][^pP]p[^pP][^pP][^pP][^pP]\/[^pP][^pP]p[^pP]p[^pP][^pP][^pP]\/[^pP][^pP]P[^pP]P[^pP][^pP][^pP]\/[^pP][^pP][^pP]P[^pP][^pP][^pP][^pP]\/PP[^pP][^pP][^pP]PPP\/[^pP]*'
    return re.match(regex, fen) is not None


def has_closed_sicilian_formation(fen):
    regex = r'[^pP]*\/pp[^pP][^pP]pppp\/[^pP][^pP][^pP]p[^pP][^pP][^pP][^pP]\/[^pP][^pP]p[^pP][^pP][^pP][^pP][^pP]\/[^pP][^pP][^pP][^pP]P[^pP][^pP][^pP]\/[^pP][^pP][^pP]P[^pP][^pP][^pP][^pP]\/PPP[^pP][^pP]PPP\/[^pP]*'
    return re.match(regex, fen) is not None


if __name__ == '__main__':
    print("functions.py is main")
