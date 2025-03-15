import pygame
import requests
import json
from settings import *
from entity import Entity
from support import import_folder  

class NPC(Entity):
    def __init__(self, npc_name, pos, groups, obstacle_sprites, interact_callback):
        super().__init__(groups)
        self.sprite_type = 'npc'
        
        self.frame_index = 0
        self.animation_speed = 0.15
        
        self.import_graphics(npc_name)
        self.status = 'idle'
        if len(self.animations[self.status]) > 0:
            self.image = self.animations[self.status][self.frame_index]
        else:
            self.image = pygame.Surface((TILESIZE, TILESIZE))
            self.image.fill('red')
            print(f"Warning: No idle animations found for NPC '{npc_name}'. Using fallback image.")
        
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect.inflate(0, -10)
        self.obstacle_sprites = obstacle_sprites

        self.npc_name = npc_name
        self.interact_callback = interact_callback  
        self.speed = 2  

        self.conversation_active = False  
        self.input_text = ""
        self.output_text = ""
        self.dialogue_text = "Hello, traveler! Welcome to our village. Press E to interact."
        self.font = pygame.font.SysFont('Arial', 24)
        
        self.e_pressed = False

        self.initial_prompt = (
            "You are a wandering spirit NPC in a JRPG game. "
            "Speak in a mystical, cryptic, and gentle tone, offering advice and hints to travelers."
        )

    def import_graphics(self, name):
        self.animations = {'idle': [], 'move': [], 'talk': []}
        main_path = f'../graphics/npcs/{name}/'
        for animation in self.animations.keys():
            path = main_path + animation
            self.animations[animation] = import_folder(path)
            if not self.animations[animation]:
                print(f"Warning: No images loaded for animation '{animation}' in NPC '{name}' from folder: {path}")

    def animate(self):
        animation = self.animations[self.status]
        if len(animation) > 0:
            self.frame_index += self.animation_speed
            if self.frame_index >= len(animation):
                self.frame_index = 0
            self.image = animation[int(self.frame_index)]
        self.rect = self.image.get_rect(center=self.hitbox.center)

    def wrap_text(self, text, font, max_width):
        """Wraps text so that each line fits within max_width."""
        words = text.split(' ')
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + " " + word if current_line != "" else word
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return lines

    def get_llama_response(self, prompt):
        """
        Sends the prompt to the Ollama Llama 3.1 model and returns the full response.
        This function streams the tokens and combines them.
        """
        full_prompt = self.initial_prompt + "\nUser: " + prompt + "\nNPC:"
        url = "http://localhost:11434/api/generate"  
        payload = {"model": "llama3.1", "prompt": full_prompt}
        try:
            response = requests.post(url, json=payload, stream=True)
            full_response = ""
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if "response" in data:
                        full_response += data["response"]
                    if data.get("done", False):
                        break
            return full_response.strip()
        except Exception as e:
            return f"Error: {e}"

    def display_dialogue_box(self):
        """
        Displays the default dialogue box with the NPC's preset dialogue.
        """
        surface = pygame.display.get_surface()
        box_width = surface.get_width() - 40
        box_height = 100
        box_x = 20
        box_y = surface.get_height() - box_height - 20
        pygame.draw.rect(surface, (0, 0, 0), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(surface, (255, 255, 255), (box_x, box_y, box_width, box_height), 2)
        wrapped_lines = self.wrap_text(self.dialogue_text, self.font, box_width - 20)
        line_height = self.font.get_height()
        total_text_height = line_height * len(wrapped_lines)
        start_y = box_y + (box_height - total_text_height) // 2
        for i, line in enumerate(wrapped_lines):
            text_surface = self.font.render(line, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(surface.get_width() // 2, start_y + i * line_height + line_height // 2))
            surface.blit(text_surface, text_rect)

    def display_conversation_box(self):
        """
        Displays two boxes:
          - An input box for the player's text.
          - An output box showing the AI model's response.
        """
        surface = pygame.display.get_surface()
        
        input_box_width = surface.get_width() - 40
        input_box_height = 50
        input_box_x = 20
        input_box_y = surface.get_height() - input_box_height - 20
        pygame.draw.rect(surface, (50, 50, 50), (input_box_x, input_box_y, input_box_width, input_box_height))
        pygame.draw.rect(surface, (255, 255, 255), (input_box_x, input_box_y, input_box_width, input_box_height), 2)
        input_text_surface = self.font.render(self.input_text, True, (255, 255, 255))
        surface.blit(input_text_surface, (input_box_x + 10, input_box_y + 10))
        
        output_box_width = surface.get_width() - 40
        output_box_height = 100
        output_box_x = 20
        output_box_y = input_box_y - output_box_height - 10
        pygame.draw.rect(surface, (0, 0, 0), (output_box_x, output_box_y, output_box_width, output_box_height))
        pygame.draw.rect(surface, (255, 255, 255), (output_box_x, output_box_y, output_box_width, output_box_height), 2)
        wrapped_lines = self.wrap_text(self.output_text, self.font, output_box_width - 20)
        line_height = self.font.get_height()
        total_text_height = line_height * len(wrapped_lines)
        start_y = output_box_y + (output_box_height - total_text_height) // 2
        for i, line in enumerate(wrapped_lines):
            output_text_surface = self.font.render(line, True, (255, 255, 255))
            text_rect = output_text_surface.get_rect(center=(surface.get_width() // 2, start_y + i * line_height + line_height // 2))
            surface.blit(output_text_surface, text_rect)

    def handle_event(self, event):
        """
        Process keyboard events for conversation mode.
        When conversation mode is inactive, E toggles it on.
        When active, all keys (including E) are added as input, and ESC exits conversation mode.
        """
        if event.type == pygame.KEYDOWN:
            if self.conversation_active:
                # In conversation mode, process keys as input
                if event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif event.key == pygame.K_RETURN:
                    self.output_text = self.get_llama_response(self.input_text)
                    self.input_text = ""
                elif event.key == pygame.K_ESCAPE:
                    self.conversation_active = False
                else:
                    # Add all keys normally, including E
                    self.input_text += event.unicode
            else:
                # If not in conversation mode, only toggle on E
                if event.key == pygame.K_e:
                    if not self.e_pressed:
                        self.conversation_active = True
                        self.e_pressed = True
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_e:
                self.e_pressed = False

    def npc_update(self, player):
        """
        Update the NPC based on the player's proximity.
        When within 150 pixels:
          - If conversation mode is active, display the conversation box.
          - Otherwise, display the default dialogue box.
        """
        npc_vec = pygame.math.Vector2(self.rect.center)
        player_vec = pygame.math.Vector2(player.rect.center)
        distance = (player_vec - npc_vec).magnitude()
        
        if distance < 150:
            if self.conversation_active:
                self.status = 'talk'
                self.display_conversation_box()
            else:
                self.status = 'idle'
                self.display_dialogue_box()
        else:
            self.status = 'idle'
            self.conversation_active = False
            
        self.animate()

    def update(self):
        pass
