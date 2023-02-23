class ImageState:
    def __init__(self, rotated=False, converted=False, uploaded=False):
        self.rotated = rotated
        self.converted = converted
        self.uploaded = uploaded

    def to_dict(self):
        return {
            "rotated": self.rotated,
            "converted": self.converted,
            "uploaded": self.uploaded
        }

    def __str__(self):
        return str(self.to_dict())

