# log.py
import logging

class KivyLogHandler(logging.Handler):
    def __init__(self, widget, formatter=None, IncludeKeywords=None, ExcludeKeywords=None, MaxLines=2000):
        super().__init__()
        self.widget = widget
        self.formatter = formatter or logging.Formatter('%(asctime)s : %(levelname)s : %(message)s')
        self.IncludeKeywords = IncludeKeywords or []
        self.ExcludeKeywords = ExcludeKeywords or []
        self.MaxLines = MaxLines

    def emit(self, record):
        try:
            msg = self.format(record)
            # Filter by include/exclude keywords
            if self.IncludeKeywords and not any(k in msg for k in self.IncludeKeywords):
                return
            if self.ExcludeKeywords and any(k in msg for k in self.ExcludeKeywords):
                return
            self.widget.text += msg + '\n'
            # Keep max lines
            lines = self.widget.text.splitlines()
            if len(lines) > self.MaxLines:
                self.widget.text = '\n'.join(lines[-self.MaxLines:])
        except Exception:
            self.handleError(record)

class UserFormatter(logging.Formatter):
    def format(self, record):
        return super().format(record)

def keyword_match(message, include, exclude):
    if include and not any(k in message for k in include):
        return False
    if exclude and any(k in message for k in exclude):
        return False
    return True

# Optional DBHandler placeholder
class DBHandler(logging.Handler):
    def __init__(self, db):
        super().__init__()
        self.db = db

    def emit(self, record):
        # Store log in database
        pass
