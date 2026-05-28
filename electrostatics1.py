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
            
# custom vector class
class Vector():

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    
    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar):
        if isinstance(scalar, (int, float)):
            return Vector(self.x * scalar, self.y * scalar)
        
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

    lmouse_down = False
    rmouse_down = False
    charge_selected = False
    selected_charge = None

    print("\n        ----        INSTRUCTIONS TO USE         ----    \n")
    print(" TO CREATE NEW CHARGE                - Left click on empty space")
    print(" TO MOVE A CHARGE                    - Left click and hold")
    print(" TO REMOVE A CHARGE                  - Right click on charge")
    print(" TO CHANGE MAGNITUDE OF CHARGE       - Left click and hold, scroll")     
    
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
        
        # draw the field and update the field with new charges
        field.draw(screen)
        field.update(charges)

        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()