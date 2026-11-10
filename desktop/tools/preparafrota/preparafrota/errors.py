"""Erros que podem ser apresentados diretamente na tela ou no console."""
class AppError(ValueError):
    pass


class SheetRequired(AppError):
    def __init__(self, path, names):
        self.path, self.names = path, names
        super().__init__('Escolha a aba do arquivo: ' + ', '.join(names))


class PendingError(AppError):
    pass
