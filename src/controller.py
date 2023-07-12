# -*- coding: utf-8 -*-
import os
import re
import subprocess
import sys
import typing
from typing import Optional, Match

from .abstract_controller import AbstractController
from .morpheme import Morpheme

try:
    from anki.utils import is_mac, is_win
except:
    is_mac = sys.platform.startswith("darwin")
    is_win = sys.platform.startswith("win32")
    pass

support_path = os.path.join(os.path.dirname(__file__), "../deps/mecabko")

if sys.platform == "win32":
    si = subprocess.STARTUPINFO()
    try:
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    except:
        si.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
else:
    si = None

control_chars_re = re.compile('[\x00-\x1f\x7f-\x9f]')


_MECAB_POS_BLACKLIST = [
    'JKV',  # vocative case
    'EF',  # termination particle
    'EC',  # connection particle
    'IC',  # interjection
    'NNP',  # proper noun
    'NR',  # literal numbers
    'SN',  # numbers
    'SH',  # hanja
    'SL',  # non korean
    'SY',  # punctuation
    'SC',  # punctuation
    'SSC',  # punctuation
    'SSO',  # punctuation
    'SE',  # punctuation
    'SF',  # punctuation
]


class MecabCmdFactory(object):
    _binPath = "mecab"
    _args = ["-d", os.path.join(support_path, "dic/mecab-ko-dic"), "--node-format=%m\t%f[0]\r",
             "--eos-format=\n"]

    @staticmethod
    def win_cmd() -> list[str]:
        return [os.path.join(support_path, MecabCmdFactory._binPath) + ".exe"] + MecabCmdFactory._args

    @staticmethod
    def other_cmd() -> list[str]:
        return [os.path.join(support_path, MecabCmdFactory._binPath)] + MecabCmdFactory._args

    @staticmethod
    def linux_cmd() -> list[str]:
        return [os.path.join(support_path, MecabCmdFactory._binPath) + ".lin"] + MecabCmdFactory._args


class Config(object):
    def __init__(self, mecab_cmd: list[str]):
        self.mecabCmd = mecab_cmd


def config_provider() -> Config:
    if is_win:
        return Config(MecabCmdFactory.win_cmd())
    elif not is_mac:
        return Config(MecabCmdFactory.linux_cmd())
    else:
        return Config(MecabCmdFactory.other_cmd())


class Controller(AbstractController):

    def __init__(self) -> None:
        self.config: Config = config_provider()
        self.mecab: Optional[subprocess.Popen[bytes]] = None
        self.mecab_encoding: Optional[str] = None

    def get_name(self) -> str:
        return "korean mecab"

    def get_description(self) -> str:
        return "korean mecab"

    def spawn_mecab(self) -> None:
        print("spawnMecab called")
        """Try to start a MeCab subprocess in the given way, or fail.

        Raises OSError if the given base_cmd and startupinfo don't work
        for starting up MeCab, or the MeCab they produce has a dictionary
        incompatible with our assumptions.
        """
        os.environ["DYLD_LIBRARY_PATH"] = support_path
        os.environ["LD_LIBRARY_PATH"] = support_path
        print(support_path)
        if not is_win:
            os.chmod(self.config.mecabCmd[0], 0o755)

        base_cmd = self.config.mecabCmd
        startupinfo = si

        def spawn_cmd(cmd: list[str]) -> subprocess.Popen[bytes]:
            return subprocess.Popen(
                cmd,
                startupinfo=startupinfo,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )

        process: subprocess.Popen[bytes] = spawn_cmd(base_cmd + ['-D'])
        assert process.stdout is not None

        dicinfo_dump = process.stdout.read()
        charset_match: Optional[Match[str]] = re.search(
            '^charset:\t(.*)$', str(dicinfo_dump, 'utf-8'), flags=re.M)
        if charset_match is None:
            raise OSError('Can\'t find charset in MeCab dictionary info (`$MECAB -D`):\n\n'
                          + str(dicinfo_dump))
        self.mecab_encoding = charset_match.group(1)
        print(base_cmd)
        self.mecab = spawn_cmd(base_cmd)

    def dispose_mecab(self) -> None:
        if not self.mecab:
            return
        self.mecab.kill()

    def get_morphemes(self, e: str) -> list[Morpheme]:
        # Remove Unicode control codes before sending to MeCab.
        e = control_chars_re.sub('', e)
        ms = [self._build_morpheme_from_mecab_output(m.split('\t')) for m in self._interact(e).split('\r')]
        ms = [m for m in ms if m is not None]
        return typing.cast(list[Morpheme], ms)

    def _interact(self, expression: str) -> str:
        """ "interacts" with 'mecab' command: writes expression to stdin of 'mecab' process and gets all the morpheme.py
        info from its stdout. """

        p: Optional[subprocess.Popen[bytes]] = self.mecab
        assert self.mecab_encoding is not None
        assert p is not None
        assert p.stdin is not None
        assert p.stdout is not None
        expr2: bytes = expression.encode(self.mecab_encoding, 'ignore')
        p.stdin.write(expr2 + b'\n')
        p.stdin.flush()
        res: str = '\r'.join([str(p.stdout.readline().rstrip(b'\r\n'), 'utf-8') for _ in expr2.split(b'\n')])
        return res

    @staticmethod
    def _build_morpheme_from_mecab_output(parts: list[str]) -> Optional[Morpheme]:
        word = parts[0]
        pos = u'UNKNOWN'
        sub_pos = u'UNKNOWN'
        norm = word
        base = word
        inflected = word
        reading = word

        if len(parts) > 1:
            pos = parts[1]
        if pos in _MECAB_POS_BLACKLIST:
            return None
        return Morpheme(
            word=word,
            pos=pos,
            sub_pos=sub_pos,
            norm=norm,
            base=base,
            inflected=inflected,
            read=reading
        )
