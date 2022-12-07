import pygame
import pygame.draw as draw
import random
import pygame.mouse as mouse
from ship import Ship

BOX_WIDTH = 80
BORDER = 50

BLACK = (0, 0, 0)
RED = (255, 0, 0)
DARK_GRAY = (150, 150, 150)
LIGHT_GRAY = (200, 200, 200)


def generate_ships():
    ships = []
    ships.append(Ship('Carrier', 5))
    ships.append(Ship('Battleship', 4))
    ships.append(Ship('Destroyer', 3))
    ships.append(Ship('Submarine', 3))
    ships.append(Ship('Patrol Boat', 2))
    for ship in ships:
        ship.pick_ship_coords(ships)
    return ships


def draw_shots(x_start_, y_start_, shots, color):
    for coord in shots:
        x_coord, y_coord = coord
        x_corner = x_start_ + BOX_WIDTH * x_coord
        y_corner = y_start_ + BOX_WIDTH * y_coord
        draw.line(screen, color,
                  (x_corner + BOX_WIDTH / 4, y_corner + BOX_WIDTH / 4),
                  (x_corner + BOX_WIDTH * 3/4, y_corner + BOX_WIDTH * 3/4),
                  width=4)
        draw.line(screen, color,
                  (x_corner + BOX_WIDTH / 4, y_corner + BOX_WIDTH * 3/4),
                  (x_corner + BOX_WIDTH * 3/4, y_corner + BOX_WIDTH / 4),
                  width=4)


def draw_grid(x_start, y_start, hits, misses, ships, show_ships):
    for x in range(11):
        for y in range(11):
            x_corner = x_start + BOX_WIDTH * x
            y_corner = y_start + BOX_WIDTH * y
            rect = pygame.Rect(x_corner, y_corner, BOX_WIDTH, BOX_WIDTH)
            draw.rect(screen, BLACK, rect, width=2)

            # Column labels
            if x == 0 and y != 0:
                text = font_label.render(f'{y}', False, BLACK)
                text_rect = text.get_rect(center=(y_corner + BOX_WIDTH / 2,
                                                  x_corner + BOX_WIDTH / 2))
                screen.blit(text, text_rect)

            # Row labels
            if y == 0 and x != 0:
                text = font_label.render(f'{chr(64 + x)}', False, BLACK)
                text_rect = text.get_rect(center=(y_corner + BOX_WIDTH / 2,
                                                  x_corner + BOX_WIDTH / 2))
                screen.blit(text, text_rect)

    for ship in ships:
        for coord in ship.coords:
            x, y = coord
            x_corner = x_start + BOX_WIDTH * x
            y_corner = y_start + BOX_WIDTH * y
            rect = pygame.Rect(x_corner, y_corner, BOX_WIDTH, BOX_WIDTH)
            if ship.num_parts_left:
                if show_ships:
                    draw.rect(screen, LIGHT_GRAY, rect)
            else:
                draw.rect(screen, DARK_GRAY, rect)

    draw_shots(x_start, y_start, hits, RED)
    draw_shots(x_start, y_start, misses, BLACK)


def get_coord(mouse_pos, grid_corner):
    mouse_x, mouse_y = mouse_pos
    grid_x, grid_y = grid_corner
    if not (grid_x + BOX_WIDTH < mouse_x < grid_x + BOX_WIDTH * 11
            and grid_y + BOX_WIDTH< mouse_y < grid_y + BOX_WIDTH * 11):
        return None
    return ((mouse_x - grid_x) // BOX_WIDTH, (mouse_y - grid_y) // BOX_WIDTH)


def bot_move():
    while True:
        shot_x = random.choice(range(1, 11))
        shot_y = random.choice(range(1, 11))
        selected_coord = shot_x, shot_y
        if selected_coord in p_hits + p_misses:
            continue
        break
    take_shot(selected_coord, p_ships, p_hits, p_misses)


def take_shot(selected_coord_, ships, hits, misses):
    msg = (f'You{"r opponent" * (ships == p_ships)} targetted '
           f'({selected_coord_[0]}, {chr(64 + selected_coord_[1])}).')
    is_hit, hit_ship = Ship.check_hit(ships, selected_coord_)
    if is_hit:
        hits.append(selected_coord_)
        update_msgs(msgs, msg + ' It was a hit.', RED)
        hit_ship.num_parts_left -= 1
        if hit_ship.num_parts_left == 0:
            msg = (f'You{"r opponent" * (ships == p_ships)} sunk '
                   f'{"your" if ships == p_ships else "their"} {hit_ship.name}!')
            update_msgs(msgs, msg, RED)
    else:
        misses.append(selected_coord_)
        update_msgs(msgs, msg + ' It was a miss.', BLACK)


def update_msgs(msgs_, new_msg, msg_col):
    for i, e in enumerate(msgs_[:0:-1]):
        msgs_[-1 - i] = msgs_[-2 - i]

    msgs_[0] = font_msg.render(f'{new_msg}', False, msg_col)


def check_gameover(ships):
    for ship in ships:
        if ship.num_parts_left != 0:
            return False
    if ships == p_ships:
        update_msgs(msgs, 'Your opponent sunk all of your ships. You Lose!', RED)
    else:
        update_msgs(msgs, 'You sunk all of your opponents ships. You Win!', RED)
    return True


if __name__ == "__main__":
    pygame.init()

    pygame.display.set_caption("Battleship")

    screen = pygame.display.set_mode((1910, 1910))
    p_board_pos = BORDER, BORDER
    op_board_pos = BORDER * 2 + BOX_WIDTH * 11, BORDER * 2 + BOX_WIDTH * 11

    pygame.font.init()
    font_label = pygame.font.SysFont(None, BOX_WIDTH)
    font_msg = pygame.font.SysFont(None, BOX_WIDTH * 5 // 8)
    font_restart = pygame.font.SysFont(None, BOX_WIDTH * 2)

    msgs = [None, None, None, None, None, None]

    p_ships = generate_ships()
    op_ships = generate_ships()

    p_hits = []
    p_misses = []
    op_hits = []
    op_misses = []

    is_player_turn = random.choice((True, False))

    is_gameover = False

    while True:
        screen.fill((109, 191, 219))
        draw_grid(p_board_pos[0], p_board_pos[1],
                  p_hits, p_misses, p_ships, True)
        draw_grid(op_board_pos[0], op_board_pos[1],
                  op_hits, op_misses, op_ships, False)
        for i, e in enumerate(msgs):
            if e != None:
                screen.blit(e, (op_board_pos[0], op_board_pos[1] - BOX_WIDTH * (1 + i)))
        
        if not is_gameover:
            if not is_player_turn:
                bot_move()
                is_player_turn = not is_player_turn
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if is_player_turn and mouse.get_pressed()[0]:
                        selected_coord = get_coord(mouse.get_pos(), op_board_pos)
                        if selected_coord not in op_hits + op_misses + [None]:
                            take_shot(selected_coord, op_ships, op_hits, op_misses)
                            is_player_turn = not is_player_turn

            is_gameover = check_gameover(op_ships) or check_gameover(p_ships)
        else:
            restart_rect = pygame.Rect(203, 1316, 575, 115)
            draw.rect(screen, LIGHT_GRAY, restart_rect)
            restart_button = font_restart.render('Play Again', False, BLACK)
            button_rect = restart_button.get_rect(center=(p_board_pos[0] + BOX_WIDTH * 11 // 2,
                                                          p_board_pos[1] + BOX_WIDTH * 33 // 2))
            screen.blit(restart_button, button_rect)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    print(mouse.get_pos())
                    if button_rect.collidepoint(mouse.get_pos()):
                        msgs = [None, None, None, None, None, None]

                        p_ships = generate_ships()
                        op_ships = generate_ships()

                        p_hits = []
                        p_misses = []
                        op_hits = []
                        op_misses = []

                        is_player_turn = random.choice((True, False))

                        is_gameover = False
                
        pygame.display.flip()