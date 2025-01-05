import inspect
import re
import time
from copy import copy, deepcopy
from typing import Any

import chess.engine
import chess.pgn
from chess import Board
from chess.pgn import GameNode

import helpers
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
from helpers import get_data_object
import pm4py
import pandas as pd
from pm4py.objects.log.util import dataframe_utils
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.algo.discovery.heuristics import algorithm as heuristics_miner
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.visualization.heuristics_net import visualizer as hn_visualizer
from pm4py.visualization.process_tree import visualizer as pt_visualizer
from pm4py.objects.conversion.process_tree import converter as pt_converter
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from pm4py.objects.log.obj import EventLog, Trace, Event
from pm4py.objects.log.exporter.xes import exporter as xes_exporter
from pm4py.util.xes_constants import DEFAULT_NAME_KEY
from datetime import datetime, timedelta
from HttpRequests.chess_api import ChessAPI
from pm4py.objects.log.importer.xes import importer as xes_importer
import zstandard as zstd

from tagger_module.mytagger import cook_positions
from tagger_module.tagger import read


def generate_puzzle_move_log(file_path = 'sample_puzzles.csv', existing_xes_path = None, without_piece_bonus = False):
    puzzles = pd.read_csv(file_path)
    game_objects = []
    for _, row in puzzles.iterrows():
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

    output_path = "event_log_" + file_path.replace(".csv", ".xes")
    data = get_data_object()

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

    for position_tags, game in game_objects:
        start = time.time()
        if without_piece_bonus:
            game_events = process_puzzle_without_piece_bonus(game, case_id, data)
        else:
            game_events = process_puzzle(game, case_id, data)

        trace = Trace()
        trace.attributes["concept:name"] = f'case_{case_id}'
        trace.attributes["puzzle_id"] = game.headers["PuzzleId"]
        trace.attributes["rating_50"] = round(int(game.headers["Rating"]) / 50) * 50
        trace.attributes["rating_100"] = round(int(game.headers["Rating"]) / 100) * 100
        trace.attributes["rating_200"] = round(int(game.headers["Rating"]) / 200) * 200
        trace.attributes["themes"] = game.headers["Themes"]
        trace.attributes["game_url"] = game.headers["GameUrl"]

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

        print(result)
        end_index = 0
        for i, event in enumerate(game_events, start=1):
            if i % 2 == 0:
                end_index = i
                moves = [move for idx, move in result if idx == i-1]
                if moves:
                    for move in moves:
                        if move:
                            trace.append(Event({
                                "concept:name": f"move: {i}, {move}",
                                "time:timestamp": event["Timestamp"],
                            }))
            else:
                trace.append(Event({
                    "concept:name": f"state: {i}, {event["Activity"]}",
                    # "concept:name": f"s: {event["Activity"]}",
                    "time:timestamp": event["Timestamp"],
                }))
                end_index = i
        end_index += 1
        if end_index % 2 == 0:
            moves = [move for idx, move in result if idx == end_index - 1]
            if moves:
                for move in moves:
                    if move:
                        trace.append(Event({
                            "concept:name": f"move: {end_index}, {move}",

                        }))
        event_log.append(trace)

        end = time.time()
        print(f"Processed Game {case_id} in {end - start:.2f} seconds")
        case_id += 1

    xes_exporter.apply(event_log, output_path)

def generate_puzzle_log(file_path = 'sample_puzzles.csv', existing_xes_path = None, without_piece_bonus = False):

    puzzles = pd.read_csv(file_path)
    game_objects = []
    for _, row in puzzles.iterrows():
        fen = row['FEN']
        moves_str = row['Moves']
        game = create_game_from_fen_and_moves(fen, moves_str)
        game.headers["PuzzleId"] = row['PuzzleId']
        game.headers["Rating"] = str(row['Rating'])
        game.headers["Themes"] = row['Themes']
        game.headers["GameUrl"] = row['GameUrl']
        game_objects.append(game)

    output_path = "event_log_" + file_path.replace(".csv", ".xes")
    data = get_data_object()

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

    for game in game_objects:
        start = time.time()
        if without_piece_bonus:
            game_events = process_puzzle_without_piece_bonus(game, case_id, data)
        else:
            game_events = process_puzzle(game, case_id, data)


        trace = Trace()
        trace.attributes["concept:name"] = f'case_{case_id}'
        trace.attributes["puzzle_id"] = game.headers["PuzzleId"]
        trace.attributes["rating"] = game.headers["Rating"]
        trace.attributes["themes"] = game.headers["Themes"]
        trace.attributes["game_url"] = game.headers["GameUrl"]

        for i, event in enumerate(game_events, start=1):
            trace.append(Event({
                "concept:name": f"{i}, {event["Activity"]}",
                # "concept:name": f"{event["Activity"]}",
                "time:timestamp": event["Timestamp"],
            }))
        event_log.append(trace)

        end = time.time()
        print(f"Processed Game {case_id} in {end - start:.2f} seconds")
        case_id += 1

    xes_exporter.apply(event_log, output_path)

def generate_theme_log(input_csv = "puzzles_0_1400.csv"):

    output_xes = "event_log_" + input_csv.replace(".csv", ".xes")

    df = pd.read_csv(input_csv)

    event_log = EventLog()

    for _, row in df.iterrows():
        puzzle_id = row['PuzzleId']
        rating = row['Rating']
        game_url = row['GameUrl']
        themes = row['Themes'].split()

        trace = Trace()
        trace.attributes["puzzle_id"] = puzzle_id
        trace.attributes["rating"] = rating
        trace.attributes["game_url"] = game_url

        for i, theme in enumerate(themes, start=1):
            event = Event({
                "concept:name": theme,
                "time:timestamp": f"{datetime(i, 1, 1, 12, 0)}"
            })
            trace.append(event)

        event_log.append(trace)
    xes_exporter.apply(event_log, output_xes)
    print(f"Event log saved to {output_xes}")


def process_puzzle_without_piece_bonus(game, case_id, data):
    print(f"Processing Game {case_id}")
    current_board = game.board()
    color = "black"
    if not current_board.turn:
        color = "white"
    item_sums, group_list = get_item_sums_and_group_list_puzzle(game, current_board, data, color)
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
                'Timestamp': f'{datetime(i, 1, 1, 12, 0)}',
                'Activity': activity_name
            })

    return game_events

def process_puzzle(game, case_id, data):
    print(f"Processing Game {case_id}")
    current_board = game.board()
    color = "white"
    if not current_board.turn:
        color = "black"
    item_sums, group_list = get_item_sums_and_group_list_puzzle(game, current_board, data, color)
    elem_list = [entry['elem'] for entry in group_list]

    game_events = []

    for i, item in enumerate(item_sums, start=1):
        item_dict = zip(item, elem_list)
        activity = max(zip(item, elem_list), key=lambda x: x[0])
        if color == "black":
            activity = min(zip(item, elem_list), key=lambda x: x[0])

        activity_name = activity[1]
        if activity[0] != 0:
            game_events.append({
                'Timestamp': f'{datetime(i, 1, 1, 12, 0)}',
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

def get_games_of_player(player_name: str = "hikaru", year: str = "2018", month: str = "01", output_file: str = "games.pgn"):
    chess_api = ChessAPI(player_name, year, month)
    games_pgn = chess_api.get_games()
    # print(games_pgn)
    if games_pgn:
        try:
            with open(output_file, "w", encoding="utf-8") as file:
                file.write(games_pgn)
            print(f"Games saved to {output_file}")
        except IOError as e:
            print(f"Error saving games to file: {e}")

def extract_sample_from_csv():
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

    sample = df.iloc[5000:6000]

    sample.to_csv('sample_puzzles_1000_after_5000.csv', index=False)

def process_game(game, case_id, data, playername: str):
    # print(f"Processing Game {game.headers['Event']}, White: {game.headers['White']}, Black {game.headers['Black']}")
    result = game.headers['Result']
    ending = None
    if result == '1-0':
        outcome = 'White won'
    elif result == '0-1':
        outcome = 'Black won'
    else:
        outcome = 'Draw'
    print(f"Processing Game {case_id}")
    current_board = game.board()
    color = "white"
    if game.headers["Black"] == playername:
        color = "black"
    item_sums, group_list = get_item_sums_and_group_list(game, current_board, data, color)
    elem_list = [entry['elem'] for entry in group_list]

    game_events = []

    for i, item in enumerate(item_sums, start=1):
        prev = (i - 1) * 4
        cur = i * 4
        largest_three = sorted(zip(item, elem_list), reverse=True)[:3]

        activity = max(zip(item, elem_list), key=lambda x: x[0])
        if color == "black":
            activity = min(zip(item, elem_list), key=lambda x: x[0])

        # activities = ", ".join([biggest[1] for biggest in largest_three])
        activity_name = activity[1]
        if activity[0] != 0:
            game_events.append({
                # 'Case ID': f'case_{case_id}',
                # 'Timestamp': f'move_{prev}-{cur}',
                # 'Activity': activities
                # 'Timestamp': f'move_{i}',
                'Timestamp': f'{datetime(i, 1, 1, 12, 0)}',
                'Activity': activity_name
            })
    if outcome != 'Draw':
        if current_board.is_checkmate():
            ending = "Checkmate"
        else:
            ending = "Time/Forfeit"

    return outcome, ending, game_events


def call_with_param(func, position):
    sig = inspect.signature(func)

    kwargs = {}

    if 'replacement_func' in sig.parameters:
        kwargs['replacement_func'] = func

    return func(position, **kwargs)


def get_group_list(position, data, king_danger_only = False):
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


def get_sliced_moves(game: GameNode, param: int) -> list[chess.Move]:
    moves = []
    for move in game.mainline():
        moves.append(move.move)

    sliced_moves = moves[0:param]

    return sliced_moves


def get_move_num_and_color(current_board: Board) -> tuple[int, bool]:
    return current_board.fullmove_number, current_board.turn


def debug_at_move(game, current_board, engine, move_num) -> None:
    sliced_moves = get_sliced_moves(game, move_num)
    for move in sliced_moves:
        current_board.push(move)

    calc_score = main_evaluation(None, None, board_to_position(current_board), "main")
    print(f"Calculated score: {calc_score}")
    info = engine.analyse(current_board, chess.engine.Limit(depth=20))
    print(f"Engine score: {info['score'].white()}")

def get_item_sums_and_group_list_puzzle(game, current_board, data, color):
    # all_groups = []
    item_sums = []
    recent_items = []
    item_length = 50
    group_list = []
    remainder = 0
    if color == "white":
        remainder = 1
    for move_num, move in enumerate(list(game.mainline_moves())[:-1], start=1):
        current_board.push(move)


        group_list = get_group_list(board_to_position(current_board), data)
        # all_groups.append(group_list)
        item_third_elements = [{group['elem']: group['item'][2]} for group in group_list]
        recent_items.append(item_third_elements)
        item_length = len(item_third_elements)

        # if move_num % 4 == 0:
        add_items(item_length, item_sums, recent_items)

    # add_items(item_length, item_sums, recent_items)

    return item_sums, group_list

def get_item_sums_and_group_list(game, current_board, data, color):
    # all_groups = []
    item_sums = []
    recent_items = []
    item_length = 50
    group_list = []
    remainder = 0
    if color == "white":
        remainder = 1
    for move_num, move in enumerate(game.mainline_moves(), start=1):
        is_captured: bool = current_board.is_capture(move)
        current_board.push(move)

        if not is_captured:
            group_list = get_group_list(board_to_position(current_board), data)
            # all_groups.append(group_list)
            item_third_elements = [{group['elem']: group['item'][2]} for group in group_list]
            recent_items.append(item_third_elements)
            item_length = len(item_third_elements)

        # if move_num % 4 == 0:
        add_items(item_length, item_sums, recent_items)

    # add_items(item_length, item_sums, recent_items)

    return item_sums, group_list


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


def run_and_evaluate_game(game, current_board) -> list[tuple[int, Any, int, int, int, bool]]:
    largest_changes = []
    prev_score: int | None = None
    for move in game.mainline_moves():
        move_num, color = get_move_num_and_color(current_board)
        is_captured: bool = current_board.is_capture(move)
        current_board.push(move)
        start = time.time()
        calc_score = round(main_evaluation(None, None, board_to_position(current_board), "main") / 208, 2)
        end = time.time()

        if prev_score is not None and not is_captured:
            change = abs(calc_score - prev_score)
            largest_changes.append((move_num, move, change, prev_score, calc_score, color))
            largest_changes = sorted(largest_changes, key=lambda x: x[2], reverse=True)[:10]

        prev_score = calc_score
        print(f"Move: {move_num}{' W' if color else ' B'} {move} Score: {calc_score}")
        # print(f"Elapsed time: {end - start}")

    return largest_changes


def run_and_evaluate_game_sf(game, current_board, engine, depth) -> list[tuple[int, Any, int, int, int, bool]]:
    largest_changes = []
    prev_score = None

    for move in game.mainline_moves():
        move_num, color = get_move_num_and_color(current_board)
        current_board.push(move)
        info = engine.analyse(current_board, chess.engine.Limit(depth=depth))
        overall_score = info['score'].white()

        if prev_score is not None:
            change = abs(overall_score.score() - prev_score.score())
            largest_changes.append((move_num, move, change, prev_score, overall_score, color))
            largest_changes = sorted(largest_changes, key=lambda x: x[2], reverse=True)[:10]

        prev_score = overall_score
        print(f"Move: {move_num}{'W' if color else 'B'} {move} Score: {overall_score}")

    return largest_changes

def add_move_to_activities(existing_xes_path = None):
    event_log = xes_importer.apply(existing_xes_path)

    for i, trace in enumerate(event_log, start=1):
        print(f"Processing trace {i}")
        for event in trace:
            # Extract the timestamp and derive the move number
            timestamp = event.get("time:timestamp")
            if timestamp:
                move_number = int(timestamp.split("-")[0])
                event_name = event["concept:name"]
                event["concept:name"] = f"{move_number}, {event_name}"

    modified_xes_path = "event_log_Hikaru_games_2024_01.xes"
    xes_exporter.apply(event_log, modified_xes_path)

    print("Event log has been updated and saved.")


def process_game_without_piece_bonus(game, case_id, data, playername: str):
    # print(f"Processing Game {game.headers['Event']}, White: {game.headers['White']}, Black {game.headers['Black']}")
    result = game.headers['Result']
    ending = None
    if result == '1-0':
        outcome = 'White won'
    elif result == '0-1':
        outcome = 'Black won'
    else:
        outcome = 'Draw'
    print(f"Processing Game {case_id}")
    current_board = game.board()
    color = "white"
    if game.headers["Black"] == playername:
        color = "black"
    item_sums, group_list = get_item_sums_and_group_list_puzzle(game, current_board, data, color)
    elem_list = [entry['elem'] for entry in group_list]

    game_events = []

    for i, item in enumerate(item_sums, start=1):
        prev = (i - 1) * 4
        cur = i * 4
        largest_three = sorted(zip(item, elem_list), reverse=True)[:3]

        activity = max(
            ((value, key) for value, key in zip(item, elem_list) if key not in {"piece_value_bonus", "psqt_bonus"}),
            key=lambda x: x[0]
        )
        if color == "black":
            activity = min(
                ((value, key) for value, key in zip(item, elem_list) if key not in {"piece_value_bonus", "psqt_bonus"}),
                key=lambda x: x[0]
            )

        # activities = ", ".join([biggest[1] for biggest in largest_three])
        activity_name = activity[1]
        if activity[0] != 0:
            game_events.append({
                # 'Case ID': f'case_{case_id}',
                # 'Timestamp': f'move_{prev}-{cur}',
                # 'Activity': activities
                # 'Timestamp': f'move_{i}',
                'Timestamp': f'{datetime(i, 1, 1, 12, 0)}',
                'Activity': activity_name
            })
    if outcome != 'Draw':
        if current_board.is_checkmate():
            ending = "Checkmate"
        else:
            ending = "Time/Forfeit"

    return outcome, ending, game_events


def generate_event_log(pgn_path = "Games/filtered_games.pgn", player_name: str = None, existing_xes_path = None, without_piece_bonus = False):
    output_path = "event_log_" + pgn_path[pgn_path.find("/") + 1:].replace(".pgn", ".xes")
    data = get_data_object()

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

    eco_mapping = get_eco_mapping()

    with open(pgn_path) as pgn:
        case_id = len(event_log) + 1
        while True:
            game = chess.pgn.read_game(pgn)
            if game is None:
                break

            start = time.time()
            if without_piece_bonus:
                outcome, ending, game_events = process_game_without_piece_bonus(game, case_id, data, player_name)
            else:
                outcome, ending, game_events = process_game(game, case_id, data, player_name)


            trace = Trace()
            trace.attributes["concept:name"] = f'case_{case_id}'
            trace.attributes["outcome"] = outcome
            if game.headers["White"] and game.headers["Black"]: trace.attributes["players"] = (game.headers["White"] +" vs. " + game.headers["Black"])
            if ending: trace.attributes["ending"] = ending
            if game.headers["White"] and game.headers["White"] == player_name:
                trace.attributes["player_color"] = "White"
            elif game.headers["Black"] and game.headers["Black"] == player_name:
                trace.attributes["player_color"] = "Black"
            for i, event in enumerate(game_events, start=1):
                trace.append(Event({
                    "concept:name": f"{i}, {event["Activity"]}",
                    "time:timestamp": event["Timestamp"],
                    # "case:concept:name": event["Case ID"]
                }))
            eco = game.headers['ECO']
            if eco:
                aggregated_eco = aggregate_eco(eco_mapping, eco)
                trace.attributes["eco"] = eco
                trace.attributes["aggregated_eco"] = aggregated_eco
            event_log.append(trace)

            end = time.time()
            print(f"Processed Game {case_id} in {end - start:.2f} seconds")
            case_id += 1

    xes_exporter.apply(event_log, output_path)

def print_largest_changes():
    engine = get_engine()
    pgn = open("Games/game_1.pgn")
    game = chess.pgn.read_game(pgn)
    current_board = game.board()
    largest_changes = run_and_evaluate_game_sf(game, current_board, engine, 14)
    print("\n")
    for move_num, move, change, prev_score, overall_score, color in largest_changes:
        print(
            f"Move: {move_num}{' W' if color else ' B'} {move}, Change: {change}, From: {prev_score} -> {overall_score}")
    engine.quit()


def get_engine():
    return chess.engine.SimpleEngine.popen_uci(
        r"C:\Users\carlj\Documents\stockfish\stockfish\stockfish-windows-x86-64-avx2.exe")


def split_csv_in_rating(input_file = "sample_puzzles.csv"):

    output_file_1 = input_file.replace(".csv", "") + "_0_1400.csv"
    output_file_2 = input_file.replace(".csv", "") + "_1400_2000.csv"
    output_file_3 = input_file.replace(".csv", "") + "_2000_plus.csv"

    df = pd.read_csv(input_file)

    puzzles_0_1400 = df[(df['Rating'] >= 0) & (df['Rating'] < 1400)]
    puzzles_1400_2000 = df[(df['Rating'] >= 1400) & (df['Rating'] <= 2000)]
    puzzles_2000_plus = df[df['Rating'] > 2000]

    puzzles_0_1400.to_csv(output_file_1, index=False)
    puzzles_1400_2000.to_csv(output_file_2, index=False)
    puzzles_2000_plus.to_csv(output_file_3, index=False)

    print("Puzzles sorted and saved into three separate files:")
    print(f"- {output_file_1}")
    print(f"- {output_file_2}")
    print(f"- {output_file_3}")


def inductive_mine_log():

    df = pd.read_csv("data/event_log_scholar.csv")
    df.rename(columns={
        "Case ID": "case:concept:name",
        "Timestamp": "time:timestamp",
        "Activity": "concept:name"
    }, inplace=True)
    df = dataframe_utils.convert_timestamp_columns_in_df(df)
    event_log = log_converter.apply(df)


    process_tree = inductive_miner.apply(event_log)


    gviz_tree = pt_visualizer.apply(process_tree)
    pt_visualizer.view(gviz_tree)


    net, initial_marking, final_marking = pt_converter.apply(process_tree)


    gviz_petri = pn_visualizer.apply(net, initial_marking, final_marking)
    pn_visualizer.view(gviz_petri)

def heuristic_mine_log(data_path="data/event_log_italian_test.csv"):
    df = pd.read_csv(data_path)
    last_line = pd.read_csv(data_path, usecols=['Case ID']).iloc[-1]
    last_case_id = last_line['Case ID']
    case_id = int(last_case_id.replace("case_", ""))
    unique_moves = sorted(df["Timestamp"].unique())
    start_time = datetime(2024, 1, 1, 12, 0)
    timestamp_mapping = {
        move: start_time + timedelta(minutes=i) for i, move in enumerate(unique_moves)
    }
    df["time:timestamp"] = df["Timestamp"].map(timestamp_mapping)

    df.rename(columns={
        "Case ID": "case:concept:name",
        "Activity": "concept:name"
    }, inplace=True)

    df["time:timestamp"] = pd.to_datetime(df["time:timestamp"]).dt.strftime('%Y-%m-%dT%H:%M:%S')


    df = dataframe_utils.convert_timestamp_columns_in_df(df)
    event_log = log_converter.apply(df)
    print(case_id)
    heu_net = heuristics_miner.apply_heu(event_log, parameters={
        heuristics_miner.Variants.CLASSIC.value.Parameters.DEPENDENCY_THRESH: 0.80,
        heuristics_miner.Variants.CLASSIC.value.Parameters.MIN_ACT_COUNT: int(0.001*case_id),
        heuristics_miner.Variants.CLASSIC.value.Parameters.MIN_DFG_OCCURRENCES: int(0.001*case_id)
    })
    print(heu_net)
    gviz = hn_visualizer.apply(heu_net)
    hn_visualizer.view(gviz)
    # xes_exporter.apply(event_log, "data/event_log.xes")


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
    current_move = start + 1
    for move_num, move in enumerate(moves, start=start + 1):
        current_move = move_num
        turn_str = "White_" if current_board.turn else "Black_"
        move_str = current_board.san(move)
        current_board.push(move)

        game_events.append({
            # "Case ID": f"case_{case_id}",
            "Timestamp": f"move_{move_num}",
            "Activity": turn_str + move_str
        })

        info = engine.analyse(current_board, chess.engine.Limit(depth=14))
        overall_score = info['score'].white()
        if overall_score.is_mate() or abs(overall_score.score()) > 100 or abs(overall_score.score() < 10):
            break

        # if current_move > 5:
        #     position = board_to_position(current_board)
        #     king_danger_score = main_evaluation(king_mg_king_danger(position) - king_mg_king_danger(colorflip(position)),
        #                                         king_eg_king_danger(position) - king_eg_king_danger(colorflip(position)),
        #                                         position) - main_evaluation(0, 0, position)
        #     # king_danger_score = get_group_list(board_to_position(current_board), helpers.get_king_data_object(), True)[0]
        #     if king_danger_score < 50:
        #         break
    if outcome != 'Draw':
        if current_board.is_checkmate():
            ending = "Checkmate"
        else:
            ending = "Time/Forfeit"


    return outcome, ending, game_events


def generate_fine_grained_event_log(csv_path=None, pgn_path="Games/filtered_games.pgn"):
    output_path = "event_log_" + pgn_path[pgn_path.find("/") + 1:]
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
            trace.attributes["concept:name"] = f'case_{case_id}'
            trace.attributes["outcome"] = outcome
            if ending: trace.attributes["ending"] = ending
            for event in game_events:
                pm_event = Event({
                    "concept:name": event["Activity"],
                    "time:timestamp": event["Timestamp"],
                    # "case:concept:name": event["Case ID"]
                })
                trace.append(pm_event)
            event_log.append(trace)

            case_id += 1


    xes_exporter.apply(event_log, output_path)
    engine.quit()


def filter_pgn(input_file, output_file, moves_prefix):
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        while True:
            game = chess.pgn.read_game(infile)
            if game is None:
                break


            board = game.board()
            moves = []
            for move in game.mainline_moves():
                moves.append(board.san(move))
                board.push(move)


                if len(moves) > len(moves_prefix):
                    break


            if moves == moves_prefix:
                outfile.write(str(game) + "\n\n")


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
        return None #"Other"

def classify_symmetric(white_count, black_count, condition):
    return condition(white_count, black_count) or condition(black_count, white_count)

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
    return total_pawns > 0 and wc['K'] == 1 and bc['K'] == 1 and (sum(wc.values()) + sum(bc.values()) == 2 + total_pawns)

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


def aggregate_endgame(classification):
    split_index = classification.find('K', 1)
    end_string = classification.find('_')
    if end_string == -1:
        end_string = len(classification)
    white_string = classification[:split_index]
    black_string = classification[split_index:end_string]
    bishop_signature = classification[end_string+1:]
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

def get_endgame_classification(current_board) -> str | None:
    fen = current_board.fen()
    fen_pos = fen.split(' ')[0]
    fen_piece_count = len([char for char in fen_pos if char.isalpha()])
    # if fen_piece_count == 7:
    #     return aggregate_endgame(classify_endgame(fen))
    material_points = calculate_material_from_fen(fen)
    if material_points['w'] <= 13 and material_points['b'] <= 13 and fen_piece_count == 7:
        return aggregate_endgame(classify_endgame(fen))
    return None


def aggregate_eco(eco_mapping, eco_code):
    for key in reversed(eco_mapping):
        if key <= eco_code:
            return key
    return "Unknown"

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
        # 'Case ID': f'case_{case_id}',
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
            # 'Case ID': f'case_{case_id}',
            'Timestamp': f'{datetime(2024, 1, 1, 12, i)}',
            'Activity': structure
            })
            end_structure = i+1

    end_classification = end_structure
    for i, classification in enumerate(endgame_classifications, start=end_structure):
        game_events.append({
            # 'Case ID': f'case_{case_id}',
            'Timestamp': f'{datetime(2024, 1, 1, 12, i)}',
            'Activity': classification
        })
        end_classification = i+1
    if outcome != 'Draw':
        if current_board.is_checkmate():
            ending = "Checkmate"
        else:
            ending = "Time/Forfeit"

    return outcome, game.headers['Opening'], game_events, ending


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


def generate_coarse_event_log_xes(csv_path=None, pgn_path="Games/filtered_games.pgn"):

    output_path = "event_log_" + pgn_path[pgn_path.find("/")+1:]

    eco_mapping = get_eco_mapping()
    event_log = EventLog()
    engine = get_engine()
    case_id = 0

    if csv_path is not None:
        try:
            last_line = pd.read_csv(csv_path, usecols=['Case ID']).iloc[-1]
            last_case_id = last_line['Case ID']
            case_id = int(last_case_id.replace("case_", "")) + 1
        except Exception:
            print("CSV is empty or improperly formatted, starting from case_id 1.")

    with open(pgn_path) as pgn:
        while True:
            game = chess.pgn.read_game(pgn)
            if game is None or case_id == 10916:
                break
            outcome, opening, game_events, ending = create_game_event(game, case_id, eco_mapping)

            trace = Trace()
            trace.attributes["concept:name"] = f'case_{case_id}'
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
    engine.quit()

def replace_numbers_with_dots(fen):
    return ''.join('.' * int(char) if char.isdigit() else char for char in fen)

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

if __name__ == '__main__':
    print("functions.py is main")