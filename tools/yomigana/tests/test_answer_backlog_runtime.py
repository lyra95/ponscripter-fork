"""Explicit full-script copied-app test; never loads or modifies personal saves."""
import argparse
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fix_answer_backlog import patch


def yellow_pixels(data):
    offset = struct.unpack_from('<I', data, 10)[0]
    width, height = struct.unpack_from('<ii', data, 18)
    bits = struct.unpack_from('<H', data, 28)[0]
    assert bits in (24, 32)
    stride = ((width * bits + 31) // 32) * 4
    return sum(data[i+2] > 220 and data[i+1] > 220 and 110 < data[i] < 200
               for y in range(abs(height)) for x in range(width)
               for i in [offset + y * stride + x * (bits // 8)])


def run(game_dir, app, offline_library=None):
    original = (game_dir / '0.u').read_bytes()
    corrected, changes = patch(original)
    assert changes == 2, 'Use the uncorrected bilingual answer script for the negative control'
    start = b'*Start\r\nsaveoff\r\nseventh_change_voice_level 0 ;initialize voice volume\r\n'
    assert original.count(start) == 1
    replacement = b'*Start\r\ngoto *DiagBoot'
    replacement += b' ' * (len(start) - len(replacement) - 2) + b'\r\n'
    with tempfile.TemporaryDirectory(prefix='yomigana-answer-backlog-') as d:
        game = Path(d)
        shutil.copytree(app, game / app.name, symlinks=True)
        for p in game_dir.iterdir():
            if p.name in ('0.u', '0.utf', 'saves', 'mysav', app.name) or p.name.startswith('.'):
                continue
            (game / p.name).symlink_to(p, target_is_directory=p.is_dir())
        env = os.environ.copy()
        if offline_library:
            env['DYLD_INSERT_LIBRARIES'] = str(offline_library)
        for language in (0, 1):
            for adv in (0, 1):
                frames = []
                for data in (original, corrected):
                    saves = game / 'saves'
                    if saves.exists():
                        shutil.rmtree(saves)
                    source = data.replace(start, replacement, 1)
                    for label in ('backlogbtn', 'backlogbtn_jp'):
                        wait = ('*' + label + '\r\n    btnwait2 %BtnRes').encode()
                        assert source.count(wait) == 1
                        source = source.replace(wait, ('*' + label + '\r\n    goto *DiagShot').encode(), 1)
                    source += f'''
*DiagBoot
showlangjp
mov %cur_language,{language}
mov %cur_read_lang,{language}
mov %advMode,{adv}
mov %textboxType,0
mov %BacklogNum,Backlogpage1
mov %jpBacklogNum,jpBacklogpage1
mov %backlogTotalNum,{1-language}
mov %jpbacklogTotalNum,{language}
mov $Textlog,"｜過去《かこ》の｜会話《かいわ》を｜表示《ひょうじ》します。"
gosub *text_tagsave
bg black,1
setwindow 95,368,32,17,24,24,0,0,0,1,1,#444444,47,315,912,525
gosub *text_cw_lookback
*DiagShot
getscreenshot 1920,1080
savescreenshot "backlog.bmp"
end
'''.replace('\n', '\r\n').encode()
                    (game / '0.u').write_bytes(source)
                    r = subprocess.run([str(game / app.name / 'Contents/MacOS/umineko8')],
                                       cwd='/', env=env, capture_output=True, timeout=45)
                    assert r.returncode == 0, r.stderr[-1500:]
                    frames.append((saves / 'backlog.bmp').read_bytes())
                if language:
                    assert yellow_pixels(frames[0]) == 0
                    assert yellow_pixels(frames[1]) > 100
                else:
                    assert frames[0] == frames[1], 'Korean branch changed'
                    assert yellow_pixels(frames[0]) > 100
                print('PASS:', 'Japanese restored' if language else 'Korean branch unchanged',
                      'ADV' if adv else 'NVL', 'without loading any saves', flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game-dir', type=Path, required=True)
    p.add_argument('--app', type=Path, required=True)
    p.add_argument('--offline-library', type=Path)
    args = p.parse_args()
    run(args.game_dir.resolve(), args.app.resolve(),
        args.offline_library.resolve() if args.offline_library else None)
