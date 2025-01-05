import csv

import chess

from tagger_module import cook
from tagger_module.tagger import read

csv_file_path = "C:\\Users\\carlj\\OneDrive\\Uni\\Master\\Thesis\\lichess-puzzler\\mypuzzles.csv"


def tag_puzzles():
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            puzzle_id = row["PuzzleId"]
            fen = row["FEN"]
            moves = row["Moves"]
            cp = 999999998

            puzzle_doc = {
                "_id": puzzle_id,
                "fen": fen,
                "line": moves,
                "cp": cp
            }

            puzzle = read(puzzle_doc)

            tags = cook.cook(puzzle)

            # Print the results
            print(f"Puzzle ID: {puzzle_id}")
            print(f"Tags: {tags}")
            print("---")

from typing import Dict, List
from tagger_module.model import Puzzle, TagKind

def cook_positions(puzzle: Puzzle) -> List[TagKind]:

    tags: List[(str, TagKind)] = []

    attraction_move, attraction = cook.attraction(puzzle)
    if attraction:
        tags.append((attraction_move, "attraction"))

    deflection_move, deflection = cook.deflection(puzzle)
    overloading_move, overloading = cook.overloading(puzzle)
    if deflection:
        tags.append((deflection_move, "deflection"))
    elif overloading:
        tags.append((overloading_move, "overloading"))

    advanced_pawn_move, advanced_pawn = cook.advanced_pawn(puzzle)
    if advanced_pawn:
        tags.append((advanced_pawn_move, "advancedPawn"))

    double_check_move, double_check = cook.double_check(puzzle)
    if double_check:
        tags.append((double_check_move, "doubleCheck"))

    quiet_move_move, quiet_move = cook.quiet_move(puzzle)
    if quiet_move:
        tags.append((quiet_move_move, "quietMove"))

    defensive_move_move, defensive_move = cook.defensive_move(puzzle)
    check_escape_move, check_escape = cook.check_escape(puzzle)
    if len(puzzle.mainline) > 2 and defensive_move or check_escape:
        move_to_tag = defensive_move_move if defensive_move else check_escape_move
        tags.append((move_to_tag, "defensiveMove"))

    sacrifice_move, sacrifice = cook.sacrifice(puzzle)
    if sacrifice:
        tags.append((sacrifice_move, "sacrifice"))

    x_ray_move, x_ray = cook.x_ray(puzzle)
    if x_ray:
        tags.append((x_ray_move, "xRayAttack"))

    move, fork = cook.fork(puzzle)
    if fork:
        tags.append((move, "fork"))

    hanging_piece_move, hanging_piece = cook.hanging_piece(puzzle)
    if len(puzzle.mainline) > 2 and hanging_piece:
        tags.append((hanging_piece_move, "hangingPiece"))

    trapped_piece_move, trapped_piece = cook.trapped_piece(puzzle)
    if trapped_piece:
        tags.append((trapped_piece_move, "trappedPiece"))

    discovered_attack_move, discovered_attack = cook.discovered_attack(puzzle)
    if discovered_attack:
        tags.append((discovered_attack_move, "discoveredAttack"))

    exposed_king_move, exposed_king = cook.exposed_king(puzzle)
    if exposed_king:
        tags.append((exposed_king_move, "exposedKing"))

    skewer_move, skewer = cook.skewer(puzzle)
    if skewer:
        tags.append((skewer_move, "skewer"))

    self_interference_move, self_interference = cook.self_interference(puzzle)
    interference_move, interference = cook.interference(puzzle)
    if self_interference or interference:
        move_to_tag = self_interference_move if self_interference else interference_move
        tags.append((move_to_tag, "interference"))

    intermezzo_move, intermezzo = cook.intermezzo(puzzle)
    if intermezzo:
        tags.append((intermezzo_move, "intermezzo"))

    pin_prevents_attack_move, pin_prevents_attack = cook.pin_prevents_attack(puzzle)
    pin_prevents_escape_move, pin_prevents_escape = cook.pin_prevents_escape(puzzle)
    if pin_prevents_attack or pin_prevents_escape:
        move_to_tag = pin_prevents_attack_move if pin_prevents_attack else pin_prevents_escape_move
        tags.append((move_to_tag, "pin"))

    attacking_f2_f7_move, attacking_f2_f7 = cook.attacking_f2_f7(puzzle)
    if attacking_f2_f7:
        tags.append((attacking_f2_f7_move, "attackingF2F7"))

    clearance_move, clearance = cook.clearance(puzzle)
    if clearance:
        tags.append((clearance_move, "clearance"))

    en_passant_move, en_passant = cook.en_passant(puzzle)
    if en_passant:
        tags.append((en_passant_move, "enPassant"))

    castling_move, castling = cook.castling(puzzle)
    if castling:
        tags.append((castling_move, "castling"))

    promotion_move, promotion = cook.promotion(puzzle)
    if promotion:
        tags.append((promotion_move, "promotion"))

    under_promotion_move, under_promotion = cook.under_promotion(puzzle)
    if under_promotion:
        tags.append((under_promotion_move, "underPromotion"))

    capturing_defender_move, capturing_defender = cook.capturing_defender(puzzle)
    if capturing_defender:
        tags.append((capturing_defender_move, "capturingDefender"))

    if "backRankMate" not in tags and "fork" not in tags:
        kingside_attack_move, kingside_attack = cook.kingside_attack(puzzle)
        queenside_attack_move, queenside_attack = cook.queenside_attack(puzzle)
        if kingside_attack:
            tags.append((kingside_attack_move, "kingsideAttack"))
        elif queenside_attack:
            tags.append((queenside_attack_move, "queensideAttack"))

        # position_tags[index] = tags
        # board.push(node.move)

    return tags


def main():
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            puzzle_doc = {
                "_id": row["PuzzleId"],
                "fen": row["FEN"],
                "line": row["Moves"],
                "cp": 999999998
            }
            puzzle = read(puzzle_doc)

    position_tags = cook_positions(puzzle)
    print(position_tags)



if __name__ == "__main__":
    main()