import arcade
import time
from display import Display
from opening import OpeningTree

def opening_explorer(filename, width, height):
    start_time = time.time()  # Record the start time
    opening_tree = OpeningTree()
    opening_tree.load_opening_tree(filename)
    end_time = time.time()  # Record the end time
    print(opening_tree.current_node)

    loading_time = end_time - start_time
    print(f"Opening tree loaded in {loading_time:.2f} seconds")

    display = Display(opening_tree, width, height)
    arcade.run()

"""opening_tree = OpeningTree()
opening_tree.build_opening_tree(min_occurrences=5000, engine_time=1)
opening_tree.save_opening_tree("Trees/masters_5000.pgn")"""
opening_explorer("Trees/masters_10000.pgn", 1300, 800)