from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import NumericProperty
from kivy.uix.screenmanager import Screen


class BaseWeatherScreen(Screen):
    """Base class for all weather screens providing responsive layout support.
    
    Handles automatic resize detection and responsive layout updates when
    window size changes. All weather screens inherit from this class to
    ensure consistent responsive behavior.
    """
    
    card_width = NumericProperty(dp(350))

    def on_kv_post(self, base_widget):
        """Called after KV file is processed for this widget.
        
        Sets up window resize event binding to trigger responsive layout
        updates whenever the window is resized.
        
        Args:
            base_widget: The root widget from the KV file
        """
        Window.bind(size=self._on_window_resize)

    def _on_window_resize(self, _window, size):
        """Handle window resize events.
        
        Internal callback triggered by window size changes. Triggers the
        on_responsive_update() method to allow subclasses to respond to
        size changes.
        
        Args:
            _window: The window object (unused)
            size: Tuple of (width, height) in pixels
        """
        self.on_responsive_update()

    def on_responsive_update(self):
        """Called when responsive layout update is needed.
        
        Override this method in subclasses to implement custom responsive
        behavior such as recalculating RecycleView heights or adjusting
        widget dimensions based on available space.
        """
        pass
