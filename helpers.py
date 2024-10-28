def get_data_object():
    return [
        {
            "name": "Main evaluation",
            "group": "",
            "text": "<b>$</b>. An evaluation function is used to heuristically determine the relative value of a positions used in general case when no specialized evaluation or tablebase evaluation is available. In Stockfish it is never applied for positions where king of either side is in check. Resulting value is computed by combining [[Middle game evaluation]] and [[End game evaluation]]. We use <a class=\"external\" href=\"https://www.chessprogramming.org/Tapered_Eval\">Tapered Eval</a>, a technique used in evaluation to make a smooth transition between the phases of the game. [[Phase]] is a coeficient of simple linear combination. Before using  [[End game evaluation]] in this formula we also scale it down using [[Scale factor]].",
            "code": "def main_evaluation(mg=None, eg=None, pos=None, *args):\n    if mg is None:\n        mg = middle_game_evaluation(pos)\n    if eg is None:\n        eg = end_game_evaluation(pos)\n    p = phase(pos)\n    rule50 = rule_50(pos)\n    scale = scale_factor(pos, eg) / 64\n    eg = eg * scale\n    v = (mg * p + (eg * (128 - p))) // 128\n    if mg is None or eg is None:\n        v = (v // 16) * 16\n    # Add tempo adjustment\n    v += tempo(pos)\n    # Apply rule50 modification\n    v = (v * (100 - rule50)) // 100\n    return v",
            "links": [
                [
                    "https://www.chessprogramming.org/Evaluation",
                    "Evaluation in cpw"
                ],
                [
                    "https://www.chessprogramming.org/Tapered_Eval",
                    "Tapered Eval in cpw"
                ],
                [
                    "https://www.chessprogramming.org/Game_Phases",
                    "Game Phases in cpw"
                ],
                [
                    "https://www.chessprogramming.org/Tempo",
                    "Tempo in cpw"
                ]
            ],
            "eval": True,
            "squares": 0,
            "highlight": 0,
            "forwhite": False,
            "graph": False,
            "elo": None
        },
        {
            "name": "Isolated",
            "group": "Pawns",
            "text": "<b>$</b> checks if pawn is isolated. In chess, an isolated pawn is a pawn which has no friendly pawn on an adjacent file.",
            "code": "",
            "links": [
                [
                    "https://en.wikipedia.org/wiki/Isolated_pawn",
                    "Isolated pawn"
                ]
            ],
            "eval": True,
            "squares": 0,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": {
                "value": "14.8",
                "error": "4.2",
                "link": "http://tests.stockfishchess.org/tests/view/5a7b374d0ebc5902971a9a58"
            }
        },
        {
            "name": "Opposed",
            "group": "Pawns",
            "text": "<b>$</b> flag is set if there is opponent opposing pawn on the same file to prevent it from advancing.",
            "code": "",
            "links": [
                [
                    "https://www.chessprogramming.org/Evaluation",
                    "Evaluation"
                ],
                [
                    "https://www.chessprogramming.org/Tapered_Eval",
                    "Tapered Eval"
                ],
                [
                    "https://www.chessprogramming.org/Game_Phases",
                    "Game Phases"
                ]
            ],
            "eval": True,
            "squares": 0,
            "highlight": 2,
            "forwhite": True,
            "graph": False
        },
        {
            "name": "Rank",
            "group": "Helpers",
            "text": "<b>$</b> calculates rank of square.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 2,
            "highlight": 0,
            "forwhite": True
        },
        {
            "name": "File",
            "group": "Helpers",
            "text": "<b>$</b> calculates file of square.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 2,
            "highlight": 0,
            "forwhite": True
        },
        {
            "name": "Phalanx",
            "group": "Pawns",
            "text": "<b>$</b> flag is set if there is friendly pawn on adjacent file and same rank.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 0,
            "highlight": 2,
            "forwhite": True,
            "graph": False
        },
        {
            "name": "Supported",
            "group": "Pawns",
            "text": "<b>$</b> counts number of pawns supporting this pawn.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False
        },
        {
            "name": "Backward",
            "group": "Pawns",
            "text": "A pawn is <b>$</b> when it is behind all pawns of the same color on the adjacent files and cannot be safely advanced.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 0,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": None
        },
        {
            "name": "Doubled",
            "group": "Pawns",
            "text": "<b>$</b> checks if pawn is doubled. In chess, an doubled pawn is a pawn which has another friendly pawn on same file but in Stockfish we attach doubled pawn penalty only for pawn which has another friendly pawn on square directly behind that pawn and is not supported.\n\n",
            "code": "",
            "links": [
                [
                    "https://en.wikipedia.org/wiki/Doubled_pawn",
                    "Doubled pawn"
                ]
            ],
            "eval": True,
            "squares": 0,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": {
                "value": "2.25",
                "error": "2.9",
                "link": "http://tests.stockfishchess.org/tests/view/5acf80740ebc59547e5380fe"
            }
        },
        {
            "name": "Connected",
            "group": "Pawns",
            "text": "<b>$</b> checks if pawn is [[Supported]] or [[Phalanx]].",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 0,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": {
                "value": "29.34",
                "error": "4.4",
                "link": "http://tests.stockfishchess.org/tests/view/5a7a1ab60ebc5902971a99ed"
            }
        },
        {
            "name": "Middle game evaluation",
            "group": "",
            "text": "<b>$</b>. Evaluates position for the middlegame and the opening phases.",
            "code": "def middle_game_evaluation(pos, nowinnable=False):\n    v = 0\n    v += piece_value_mg(pos) - piece_value_mg(colorflip(pos))\n    v += psqt_mg(pos) - psqt_mg(colorflip(pos))\n    v += imbalance_total(pos)\n    v += pawns_mg(pos) - pawns_mg(colorflip(pos))\n    v += pieces_mg(pos) - pieces_mg(colorflip(pos))\n    v += mobility_mg(pos) - mobility_mg(colorflip(pos))\n    v += threats_mg(pos) - threats_mg(colorflip(pos))\n    v += passed_mg(pos) - passed_mg(colorflip(pos))\n    v += space(pos) - space(colorflip(pos))\n    v += king_mg(pos) - king_mg(colorflip(pos))\n    if not nowinnable:\n        v += winnable_total_mg(pos, v)\n    return v",
            "links": [],
            "eval": True,
            "squares": 0,
            "highlight": 0,
            "forwhite": False,
            "graph": False,
            "elo": None
        },
        {
            "name": "End game evaluation",
            "group": "",
            "text": "<b>$</b>. Evaluates position for the endgame phase.",
            "code": "def end_game_evaluation(pos, nowinnable=False):\n    v = 0\n    v += piece_value_eg(pos) - piece_value_eg(colorflip(pos))\n    v += psqt_eg(pos) - psqt_eg(colorflip(pos))\n    v += imbalance_total(pos)\n    v += pawns_eg(pos) - pawns_eg(colorflip(pos))\n    v += pieces_eg(pos) - pieces_eg(colorflip(pos))\n    v += mobility_eg(pos) - mobility_eg(colorflip(pos))\n    v += threats_eg(pos) - threats_eg(colorflip(pos))\n    v += passed_eg(pos) - passed_eg(colorflip(pos))\n    v += king_eg(pos) - king_eg(colorflip(pos))\n    if not nowinnable:\n        v += winnable_total_eg(pos, v)\n    return v",
            "links": [],
            "eval": True,
            "squares": 0,
            "highlight": 0,
            "forwhite": False,
            "graph": False,
            "elo": None
        },
        {
            "name": "Scale factor",
            "group": "",
            "text": "<b>$</b>. The scale factors are used to scale the endgame evaluation score down.",
            "code": "",
            "links": [
                [
                    "https://www.chessprogramming.org/Bishops_of_Opposite_Colors",
                    "Bishops of Opposite Colors in cpw"
                ]
            ],
            "eval": True,
            "squares": 0,
            "highlight": 0,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "Phase",
            "group": "",
            "text": "<b>$</b>. We define phase value for tapered eval based on the amount of non-pawn material on the board.",
            "code": "",
            "links": [
                [
                    "https://www.chessprogramming.org/Game_Phases",
                    "Game Phases in cpw"
                ],
                [
                    "https://www.chessprogramming.org/Tapered_Eval",
                    "Tapered Eval in cpw"
                ]
            ],
            "eval": True,
            "squares": 0,
            "highlight": 0,
            "forwhite": False
        },
        {
            "name": "Imbalance",
            "group": "Imbalance",
            "text": "<b>$</b> calculates the imbalance by comparing the piece count of each piece type for both colors. Evaluate the material imbalance. We use a place holder for the bishop pair \"extended piece\", which allows us to be more flexible in defining bishop pair bonuses.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 0,
            "forwhite": True,
            "graph": True,
            "elo": None
        },
        {
            "name": "Bishop count",
            "group": "Helpers",
            "text": "<b>$</b> counts number of our bishops.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True
        },
        {
            "name": "Bishop pair",
            "group": "Imbalance",
            "text": "<b>$</b>. The player with two bishops is said to have the bishop pair.",
            "code": "",
            "links": [
                [
                    "https://www.chessprogramming.org/Bishop_Pair",
                    "Bishop Pair on cpw"
                ]
            ],
            "eval": True,
            "squares": 0,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": None
        },
        {
            "name": "Pinned direction",
            "group": "Attack",
            "text": "<b>$</b>. Helper function for detecting blockers for king. For our pinned pieces result is positive for enemy blockers negative and value encodes direction of pin. 1 - horizontal, 2 - topleft to bottomright, 3 - vertical, 4 - topright to bottomleft",
            "code": "",
            "links": [
                [
                    "https://en.wikipedia.org/wiki/Pin_(chess)",
                    "Pin in wikipedia"
                ],
                [
                    "https://www.chessprogramming.org/Pin",
                    "Pin in cpw"
                ]
            ],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "Mobility",
            "group": "Mobility",
            "text": "<b>$</b>. Number of attacked squares in the [[Mobility area]]. For queen squares defended by opponent knight, bishop or rook are ignored. For minor pieces squares occupied by our  queen are ignored.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False
        },
        {
            "name": "Mobility area",
            "group": "Mobility",
            "text": "<b>$</b>. Do not include in mobility area squares protected by enemy pawns, or occupied by our blocked pawns or king. Pawns blocked or on ranks 2 and 3 will be excluded from the mobility area. Also excludes blockers for king from mobility area - blockers for king can't really move until king moves (in most cases) so logic behind it is the same as behind excluding king square from mobility area.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 0,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "Mobility bonus",
            "group": "Mobility",
            "text": "<b>$</b> attach bonuses for middlegame and endgame by piece type and [[Mobility]].",
            "code": "",
            "links": [],
            "eval": False,
            "squares": 0,
            "highlight": 0,
            "forwhite": True,
            "graph": True,
            "elo": None
        },
        {
            "name": "Knight attack",
            "group": "Attack",
            "text": "<b>$</b> counts number of attacks on square by knight.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False
        },
        {
            "name": "Bishop xray attack",
            "group": "Attack",
            "text": "<b>$</b> counts number of attacks on square by bishop. Includes x-ray attack through queens.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False
        },
        {
            "name": "Rook xray attack",
            "group": "Attack",
            "text": "<b>$</b> counts number of attacks on square by rook. Includes x-ray attack through queens and our rook.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False
        },
        {
            "name": "Queen attack",
            "group": "Attack",
            "text": "<b>$</b> counts number of attacks on square by queen.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False
        },
        {
            "name": "Outpost",
            "group": "Pieces",
            "text": "<b>$</b>. Outpost for knight or bishop.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False
        },
        {
            "name": "Outpost square",
            "group": "Pieces",
            "text": "<b>$</b>. Outpost squares for knight or bishop.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": None
        },
        {
            "name": "Reachable outpost",
            "group": "Pieces",
            "text": "<b>$</b>. Knights and bishops which can reach an outpost square in one move.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "Minor behind pawn",
            "group": "Pieces",
            "text": "<b>$</b>. Knight or bishop when behind a pawn.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": {
                "value": "-0.35",
                "error": "4.5",
                "link": "http://tests.stockfishchess.org/tests/view/5a723b850ebc590f2c86e9e5"
            }
        },
        {
            "name": "Bishop pawns",
            "group": "Pieces",
            "text": "<b>$</b>. Number of pawns on the same color square as the bishop multiplied by one plus the number of our blocked pawns in the center files C, D, E or F.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": {
                "value": "10.57",
                "error": "4.6",
                "link": "http://tests.stockfishchess.org/tests/view/5a7262390ebc590f2c86e9fc"
            }
        },
        {
            "name": "Rook on file",
            "group": "Pieces",
            "text": "<b>$</b>. Rook when on an open or semi-open file.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": {
                "value": "13.59",
                "error": "4.2",
                "link": "http://tests.stockfishchess.org/tests/view/5a78c23c0ebc5902971a991b"
            }
        },
        {
            "name": "Trapped rook",
            "group": "Pieces",
            "text": "<b>$</b>. Penalize rook when trapped by the king, even more if the king cannot castle.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": {
                "value": "2.92",
                "error": "3.7",
                "link": "http://tests.stockfishchess.org/tests/view/5a876e560ebc590297cc82d9"
            }
        },
        {
            "name": "Weak queen",
            "group": "Pieces",
            "text": "<b>$</b>. Penalty if any relative pin or discovered attack against the queen.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": {
                "value": "6.36",
                "error": "4.6",
                "link": "http://tests.stockfishchess.org/tests/view/5a73900b0ebc5902971a96a8"
            }
        },
        {
            "name": "Space area",
            "group": "Space",
            "text": "<b>$</b>. Number of safe squares available for minor pieces on the central four files on ranks 2 to 4. Safe squares one, two or three squares behind a friendly pawn are counted twice.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "Pawn attack",
            "group": "Attack",
            "text": "<b>$</b> counts number of attacks on square by pawn. Pins or en-passant attacks are not considered here.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "King attack",
            "group": "Attack",
            "text": "<b>$</b> counts number of attacks on square by king.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True
        },
        {
            "name": "Attack",
            "group": "Attack",
            "text": "<b>$</b> counts number of attacks on square by all pieces. For bishop and rook x-ray attacks are included. For pawns pins or en-passant are ignored.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 0,
            "forwhite": True
        },
        {
            "name": "Non pawn material",
            "group": "Material",
            "text": "<b>$</b>. Middlegame value of non-pawn material.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 0,
            "forwhite": True,
            "graph": False
        },
        {
            "name": "Safe pawn",
            "group": "Threats",
            "text": "<b>$</b>. Check if our pawn is not attacked or is defended.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True
        },
        {
            "name": "Threat safe pawn",
            "group": "Threats",
            "text": "<b>$</b>. Non-pawn enemies attacked by a [[Safe pawn]].",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": {
                "value": 14.95,
                "error": 4.6,
                "link": "http://tests.stockfishchess.org/tests/view/5a74bb6f0ebc5902971a9701"
            }
        },
        {
            "name": "Weak enemies",
            "group": "Threats",
            "text": "<b>$</b>. Enemies not defended by a pawn and under our attack.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False
        },
        {
            "name": "Minor threat",
            "group": "Threats",
            "text": "<b>$</b>. Threat type for knight and bishop attacking pieces.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True
        },
        {
            "name": "Rook threat",
            "group": "Threats",
            "text": "<b>$</b>. Threat type for attacked by rook pieces.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": {
                "value": "10.98",
                "error": "4.2",
                "link": "http://tests.stockfishchess.org/tests/view/5a7a14000ebc5902971a99e6"
            }
        },
        {
            "name": "Hanging",
            "group": "Threats",
            "text": "<b>$</b>. [[Weak enemies]] not defended by opponent or non-pawn [[weak enemies]] attacked twice.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": {
                "value": "2.78",
                "error": "4.6",
                "link": "http://tests.stockfishchess.org/tests/view/5a74c1ef0ebc5902971a9707"
            }
        },
        {
            "name": "King threat",
            "group": "Threats",
            "text": "<b>$</b>. Threat by king.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": {
                "value": "4.69",
                "error": "4.2",
                "link": "http://tests.stockfishchess.org/tests/view/5a7a4dea0ebc5902971a99ff"
            }
        },
        {
            "name": "Pawn push threat",
            "group": "Threats",
            "text": "<b>$</b>. Bonus if some pawns can safely push and attack an enemy piece.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": {
                "value": "7.89",
                "error": "4.5",
                "link": "http://tests.stockfishchess.org/tests/view/5a74f1300ebc5902971a9717"
            }
        },
        {
            "name": "Candidate passed",
            "group": "Passed pawns",
            "text": "<b>$</b> checks if pawn is passed or candidate passer. \nA pawn is passed if one of the three following conditions is True:\n<ul>\n<li>(a) there is no stoppers except some levers</li>\n<li>(b) the only stoppers are the leverPush, but we outnumber them</li>\n<li>(c) there is only one front stopper which can be levered.</li>\n</ul>\nIf there is a pawn of our color in the same file in front of a current pawn it's no longer counts as passed.",
            "code": "",
            "links": [
                [
                    "https://en.wikipedia.org/wiki/Passed_pawn",
                    "Passed pawn"
                ]
            ],
            "eval": True,
            "squares": 0,
            "highlight": 2,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "King proximity",
            "group": "Passed pawns",
            "text": "<b>$</b> is endgame bonus based on the king's proximity. If block square is not the queening square then consider also a second push.",
            "code": "",
            "links": [
                [
                    "https://en.wikipedia.org/wiki/Isolated_pawn",
                    "Isolated pawn"
                ]
            ],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": None
        },
        {
            "name": "Passed block",
            "group": "Passed pawns",
            "text": "<b>$</b> adds bonus if passed pawn is free to advance. Bonus is adjusted based on attacked and defended status of block square and entire path in front of pawn.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": None
        },
        {
            "name": "Passed file",
            "group": "Passed pawns",
            "text": "<b>$</b> is a bonus according to the file of a passed pawn.",
            "code": "",
            "links": [
                [
                    "https://en.wikipedia.org/wiki/Isolated_pawn",
                    "Isolated pawn"
                ]
            ],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": {
                "value": "4.08",
                "error": "4.1",
                "link": "http://tests.stockfishchess.org/tests/view/5a84ed040ebc590297cc8144"
            }
        },
        {
            "name": "Passed rank",
            "group": "Passed pawns",
            "text": "<b>$</b> is a bonus according to the rank of a passed pawn.",
            "code": "",
            "links": [
                [
                    "https://en.wikipedia.org/wiki/Isolated_pawn",
                    "Isolated pawn"
                ]
            ],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": {
                "value": "73.24",
                "error": "4.9",
                "link": "http://tests.stockfishchess.org/tests/view/5a84edbb0ebc590297cc8146"
            }
        },
        {
            "name": "Pawnless flank",
            "group": "King",
            "text": "<b>$</b>. Penalty when our king is on a pawnless flank.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 0,
            "highlight": 0,
            "forwhite": True,
            "graph": True,
            "elo": {
                "value": "1.29",
                "error": "4.5",
                "link": "http://tests.stockfishchess.org/tests/view/5a73a7000ebc5902971a96b6"
            }
        },
        {
            "name": "Strength square",
            "group": "King",
            "text": "<b>$</b>. King shelter strength for each square on board.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 0,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "Storm square",
            "group": "King",
            "text": "<b>$</b>. Enemy pawns storm for each square on board.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 0,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "Shelter strength",
            "group": "King",
            "text": "<b>$</b>. King shelter bonus for king position. If we can castle use the penalty after the castling if ([[Shelter strength]] + [[Shelter storm]]) is smaller.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 0,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": None
        },
        {
            "name": "Shelter storm",
            "group": "King",
            "text": "<b>$</b>. Shelter strom penalty for king position. If we can castle use the penalty after the castling if ([[Shelter weakness]] + [[Shelter storm]]) is smaller.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 0,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": None
        },
        {
            "name": "King pawn distance",
            "group": "King",
            "text": "<b>$</b>. Minimal distance of our king to our pawns.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 0,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": {
                "value": "3.71",
                "error": "4.2",
                "link": "http://tests.stockfishchess.org/tests/view/5a7dacfd0ebc5902971a9bc3"
            }
        },
        {
            "name": "Check",
            "group": "King",
            "text": "<b>$</b>. Possible checks by knight, bishop, rook or queen. Defending queen is not considered as check blocker.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False
        },
        {
            "name": "Safe check",
            "group": "King",
            "text": "<b>$</b>. Analyse the safe enemy's checks which are possible on next move. Enemy queen safe checks: we count them only if they are from squares from which we can't give a rook check, because rook checks are more valuable. Enemy bishops checks: we count them only if they are from squares from which we can't give a queen check, because queen checks are more valuable.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "Queen count",
            "group": "Helpers",
            "text": "<b>$</b> counts number of our queens.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True
        },
        {
            "name": "King attackers count",
            "group": "King",
            "text": "<b>$</b> is the number of pieces of the given color which attack a square in the kingRing of the enemy king. For pawns we count number of attacked squares in kingRing.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "King attackers weight",
            "group": "King",
            "text": "<b>$</b> is the sum of the \"weights\" of the pieces of the given color which attack a square in the kingRing of the enemy king.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "King attacks",
            "group": "King",
            "text": "<b>$</b> is the number of attacks by the given color to squares directly adjacent to the enemy king. Pieces which attack more than one square are counted multiple times. For instance, if there is a white knight on g5 and black's king is on g8, this white knight adds 2.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "Weak bonus",
            "group": "King",
            "text": "<b>$</b>. Weak squares in king ring.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False
        },
        {
            "name": "Weak squares",
            "group": "King",
            "text": "<b>$</b>. Attacked squares defended at most once by our queen or king.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False
        },
        {
            "name": "Winnable",
            "group": "Winnable",
            "text": "<b>$</b> computes the winnable correction value for the position, i.e., second order bonus/malus based on the known attacking/defending status of the players.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 0,
            "highlight": 0,
            "forwhite": False,
            "graph": True,
            "elo": None
        },
        {
            "name": "Unsafe checks",
            "group": "King",
            "text": "<b>$</b>. Unsafe checks.\n",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": None
        },
        {
            "name": "Tempo",
            "group": "",
            "text": "<b>$</b>. In chess, tempo refers to a \"turn\" or single move. When a player achieves a desired result in one fewer move, the player \"gains a tempo\"; and conversely when a player takes one more move than necessary, the player \"loses a tempo\". We add small bonus for having the right to move.",
            "code": "",
            "links": [
                [
                    "https://en.wikipedia.org/wiki/Tempo_(chess)",
                    "Tempo (chess) in wikipedia"
                ],
                [
                    "https://www.chessprogramming.org/Tempo",
                    "Tempo in cpw"
                ]
            ],
            "eval": True,
            "squares": 0,
            "highlight": 0,
            "forwhite": False,
            "graph": False,
            "elo": None
        },
        {
            "name": "Pawn count",
            "group": "Helpers",
            "text": "<b>$</b> counts number of our pawns.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True
        },
        {
            "name": "Connected bonus",
            "group": "Pawns",
            "text": "<b>$</b> is bonus for connected pawns.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "Mobility mg",
            "group": "Mobility",
            "text": "<b>$</b>. [[Mobility bonus]] for middlegame.",
            "code": "def eval_func(pos, square=None, param=None):\n    if square is None:\n        return sum_function(pos, mobility_mg, param)\n    return mobility_bonus(pos, square, True)",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True
        },
        {
            "name": "Mobility eg",
            "group": "Mobility",
            "text": "<b>$</b>. [[Mobility bonus]] for endgame.",
            "code": "def eval_func(pos, square=None, param=None):\n    if square is None:\n        return sum_function(pos, mobility_eg, param)\n    return mobility_bonus(pos, square, False)",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True
        },
        {
            "name": "Piece value bonus",
            "group": "Material",
            "text": "<b>$</b>. Material values for middlegame and engame.",
            "code": "",
            "links": [],
            "eval": False,
            "squares": 0,
            "highlight": 0,
            "forwhite": True,
            "graph": True,
            "elo": None
        },
        {
            "name": "Psqt bonus",
            "group": "Material",
            "text": "<b>$</b>. Piece square table bonuses. For each piece type on a given square a (middlegame, endgame) score pair is assigned.",
            "code": "",
            "links": [],
            "eval": False,
            "squares": 0,
            "highlight": 0,
            "forwhite": True,
            "graph": True,
            "elo": None
        },
        {
            "name": "Piece value mg",
            "group": "Material",
            "text": "<b>$</b>. Material - middlegame.",
            "code": "def eval_func(pos, square=None, param=None):\n    if square is None:\n        return sum_function(pos, piece_value_mg, param)\n    return piece_value_bonus(pos, square, True)",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 0,
            "forwhite": True
        },
        {
            "name": "Piece value eg",
            "group": "Material",
            "text": "<b>$</b>. Material - endgame.",
            "code": "def eval_func(pos, square=None, param=None):\n    if square is None:\n        return sum_function(pos, piece_value_eg, param)\n    return piece_value_bonus(pos, square, False)",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 0,
            "forwhite": True
        },
        {
            "name": "Psqt mg",
            "group": "Material",
            "text": "<b>$</b>. Piece square table bonuses - middlegame.",
            "code": "def eval_func(pos, square=None, param=None):\n    if square is None:\n        return sum_function(pos, psqt_mg, param)\n    return psqt_bonus(pos, square, True)",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 0,
            "forwhite": True
        },
        {
            "name": "Psqt eg",
            "group": "Material",
            "text": "<b>$</b>. Piece square table bonuses - endgame.",
            "code": "def eval_func(pos, square=None, param=None):\n    if square is None:\n        return sum_function(pos, psqt_eg, param)\n    return psqt_bonus(pos, square, False)",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 0,
            "forwhite": True
        },
        {
            "name": "King protector",
            "group": "Pieces",
            "text": "<b>$</b> add penalties and bonuses for pieces, depending on the distance from the own king.",
            "code": "",
            "links": [],
            "eval": False,
            "squares": 0,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": {
                "value": "5.82",
                "error": "4.1",
                "link": "http://tests.stockfishchess.org/tests/view/5a7af24e0ebc5902971a9a3c"
            }
        },
        {
            "name": "Knight count",
            "group": "Helpers",
            "text": "<b>$</b> counts number of our knights.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False
        },
        {
            "name": "Imbalance total",
            "group": "Imbalance",
            "text": "<b>$</b>. Second-degree polynomial material imbalance by Tord Romstad.",
            "code": "def eval_func(pos, square=None):\n    v = 0\n    v += imbalance(pos) - imbalance(colorflip(pos))\n    v += bishop_pair(pos) - bishop_pair(colorflip(pos))\n    return int(v / 16)",
            "links": [],
            "eval": True,
            "squares": 0,
            "highlight": 0,
            "forwhite": False,
            "graph": False
        },
        {
            "name": "Weak unopposed pawn",
            "group": "Pawns",
            "text": "<b>$</b>. Check if our pawn is weak and unopposed.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": {
                "value": "1.25",
                "error": "4.5",
                "link": "http://tests.stockfishchess.org/tests/view/5a74e8d40ebc5902971a9715"
            }
        },
        {
            "name": "Rook count",
            "group": "Helpers",
            "text": "<b>$</b> counts number of our rooks.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False
        },
        {
            "name": "Opposite bishops",
            "group": "Helpers",
            "text": "<b>$</b> determines if we have bishops of opposite colors.",
            "code": "",
            "links": [
                [
                    "https://www.chessprogramming.org/Bishops_of_Opposite_Colors",
                    "Bishops of Opposite Colors in cpw"
                ]
            ],
            "eval": True,
            "squares": 0,
            "highlight": 0,
            "forwhite": False,
            "graph": False
        },
        {
            "name": "King distance",
            "group": "Helpers",
            "text": "<b>$</b> counts distance to our king.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "Long diagonal bishop",
            "group": "Pieces",
            "text": "<b>$</b>. Bonus for bishop on a long diagonal which can \"see\" both center squares.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": {
                "value": "-1.15",
                "error": "2.9",
                "link": "http://tests.stockfishchess.org/tests/view/5a75acec0ebc5902971a975f"
            }
        },
        {
            "name": "Queen attack diagonal",
            "group": "Attack",
            "text": "<b>$</b> counts number of attacks on square by queen only with diagonal direction.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False
        },
        {
            "name": "Pinned",
            "group": "Attack",
            "text": "<b>$</b>. In chess, absolute pin is a situation brought on by a sliding attacking piece in which a defending piece cannot move because moving away the pinned piece would illegally expose the king to check.",
            "code": "",
            "links": [
                [
                    "https://en.wikipedia.org/wiki/Pin_(chess)",
                    "Pin in wikipedia"
                ],
                [
                    "https://www.chessprogramming.org/Pin",
                    "Pin in cpw"
                ]
            ],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False
        },
        {
            "name": "King ring",
            "group": "Helpers",
            "text": "<b>$</b> is square occupied by king and 8 squares around king. Squares defended by two pawns are removed from king ring.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "Slider on queen",
            "group": "Threats",
            "text": "<b>$</b>. Add a bonus for safe slider attack threats on opponent queen.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": None
        },
        {
            "name": "Knight on queen",
            "group": "Threats",
            "text": "<b>$</b>. Add a bonus for safe knight attack threats on opponent queen.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": None
        },
        {
            "name": "Outpost total",
            "group": "Pieces",
            "text": "<b>$</b>. Middlegame and endgame bonuses for knights and bishops outposts, bigger if outpost piece is supported by a pawn.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 0,
            "forwhite": True,
            "graph": True,
            "elo": {
                "value": "12.05",
                "error": "4.2",
                "link": "http://tests.stockfishchess.org/tests/view/5a774a8b0ebc5902971a9877"
            }
        },
        {
            "name": "Restricted",
            "group": "Threats",
            "text": "<b>$</b>. Bonus for restricting their piece moves.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": None
        },
        {
            "name": "Knight defender",
            "group": "King",
            "text": "<b>$</b>. Squares defended by knight near our king.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "Endgame shelter",
            "group": "King",
            "text": "<b>$</b>. Add an endgame component to the blockedstorm penalty so that the penalty applies more uniformly through the game.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 0,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": None
        },
        {
            "name": "Space",
            "group": "Space",
            "text": "<b>$</b> computes the space evaluation for a given side. The [[Space area]] bonus is multiplied by a weight: number of our pieces minus two times number of open files. The aim is to improve play on game opening.",
            "code": "def eval_func(pos, square=None):\n    if non_pawn_material(pos) + non_pawn_material(colorflip(pos)) < 12222:\n        return 0\n    piece_count = 0\n    blocked_count = 0\n    for x in range(8):\n        for y in range(8):\n            piece = board(pos, x, y)\n            if \"PNBRQK\".find(piece) >= 0:\n                piece_count += 1\n            if piece == \"P\" and (board(pos, x, y - 1) == \"p\" or (\n                    board(pos, x - 1, y - 2) == \"p\" and board(pos, x + 1, y - 2) == \"p\")):\n                blocked_count += 1\n            if piece == \"p\" and (board(pos, x, y + 1) == \"P\" or (\n                    board(pos, x - 1, y + 2) == \"P\" and board(pos, x + 1, y + 2) == \"P\")):\n                blocked_count += 1\n    weight = piece_count - 3 + min(blocked_count, 9)\n    return int(space_area(pos, square) * weight * weight / 16)",
            "links": [],
            "eval": True,
            "squares": 0,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": None
        },
        {
            "name": "Weak lever",
            "group": "Pawns",
            "text": "<b>$</b>. Penalize our unsupported pawns attacked twice by enemy pawns",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": None
        },
        {
            "name": "Blockers for king",
            "group": "King",
            "text": "<b>$</b>. Blockers for king\n",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": None
        },
        {
            "name": "Rook on queen file",
            "group": "Pieces",
            "text": "<b>$</b>. simple bonus for a rook that is on the same file as any queen.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": None
        },
        {
            "name": "Winnable total mg",
            "group": "Winnable",
            "text": "<b>$</b>. Middle game winnable.",
            "code": "def eval_func(pos, v=None):\n    if v is None:\n        v = middle_game_evaluation(pos, nowinnable=True)\n    return (1 if v > 0 else -1 if v < 0 else 0) * max(min(winnable(pos) + 50, 0), -abs(v))",
            "links": [],
            "eval": False,
            "squares": 0,
            "highlight": 0,
            "forwhite": False,
            "graph": False,
            "elo": None
        },
        {
            "name": "Winnable total eg",
            "group": "Winnable",
            "text": "<b>$</b>. End game winnable.",
            "code": "def eval_func(pos, v=None):\n    if v is None:\n        v = end_game_evaluation(pos, nowinnable=True)\n    return (1 if v > 0 else -1 if v < 0 else 0) * max(winnable(pos), -abs(v))",
            "links": [],
            "eval": False,
            "squares": 0,
            "highlight": 0,
            "forwhite": False,
            "graph": False,
            "elo": None
        },
        {
            "name": "Flank attack",
            "group": "King",
            "text": "<b>$</b>. Find the squares that opponent attacks in our king flank and the squares which they attack twice in that flank.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 0,
            "forwhite": True,
            "graph": True,
            "elo": {
                "value": "2.19",
                "error": "4.6",
                "link": "http://tests.stockfishchess.org/tests/view/5a7399f10ebc5902971a96b3"
            }
        },
        {
            "name": "Flank defense",
            "group": "King",
            "text": "<b>$</b>. Find the squares that we defend in our king flank.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 0,
            "forwhite": True,
            "graph": True,
            "elo": {
                "value": "2.19",
                "error": "4.6",
                "link": "http://tests.stockfishchess.org/tests/view/5a7399f10ebc5902971a96b3"
            }
        },
        {
            "name": "King danger",
            "group": "King",
            "text": "<b>$</b>. The initial value is based on the number and types of the enemy's attacking pieces, the number of attacked and undefended squares around our king and the quality of the pawn shelter.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 0,
            "highlight": 0,
            "forwhite": True,
            "graph": True,
            "elo": None
        },
        {
            "name": "King mg",
            "group": "King",
            "text": "<b>$</b> assigns middlegame bonuses and penalties for attacks on enemy king.",
            "code": "def eval_func(pos):\n    v = 0\n    kd = king_danger(pos)\n    v -= shelter_strength(pos)\n    v += shelter_storm(pos)\n    v += int(kd * kd / 4096)\n    v += 8 * flank_attack(pos)\n    v += 17 * pawnless_flank(pos)\n    return v",
            "links": [],
            "eval": True,
            "squares": 0,
            "highlight": 0,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "King eg",
            "group": "King",
            "text": "<b>$</b> assigns endgame bonuses and penalties for attacks on enemy king.",
            "code": "def eval_func(pos):\n    v = 0\n    v -= 16 * king_pawn_distance(pos)\n    v += endgame_shelter(pos)\n    v += 95 * pawnless_flank(pos)\n    v += int((king_danger(pos) / 16))\n    return v",
            "links": [],
            "eval": True,
            "squares": 0,
            "highlight": 0,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "Weak queen protection",
            "group": "Threats",
            "text": "<b>$</b>. Additional bonus if weak piece is only protected by a queen",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": None
        },
        {
            "name": "Threats mg",
            "group": "Threats",
            "text": "<b>$</b>. Middlegame threats bonus.",
            "code": "def eval_func(pos):\n    v = 0\n    v += 69 * hanging(pos)\n    v += 24 if king_threat(pos) > 0 else 0\n    v += 48 * pawn_push_threat(pos)\n    v += 173 * threat_safe_pawn(pos)\n    v += 60 * slider_on_queen(pos)\n    v += 16 * knight_on_queen(pos)\n    v += 7 * restricted(pos)\n    v += 14 * weak_queen_protection(pos)\n    for x in range(8):\n        for y in range(8):\n            s = {'x': x, 'y': y}\n            v += [0, 5, 57, 77, 88, 79, 0][minor_threat(pos, s)]\n            v += [0, 3, 37, 42, 0, 58, 0][rook_threat(pos, s)]\n    return v",
            "links": [],
            "eval": True,
            "squares": 0,
            "highlight": 0,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "Threats eg",
            "group": "Threats",
            "text": "<b>$</b>. Endgame threats bonus.",
            "code": "def eval_func(pos):\n    v = 0\n    v += 36 * hanging(pos)\n    v += 89 if king_threat(pos) > 0 else 0\n    v += 39 * pawn_push_threat(pos)\n    v += 94 * threat_safe_pawn(pos)\n    v += 18 * slider_on_queen(pos)\n    v += 11 * knight_on_queen(pos)\n    v += 7 * restricted(pos)\n    for x in range(8):\n        for y in range(8):\n            s = {'x': x, 'y': y}\n            v += [0, 32, 41, 56, 119, 161, 0][minor_threat(pos, s)]\n            v += [0, 46, 68, 60, 38, 41, 0][rook_threat(pos, s)]\n    return v",
            "links": [],
            "eval": True,
            "squares": 0,
            "highlight": 0,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "Passed leverable",
            "group": "Passed pawns",
            "text": "<b>$</b>. Candidate passers without candidate passers w/o feasible lever.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 0,
            "highlight": 2,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "Passed mg",
            "group": "Passed pawns",
            "text": "<b>$</b> middlegame bonuses for passed pawns. Scale down bonus for candidate passers which need more than one pawn push to become passed, or have a pawn in front of them.",
            "code": "def eval_func(pos, square=None, param=None, replacement_func=None):\n    if square is None:\n        func = replacement_func if replacement_func is not None else passed_mg\n        return sum_function(pos, func, param)\n    if not passed_leverable(pos, square):\n        return 0\n    v = 0\n    v += [0, 10, 17, 15, 62, 168, 276, None][passed_rank(pos, square)]\n    v += passed_block(pos, square)\n    v -= 11 * passed_file(pos, square)\n    return v",
            "links": [
                [
                    "https://en.wikipedia.org/wiki/Isolated_pawn",
                    "Isolated pawn"
                ]
            ],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "Passed eg",
            "group": "Passed pawns",
            "text": "<b>$</b> endgame bonuses for passed pawns. Scale down bonus for candidate passers which need more than one pawn push to become passed, or have a pawn in front of them.",
            "code": "def eval_func(pos, square=None, param=None, replacement_func=None):\n    if square is None:\n        func = replacement_func if replacement_func is not None else passed_eg\n        return sum_function(pos, func)\n    if not passed_leverable(pos, square):\n        return 0\n    v = 0\n    v += king_proximity(pos, square)\n    v += [0, 28, 33, 41, 72, 177, 260, None][passed_rank(pos, square)]\n    v += passed_block(pos, square)\n    v -= 8 * passed_file(pos, square)\n    return v",
            "links": [
                [
                    "https://en.wikipedia.org/wiki/Isolated_pawn",
                    "Isolated pawn"
                ]
            ],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "Piece count",
            "group": "Helpers",
            "text": "<b>$</b> counts number of our pieces (including pawns and king).",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "Bishop xray pawns",
            "group": "Pieces",
            "text": "<b>$</b>. Penalty for all enemy pawns xrayed by our bishop.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": None
        },
        {
            "name": "Rook on king ring",
            "group": "Pieces",
            "text": "<b>$</b>. Give bonus for rooks that are alligned with enemy kingring.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": None
        },
        {
            "name": "Bishop on king ring",
            "group": "Pieces",
            "text": "<b>$</b>. Give bonus for bishops that are alligned with enemy kingring.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": None
        },
        {
            "name": "Queen infiltration",
            "group": "Pieces",
            "text": "<b>$</b>. Bonus for queen on weak square in enemy camp. Idea is that queen feels much better when it can't be kicked away now or later by pawn moves, especially in endgame.",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": None
        },
        {
            "name": "Pieces mg",
            "group": "Pieces",
            "text": "<b>$</b>. Middlegame bonuses and penalties to the pieces of a given color and type. Mobility not included here.",
            "code": "def eval_func(pos, square=None, param=None, replacement_func=None):\n    if square is None:\n        func = replacement_func if replacement_func is not None else pieces_mg\n        return sum_function(pos, func, param)\n    if \"NBRQ\".find(board(pos, square['x'], square['y'])) < 0:\n        return 0\n    v = 0\n    v += [0, 31, -7, 30, 56][outpost_total(pos, square)]\n    v += 18 * minor_behind_pawn(pos, square)\n    v -= 3 * bishop_pawns(pos, square)\n    v -= 4 * bishop_xray_pawns(pos, square)\n    v += 6 * rook_on_queen_file(pos, square)\n    v += 16 * rook_on_king_ring(pos, square)\n    v += 24 * bishop_on_king_ring(pos, square)\n    v += [0, 19, 48][rook_on_file(pos, square)]\n    v -= trapped_rook(pos, square) * 55 * (1 if pos['c'][0] or pos['c'][1] else 2)\n    v -= 56 * weak_queen(pos, square)\n    v -= 2 * queen_infiltration(pos, square)\n    v -= (8 if board(pos, square['x'], square['y']) == \"N\" else 6) * king_protector(pos, square)\n    v += 45 * long_diagonal_bishop(pos, square)\n    return v",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "Pieces eg",
            "group": "Pieces",
            "text": "<b>$</b>. Endgame bonuses and penalties to the pieces of a given color and type. Mobility not included here.",
            "code": "def eval_func(pos, square=None, param=None, replacement_func=None):\n    if square is None:\n        func = replacement_func if replacement_func is not None else pieces_eg\n        return sum_function(pos, func, param)\n    if \"NBRQ\".find(board(pos, square['x'], square['y'])) < 0:\n        return 0\n    v = 0\n    v += [0, 22, 36, 23, 36][outpost_total(pos, square)]\n    v += 3 * minor_behind_pawn(pos, square)\n    v -= 7 * bishop_pawns(pos, square)\n    v -= 5 * bishop_xray_pawns(pos, square)\n    v += 11 * rook_on_queen_file(pos, square)\n    v += [0, 7, 29][rook_on_file(pos, square)]\n    v -= trapped_rook(pos, square) * 13 * (1 if pos['c'][0] or pos['c'][1] else 2)\n    v -= 15 * weak_queen(pos, square)\n    v += 14 * queen_infiltration(pos, square)\n    v -= 9 * king_protector(pos, square)\n    return v",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "Blocked",
            "group": "Pawns",
            "text": "<b>$</b>. Bonus for blocked pawns at 5th or 6th rank",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": None
        },
        {
            "name": "Pawn attacks span",
            "group": "Helpers",
            "text": "<b>$</b> Compute additional span if pawn is not backward nor blocked",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "Doubled isolated",
            "group": "Pawns",
            "text": "<b>$</b> is penalty if a doubled isolated pawn is stopped\nonly by a single opponent pawn on the same file.\n",
            "code": "",
            "links": [
                [
                    "https://en.wikipedia.org/wiki/Doubled_pawn",
                    "Doubled pawn"
                ]
            ],
            "eval": True,
            "squares": 0,
            "highlight": 2,
            "forwhite": True,
            "graph": True,
            "elo": None
        },
        {
            "name": "Pawns mg",
            "group": "Pawns",
            "text": "<b>$</b> is middlegame evaluation for pawns.",
            "code": "def eval_func(pos, square=None, param=None, replacement_func=None):\n    if square is None:\n        func = replacement_func if replacement_func is not None else pawns_mg\n        return sum_function(pos, func, param)\n    v = 0\n    if doubled_isolated(pos, square):\n        v -= 11\n    elif isolated(pos, square):\n        v -= 5\n    elif backward(pos, square):\n        v -= 9\n    v -= doubled(pos, square) * 11\n    v += connected(pos, square) * connected_bonus(pos, square)\n    v -= 13 * weak_unopposed_pawn(pos, square)\n    v += [0, -11, -3][blocked(pos, square)]\n    return v",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "Pawns eg",
            "group": "Pawns",
            "text": "<b>$</b> is endgame evaluation for pawns.",
            "code": "def eval_func(pos, square=None, param=None, replacement_func=None):\n    if square is None:\n        func = replacement_func if replacement_func is not None else pawns_eg\n        return sum_function(pos, func, param)\n    v = 0\n    if doubled_isolated(pos, square):\n        v -= 56\n    elif isolated(pos, square):\n        v -= 15\n    elif backward(pos, square):\n        v -= 24\n    v -= doubled(pos, square) * 56\n    if connected(pos, square):\n        v += int(connected_bonus(pos, square) * (rank(pos, square) - 3) / 4)\n    v -= 27 * weak_unopposed_pawn(pos, square)\n    v -= 56 * weak_lever(pos, square)\n    v += [0, -4, 4][blocked(pos, square)]\n    return v",
            "links": [],
            "eval": True,
            "squares": 1,
            "highlight": 2,
            "forwhite": True,
            "graph": False,
            "elo": None
        },
        {
            "name": "Rule 50",
            "group": "",
            "text": "<b>$</b>",
            "code": "",
            "links": [],
            "eval": True,
            "squares": 0,
            "highlight": 0,
            "forwhite": False,
            "graph": False,
            "elo": None
        }
    ]
