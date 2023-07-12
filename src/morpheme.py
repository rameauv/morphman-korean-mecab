class Morpheme(object):
    def __init__(self, word: str, pos: str, sub_pos: str, norm: str, base: str, inflected: str, read: str):
        self.word: str = word
        self.pos: str = pos
        self.subPos: str = sub_pos
        self.norm: str = norm
        self.base: str = base
        self.inflected: str = inflected
        self.read: str = read
