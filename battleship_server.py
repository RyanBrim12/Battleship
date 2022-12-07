import pygame
import pygame.draw as draw
import random
import pygame.mouse as mouse
import socket
from ship import Ship
import pickle

BOX_WIDTH = 25
BORDER = 10

BLACK = (0, 0, 0)
RED = (255, 0, 0)
DARK_GRAY = (150, 150, 150)
LIGHT_GRAY = (200, 200, 200)

class Battleship:
    
    
    def __init__(self):
        pygame.init()

        pygame.display.set_caption("Battleship")

        self.screen = pygame.display.set_mode((580, 580))
        self.p_board_pos = BORDER, BORDER
        self.op_board_pos = BORDER * 2 + BOX_WIDTH * 11, BORDER * 2 + BOX_WIDTH * 11

        pygame.font.init()
        self.font_label = pygame.font.SysFont(None, BOX_WIDTH)
        self.font_msg = pygame.font.SysFont(None, BOX_WIDTH * 5 // 8)
        self.font_restart = pygame.font.SysFont(None, BOX_WIDTH * 2)

        self.msgs = [None, None, None, None, None, None]
        
        self.p_ships = []
        self.op_ships = []
        self.p_hits = []
        self.p_misses = []
        self.op_hits = []
        self.op_misses = []

        self.is_player_turn = False

        self.game_over = False
        
        
    def host_game(self, host, port):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((host, port))
        server.listen(1)
        
        client, addr = server.accept()
        
        self.p_ships = self.generate_ships()
        self.op_ships = self.generate_ships()
        self.is_player_turn = random.choice((True, False))
        data_array = []
        for ship in self.p_ships + self.op_ships:
            data_array.append(pickle.dumps(ship))
        data_array.append(pickle.dumps(not self.is_player_turn))
        client.send(pickle.dumps(data_array))
        self.handle_connection(client)
        server.close()
        
        
    def connect_to_game(self, host, port):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((host, port))
        
        all_data_recieved = False
        while not all_data_recieved:
            data_array = pickle.loads(client.recv(5000))
            for d in data_array:
                if len(self.op_ships) < 5:
                    self.op_ships.append(pickle.loads(d))
                elif len(self.p_ships) < 5:
                    self.p_ships.append(pickle.loads(d))
                else:
                    self.is_player_turn = bool(pickle.loads(d))
                    all_data_recieved = True
        self.handle_connection(client)
       
       
    def handle_connection(self, client):
        while not self.game_over:
            self.display_board()
            if self.is_player_turn:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if mouse.get_pressed()[0]:
                            selected_coord = self.get_coord(mouse.get_pos(), self.op_board_pos)
                            if selected_coord not in self.op_hits + self.op_misses + [None]:
                                self.take_shot(selected_coord, self.op_ships, self.op_hits, self.op_misses)
                                self.is_player_turn = not self.is_player_turn
                                client.send(pickle.dumps(selected_coord))
            else:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()
                data = client.recv(1024)
                if not data:
                    break
                else:
                    self.take_shot(pickle.loads(data), self.p_ships, self.p_hits, self.p_misses)
                    self.is_player_turn = not self.is_player_turn
        client.close()

    @staticmethod
    def get_coord(mouse_pos, grid_corner):
        mouse_x, mouse_y = mouse_pos
        grid_x, grid_y = grid_corner
        if not (grid_x + BOX_WIDTH < mouse_x < grid_x + BOX_WIDTH * 11
                and grid_y + BOX_WIDTH< mouse_y < grid_y + BOX_WIDTH * 11):
            return None
        return ((mouse_x - grid_x) // BOX_WIDTH, (mouse_y - grid_y) // BOX_WIDTH)


    def take_shot(self, selected_coord_, ships, hits, misses):
        msg = (f'You{"r opponent" * (ships == self.p_ships)} targetted '
               f'({selected_coord_[0]}, {chr(64 + selected_coord_[1])}).')
        is_hit, hit_ship = Ship.check_hit(ships, selected_coord_)
        if is_hit:
            hits.append(selected_coord_)
            self.update_msgs(self.msgs, msg + ' It was a hit.', RED)
            hit_ship.num_parts_left -= 1
            if hit_ship.num_parts_left == 0:
                msg = (f'You{"r opponent" * (ships == self.p_ships)} sunk '
                       f'{"your" if ships == self.p_ships else "their"} {hit_ship.name}!')
                self.update_msgs(self.msgs, msg, RED)
            return 
        else:
            misses.append(selected_coord_)
            self.update_msgs(self.msgs, msg + ' It was a miss.', BLACK)


    def update_msgs(self, msgs_, new_msg, msg_col):
        for i, e in enumerate(msgs_[:0:-1]):
            msgs_[-1 - i] = msgs_[-2 - i]

        msgs_[0] = self.font_msg.render(f'{new_msg}', False, msg_col)


    def generate_ships(self):
        ships = []
        ships.append(Ship('Carrier', 5))
        ships.append(Ship('Battleship', 4))
        ships.append(Ship('Destroyer', 3))
        ships.append(Ship('Submarine', 3))
        ships.append(Ship('Patrol Boat', 2))
        for ship in ships:
            ship.pick_ship_coords(ships)
        return ships


    def display_board(self):
        self.screen.fill((109, 191, 219))
        self.draw_grid(self.p_board_pos[0], self.p_board_pos[1],
                  self.p_hits, self.p_misses, self.p_ships, True)
        self.draw_grid(self.op_board_pos[0], self.op_board_pos[1],
                  self.op_hits, self.op_misses, self.op_ships, False)
        for i, e in enumerate(self.msgs):
            if e != None:
                self.screen.blit(e, (self.op_board_pos[0],
                                     self.op_board_pos[1] - BOX_WIDTH * (1 + i)))
        pygame.display.flip()

    def draw_shots(self, x_start_, y_start_, shots, color):
        for coord in shots:
            x_coord, y_coord = coord
            x_corner = x_start_ + BOX_WIDTH * x_coord
            y_corner = y_start_ + BOX_WIDTH * y_coord
            draw.line(self.screen, color,
                      (x_corner + BOX_WIDTH / 4, y_corner + BOX_WIDTH / 4),
                      (x_corner + BOX_WIDTH * 3/4, y_corner + BOX_WIDTH * 3/4),
                      width=1)
            draw.line(self.screen, color,
                      (x_corner + BOX_WIDTH / 4, y_corner + BOX_WIDTH * 3/4),
                      (x_corner + BOX_WIDTH * 3/4, y_corner + BOX_WIDTH / 4),
                      width=1)


    def draw_grid(self, x_start, y_start, hits, misses, ships, show_ships):
        for x in range(11):
            for y in range(11):
                x_corner = x_start + BOX_WIDTH * x
                y_corner = y_start + BOX_WIDTH * y
                rect = pygame.Rect(x_corner, y_corner, BOX_WIDTH, BOX_WIDTH)
                draw.rect(self.screen, BLACK, rect, width=2)

                # Column labels
                if x == 0 and y != 0:
                    text = self.font_label.render(f'{y}', False, BLACK)
                    text_rect = text.get_rect(center=(y_corner + BOX_WIDTH / 2,
                                                      x_corner + BOX_WIDTH / 2))
                    self.screen.blit(text, text_rect)

                # Row labels
                if y == 0 and x != 0:
                    text = self.font_label.render(f'{chr(64 + x)}', False, BLACK)
                    text_rect = text.get_rect(center=(y_corner + BOX_WIDTH / 2,
                                                      x_corner + BOX_WIDTH / 2))
                    self.screen.blit(text, text_rect)

        for ship in ships:
            for coord in ship.coords:
                x, y = coord
                x_corner = x_start + BOX_WIDTH * x
                y_corner = y_start + BOX_WIDTH * y
                rect = pygame.Rect(x_corner, y_corner, BOX_WIDTH, BOX_WIDTH)
                if ship.num_parts_left:
                    if show_ships:
                        draw.rect(self.screen, LIGHT_GRAY, rect)
                else:
                    draw.rect(self.screen, DARK_GRAY, rect)

        self.draw_shots(x_start, y_start, hits, RED)
        self.draw_shots(x_start, y_start, misses, BLACK)
                
if __name__ == '__main__':
    game = Battleship()
    game.host_game("localhost", 2345)
