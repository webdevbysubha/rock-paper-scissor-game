import pygame
import sys
import random
from pygame import mixer

# Initialize Pygame
pygame.init()

# Initialize audio mixer with proper settings
try:
    mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    audio_enabled = True
    print("Audio initialized successfully")
except pygame.error as e:
    audio_enabled = False
    print(f"Audio initialization failed: {e}. Continuing without sound.")

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (100, 149, 237)
DARK_BLUE = (25, 25, 112)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
GOLD = (255, 215, 0)
PURPLE = (138, 43, 226)
ORANGE = (255, 165, 0)

# Game window setup
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Beat the Hand: Rock Paper Scissors")
clock = pygame.time.Clock()

# Game states
MENU = "menu"
PLAYING = "playing"
RESULT = "result"
VICTORY = "victory"
DEFEAT = "defeat"

# Load images and sounds
try:
    bg_img = pygame.image.load("assets/background.png").convert_alpha()
    bg_img = pygame.transform.scale(bg_img, (WINDOW_WIDTH, WINDOW_HEIGHT))
    
    rock_img = pygame.image.load("assets/rock.png").convert_alpha()
    paper_img = pygame.image.load("assets/paper.png").convert_alpha()
    scissors_img = pygame.image.load("assets/scissors.png").convert_alpha()
    
    rock_img = pygame.transform.scale(rock_img, (120, 120))
    paper_img = pygame.transform.scale(paper_img, (120, 120))
    scissors_img = pygame.transform.scale(scissors_img, (120, 120))
    
    # Load sounds if audio is enabled
    if audio_enabled:
        try:
            # Set volume for all sounds (0.0 to 1.0)
            click_sound = mixer.Sound("assets/click.wav")
            click_sound.set_volume(0.5)
            
            win_sound = mixer.Sound("assets/win.wav")
            win_sound.set_volume(0.4)
            
            lose_sound = mixer.Sound("assets/lose.wav")
            lose_sound.set_volume(0.4)
            
            tie_sound = mixer.Sound("assets/tie.wav")
            tie_sound.set_volume(0.4)
            
            victory_sound = mixer.Sound("assets/victory.wav")
            victory_sound.set_volume(0.6)
            
            defeat_sound = mixer.Sound("assets/defeat.wav")
            defeat_sound.set_volume(0.6)
        except Exception as e:
            print(f"Error loading sound files: {e}")
            audio_enabled = False
except Exception as e:
    print(f"Error loading assets: {e}. Please ensure all required files are in the assets folder.")
    pygame.quit()
    sys.exit()

class Button:
    def __init__(self, x, y, width, height, text, image=None, color=None, hover_color=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.image = image
        self.color = color if color else BLUE
        self.hover_color = hover_color if hover_color else DARK_BLUE
        self.is_hovered = False
        self.original_y = y
        self.current_y = y
        self.bounce_speed = 0
        self.was_hovered = False
        
    def draw(self, surface):
        if self.image:
            img_rect = self.image.get_rect(center=(self.rect.centerx, self.current_y))
            surface.blit(self.image, img_rect)
            
            if self.is_hovered:
                pygame.draw.rect(surface, GOLD, (img_rect.x-5, img_rect.y-5, 
                                img_rect.width+10, img_rect.height+10), 3, border_radius=10)
        else:
            color = self.hover_color if self.is_hovered else self.color
            pygame.draw.rect(surface, color, self.rect, border_radius=12)
            
            font = pygame.font.Font(None, 36)
            text_surface = font.render(self.text, True, WHITE)
            text_rect = text_surface.get_rect(center=self.rect.center)
            surface.blit(text_surface, text_rect)
    
    def update(self):
        if self.is_hovered and self.bounce_speed == 0:
            self.bounce_speed = -5
        elif not self.is_hovered and self.current_y != self.original_y:
            self.current_y = self.original_y
        
        if self.bounce_speed != 0:
            self.current_y += self.bounce_speed
            self.bounce_speed += 0.3
            if self.current_y >= self.original_y:
                self.current_y = self.original_y
                self.bounce_speed = 0
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.was_hovered = self.is_hovered
            self.is_hovered = self.rect.collidepoint(event.pos)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                if audio_enabled:
                    click_sound.play()
                return True
        return False

class Game:
    def __init__(self):
        self.state = MENU
        self.player_choice = None
        self.computer_choice = None
        self.result = None
        self.scores = {"player": 0, "computer": 0, "draws": 0}
        self.choice_made = False
        self.computer_reveal_timer = 0
        self.computer_revealed = False
        self.match_winner = None
        self.victory_sound_played = False
        self.defeat_sound_played = False
        self.popup_alpha = 0
        
        # Create buttons
        button_width = 200
        button_height = 60
        center_x = WINDOW_WIDTH // 2 - button_width // 2
        
        self.play_button = Button(center_x - 110, 500, button_width, button_height, "Play Game", 
                                color=GREEN, hover_color=(0, 150, 0))
        self.quit_button = Button(center_x + 110, 500, button_width, button_height, "Quit", 
                                color=RED, hover_color=(150, 0, 0))
        
        # Choice buttons
        self.rock_button = Button(120, 400, 120, 120, "", rock_img)
        self.paper_button = Button(340, 400, 120, 120, "", paper_img)
        self.scissors_button = Button(560, 400, 120, 120, "", scissors_img)
        
        self.play_again_button = Button(center_x, 450, button_width, button_height, "Play Again",
                                      color=GREEN, hover_color=(0, 150, 0))
        self.menu_button = Button(center_x, 530, button_width, button_height, "Main Menu",
                                color=BLUE, hover_color=DARK_BLUE)
        self.next_match_button = Button(center_x, 400, button_width, button_height, "Next Match",
                                      color=GREEN, hover_color=(0, 150, 0))
    
    def reset_scores(self):
        self.scores = {"player": 0, "computer": 0, "draws": 0}
    
    def reset_match(self):
        self.reset_scores()
        self.reset_round()
        self.victory_sound_played = False
        self.defeat_sound_played = False
    
    def handle_menu(self, event):
        if self.play_button.handle_event(event):
            self.state = PLAYING
            self.reset_match()
        elif self.quit_button.handle_event(event):
            pygame.quit()
            sys.exit()
    
    def handle_playing(self, event):
        if not self.choice_made:
            if self.rock_button.handle_event(event):
                self.make_choice("rock")
            elif self.paper_button.handle_event(event):
                self.make_choice("paper")
            elif self.scissors_button.handle_event(event):
                self.make_choice("scissors")
    
    def handle_result(self, event):
        if self.play_again_button.handle_event(event):
            self.state = PLAYING
            self.reset_round()
        elif self.menu_button.handle_event(event):
            self.state = MENU
            self.reset_round()
            self.reset_scores()
    
    def handle_victory_defeat(self, event):
        if self.next_match_button.handle_event(event):
            self.state = PLAYING
            self.reset_match()
        elif self.menu_button.handle_event(event):
            self.state = MENU
            self.reset_match()
    
    def make_choice(self, choice):
        self.player_choice = choice
        self.computer_choice = random.choice(["rock", "paper", "scissors"])
        self.choice_made = True
        self.computer_revealed = False
        self.computer_reveal_timer = pygame.time.get_ticks()
    
    def update(self):
        # Update all buttons
        self.play_button.update()
        self.quit_button.update()
        self.rock_button.update()
        self.paper_button.update()
        self.scissors_button.update()
        self.play_again_button.update()
        self.menu_button.update()
        self.next_match_button.update()
        
        # Handle computer choice reveal animation
        if self.choice_made and not self.computer_revealed:
            if pygame.time.get_ticks() - self.computer_reveal_timer > 1000:
                self.computer_revealed = True
                self.calculate_result()
        
        # Animation updates
        if self.state == RESULT:
            self.player_choice_anim = min(self.player_choice_anim + 2, 20)
            self.computer_choice_anim = min(self.computer_choice_anim + 2, 20)
        else:
            self.player_choice_anim = 0
            self.computer_choice_anim = 0
        
        # Popup animation
        if self.state in (VICTORY, DEFEAT):
            self.popup_alpha = min(self.popup_alpha + 5, 180)
        else:
            self.popup_alpha = 0
    
    def calculate_result(self):
        if self.player_choice == self.computer_choice:
            self.result = "It's a tie!"
            self.scores["draws"] += 1
            if audio_enabled:
                tie_sound.play()
            self.state = RESULT
        elif ((self.player_choice == "rock" and self.computer_choice == "scissors") or
              (self.player_choice == "paper" and self.computer_choice == "rock") or
              (self.player_choice == "scissors" and self.computer_choice == "paper")):
            self.scores["player"] += 1
            if self.scores["player"] >= 5:
                self.result = "You won the match!"
                self.state = VICTORY
                if audio_enabled and not self.victory_sound_played:
                    victory_sound.play()
                    self.victory_sound_played = True
            else:
                self.result = "You win this round!"
                if audio_enabled:
                    win_sound.play()
                self.state = RESULT
        else:
            self.scores["computer"] += 1
            if self.scores["computer"] >= 5:
                self.result = "Computer won the match!"
                self.state = DEFEAT
                if audio_enabled and not self.defeat_sound_played:
                    defeat_sound.play()
                    self.defeat_sound_played = True
            else:
                self.result = "Computer wins this round!"
                if audio_enabled:
                    lose_sound.play()
                self.state = RESULT
    
    def reset_round(self):
        self.player_choice = None
        self.computer_choice = None
        self.result = None
        self.choice_made = False
        self.computer_revealed = False
        self.player_choice_anim = 0
        self.computer_choice_anim = 0
    
    def draw_scoreboard(self):
        # Draw scoreboard background
        scoreboard_rect = pygame.Rect(20, 20, 760, 80)
        pygame.draw.rect(screen, (30, 30, 60), scoreboard_rect, border_radius=15)
        pygame.draw.rect(screen, PURPLE, scoreboard_rect, 3, border_radius=15)
        
        # Draw scoreboard title
        font = pygame.font.Font(None, 32)
        title = font.render("SCOREBOARD (First to 5 wins)", True, GOLD)
        screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 30))
        
        # Draw scores
        font = pygame.font.Font(None, 36)
        player_text = font.render(f"YOU: {self.scores['player']}", True, GREEN)
        computer_text = font.render(f"COMPUTER: {self.scores['computer']}", True, RED)
        draws_text = font.render(f"DRAWS: {self.scores['draws']}", True, WHITE)
        
        screen.blit(player_text, (100, 60))
        screen.blit(computer_text, (WINDOW_WIDTH//2 - computer_text.get_width()//2, 60))
        screen.blit(draws_text, (WINDOW_WIDTH - 180, 60))
    
    def draw_choices(self):
        if self.player_choice:
            y_offset = -self.player_choice_anim
            if self.player_choice == "rock":
                screen.blit(rock_img, (120, 300 + y_offset))
                font = pygame.font.Font(None, 36)
                label = font.render("YOUR CHOICE", True, GREEN)
                screen.blit(label, (120 + 60 - label.get_width()//2, 270 + y_offset))
            elif self.player_choice == "paper":
                screen.blit(paper_img, (340, 300 + y_offset))
                font = pygame.font.Font(None, 36)
                label = font.render("YOUR CHOICE", True, GREEN)
                screen.blit(label, (340 + 60 - label.get_width()//2, 270 + y_offset))
            elif self.player_choice == "scissors":
                screen.blit(scissors_img, (560, 300 + y_offset))
                font = pygame.font.Font(None, 36)
                label = font.render("YOUR CHOICE", True, GREEN)
                screen.blit(label, (560 + 60 - label.get_width()//2, 270 + y_offset))
        
        if self.computer_choice and self.computer_revealed:
            y_offset = -self.computer_choice_anim
            if self.computer_choice == "rock":
                screen.blit(rock_img, (120, 300 + y_offset))
                font = pygame.font.Font(None, 36)
                label = font.render("COMPUTER'S CHOICE", True, RED)
                screen.blit(label, (120 + 60 - label.get_width()//2, 270 + y_offset))
            elif self.computer_choice == "paper":
                screen.blit(paper_img, (340, 300 + y_offset))
                font = pygame.font.Font(None, 36)
                label = font.render("COMPUTER'S CHOICE", True, RED)
                screen.blit(label, (340 + 60 - label.get_width()//2, 270 + y_offset))
            elif self.computer_choice == "scissors":
                screen.blit(scissors_img, (560, 300 + y_offset))
                font = pygame.font.Font(None, 36)
                label = font.render("COMPUTER'S CHOICE", True, RED)
                screen.blit(label, (560 + 60 - label.get_width()//2, 270 + y_offset))
    
    def draw_menu(self):
        # Draw title
        font = pygame.font.Font(None, 72)
        title = font.render("BEAT THE HAND", True, GOLD)
        subtitle = font.render("Rock Paper Scissors", True, ORANGE)
        
        title_rect = title.get_rect(center=(WINDOW_WIDTH//2, 140))
        subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH//2, 200))
        
        screen.blit(title, title_rect)
        screen.blit(subtitle, subtitle_rect)
        
        # Draw game info
        font = pygame.font.Font(None, 28)
        lines = [
            "A strategic battle of hands!",
            "Challenge the computer in the classic game",
            "of Rock-Paper-Scissors with a modern twist.",
            "",
            "Rules:",
            "- Rock crushes Scissors",
            "- Paper covers Rock",
            "- Scissors cut Paper",
            "",
            "First to 5 wins becomes the ultimate champion!"
        ]
        
        for i, line in enumerate(lines):
            text = font.render(line, True, WHITE)
            screen.blit(text, (WINDOW_WIDTH//2 - text.get_width()//2, 240 + i*25))
        
        # Draw buttons
        self.play_button.draw(screen)
        self.quit_button.draw(screen)
    
    def draw_playing(self):
        font = pygame.font.Font(None, 48)
        text = font.render("Choose your weapon:", True, WHITE)
        text_rect = text.get_rect(center=(WINDOW_WIDTH//2, 200))
        screen.blit(text, text_rect)
        
        if not self.choice_made:
            self.rock_button.draw(screen)
            self.paper_button.draw(screen)
            self.scissors_button.draw(screen)
            
            # Draw labels
            font = pygame.font.Font(None, 36)
            rock_text = font.render("ROCK", True, WHITE)
            paper_text = font.render("PAPER", True, WHITE)
            scissors_text = font.render("SCISSORS", True, WHITE)
            
            screen.blit(rock_text, (120 + 60 - rock_text.get_width()//2, 530))
            screen.blit(paper_text, (340 + 60 - paper_text.get_width()//2, 530))
            screen.blit(scissors_text, (560 + 60 - scissors_text.get_width()//2, 530))
        else:
            if not self.computer_revealed:
                font = pygame.font.Font(None, 36)
                thinking_text = font.render("Computer is choosing...", True, WHITE)
                screen.blit(thinking_text, (WINDOW_WIDTH//2 - thinking_text.get_width()//2, 230))
            
            self.draw_choices()
    
    def draw_result(self):
        self.draw_choices()
        
        font = pygame.font.Font(None, 48)
        result_text = font.render(self.result, True, GOLD if "win" in self.result else WHITE)
        screen.blit(result_text, (WINDOW_WIDTH//2 - result_text.get_width()//2, 200))
        
        self.play_again_button.draw(screen)
        self.menu_button.draw(screen)
    
    def draw_victory(self):
        # Draw dark overlay
        s = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, self.popup_alpha))
        screen.blit(s, (0, 0))
        
        # Draw popup
        popup_rect = pygame.Rect(100, 150, 600, 300)
        pygame.draw.rect(screen, (40, 80, 40), popup_rect, border_radius=20)
        pygame.draw.rect(screen, GOLD, popup_rect, 4, border_radius=20)
        
        # Draw stars decoration
        star_img = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.polygon(star_img, GOLD, [(10, 0), (12, 7), (20, 7), (14, 12), (16, 20), 
                                            (10, 15), (4, 20), (6, 12), (0, 7), (8, 7)])
        
        for i in range(8):
            angle = i * 45
            pos_x = WINDOW_WIDTH//2 + 250 * pygame.math.Vector2(1, 0).rotate(angle).x
            pos_y = WINDOW_HEIGHT//2 + 150 * pygame.math.Vector2(1, 0).rotate(angle).y
            screen.blit(star_img, (pos_x - 10, pos_y - 10))
        
        # Draw text
        font = pygame.font.Font(None, 72)
        title = font.render("ULTIMATE CHAMPION!", True, GOLD)
        screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 180))
        
        font = pygame.font.Font(None, 48)
        subtitle = font.render(f"You won :  {self.scores['player']}-{self.scores['computer']}", True, WHITE)
        screen.blit(subtitle, (WINDOW_WIDTH//2 - subtitle.get_width()//2, 260))
        
        font = pygame.font.Font(None, 28)
        instruction = font.render("First to 5 wins takes the match!", True, WHITE)
        screen.blit(instruction, (WINDOW_WIDTH//2 - instruction.get_width()//2, 330))
        
        self.next_match_button.draw(screen)
        self.menu_button.draw(screen)
    
    def draw_defeat(self):
        # Draw dark overlay
        s = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, self.popup_alpha))
        screen.blit(s, (0, 0))
        
        # Draw popup
        popup_rect = pygame.Rect(100, 150, 600, 300)
        pygame.draw.rect(screen, (80, 40, 40), popup_rect, border_radius=20)
        pygame.draw.rect(screen, RED, popup_rect, 4, border_radius=20)
        
        # Draw text
        font = pygame.font.Font(None, 72)
        title = font.render("MATCH LOST", True, RED)
        screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 180))
        
        font = pygame.font.Font(None, 48)
        subtitle = font.render(f"Computer won :  {self.scores['computer']}-{self.scores['player']}", True, WHITE)
        screen.blit(subtitle, (WINDOW_WIDTH//2 - subtitle.get_width()//2, 260))
        
        font = pygame.font.Font(None, 28)
        instruction = font.render("Better luck next time!", True, WHITE)
        screen.blit(instruction, (WINDOW_WIDTH//2 - instruction.get_width()//2, 330))
        
        self.next_match_button.draw(screen)
        self.menu_button.draw(screen)
    
    def draw(self):
        # Draw background
        screen.blit(bg_img, (0, 0))
        
        # Always draw scoreboard
        self.draw_scoreboard()
        
        if self.state == MENU:
            self.draw_menu()
        elif self.state == PLAYING:
            self.draw_playing()
        elif self.state == RESULT:
            self.draw_result()
        elif self.state == VICTORY:
            self.draw_playing()  # Show last move behind popup
            self.draw_victory()
        elif self.state == DEFEAT:
            self.draw_playing()  # Show last move behind popup
            self.draw_defeat()

def main():
    game = Game()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if game.state == MENU:
                game.handle_menu(event)
            elif game.state == PLAYING:
                game.handle_playing(event)
            elif game.state == RESULT:
                game.handle_result(event)
            elif game.state in (VICTORY, DEFEAT):
                game.handle_victory_defeat(event)
        
        game.update()
        game.draw()
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()