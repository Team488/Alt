import kivy

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.clock import Clock

from kivy.core.window import Window


class HexagonLayout(RelativeLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Original image dimensions
        self.bg_width = int(1886 * 1.0)
        self.bg_height = int(1528 * 1.0)

        # Force window size to match original image size
        Window.size = (self.bg_width, self.bg_height)

        # Create background image with explicit size
        self.background = Image(
            source="blue_field.jpg",
            size_hint=(None, None),  # Disable automatic scaling
            allow_stretch=True,  
            keep_ratio=True  # Preserve aspect ratio
        )
        self.add_widget(self.background)

        # Define alphabet buttons with fixed positions
        alphabet_buttons = [
            {"text": "A", "pos": (1015, 800)},
            {"text": "B", "pos": (1015, 700)},
            {"text": "C", "pos": (1035, 650)},  # Example with diagonal offset
            {"text": "D", "pos": (1100, 600)},
            {"text": "E", "pos": (1200, 600)},
            {"text": "F", "pos": (1275, 650)},
            {"text": "G", "pos": (1300, 700)},
            {"text": "H", "pos": (1300, 800)},
            {"text": "I", "pos": (1275, 850)},
            {"text": "J", "pos": (1200, 900)},
            {"text": "K", "pos": (1100, 900)},
            {"text": "L", "pos": (1035, 850)},
        ]

        # Define L2 offsets and L3/L4 spacing direction per alphabet button
        l2_offsets = {
            "A": {"offset": (-50, 0), "l_spacing": -50},   # Left spacing
            "B": {"offset": (-50, 0), "l_spacing": -50},   # Left spacing
            "C": {"offset": (-40, -40), "l_spacing": 0},   # Diagonal spacing
            "D": {"offset": (-40, -40), "l_spacing": 0},   # Diagonal spacing
            "E": {"offset": (40, -40), "l_spacing": 0},    # Diagonal spacing
            "F": {"offset": (40, -40), "l_spacing": 0},    # Diagonal spacing
            "G": {"offset": (50, 0), "l_spacing": 50},     # Right spacing
            "H": {"offset": (50, 0), "l_spacing": 50},     # Right spacing
            "I": {"offset": (40, 40), "l_spacing": 0},     # Diagonal spacing
            "J": {"offset": (40, 40), "l_spacing": 0},     # Diagonal spacing
            "K": {"offset": (-40, 40), "l_spacing": 0},     # Diagonal spacing
            "L": {"offset": (-40, 40), "l_spacing": 0},     # Diagonal spacing
        }

        # Generate buttons list dynamically
        self.buttons_data = []

        for btn in alphabet_buttons:
            self.buttons_data.append(btn)  # Add alphabet button

            base_x, base_y = btn["pos"]
            letter = btn["text"]

            if letter in l2_offsets:
                l2_x_offset, l2_y_offset = l2_offsets[letter]["offset"]
                l_spacing = l2_offsets[letter]["l_spacing"]  # Determine spacing direction

                # Generate L2
                l2_x = base_x + l2_x_offset
                l2_y = base_y + l2_y_offset
                self.buttons_data.append({"text": "L2", "pos": (l2_x, l2_y)})

                # Determine L3 and L4 positioning logic
                if l2_y_offset == 0:  # If L2 is only shifted horizontally, keep parallel
                    self.buttons_data.append({"text": "L3", "pos": (l2_x + l_spacing, l2_y)})
                    self.buttons_data.append({"text": "L4", "pos": (l2_x + 2 * l_spacing, l2_y)})
                else:  # If L2 has a diagonal offset, apply the same diagonal shift
                    self.buttons_data.append({"text": "L3", "pos": (l2_x + l2_x_offset, l2_y + l2_y_offset)})
                    self.buttons_data.append({"text": "L4", "pos": (l2_x + 2 * l2_x_offset, l2_y + 2 * l2_y_offset)})

        # Create buttons
        self.buttons = []
        for data in self.buttons_data:
            button = Button(text=data["text"], size_hint=(None, None))
            self.add_widget(button)
            self.buttons.append(button)

        # Bind resizing event
        Window.bind(on_resize=self.update_layout)
        self.update_layout(Window, Window.width, Window.height)

        # Mouse position label (for development)
        self.mouse = Label(text="Mouse Position: (0, 0)", size_hint=(None, None), pos=(10, 10))
        Clock.schedule_interval(self.update_mouse_position, 0.05)
        self.add_widget(self.mouse)

    def update_layout(self, instance, width, height):
        # Ensure background size matches the window
        self.background.size = (width, height)
        self.background.pos = (0, 0)

        # Scale button size proportionally
        button_size_ratio = 0.02  # Adjust ratio as needed
        button_width = width * button_size_ratio
        button_height = height * button_size_ratio

        for button, data in zip(self.buttons, self.buttons_data):
            original_x, original_y = data["pos"]
            button.size = (button_width, button_height)

            # Scale button positions relative to the new background size
            button_x_ratio = original_x / self.bg_width
            button_y_ratio = original_y / self.bg_height
            button.pos = (
                width * button_x_ratio,  
                height * button_y_ratio  
            )

    def update_mouse_position(self, dt):
        x, y = Window.mouse_pos
        self.mouse.text = f"Mouse Position: ({int(x)}, {int(y)})"

class ReefVisualizer(App):
    def build(self):
        return HexagonLayout()

if __name__ == '__main__':
    ReefVisualizer().run()