class Images:

    def __int__(self, path, size, ext, mod_time):
        self.path = path
        self.size = size
        self.ext = ext
        self.mod_time = mod_time

    def __str__(self):
        return f'File {self.path}'


