import importlib
import unittest

class TestMecabMorphemizer(unittest.TestCase):
    def setUp(self) -> None:
        module = importlib.import_module('src')
        self.controller = module.Controller()
        self.controller.spawn_mecab()

    def tearDown(self) -> None:
        self.controller.dispose_mecab()

    def test_morpheme_generation(self) -> None:
        sentence_1 = "안녕하세요 제이름은 발렌타인입니다"
        case_1 = ["안녕", "하", "세요", "제", "이름", "은", "입니다", "입니다"]
        for idx, m in enumerate(self.controller.get_morphemes(sentence_1)):
            self.assertEqual(m.base, case_1[idx])

unittest.main()
