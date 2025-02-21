import time
import random
from kivy.clock import Clock
from threading import Thread
from ReefVisualizer import ReefVisualizer

def simulate_backend_update(app):
    colors = {
        "red": (255, 0, 0, 1),
        "green": (0, 255, 0, 1),
        "blue": (0, 0, 255, 1),
        "yellow": (255, 255, 0, 1),
        "white": (255, 255, 255, 1)
    }


    button_labels = list(app.button_dictionary.keys())

    while True:
        button = random.choice(button_labels)
        #print(type(button), button)
        color = random.choice(list(colors.values()))
        #print("Initial")
        #app.get_background_colors(button)
        #print(f"Updating {button} to color {color}")
        # Add update to the queue (safe for threads)
        app.queue_color_update(button, color)
        #print("After")
        #app.get_background_colors(button)
        #print("========================")
        time.sleep(1)  # Simulate processing time

if __name__ == '__main__':
    app = ReefVisualizer()
    app_instance = app.build()

    backend_thread = Thread(target=simulate_backend_update, args=(app_instance,))
    backend_thread.daemon = True
    backend_thread.start()
    app_instance.update_button_color("A", (255, 0, 0, 1))
    
    app.run()
