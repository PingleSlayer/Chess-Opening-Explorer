import arcade
import sys
import math
import chess
from opening import OpeningTree  # Import your OpeningTree class from the opening module


class Display(arcade.Window):
    def __init__(self, opening_tree, width, height):
        super().__init__(width, height, "Chess Opening Explorer")
        arcade.set_background_color((25, 81, 85))
        self.width = width
        self.height = height
        self.x = 0
        self.y = 0
        self.current_segment = None
        self.current_button = None
        self.pov = "White"
        self.current_mode = "Frequency"
        self.current_arrows = "All"
        self.opening_tree = opening_tree

    def on_draw(self):
        self.clear()
        self.show_board()
        self.show_opening_graph(max_depth=6)
        self.show_current_node_info()
        self.show_buttons()

    def show_board(self):
        board_size = self.width / 2.5
        center_x, center_y = (3 * self.width / 2) // 2, self.height // 2

        # Create a chess board instance
        board = chess.Board(self.opening_tree.current_node.board().fen())

        # Draw the chess board
        square_size = board_size / 8
        for row in range(8):
            for col in range(8):
                if self.pov == "White":
                    square_x = center_x - (board_size / 2) + col * square_size
                    square_y = center_y - (board_size / 2) + (7 - row) * square_size
                else:
                    square_x = center_x - (board_size / 2) + (7 - col) * square_size
                    square_y = center_y - (board_size / 2) + row * square_size

                # Draw board
                if (row + col) % 2 == 0:
                    arcade.draw_rectangle_filled(square_x + square_size / 2, square_y + square_size / 2, square_size, square_size, (240, 226, 188))
                else:
                    arcade.draw_rectangle_filled(square_x + square_size / 2, square_y + square_size / 2, square_size, square_size, (52, 52, 44))

                # Draw pieces
                piece = board.piece_at(chess.square(col, 7 - row))
                if piece:
                    piece_symbol = piece.symbol().upper()
                    piece_color = "w" if piece.color == chess.WHITE else "b"
                    image_path = f"Images/{piece_color}{piece_symbol}.png"
                    texture = arcade.load_texture(image_path)
                    arcade.draw_texture_rectangle(square_x + square_size / 2, square_y + square_size / 2, square_size, square_size, texture)

        if self.current_segment and self.current_arrows != "None":
            node = self.current_segment
            while node:
                if node == self.opening_tree.current_node:
                    node = None
                else:
                    move_from = node.move.uci()[:2]  # Extract the starting square from UCI notation
                    move_to = node.move.uci()[2:]  # Extract the ending square from UCI notation

                    # Convert coordinates to integers
                    start_x = center_x - (board_size / 2) + int(ord(move_from[0].lower()) - ord('a')) * square_size + square_size / 2
                    start_y = center_y - (board_size / 2) + (8 - int(move_from[1])) * square_size + square_size / 2
                    end_x = center_x - (board_size / 2) + int(ord(move_to[0].lower()) - ord('a')) * square_size + square_size / 2
                    end_y = center_y - (board_size / 2) + (8 - int(move_to[1])) * square_size + square_size / 2

                    # Adjust coordinates based on the point of view (pov)
                    if self.pov == "White":
                        start_y, end_y = self.height - start_y, self.height - end_y

                    arrow_color = (20, 200, 20)

                    # Calculate arrowhead points
                    arrowhead_size = 25
                    angle = math.atan2(end_y - start_y, end_x - start_x)
                    arrowhead1_x = end_x - arrowhead_size * math.cos(angle + math.pi / 4)
                    arrowhead1_y = end_y - arrowhead_size * math.sin(angle + math.pi / 4)
                    arrowhead2_x = end_x - arrowhead_size * math.cos(angle - math.pi / 4)
                    arrowhead2_y = end_y - arrowhead_size * math.sin(angle - math.pi / 4)

                    # Draw the arrow
                    arcade.draw_line_strip([(start_x, start_y), (end_x, end_y), (arrowhead1_x, arrowhead1_y), (end_x, end_y), (arrowhead2_x, arrowhead2_y)], arrow_color, line_width=15)
                    node = node.parent
        elif self.current_arrows != "None":
            # Draw arrows
            child_nodes = self.opening_tree.current_node.variations

            # Sort child nodes based on frequency or evaluation, depending on current_mode setting
            if self.current_mode == "Frequency":
                child_nodes.sort(key=lambda node: self.opening_tree.get_node_information(node)["frequency"], reverse=True)
            else:
                child_nodes.sort(key=lambda node: self.opening_tree.get_node_information(node)["eval"], reverse=True)

            # Take the top 1 or 3 nodes, depending on current_arrows setting
            if self.current_arrows == "All":
                nodes_to_draw = child_nodes
            elif self.current_arrows == "1":
                nodes_to_draw = child_nodes[:1]
            elif self.current_arrows == "3":
                nodes_to_draw = child_nodes[:3]

            for child_node in nodes_to_draw:
                child_info = self.opening_tree.get_node_information(child_node)
                move_from = child_node.move.uci()[:2]  # Extract the starting square from UCI notation
                move_to = child_node.move.uci()[2:]  # Extract the ending square from UCI notation

                # Convert coordinates to integers
                start_x = center_x - (board_size / 2) + int(ord(move_from[0].lower()) - ord('a')) * square_size + square_size / 2
                start_y = center_y - (board_size / 2) + (8 - int(move_from[1])) * square_size + square_size / 2
                end_x = center_x - (board_size / 2) + int(ord(move_to[0].lower()) - ord('a')) * square_size + square_size / 2
                end_y = center_y - (board_size / 2) + (8 - int(move_to[1])) * square_size + square_size / 2

                # Adjust coordinates based on the point of view (pov)
                if self.pov == "White":
                    start_y, end_y = self.height - start_y, self.height - end_y

                if self.current_mode == "Frequency":
                    color_value = child_info["frequency"] * 2.55
                    arrow_color = (int(color_value), int(color_value), int(color_value))
                else:
                    color_value = max(0, min(255, (1 / (1 + math.exp(-5 * child_info["eval"]))) * 255))
                    arrow_color = (int(color_value), int(color_value), int(color_value))

                # Calculate arrowhead points
                arrowhead_size = 25
                angle = math.atan2(end_y - start_y, end_x - start_x)
                arrowhead1_x = end_x - arrowhead_size * math.cos(angle + math.pi / 4)
                arrowhead1_y = end_y - arrowhead_size * math.sin(angle + math.pi / 4)
                arrowhead2_x = end_x - arrowhead_size * math.cos(angle - math.pi / 4)
                arrowhead2_y = end_y - arrowhead_size * math.sin(angle - math.pi / 4)

                # Draw the arrow
                arcade.draw_line_strip([(start_x, start_y), (end_x, end_y), (arrowhead1_x, arrowhead1_y), (end_x, end_y), (arrowhead2_x, arrowhead2_y)], arrow_color, line_width=15)

    def show_opening_graph(self, _start_angle=0, _end_angle=360, max_depth=3, cur_depth=1):
        if cur_depth > max_depth:
            return

        max_width = self.width / 5
        # Draw the sunburst diagram
        center_x, center_y = (self.width/2) // 2, self.height // 2
        width = max_width/max_depth
        cumulative_angle = _start_angle
        child_nodes = self.opening_tree.current_node.variations
        for child_node in child_nodes:
            self.opening_tree.current_node = child_node
            child_info = self.opening_tree.get_node_information()
            self.opening_tree.current_node = child_node.parent

            # Calculate segment properties
            end_angle = cumulative_angle + (_end_angle - _start_angle) * (child_info["frequency"] / 100) 
            if (end_angle - cumulative_angle) > 1:
                self.opening_tree.current_node = child_node
                self.show_opening_graph(_start_angle=cumulative_angle, _end_angle=end_angle, max_depth=max_depth, cur_depth=cur_depth + 1)
                self.opening_tree.current_node = child_node.parent

                # Calculate color based on white wins percentage
                if child_node is not self.current_segment:
                    if (self.current_segment is not None) and (child_node.board().fen() == self.current_segment.board().fen()):
                        color = (50, 250, 50)
                    elif self.current_mode == "Frequency":
                        win_percentage = child_info["white_wins"] / (child_info["white_wins"] + child_info["black_wins"])
                        color_value = (1 / (1 + math.exp(-15 * (win_percentage - 0.5)))) * 255
                        color = (int(color_value), int(color_value), int(color_value))
                    else:
                        color_value = max(0, min(255, (1 / (1 + math.exp(-3 * child_info["eval"]))) * 255))
                        color = (int(color_value), int(color_value), int(color_value))
                else:
                    color = (20, 200, 20)

                # Draw the pie segment with black outline
                arcade.draw_arc_filled(center_x, center_y, 2 * cur_depth * width, 2 * cur_depth * width, color, cumulative_angle, end_angle)
                
                # Add information text
                text_x = center_x + width * (cur_depth-0.5) * math.cos(math.radians((cumulative_angle + end_angle)/2))
                text_y = center_y + width * (cur_depth-0.5) * math.sin(math.radians((cumulative_angle + end_angle)/2))
                move_text = f"{child_node.parent.board().san(child_node.move)}"

                # Display text
                arcade.draw_text(move_text, text_x, text_y, arcade.color.BLACK, font_size=10, anchor_x="center", anchor_y="center")

                
                mouse_dist = math.sqrt((self.x - center_x) ** 2 + (self.y - center_y) ** 2)
                # Check if the mouse is over the sunburst diagram
                if mouse_dist <= max_depth * width:
                    mouse_angle = math.atan2(self.y - center_y, self.x - center_x)  # atan2 handles all quadrants
                    mouse_angle = (math.degrees(mouse_angle)) % 360  # Convert radians to degrees and adjust range to [0, 360)

                    # Check if mouse is over the current segment
                    if (cumulative_angle <= mouse_angle <= end_angle) and ((cur_depth - 1) * width < mouse_dist < cur_depth * width):
                        self.current_segment = child_node
                else:
                    self.current_segment = None

            # Update cumulative angle for the next segment
            cumulative_angle = end_angle

    def show_current_node_info(self):
        if self.current_segment:
            node_info = self.opening_tree.get_node_information(self.current_segment)
        else:
            node_info = self.opening_tree.get_node_information()

        eco = node_info["eco"]
        opening_name = node_info["openingname"]
        opening_text = f"ECO: {eco}\nName: {opening_name}"
        arcade.draw_text(opening_text, 10, self.height + 35 , arcade.color.WHITE, font_size=15, anchor_x="left", anchor_y="top")
        
        total_occurrences = node_info["total_occurrence"]
        relative_frequency = node_info["frequency"]
        freq_text = f"Total: {total_occurrences}\nRelative Frequency: {relative_frequency}%"
        arcade.draw_text(freq_text, 10, self.height, arcade.color.WHITE, font_size=12, anchor_x="left", anchor_y="top")


        white_percentage = node_info["white_percentage"]
        black_percentage = node_info["black_percentage"]
        draw_percentage = node_info["draw_percentage"]
        stats_text = f"White Wins: {node_info['white_wins']} ({white_percentage}%)\nDraws: {node_info['draws']} ({draw_percentage}%)\nBlack Wins: {node_info['black_wins']} ({black_percentage}%)"
        arcade.draw_text(stats_text, 10, self.height - 25, arcade.color.WHITE, font_size=12, anchor_x="left", anchor_y="top")

        eval = node_info["eval"]
        eval_depth = node_info["evaldepth"]
        eval_text = f"Eval: {eval}\nDepth: {eval_depth}"
        arcade.draw_text(eval_text, 10, self.height - 50, arcade.color.WHITE, font_size=12, anchor_x="left", anchor_y="top")

    def show_buttons(self):
        if self.current_mode == "Frequency":
            next_text = "Next (most common)"
            colors_text = "Mode: Frequency"
        else:
            next_text = "Next (best)"
            colors_text = "Mode: Engine"
        arrows_text = "Arrows: " + self.current_arrows
        button_labels = [colors_text, arrows_text, "Start", "Previous", next_text, "Flip"]
        button_width = (self.width + 20) / len(button_labels)
        button_height = 40

        
        for i, label in enumerate(button_labels):
            button_x = (2 * i + 1) * button_width / 2
            button_y = 20

            # Determine button color based on mouse hover
            button_color = arcade.color.LIGHT_GRAY
            if (button_y - button_height / 2 <= self.y <= button_y + button_height / 2):
                if (button_x - button_width / 2 <= self.x <= button_x + button_width / 2):
                    button_color = arcade.color.GRAY
                    self.current_button = label
            else:
                self.current_button = None
            # Draw buttons
            arcade.draw_rectangle_filled(button_x, button_y, button_width, button_height, button_color)
            arcade.draw_text(label, button_x, button_y, arcade.color.BLACK, font_size=12, anchor_x="center", anchor_y="center")


    def on_mouse_motion(self, x, y, dx, dy):
        # Redraw to update hovered node information
        self.x = x 
        self.y = y 
        self.on_draw()

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.ESCAPE:
            arcade.close_window()
        
    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT and self.current_segment:
            self.opening_tree.current_node = self.current_segment
        if button == arcade.MOUSE_BUTTON_LEFT and self.current_button:
            if "Mode" in self.current_button:
                if self.current_mode == "Frequency":
                    self.current_mode = "Engine"
                else:
                    self.current_mode = "Frequency"
            if "Arrows" in self.current_button:
                if self.current_arrows == "All":
                    self.current_arrows = "None"
                elif self.current_arrows == "None":
                    self.current_arrows = "1"
                elif self.current_arrows == "1":
                    self.current_arrows = "3"
                else:
                    self.current_arrows = "All"
            if self.current_button == "Start":
                node = self.opening_tree.current_node
                while node.parent:
                    node = node.parent
                self.opening_tree.current_node = node
            if self.current_button == "Previous":
                if self.opening_tree.current_node.parent:
                    self.opening_tree.current_node = self.opening_tree.current_node.parent
            if "Next" in self.current_button and not self.opening_tree.current_node.is_end():
                is_white_turn = self.opening_tree.current_node.turn() == chess.WHITE

                key_function = lambda node: self.opening_tree.get_node_information(node)["eval"] * (1 if is_white_turn else -1)
                self.opening_tree.current_node.variations.sort(key=key_function, reverse=True)
                self.opening_tree.current_node = self.opening_tree.current_node.variations[0]
            if self.current_button == "Flip":
                if self.pov == "White":
                    self.pov = "Black"
                else:
                    self.pov = "White"
