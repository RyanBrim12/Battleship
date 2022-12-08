import random
import socket
import selectors
import pickle
import pygame
import pygame.draw as draw
import pygame.mouse as mouse
from ship import Ship

BOX_WIDTH = 25
BORDER = 10

BLACK = (0, 0, 0)
RED = (255, 0, 0)
DARK_GRAY = (150, 150, 150)
LIGHT_GRAY = (200, 200, 200)


class Battleship:

    def __init__(self, screen):
        self.screen = screen
        self.p_board_pos = BORDER, BORDER
        self.op_board_pos = (BORDER * 2 + BOX_WIDTH * 11,
                             BORDER * 2 + BOX_WIDTH * 11)

        pygame.font.init()
        self.font_label = pygame.font.SysFont(None, BOX_WIDTH)
        self.font_msg = pygame.font.SysFont(None, BOX_WIDTH * 5 // 7)

        self.msgs = [None, None, None, None, None, None]

        self.p_ships = []
        self.op_ships = []
        self.p_hits = []
        self.p_misses = []
        self.op_hits = []
        self.op_misses = []

        self.p_turn = False

        self.game_over = False

        self.bot_next_targets = []

    def host_game(self, host, port):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((host, port))
        server.listen(1)

        sel = selectors.DefaultSelector()
        sel.register(server, selectors.EVENT_READ)

        made_connection = False
        while not made_connection:
            screen.fill((109, 191, 219))
            wait_button = font_btn.render('Waiting...', False, BLACK)
            wait_button_rect = wait_button.get_rect(center=(290,290))
            screen.blit(wait_button, wait_button_rect)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()

            for key, mask in sel.select(timeout=1):
                if mask & selectors.EVENT_READ:
                    client, addr = server.accept()
                    made_connection = True

        sel = selectors.DefaultSelector()
        sel.register(client, selectors.EVENT_READ | selectors.EVENT_WRITE)

        self.p_ships = self.generate_ships()
        self.op_ships = self.generate_ships()
        self.p_turn = random.choice((True, False))

        data_array = []
        for ship in self.p_ships + self.op_ships:
            data_array.append(pickle.dumps(ship))
        data_array.append(pickle.dumps(not self.p_turn))
        client.send(pickle.dumps(data_array))
        self.handle_connection(client, sel, False)
        server.close()

    def connect_to_game(self, host, port):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((host, port))
        sel = selectors.DefaultSelector()
        sel.register(client, selectors.EVENT_READ | selectors.EVENT_WRITE)

        all_data_recieved = False
        while not all_data_recieved:
            data_array = pickle.loads(client.recv(5000))
            for d in data_array:
                if len(self.op_ships) < 5:
                    self.op_ships.append(pickle.loads(d))
                elif len(self.p_ships) < 5:
                    self.p_ships.append(pickle.loads(d))
                else:
                    self.p_turn = bool(pickle.loads(d))
                    all_data_recieved = True
        self.handle_connection(client, sel, False)

    def start_bot_game(self):
        self.p_ships = self.generate_ships()
        self.op_ships = self.generate_ships()
        self.p_turn = random.choice((True, False))
        if not self.p_turn:
            self.bot_move()
            self.p_turn = True
        self.handle_connection(None, None, True)

    def handle_connection(self, client, sel, against_bot):
        while not self.game_over:
            self.game_over = (self.check_gameover(self.p_ships)
                              or self.check_gameover(self.op_ships))
            self.display_board()
            if self.p_turn:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if mouse.get_pressed()[0]:
                            selected_coord = self.get_coord(mouse.get_pos(),
                                                            self.op_board_pos)
                            if (selected_coord not in self.op_hits
                                    + self.op_misses + [None]):
                                self.take_shot(selected_coord, self.op_ships,
                                               self.op_hits, self.op_misses)
                                if against_bot:
                                    self.bot_move()
                                else:
                                    self.p_turn = not self.p_turn
                                    client.send(pickle.dumps(selected_coord))
            else:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()
                no_data = False
                for key, mask in sel.select(timeout=1):
                    if mask & selectors.EVENT_READ:
                        data = client.recv(1024)
                        if not data:
                            no_data = True
                        else:
                            self.take_shot(pickle.loads(data), self.p_ships,
                                           self.p_hits, self.p_misses)
                            self.p_turn = not self.p_turn
                if no_data:
                    break
        if not against_bot:
            client.close()
        see_board = True
        while see_board:
            restart_rect = pygame.Rect(35, 400, 225, 40)
            draw.rect(screen, LIGHT_GRAY, restart_rect)
            restart_button = font_btn.render('Back to menu', False, BLACK)
            button_rect = restart_button.get_rect(
                 center=(self.p_board_pos[0] + BOX_WIDTH * 11 // 2,
                         self.p_board_pos[1] + BOX_WIDTH * 33 // 2))
            screen.blit(restart_button, button_rect)
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if button_rect.collidepoint(mouse.get_pos()):
                        see_board = False

    @staticmethod
    def get_coord(mouse_pos, grid_corner):
        mouse_x, mouse_y = mouse_pos
        grid_x, grid_y = grid_corner
        if not (grid_x + BOX_WIDTH < mouse_x < grid_x + BOX_WIDTH * 11
                and grid_y + BOX_WIDTH< mouse_y < grid_y + BOX_WIDTH * 11):
            return None
        return ((mouse_x - grid_x) // BOX_WIDTH,
                (mouse_y - grid_y) // BOX_WIDTH)

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
                       f'{"your" if ships == self.p_ships else "their"} '
                       f'{hit_ship.name}!')
                self.update_msgs(self.msgs, msg, RED)
            return True
        else:
            misses.append(selected_coord_)
            self.update_msgs(self.msgs, msg + ' It was a miss.', BLACK)
            return False

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
        if self.msgs[0] == None:
            self.update_msgs(self.msgs,
                             f'your{" opponents" * (not self.p_turn)} '
                             f'turn first', BLACK)
        for i, e in enumerate(self.msgs):
            if e != None:
                self.screen.blit(e,
                                 (self.op_board_pos[0],
                                  self.op_board_pos[1] - BOX_WIDTH * (1 + i)))
        pygame.display.flip()

    def draw_shots(self, x_start_, y_start_, shots, color):
        for coord in shots:
            x_coord, y_coord = coord
            x_corner = x_start_ + BOX_WIDTH * x_coord
            y_corner = y_start_ + BOX_WIDTH * y_coord
            draw.line(self.screen, color,
                      (x_corner + BOX_WIDTH / 4, y_corner + BOX_WIDTH / 4),
                      (x_corner + BOX_WIDTH * 3/4,
                       y_corner + BOX_WIDTH * 3/4),
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
                    text_rect = text.get_rect(
                         center=(y_corner + BOX_WIDTH / 2,
                                 x_corner + BOX_WIDTH / 2))
                    self.screen.blit(text, text_rect)

                # Row labels
                if y == 0 and x != 0:
                    text = self.font_label.render(f'{chr(64 + x)}',
                                                  False, BLACK)
                    text_rect = text.get_rect(
                         center=(y_corner + BOX_WIDTH / 2,
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

    def check_gameover(self, ships):
        for ship in ships:
            if ship.num_parts_left != 0:
                return False
        if ships == self.p_ships:
            self.update_msgs(self.msgs,
                             'Your opponent sunk all of your ships. '
                             'You Lose!',
                             RED)
        else:
            self.update_msgs(self.msgs,
                             'You sunk all of your opponents ships. You Win!',
                             RED)
        return True

    def bot_move(self):
        while True:
            if self.bot_next_targets:
                shot_x, shot_y = self.bot_next_targets.pop()
            else:
                shot_x = random.choice(range(1, 11))
                shot_y = random.choice(range(1, 11))
            selected_coord = shot_x, shot_y
            if selected_coord in self.p_hits + self.p_misses:
                continue
            break
        if self.take_shot(selected_coord, self.p_ships, self.p_hits,
                          self.p_misses):
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            for d in directions:
                coord = selected_coord[0] + d[0], selected_coord[1] + d[1]
                if (coord not in self.p_hits + self.p_misses and
                        coord[0] > 0 and coord[0] < 11 and
                        coord[1] > 0 and coord[1] < 11):
                    self.bot_next_targets.append(coord)


if __name__ == '__main__':
    pygame.init()

    pygame.display.set_caption('Battleship')

    screen = pygame.display.set_mode((580, 580))
    font_btn = pygame.font.SysFont(None, BOX_WIDTH * 2)

    while True:
        screen.fill((109, 191, 219))

        bot_rect = pygame.Rect(190, 180, 200, 40)
        draw.rect(screen, LIGHT_GRAY, bot_rect)
        bot_button = font_btn.render('Play Bot', False, BLACK)
        bot_button_rect = bot_button.get_rect(center=(290,200))
        screen.blit(bot_button, bot_button_rect)

        host_rect = pygame.Rect(190, 270, 200, 40)
        draw.rect(screen, LIGHT_GRAY, host_rect)
        host_button = font_btn.render('Host Game', False, BLACK)
        host_button_rect = host_button.get_rect(center=(290,290))
        screen.blit(host_button, host_button_rect)

        join_rect = pygame.Rect(190, 360, 200, 40)
        draw.rect(screen, LIGHT_GRAY, join_rect)
        join_button = font_btn.render('Join Game', False, BLACK)
        join_button_rect = join_button.get_rect(center=(290,380))
        screen.blit(join_button, join_button_rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if bot_button_rect.collidepoint(mouse.get_pos()):
                    game = Battleship(screen)
                    game.start_bot_game()
                elif host_button_rect.collidepoint(mouse.get_pos()):
                    game = Battleship(screen)
                    game.host_game('localhost', 2345)
                elif join_button_rect.collidepoint(mouse.get_pos()):
                    game = Battleship(screen)
                    game.connect_to_game('localhost', 2345)

