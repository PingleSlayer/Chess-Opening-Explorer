import requests
import time
import copy
import chess
import chess.pgn
import re

class OpeningTree:
    def __init__(self):
        self.game = chess.pgn.Game()
        self.current_node = self.game
        self.memoization_dict = {}

    def get_node_information(self, node=None):
        node_information = {}
        original_node = self.current_node
        if node:   
            self.current_node = node
        node_information = self.get_opening_details(node_information)
        node_information = self.get_player_details(node_information)
        node_information = self.get_engine_details(node_information)
        self.current_node = original_node

        return node_information
    
    def get_opening_details(self, node_information):
        comment = self.current_node.comment
        opening_match = re.search(r'\[open: (.*?), (.*?)\]', comment)

        if opening_match:
            node_information['eco'] = opening_match.group(1)
            node_information['openingname'] = opening_match.group(2)
        else:
            node_information['eco'] = ""
            node_information['openingname'] = ""

            # Recursively check parents if details are empty
            if self.current_node.parent:
                original_node = self.current_node
                self.current_node = self.current_node.parent
                parent_info = {}
                parent_info = self.get_opening_details(parent_info)

                # Update current node's information if parent's details are not empty
                if parent_info['eco']:
                    node_information['eco'] = parent_info['eco']
                    node_information['openingname'] = parent_info['openingname']

                self.current_node = original_node

        return node_information
    
    def get_player_details(self, node_information):
        comment = self.current_node.comment
        wdb_match = re.search(r'\[freq: (\d+), (\d+(?:\.\d+)?)\]\[wdb: (\d+), (\d+), (\d+)\]\[wdb%: (\d+(?:\.\d+)?), (\d+(?:\.\d+)?), (\d+(?:\.\d+)?)\]', comment)
        if wdb_match:
            node_information['total_occurrence'] = int(wdb_match.group(1))
            node_information['frequency'] = float(wdb_match.group(2))
            node_information['white_wins'] = int(wdb_match.group(3))
            node_information['draws'] = int(wdb_match.group(4))
            node_information['black_wins'] = int(wdb_match.group(5))
            node_information['white_percentage'] = float(wdb_match.group(6))
            node_information['draw_percentage'] = float(wdb_match.group(7))
            node_information['black_percentage'] = float(wdb_match.group(8))
        else:
            node_information['total_occurrence'] = 0
            node_information['frequency'] = 0.0
            node_information['white_wins'] = 0
            node_information['draws'] = 0
            node_information['black_wins'] = 0
            node_information['white_percentage'] = 0.0
            node_information['draw_percentage'] = 0.0
            node_information['black_percentage'] = 0.0

        return node_information

    def get_engine_details(self, node_information):
        comment = self.current_node.comment
        eval_match = re.search(r'\[%eval ([-+]?\d*\.\d+|\d+),(\d+)\]', comment)
        if eval_match:
            node_information['eval'] = float(eval_match.group(1))
            node_information['evaldepth'] = int(eval_match.group(2))
        else:
            node_information['eval'] = "?"
            node_information['evaldepth'] = 0
        
        return node_information

    def build_opening_tree(self, url="https://explorer.lichess.ovh/masters", relative_freq=100, min_occurrences=10000, engine_time=0.1):
        fen = self.current_node.board().fen()

        if fen in self.memoization_dict:
            transposition = self.memoization_dict[fen]
            # Replace the current node with the transposition in the parent node's variations
            def add_subtree(transposition, counter):
                # Replace only the relative frequency in the copied node's comment, keeping the original total occurrences
                counter += 1
                self.current_node.comment = transposition.comment
                for transposition_variation in transposition.variations:
                    child_node = self.current_node.add_variation(chess.Move.from_uci(transposition_variation.move.uci()))
                    self.current_node = child_node
                    counter = add_subtree(transposition_variation, counter)
                    self.current_node = self.current_node.parent
                return counter
            
            counter = add_subtree(transposition, 0)
            self.current_node.comment = re.sub(r'\[freq: (\d+), \d+\]', f'[freq: \g<1>, {relative_freq}]', self.current_node.comment)

            print(f"Transposition encountered for {fen} (size: {counter})")
            return self.current_node
                
        position_info = get_position_info(fen, url)
        eval = get_stockfish_eval(self.current_node.board(), engine_time=engine_time)
        self.current_node.set_eval(eval[0], eval[1])

        opening = position_info.get("opening")
        white_wins = position_info.get("white")
        black_wins = position_info.get("black")
        draws = position_info.get("draws")
        total_occurrences = white_wins + black_wins + draws

        white_percentage = round(white_wins / total_occurrences * 100, 2)
        black_percentage = round(black_wins / total_occurrences * 100, 2)
        draw_percentage = round(draws / total_occurrences * 100, 2)

        if opening:
            self.current_node.comment += f'[open: {opening["eco"]}, {opening["name"]}]'

        self.current_node.comment += f'[freq: {total_occurrences}, {relative_freq}][wdb: {white_wins}, {draws}, {black_wins}][wdb%: {white_percentage}, {draw_percentage}, {black_percentage}]'

        print(self.current_node)
        for move in position_info.get("moves"):
            move_occurrences = move["white"] + move["draws"] + move["black"]
            if move_occurrences >= min_occurrences:
                child_node = self.current_node.add_variation(chess.Move.from_uci(move["uci"]))
                self.current_node = child_node
                relative_frequency = round(move_occurrences / total_occurrences * 100, 2)
                self.build_opening_tree(relative_freq=relative_frequency, min_occurrences=min_occurrences, engine_time=engine_time)
                self.current_node = self.current_node.parent

        self.memoization_dict[fen] = self.current_node
        return self.current_node
    
    def get_size(self, node):
        def calculate_size(current_node, current_depth):
            nonlocal size

            # Update nodes amount
            size["nodes_amount"] += 1

            # Update breadth information
            current_breadth = len(current_node.variations)
            size["total_breadth"] += current_breadth
            size["min_breadth"] = min(size["min_breadth"], current_breadth)
            size["max_breadth"] = max(size["max_breadth"], current_breadth)

            # Update depth information
            size["total_depth"] += current_depth
            size["min_depth"] = min(size["min_depth"], current_depth)
            size["max_depth"] = max(size["max_depth"], current_depth)

            # Recursively calculate size for child nodes
            for variation in current_node.variations:
                calculate_size(variation, current_depth + 1)

        # Initialize size dictionary
        size = {
            "nodes_amount": 0,
            "min_breadth": float('inf'),
            "max_breadth": 0,
            "total_breadth": 0,
            "avg_breadth": 0,
            "min_depth": float('inf'),
            "max_depth": 0,
            "total_depth": 0,
            "avg_depth": 0
        }

        # Start calculating size from the root node
        calculate_size(node, 0)

        # Calculate average breadth and depth
        size["avg_breadth"] = size["total_breadth"] / size["nodes_amount"] if size["nodes_amount"] > 0 else 0
        size["avg_depth"] = size["total_depth"] / size["nodes_amount"] if size["nodes_amount"] > 0 else 0

        return size

    def load_opening_tree(self, filename):
        with open(filename, 'r') as file:
            self.game = chess.pgn.read_game(file)
            self.current_node = self.game

    def save_opening_tree(self, filename):
        with open(filename, 'w') as file:
            file.write(str(self.game))


def get_position_info(fen, url):
    params = {"fen": fen}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 429:
        print("Opening explorer: Too many requests -> Waiting 1 minute")
        time.sleep(60)
        return get_position_info(fen, url)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return []
    

def get_stockfish_eval(board, engine_time=0.1):
    stockfish_path = "stockfish.exe"  
    with chess.engine.SimpleEngine.popen_uci(stockfish_path) as engine:
            result = engine.analyse(board, chess.engine.Limit(time=engine_time))
            pov_score = result["score"]
            depth = result["depth"]
            return pov_score, depth



