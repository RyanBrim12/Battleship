import pygame
import pygame.draw as draw
import random

BOX_WIDTH = 80
BORDER = 50

BLACK = (0, 0, 0)
RED = (255, 0, 0)
DARK_GRAY = (150, 150, 150)
LIGHT_GRAY = (200, 200, 200)


def generate_ships():
    ships = []
    ships.append(['Carrier', 5, pick_ship_coords(5, ships)])
    ships.append(['Battleship', 4, pick_ship_coords(4, ships)])
    ships.append(['Destroyer', 3, pick_ship_coords(3, ships)])
    ships.append(['Submarine', 3, pick_ship_coords(3, ships)])
    ships.append(['Patrol Boat', 2, pick_ship_coords(2, ships)])
    return ships


def pick_ship_coords(ship_len, ships):
    while True:
        coords = []
        x_start = random.choice(range(1, 11))
        y_start = random.choice(range(1, 11))
        if check_hit(ships, (x_start, y_start))[0]:
            continue
        coords.append((x_start, y_start))
        dir = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        for _ in range(1, ship_len):
            coord = coords[-1][0] + dir[0], coords[-1][1] + dir[1]
            if (coord[0] > 10 or coord[0] < 1
                or coord[1] > 10 or coord[1] < 1
                or check_hit(ships, coord)[0]):
                break
            coords.append(coord)
        if len(coords) == ship_len:
            return coords


def check_hit(ships, shot_coord):
    for ship in ships:
        if ship[1] > 0:
            for ship_coord in ship[2]:
                if ship_coord == shot_coord:
                    return (True, ship)
    return (False, None)


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
                text = font.render(f'{y}', True, BLACK)
                text_rect = text.get_rect(center=(y_corner + BOX_WIDTH / 2,
                                                  x_corner + BOX_WIDTH / 2))
                screen.blit(text, text_rect)

            # Row labels
            if y == 0 and x != 0:
                text = font.render(f'{chr(64 + x)}', True, BLACK)
                text_rect = text.get_rect(center=(y_corner + BOX_WIDTH / 2,
                                                  x_corner + BOX_WIDTH / 2))
                screen.blit(text, text_rect)

    for ship in ships:
        for coord in ship[2]:
            x, y = coord
            x_corner = x_start + BOX_WIDTH * x
            y_corner = y_start + BOX_WIDTH * y
            rect = pygame.Rect(x_corner, y_corner, BOX_WIDTH, BOX_WIDTH)
            if ship[1]:
                if show_ships:
                    draw.rect(screen, LIGHT_GRAY, rect)
            else:
                draw.rect(screen, DARK_GRAY, rect)

    draw_shots(x_start, y_start, hits, RED)
    draw_shots(x_start, y_start, misses, BLACK)


def get_coord(mouse_pos, grid_corner):
    mouse_x, mouse_y = mouse_pos
    grid_x, grid_y = grid_corner
    if not (grid_x < mouse_x < grid_x + BOX_WIDTH * 11
            and grid_y < mouse_y < grid_y + BOX_WIDTH * 11):
        return None
    return ((mouse_x - grid_x) // BOX_WIDTH, (mouse_y - grid_y) // BOX_WIDTH)


def bot_move():
    while True:
        shot_x = random.choice(range(1, 11))
        shot_y = random.choice(range(1, 11))
        selected_coord = shot_x, shot_y
        if selected_coord in p_hits + p_misses:
            continue
        is_hit, hit_ship = check_hit(p_ships, selected_coord)
        if is_hit:
            p_hits.append(selected_coord)
            hit_ship[1] -= 1
        else:
            p_misses.append(selected_coord)
        break


if __name__ == "__main__":
    pygame.init()

    pygame.display.set_caption("Battleship")

    screen = pygame.display.set_mode((1910, 1910))
    p_board_pos = BORDER, BORDER
    op_board_pos = BORDER * 2 + BOX_WIDTH * 11, BORDER * 2 + BOX_WIDTH * 11

    pygame.font.init()
    font = pygame.font.SysFont(None, BOX_WIDTH)

    p_ships = generate_ships()
    op_ships = generate_ships()

    p_hits = []
    p_misses = []
    op_hits = []
    op_misses = []
    
    is_player_turn = random.choice((True, False))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if is_player_turn:
                    if pygame.mouse.get_pressed()[0]:
                        selected_coord = get_coord(pygame.mouse.get_pos(),
                                                   op_board_pos)
                        if selected_coord not in op_hits + op_misses:
                            if selected_coord:
                                is_hit, hit_ship = check_hit(op_ships,
                                                             selected_coord)
                                if is_hit:
                                    op_hits.append(selected_coord)
                                    hit_ship[1] -= 1
                                else:
                                    op_misses.append(selected_coord)
                                is_player_turn = not is_player_turn

        if not is_player_turn:
            bot_move()
            is_player_turn = not is_player_turn


        screen.fill((109, 191, 219))
        draw_grid(p_board_pos[0], p_board_pos[1],
                  p_hits, p_misses, p_ships, True)
        draw_grid(op_board_pos[0], op_board_pos[1],
                  op_hits, op_misses, op_ships, False)
        pygame.display.flip()
