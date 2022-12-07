import random


class Ship:    


    def __init__(self, name, ship_len):
        self.name = name
        self.num_parts_left = ship_len
        self.coords = []
        
    
    def pick_ship_coords(self, ships):
        while True:
            coords = []
            x_start = random.choice(range(1, 11))
            y_start = random.choice(range(1, 11))
            if self.check_hit(ships, (x_start, y_start))[0]:
                continue
            coords.append((x_start, y_start))
            direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            for _ in range(1, self.num_parts_left):
                coord = coords[-1][0] + direction[0], coords[-1][1] + direction[1]
                if (coord[0] > 10 or coord[0] < 1
                    or coord[1] > 10 or coord[1] < 1
                    or self.check_hit(ships, coord)[0]):
                    break
                coords.append(coord)
            if len(coords) == self.num_parts_left:
                self.coords = coords
                break

    @staticmethod
    def check_hit(ships, shot_coord):
        for ship in ships:
            if ship.num_parts_left > 0:
                for ship_coord in ship.coords:
                    if ship_coord == shot_coord:
                        return (True, ship)
        return (False, None)
