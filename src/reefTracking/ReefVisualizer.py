"""
Graphical reef visualization system.

This module provides a visualization tool for viewing and monitoring the state
of the reef in real-time. It creates a graphical representation of the
competition field with interactive elements that update to reflect the current
state of coral slots and algae presence.

The visualization uses Kivy for the user interface, supporting resizable
layouts and color-coded feedback about reef state.
"""

import kivy

from enum import Enum

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.core.window import Window

from queue import Queue


class HexagonLayout(RelativeLayout):
    """
    Main layout for the reef visualization display.
    
    This class builds and manages the visual representation of the reef state,
    including the background field image, coral slot buttons arranged in their
    hexagonal pattern, and algae indicators. It supports dynamic resizing and
    real-time color updates based on state changes.
    
    Attributes:
        button_dictionary: Mapping of button identifiers to Button widgets
        init_dictionary: Configuration data for button positioning
        update_queue: Thread-safe queue for color update requests
        background: Background image of the competition field
    """
    
    def __init__(self, **kwargs) -> None:
        """
        Initialize the reef visualization layout.
        
        Sets up the background, reef buttons, and algae indicators, then
        configures event handlers for resizing and updates.
        
        Args:
            **kwargs: Keyword arguments passed to the parent RelativeLayout
        """
        super().__init__(**kwargs)

        self.init_background()
        self.init_reef_buttons()
        self.init_algae_buttons()

        # Bind resizing event
        Window.bind(on_resize=self.update_layout)
        self.update_layout(Window, Window.width, Window.height)

        # Mouse position label (for development)
        self.mouse = Label(
            text="Mouse Position: (0, 0)", size_hint=(None, None), pos=(100, 10)
        )
        Clock.schedule_interval(self.update_mouse_position, 0.05)
        self.add_widget(self.mouse)

        # Store the data queue for updating colors:
        self.update_queue = Queue()
        Clock.schedule_interval(self.process_queue_updates, 0.05)

    def init_background(self) -> None:
        """
        Initialize the background image of the competition field.
        
        Sets up the window size to match the background image dimensions
        and adds the field image as the background layer.
        """
        # Original image dimensions
        self.bg_width = int(1886 * 1.0)
        self.bg_height = int(1528 * 1.0)

        # Force window size to match original image size
        Window.size = (self.bg_width, self.bg_height)

        # Create background image with explicit size
        self.background = Image(
            source="./assets/blue_field.jpg",
            size_hint=(None, None),  # Disable automatic scaling
            allow_stretch=True,
            keep_ratio=True,  # Preserve aspect ratio
        )
        self.add_widget(self.background)

    def init_reef_buttons(self) -> None:
        # print("INITIALIZE REEF BUTTONS")
        # Define alphabet buttons with fixed positions
        alphabet_buttons = [
            {"text": "A", "pos": (1015, 800)},
            {"text": "B", "pos": (1015, 700)},
            {"text": "C", "pos": (1035, 650)},
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
            "A": {"offset": (-50, 0), "l_spacing": -50},  # Left spacing
            "B": {"offset": (-50, 0), "l_spacing": -50},  # Left spacing
            "C": {"offset": (-40, -40), "l_spacing": 0},  # Diagonal spacing
            "D": {"offset": (-40, -40), "l_spacing": 0},  # Diagonal spacing
            "E": {"offset": (40, -40), "l_spacing": 0},  # Diagonal spacing
            "F": {"offset": (40, -40), "l_spacing": 0},  # Diagonal spacing
            "G": {"offset": (50, 0), "l_spacing": 50},  # Right spacing
            "H": {"offset": (50, 0), "l_spacing": 50},  # Right spacing
            "I": {"offset": (40, 40), "l_spacing": 0},  # Diagonal spacing
            "J": {"offset": (40, 40), "l_spacing": 0},  # Diagonal spacing
            "K": {"offset": (-40, 40), "l_spacing": 0},  # Diagonal spacing
            "L": {"offset": (-40, 40), "l_spacing": 0},  # Diagonal spacing
        }

        # Generate buttons list dynamically
        self.init_dictionary = {}
        for btn in alphabet_buttons:
            base_x, base_y = btn["pos"]
            letter = btn["text"]

            self.init_dictionary[letter] = {"button": None, "data": btn}
            for level in ["L2", "L3", "L4"]:
                index = f"{letter}_{level}"
                self.init_dictionary[index] = {"button": None, "data": None}

            if letter in l2_offsets:
                l2_x_offset, l2_y_offset = l2_offsets[letter]["offset"]
                l_spacing = l2_offsets[letter][
                    "l_spacing"
                ]  # Determine spacing direction

                # Generate L2
                l2_x = base_x + l2_x_offset
                l2_y = base_y + l2_y_offset
                self.init_dictionary[f"{letter}_L2"]["data"] = {
                    "text": "L2",
                    "pos": (l2_x, l2_y),
                }

                # Determine L3 and L4 positioning logic
                if (
                    l2_y_offset == 0
                ):  # If L2 is only shifted horizontally, keep parallel
                    self.init_dictionary[f"{letter}_L3"]["data"] = {
                        "text": "L3",
                        "pos": (l2_x + l_spacing, l2_y),
                    }
                    self.init_dictionary[f"{letter}_L4"]["data"] = {
                        "text": "L4",
                        "pos": (l2_x + 2 * l_spacing, l2_y),
                    }
                else:  # If L2 has a diagonal offset, apply the same diagonal shift
                    self.init_dictionary[f"{letter}_L3"]["data"] = {
                        "text": "L3",
                        "pos": (l2_x + l2_x_offset, l2_y + l2_y_offset),
                    }
                    self.init_dictionary[f"{letter}_L4"]["data"] = {
                        "text": "L4",
                        "pos": (l2_x + 2 * l2_x_offset, l2_y + 2 * l2_y_offset),
                    }

        # Create buttons
        self.button_dictionary = {}
        for key in self.init_dictionary.keys():
            data = self.init_dictionary[key]["data"]
            background_color = (1, 1, 0, 1)
            text = data["text"]
            if len(text) == 1:  # If it's a letter or level ("A" vs "L2")
                background_color = (1, 1, 1, 1)
            button = Button(
                text=data["text"],
                size_hint=(None, None),
                background_color=background_color,
                background_normal="",  # INVESTIGATE THIS
                background_down="",
                color=(0, 0, 0, 1),
                font_size=32,
            )
            self.add_widget(button)
            self.button_dictionary[key] = button

    def init_algae_buttons(self) -> None:
        algae_buttons = [
            {"text": "CL", "pos": (1100, 850)},
            {"text": "CM", "pos": (1050, 760)},
            {"text": "CR", "pos": (1100, 650)},
            {"text": "FL", "pos": (1215, 650)},
            {"text": "FM", "pos": (1250, 760)},
            {"text": "FR", "pos": (1215, 850)},
        ]

        for btn in algae_buttons:
            text = btn["text"]
            pos = btn["pos"]

            self.init_dictionary[text] = {"button": None, "data": btn}

            # Create the Button widget
            button = Button(
                text=text,
                size_hint=(None, None),
                size=(40, 40),
                pos=pos,
                background_color=(0.2, 0.5, 1, 1),
                background_normal="",
                color=(0, 0, 0, 1),
                font_size=20,
            )

            self.add_widget(button)
            self.init_dictionary[text]["button"] = button
            self.button_dictionary[text] = button



    def update_layout(self, instance, width, height) -> None:
        """
        Adjust the layout when the window is resized.
        
        Scales all elements proportionally to the new window size,
        including the background image and all buttons.
        
        Args:
            instance: The window instance that was resized
            width: New window width
            height: New window height
        """
        # Ensure background size matches the window
        self.background.size = (width, height)
        self.background.pos = (0, 0)

        # Scale button size proportionally
        button_size_ratio = 0.02  # Adjust ratio as needed
        button_width = width * button_size_ratio
        button_height = height * button_size_ratio

        for key, button in self.button_dictionary.items():
            data = self.init_dictionary[key]["data"]
            original_x, original_y = data["pos"]  # original positioning
            button.size = (button_width, button_height)

            # Scale button positions relative to the new background size
            button_x_ratio = original_x / self.bg_width
            button_y_ratio = original_y / self.bg_height
            button.pos = (width * button_x_ratio, height * button_y_ratio)

    def update_button_color(self, button_text, color) -> None:
        """
        Update the color of a specific button.
        
        Args:
            button_text: Identifier of the button to update
            color: New RGBA color tuple (r, g, b, a) with values from 0-1
        """
        if button_text in self.button_dictionary:
            self.button_dictionary[button_text].background_color = color

    def update_mouse_position(self, dt) -> None:
        """
        Update the mouse position display.
        
        Called periodically to show the current mouse coordinates
        in the visualization window.
        
        Args:
            dt: Time delta since last update (provided by Kivy clock)
        """
        x, y = Window.mouse_pos
        self.mouse.text = f"Mouse Position: ({int(x)}, {int(y)})"

    def queue_color_update(self, button_text, color) -> None:
        """
        Queue a color update request for thread-safe operation.
        
        This method allows color updates to be requested from any thread
        and processed safely on the main UI thread.
        
        Args:
            button_text: Identifier of the button to update
            color: New RGBA color tuple (r, g, b, a) with values from 0-1
        """
        self.update_queue.put((button_text, color))

    def process_queue_updates(self, dt) -> None:
        """
        Process queued color update requests.
        
        Called periodically to apply all queued color updates
        in the main UI thread.
        
        Args:
            dt: Time delta since last update (provided by Kivy clock)
        """
        while not self.update_queue.empty():
            button_text, color = self.update_queue.get()
            Clock.schedule_once(
                lambda dt, bt=button_text, c=color: self.update_button_color(bt, c)
            )


layout = HexagonLayout()


class ReefVisualizerApp(App):
    """
    Kivy application for the reef state visualization.
    
    This class sets up the Kivy application and returns the main
    HexagonLayout as the root widget.
    """
    
    def build(self):
        """
        Build the application and return the root widget.
        
        Returns:
            The HexagonLayout instance to use as the root widget
        """
        return layout


if __name__ == "__main__":
    # Standalone execution for development and testing
    app = ReefVisualizerApp()
    app_instance = app.build()
    # Example color update for testing
    app_instance.queue_color_update("CL", (0.5, 0.5, 0.5, 1))
    app.run()
