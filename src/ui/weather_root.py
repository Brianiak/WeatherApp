from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import SlideTransition


class WeatherRoot(BoxLayout):
    """Root widget managing screen navigation and transitions.
    
    Controls the screen manager, handles navigation between weather screens
    (Today, Tomorrow, 5-day forecast) with animated slide transitions, and
    keeps the navigation bar synchronized with the current screen.
    """
    
    def on_kv_post(self, base_widget):
        """Called after KV file is processed.
        
        Initializes the root widget by navigating to the 'today' screen.
        
        Args:
            base_widget: The root widget from the KV file
        """
        self.navigate("today")

    def navigate(self, key: str):
        """Navigate to a different screen with animated transition.
        
        Attempts to navigate to the specified screen with a slide transition
        effect. Determines transition direction based on current and target
        screen positions.
        
        Args:
            key (str): Screen identifier ('today', 'tomorrow', or '5days')
        """
        sm = self.ids.sm
        mapping = {"today": "today", "tomorrow": "tomorrow", "5days": "five_days"}
        target = mapping.get(key)
        if not target:
            return

        # determine transition direction based on current and target indices
        try:
            names = list(sm.screen_names)
            current_index = names.index(sm.current) if sm.current in names else 0
            target_index = names.index(target)
            if target_index > current_index:
                direction = "left"
            elif target_index < current_index:
                direction = "right"
            else:
                direction = None
        except Exception:
            direction = None

        if direction:
            sm.transition = SlideTransition(direction=direction, duration=0.5)

        sm.current = target
        self._sync_nav_for_current()

    def _sync_nav_for_current(self):
        """Update navigation buttons to highlight the current screen.
        
        Sets the appropriate navigation button to 'down' state to visually
        indicate which screen is currently displayed.
        """
        sm = self.ids.sm
        screen = sm.get_screen(sm.current)
        if "nav" not in screen.ids:
            return

        nav = screen.ids.nav
        if sm.current == "today":
            nav.ids.btn_today.state = "down"
        elif sm.current == "tomorrow":
            nav.ids.btn_tomorrow.state = "down"
        elif sm.current == "five_days":
            nav.ids.btn_5days.state = "down"
