from attrs import field
import pygame
import math
import numpy as np


class Charge():

    def __init__(self, pos: tuple, mag: float):
        # position and magnitude of the charge
        self.pos = Vector(pos[0], pos[1])
        self.mag = mag

        # + / - sign text
        self.cfont = pygame.font.SysFont('couriernew, consolas, monospace', 20, bold=True)
        if self.mag > 0 :
            self.csurface = self.cfont.render("+", True, (255,255,255))
        else:
            self.csurface = self.cfont.render("-", True, (255,255,255))
        self.crect = self.csurface.get_rect(center=(int(self.pos.x), int(self.pos.y)))

        # magnitude text
        self.mfont = pygame.font.SysFont('couriernew, consolas, monospace', 15, bold=True)
        self.msurface = self.mfont.render(f"{self.mag} C", True, (150,150,150))
        self.mrect = self.msurface.get_rect(center=(int(self.pos.x), int(self.pos.y + self.csurface.get_height()/2 + 10)))

        # radius of circle around the charge
        self.radius = self.csurface.get_width()/2+4

    # update the magnitude and sign of charge 
    def update(self):
        if self.mag > 0 :
            self.csurface = self.cfont.render("+", True, (255,255,255))
            self.crect = self.csurface.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        else:
            self.csurface = self.cfont.render("-", True, (255,255,255))
            self.crect = self.csurface.get_rect(center=(int(self.pos.x), int(self.pos.y)))

        self.msurface = self.mfont.render(f"{self.mag} C", True, (90,90,90))
        self.mrect = self.msurface.get_rect(center=(int(self.pos.x), int(self.pos.y + self.csurface.get_height()/2 + 6)))

    # draw the charges (+ / - , circle, magnitude)
    def draw_charge(self, surface):
        pygame.draw.circle(surface, (255,255,255), self.crect.center, self.radius, width=1)
        surface.blit(self.csurface, self.crect)
        surface.blit(self.msurface, self.mrect)
        
class Hair():

    def __init__(self, charges, screen_size, density=0.035):
        self.charges = charges
        self.width = screen_size[0]
        self.height = screen_size[1]
        self.density = density
        self.angles = np.zeros((int(self.density*self.width + 3), int(self.density*self.height + 3)))
        
    def update(self, charges):
        self.charges = charges
    
    def calculate_angle(self, net_field):
        return math.atan2(-net_field.y, net_field.x)
    
    def calculate_field(self, x, y):
        net_field = Vector(0,0)
        p = Vector(x, y)
        for charge in self.charges:
            r = p - charge.pos
            dist = abs(r)
            if dist < 1:
                continue
            ru = r.normalize()
            field = ru*(charge.mag/(abs(r)*abs(r)))
            net_field = net_field + field
        return net_field

    def draw(self, screen):
        for i in range(int(self.density*self.width + 3)):
            for j in range(int(self.density*self.height + 3)):
                x = i/self.density
                y = j/self.density
                field = self.calculate_field(x, y)
                angle = self.calculate_angle(field)
                t = 1 / (1 + np.exp(-abs(field)*800))

                end_x = x + 20*t*np.cos(angle)
                end_y = y - 20*t*np.sin(angle)
                pygame.draw.line(screen, (100,100,100), (x, y), (end_x, end_y), width=1)

class Field():

    def __init__(self, charges, screen_size, lines_per_charge=6):
        self.charges = charges
        self.angles = np.linspace(0, 2*np.pi, num=lines_per_charge+1)
        self.width = screen_size[0]
        self.height = screen_size[1]

    # update number of charges
    def update(self, charges):
        self.charges = charges

    # calculate and return the net field (Vector) at a point (x,y)
    def calculate_field(self, x, y):
        net_field = Vector(0,0)
        p = Vector(x, y)
        for charge in self.charges:
            r = p - charge.pos
            dist = abs(r)
            if dist < 1:
                continue
            ru = r.normalize()
            field = ru*(charge.mag/(abs(r)*abs(r)))
            net_field = net_field + field
        return net_field
    
    # draw all the lines for all the charges
    def draw(self, screen):
        for charge in self.charges:
            if charge.mag == 0:
                continue
            for angle in self.angles:
                # point 2 outside the charge circle
                x = charge.pos.x + ((charge.radius + 2) * np.cos(angle))
                y = charge.pos.y + ((charge.radius + 2) * np.sin(angle))

                if charge.mag < 0:
                    self.draw_fline(x, y, screen, reverse=True)
                else:
                    self.draw_fline(x, y, screen, reverse=False)

    # draw a single field line based on the starting coordinates
    def draw_fline(self, x, y, screen, reverse=False):
        curr_x = x
        curr_y = y

        # an upper bound to steps ensure that the loop doesn't get stuck between a equilibrium point, and run back and forth infinitely
        steps = 0
        max_steps = 2000

        # keep drawing the line as long as it stays inside the screen and num of steps dont exceed max steps
        while(curr_x < self.width and curr_y < self.height and curr_x > 0 and curr_y > 0 and steps < max_steps):
            steps += 1

            # to check if the line hits a charge, because then the field will become infinite (1/0 while calculating field in the next step)
            hit_charge = False
            curr_p = Vector(curr_x, curr_y)
            for charge in self.charges:
                if abs(curr_p - charge.pos) < charge.radius:
                    hit_charge = True
                    break
            
            if hit_charge:
                break

            # net field at current pos (curr_x, curr_y)
            curr_f = self.calculate_field(curr_x, curr_y)
            # break loop if the field is too week
            if abs(curr_f) <= 0.00001:
                break           
            
            # init vector in the direction of net field
            curr_fu = curr_f.normalize()
            if reverse:
                # for negative charges, the lines are integrated in the opposite dirn to the field vector
                end_x = curr_x - curr_fu.x * 4
                end_y = curr_y - curr_fu.y * 4
            else:
                # for positive charges, the lines are integrated along the field vector
                end_x = curr_x + curr_fu.x * 4
                end_y = curr_y + curr_fu.y * 4
            
            pygame.draw.line(screen, (100,100,100), (curr_x, curr_y), (end_x, end_y), width=1)
            
            curr_x = end_x
            curr_y = end_y

class Heatmap():
    
    def __init__(self, charges, screen_size, density=0.09):
        self.charges = charges
        self.width = screen_size[0]
        self.height = screen_size[1]
        self.density = density
        self.angles = np.zeros((int(self.density*self.width + 3), int(self.density*self.height + 3)))
        
    def update(self, charges):
        self.charges = charges
    
    def calculate_potential(self, x, y):
        potential = 0
        p = Vector(x, y)
        for charge in self.charges:
            r = p - charge.pos
            dist = abs(r)
            if dist < 1:
                continue
            potential += charge.mag/dist
        return potential
    
    def get_color(self, level, min_val, max_val):
        level = max(min_val, min(max_val, level))
        t = (level - min_val) / (max_val - min_val)
        
        # 3 color points: Cold (Blue), Mid (Green), Hot (Red)
        c_blue  = (0, 0, 80)
        c_purple = (30, 0, 50)
        c_red   = (150, 0, 0)
        
        if t < 0.5:
            # Scale t from [0.0, 0.5] to [0.0, 1.0] range for the first transition
            t_sub = t / 0.5
            r = int(c_blue[0] + t_sub * (c_purple[0] - c_blue[0]))
            g = int(c_blue[1] + t_sub * (c_purple[1] - c_blue[1]))
            b = int(c_blue[2] + t_sub * (c_purple[2] - c_blue[2]))
        else:
            # Scale t from [0.5, 1.0] [0.0, 1.0] range for the second transition
            t_sub = (t - 0.5) / 0.5
            r = int(c_purple[0] + t_sub * (c_red[0] - c_purple[0]))
            g = int(c_purple[1] + t_sub * (c_red[1] - c_purple[1]))
            b = int(c_purple[2] + t_sub * (c_red[2] - c_purple[2]))
            
        return (r, g, b)
    
    def draw(self, screen):
        for i in range(int(self.density*self.width )):
            for j in range(int(self.density*self.height )):
                x = i/self.density
                y = j/self.density
                potential = self.calculate_potential(x, y)
                color = self.get_color(1.2*potential, -.6, .6)

    

                pygame.draw.rect(screen, color, (x, y, 1/self.density, 1/self.density), width=0)

class Equipotential():
    def __init__(self, charges, screen_size, cell_size=10, v_step=0.2, max_v=1.5):
        self.charges = charges
        self.width = screen_size[0]
        self.height = screen_size[1]
        self.cell_size = cell_size  # Size of each grid square in pixels
        self.v_step = v_step        # Potential difference between consecutive rings (ΔV)
        self.max_v = max_v          # Maximum potential to draw (to prevent infinity at centers)
        
        # Grid dimensions
        self.cols = int(self.width / self.cell_size) + 1
        self.rows = int(self.height / self.cell_size) + 1
        
        # Pre-generate target potential levels: [-max_v, ..., -v_step, v_step, ..., max_v]
        pos_levels = np.arange(self.v_step, self.max_v, self.v_step)
        neg_levels = np.arange(-self.max_v, 0, self.v_step)
        self.levels = np.concatenate((neg_levels, pos_levels))

    def update(self, charges):
        self.charges = charges

    def calculate_potential_grid(self):
        # Calculates scalar potential across a 2D grid using fast numpy broadcasting.
        x = np.linspace(0, self.width, self.cols)
        y = np.linspace(0, self.height, self.rows)
        xx, yy = np.meshgrid(x, y)
        
        grid = np.zeros((self.rows, self.cols))
        
        for charge in self.charges:
            if charge.mag == 0:
                continue
            # Euclidean distance from every grid point to the charge
            dx = xx - charge.pos.x
            dy = yy - charge.pos.y
            dist = np.sqrt(dx*dx + dy*dy)
            
            # Prevent division by zero inside the charge radius
            dist[dist < 5] = 5
            
            grid += charge.mag / dist
            
        return grid

    def interpolate(self, x1, y1, val1, x2, y2, val2, target_val):
        """Linearly interpolates the exact coordinate where the edge crosses target_val."""
        if val1 == val2:
            return (x1, y1)
        t = (target_val - val1) / (val2 - val1)
        t = max(0.0, min(1.0, t))  # Clamp between 0 and 1
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))

    def draw(self, screen):
        # 1. Compute potential at all grid intersections
        grid = self.calculate_potential_grid()
        cs = self.cell_size

        # 2. Iterate through target potential levels (ΔV)
        for val in self.levels:
            # Choose color: red/orange for positive potential, cyan/blue for negative
            color = (255, 100, 50) if val > 0 else (50, 180, 255)

            # 3. Marching Squares: evaluate each cell
            for r in range(self.rows - 1):
                for c in range(self.cols - 1):
                    # Corner potentials of the current cell
                    tl = grid[r, c]
                    tr = grid[r, c+1]
                    br = grid[r+1, c+1]
                    bl = grid[r+1, c]

                    # Determine 4-bit binary state (which corners are above threshold)
                    state = 0
                    if tl > val: state |= 8
                    if tr > val: state |= 4
                    if br > val: state |= 2
                    if bl > val: state |= 1

                    # If all corners are above or all below, line doesn't cross this cell
                    if state == 0 or state == 15:
                        continue

                    # Corner coordinates in pixel space
                    x_left = c * cs
                    x_right = (c + 1) * cs
                    y_top = r * cs
                    y_bottom = (r + 1) * cs

                    # Interpolate crossing points along the 4 edges
                    top = self.interpolate(x_left, y_top, tl, x_right, y_top, tr, val)
                    right = self.interpolate(x_right, y_top, tr, x_right, y_bottom, br, val)
                    bottom = self.interpolate(x_left, y_bottom, bl, x_right, y_bottom, br, val)
                    left = self.interpolate(x_left, y_top, tl, x_left, y_bottom, bl, val)

                    # Connect crossing edges based on cell state
                    lines = []
                    if state in (1, 14):   lines = [(left, bottom)]
                    elif state in (2, 13): lines = [(bottom, right)]
                    elif state in (3, 12): lines = [(left, right)]
                    elif state in (4, 11): lines = [(top, right)]
                    # elif state in (5):     lines = [(top, left), (bottom, right)] # Saddle point
                    elif state in (6, 9):  lines = [(top, bottom)]
                    elif state in (7, 8):  lines = [(top, left)]
                    # elif state in (10):    lines = [(top, right), (bottom, left)] # Saddle point

                    # Draw the segments for this cell
                    for p1, p2 in lines:
                        pygame.draw.line(screen, color, p1, p2, width=1)
    

# custom vector class
class Vector():

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    
    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y)
    
    # def __mul__(self, scalar):
    #     if isinstance(scalar, (int, float)):
    #         return Vector(self.x * scalar, self.y * scalar)
    
    def __mul__(self, other):
        if isinstance(other, Vector):
            return self.x * other.x + self.y * other.y
        elif isinstance(other, (int, float)):
            return Vector(self.x * other, self.y * other)

    def __abs__(self):
        return math.sqrt(self.x * self.x + self.y * self.y)
    
    def normalize(self):
        return self*(1/abs(self))



def main():

    pygame.init()
    HEIGHT, WIDTH = 800, 800
    screen = pygame.display.set_mode((WIDTH,HEIGHT))
    pygame.display.set_caption("Electrostatics Simulation")
    font = pygame.font.SysFont('couriernew, consolas, monospace', 15, bold=True)
    clock = pygame.time.Clock()
    running = True

    # initial charge
    c = Charge((300, 300), 40)
    charges = [c]

    lines_per_charge = 8

    field = Field(charges=charges, screen_size=(WIDTH, HEIGHT), lines_per_charge=lines_per_charge)
    hair = Hair(charges=charges, screen_size=(WIDTH, HEIGHT))
    heatmap = Heatmap(charges=charges, screen_size=(WIDTH, HEIGHT))
    equipotential = Equipotential(charges=charges, screen_size=(WIDTH, HEIGHT))

    field_on = False
    hair_on = True
    heatmap_on = True
    equipotential_on = False

    lmouse_down = False
    rmouse_down = False
    charge_selected = False
    selected_charge = None

    print("\n        ----        INSTRUCTIONS TO USE         ----    \n")
    print(" TO CREATE NEW CHARGE                - Left click on empty space")
    print(" TO MOVE A CHARGE                    - Left click, hold, drag")
    print(" TO REMOVE A CHARGE                  - Right click on charge")
    print(" TO CHANGE MAGNITUDE OF CHARGE       - Left click and hold, scroll")  
    print("\n        ----               MODES                ----    \n")
    print(" FIELD LINES                         - Press 1 to toggle on/off")     
    print(" HAIR                                - Press 2 to toggle on/off")     
    print(" HEATMAP                             - Press 3 to toggle on/off")     
    print(" EQUIPOTENTIAL                       - Press 4 to toggle on/off")     
    
    while running:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                # elif event.key == pygame.K_RETURN:
                #     charges.append(Charge((mouse_pos[0], mouse_pos[1]), 40))
                # elif event.key == pygame.K_BACKSPACE:
                #     if charge_selected:
                #         charges.remove(selected_charge)
                #         charge_selected = False
                #         selected_charge = None

                # Toggle different Modes
                if event.key == pygame.K_1:
                    field_on = not field_on
                elif event.key == pygame.K_2:
                    hair_on = not hair_on
                elif event.key == pygame.K_3:
                    heatmap_on = not heatmap_on
                elif event.key == pygame.K_4:
                    equipotential_on = not equipotential_on

            # check for mouse down
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    lmouse_down = True
                elif event.button == 3:
                    rmouse_down = True
            
            # check for mouse up
            elif event.type == pygame.MOUSEBUTTONUP:
                # diselect selected charge
                if event.button == 1:
                    lmouse_down = False
                    charge_selected = False
                    selected_charge = None
                if event.button == 3:
                    rmouse_down = False
            
            # check for mouse scroll
            elif event.type == pygame.MOUSEWHEEL:
                if charge_selected:
                    if event.y > 0:
                        selected_charge.mag += 1
                    elif event.y < 0:
                        selected_charge.mag -= 1

        screen.fill((0,0,0))

        # draw the field and update the field with new charges

        if heatmap_on:
            heatmap.draw(screen)
            heatmap.update(charges)
        if field_on:
            field.draw(screen)
            field.update(charges)
        if hair_on:
            hair.draw(screen)
            hair.update(charges)
        if equipotential_on:
            equipotential.draw(screen)
            equipotential.update(charges)


        # get mouse position (x, y)
        mouse_pos = pygame.mouse.get_pos()

        postext = font.render(f"mouse pos: x: {mouse_pos[0]}  y: {HEIGHT-mouse_pos[1]}", True, (255,255,255), (50,50,50))
        net_field = Vector(0,0)
        if not charge_selected:
            net_field = field.calculate_field(mouse_pos[0], mouse_pos[1])
        etext = font.render(f"field at mouse:  {1000*net_field.x:.4f} i + {-1000*net_field.y:.4f} j", True, (255,255,255), (50,50,50))
        screen.blit(postext, (0,0))
        screen.blit(etext, (0, postext.get_height()))

        for charge in charges:
            # check if mouse pos coinsides with charge positon and LMB is down
            if charge.crect.collidepoint(mouse_pos) and lmouse_down and not charge_selected:
                selected_charge = charge
                charge_selected = True
                # # changes selected charge's position to mouse's mosition
                # charge.pos = Vector(mouse_pos[0], mouse_pos[1])
                # charge.update()

            # to remove a charge if RMB is down
            if charge.crect.collidepoint(mouse_pos) and rmouse_down and not charge_selected:
                charges.remove(charge)

            # draw the charge
            charge.draw_charge(screen)
        
        # carry the charge along the mouse 
        if charge_selected:
            selected_charge.pos = Vector(mouse_pos[0], mouse_pos[1])
            selected_charge.update()

        # create a charge if LMB is down and no charge is selected
        if lmouse_down and not charge_selected:
            charges.append(Charge((mouse_pos[0], mouse_pos[1]), 40))
        
        

        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()