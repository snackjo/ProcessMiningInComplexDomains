# Process Mining in Complex Domains

This project contains the code which supports the analysis carried out in my master thesis project: "Process Mining in Complex Domains".

## Description

The project contains implementations of techniques used to extract high-level representations from low-level data. 
The code supports three different use cases. 

The input data is chess games in the form of PGN files or chess puzzles from the [Lichess Database](https://database.lichess.org/). The output is an event log in XES file format.

## Getting Started

### Dependencies

* Python 3.8+

* python-chess

* pm4py

* pandas

* zstandard

* chess engine such as [Stockfish](https://stockfishchess.org/download/)

### Installing

* Update path in get_engine() to your engine path
* Download game or puzzle data from the [Lichess Database](https://database.lichess.org/)

### Executing program

Depending on the use case, from main.py run
1. ```generate_fine_grained_event_log(pgn_path="Games/2017-May.pgn")```
2. ```generate_coarse_event_log_xes(pgn_path="Games/2014-March.pgn")```
3. ```generate_puzzle_move_log(file_path="0_120000_puzzles.csv", existing_xes_path=None, elo_limit=2400)```

Each function will create an event log (xes file) in the root directory. The event logs can be analysed using other tools such as [Disco](https://fluxicon.com/disco/) or [ProM](https://promtools.org/).

## Authors

Carl Jackson  
carlj0908@gmail.com

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

[Stockfish Evaluation Guide](https://hxim.github.io/Stockfish-Evaluation-Guide/)  
[lichess-puzzler](https://github.com/ornicar/lichess-puzzler)  
[Technical University of Denmark](https://www.dtu.dk/english/)  
[Humboldt University of Berlin](https://www.hu-berlin.de/en)  
