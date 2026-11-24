# 全部のテストを順に動かして、結果をまとめて出す。
# 使い方（リポジトリの一番上で）：python3 test/run_all.py
# 先に一度だけ：pip install playwright（ブラウザは環境に入っているものを使う）
import os, subprocess, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__))
files = ['run.py'] + sorted(os.path.basename(f) for f in glob.glob(os.path.join(HERE, '*.py')) if os.path.basename(f) not in ('run.py', 'run_all.py', 'screenshots.py'))
ng = []
for f in files:
    r = subprocess.run([sys.executable, os.path.join(HERE, f)], cwd=os.path.dirname(HERE), capture_output=True, text=True, timeout=300)
    out = (r.stdout + r.stderr).strip()
    bad = r.returncode != 0 or "Error" in out
    print(('NG ' if bad else 'OK ') + f)
    if bad: ng.append(f); print('   ' + out[-800:].replace('\n', '\n   '))
print(f'\n{len(files) - len(ng)}/{len(files)} 通過' + (f'　失敗：{", ".join(ng)}' if ng else ''))
sys.exit(1 if ng else 0)
