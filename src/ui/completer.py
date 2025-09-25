from PyQt5.QtWidgets import QCompleter


class MultiTagCompleter(QCompleter):
    """
    A custom QCompleter that handles comma-separated values.
    It suggests completions for the text segment after the last comma.
    """
    def __init__(self, model, parent=None):
        super().__init__(model, parent)

    def pathFromIndex(self, index):
        """
        Constructs the full text string when a completion is selected.
        """
        completion = super().pathFromIndex(index)
        current_text = self.widget().text()
        last_comma_pos = current_text.rfind(',')

        if last_comma_pos == -1:
            return completion

        prefix = current_text[:last_comma_pos]
        return f"{prefix.strip()}, {completion}"

    def splitPath(self, path):
        """
        Splits the text to determine which part to use for completion.
        """
        last_comma_pos = path.rfind(',')
        if last_comma_pos != -1:
            return [path[last_comma_pos + 1:].lstrip()]
        return [path]