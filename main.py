"""from HttpRequests.chess_api import ChessAPI
chess_api_hikaru = ChessAPI("hikaru", "2018", "01")
games_pgn = chess_api_hikaru.get_games()
print(games_pgn)
"""
import inspect
import pandas as pd
import re
import time
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
from helpers import get_data_object
import pm4py
import pandas as pd
from pm4py.objects.log.util import dataframe_utils
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.algo.discovery.heuristics import algorithm as heuristics_miner
from pm4py.visualization.heuristics_net import visualizer as hn_visualizer


def process_game(game, case_id, data):
    # print(f"Processing Game {game.headers['Event']}, White: {game.headers['White']}, Black {game.headers['Black']}")
    print(f"Processing Game {case_id}")
    current_board = game.board()
    item_sums, group_list = run_and_get_grouplist(game, current_board, data)
    elem_list = [entry['elem'] for entry in group_list]

    game_events = []

    for i, item in enumerate(item_sums, start=1):
        prev = (i - 1) * 4
        cur = i * 4
        largest_three = sorted(zip(item, elem_list), reverse=True)[:3]

        activities = ", ".join([biggest[1] for biggest in largest_three])

        game_events.append({
            'Case ID': f'case_{case_id}',
            'Timestamp': f'move_{prev}-{cur}',
            'Activity': activities
        })

    return game_events


def call_with_param(func, position):
    sig = inspect.signature(func)

    kwargs = {}

    if 'replacement_func' in sig.parameters:
        kwargs['replacement_func'] = func

    return func(position, **kwargs)


def get_group_list(position, data):
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


def run_and_get_grouplist(game, current_board, data):
    # all_groups = []
    item_sums = []
    recent_items = []
    item_length = 50
    group_list = []
    for move_num, move in enumerate(game.mainline_moves(), start=1):
        is_captured: bool = current_board.is_capture(move)
        current_board.push(move)

        if not is_captured:
            group_list = get_group_list(board_to_position(current_board), data)
            # all_groups.append(group_list)
            item_third_elements = [{group['elem']: group['item'][2]} for group in group_list]
            recent_items.append(item_third_elements)
            item_length = len(item_third_elements)

        if move_num % 4 == 0:
            add_items(item_length, item_sums, recent_items)

    add_items(item_length, item_sums, recent_items)

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


def generate_event_log():
    data = get_data_object()
    event_log = []
    pgn_path = "Games/RuyLopezChigorin2019.pgn"
    with open(pgn_path) as pgn:
        case_id = 1
        while True:
            game = chess.pgn.read_game(pgn)
            if game is None or case_id == 300:
                break
            start = time.time()
            game_events = process_game(game, case_id, data)
            event_log.extend(game_events)
            end = time.time()
            print(end - start)

            case_id += 1
    event_log_df = pd.DataFrame(event_log)
    event_log_df.to_csv('event_log.csv', index=False)


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


def mine_log():
    df = pd.read_csv("event_log.csv")
    df.rename(columns={
        "Case ID": "case:concept:name",
        "Timestamp": "time:timestamp",
        "Activity": "concept:name"
    }, inplace=True)
    df = dataframe_utils.convert_timestamp_columns_in_df(df)
    event_log = log_converter.apply(df)
    heu_net = heuristics_miner.apply_heu(event_log, parameters={
        heuristics_miner.Variants.CLASSIC.value.Parameters.DEPENDENCY_THRESH: 0.9,
        heuristics_miner.Variants.CLASSIC.value.Parameters.MIN_ACT_COUNT: 5,
        heuristics_miner.Variants.CLASSIC.value.Parameters.MIN_DFG_OCCURRENCES: 5
    })
    print(heu_net)
    gviz = hn_visualizer.apply(heu_net)
    hn_visualizer.view(gviz)


def main() -> None:
    print_largest_changes()

    # debug_at_move(game, board, engine, 53)

    # generate_event_log()

    # mine_log()


if __name__ == '__main__':
    main()
