"""Small macOS packaging helpers used by the top-level Makefile."""
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys


def run(*args):
    return subprocess.check_output(args, text=True)


def binaries(app):
    magic = {bytes.fromhex(s) for s in (
        'feedface', 'cefaedfe', 'feedfacf', 'cffaedfe',
        'cafebabe', 'bebafeca', 'cafebabf', 'bfbafeca')}
    for p in app.rglob('*'):
        if p.is_file() and not p.is_symlink():
            with p.open('rb') as f:
                if f.read(4) in magic:
                    yield p


def architectures(p, wanted):
    actual = set(run('lipo', '-archs', str(p)).split())
    if not set(wanted) <= actual:
        raise RuntimeError(f'{p}: requires {wanted}, contains {sorted(actual)}. '
                           'For Universal, select a Qt installation with arm64 and x86_64: '
                           'make configure QT_ROOT=/path/to/universal/Qt')


def check(qt, *archs):
    if not archs or set(archs) - {'arm64', 'x86_64'}:
        raise RuntimeError('ARCHS must contain arm64 and/or x86_64.')
    architectures(Path(qt) / 'lib/QtCore.framework/Versions/A/QtCore', archs)


def configure(qt, host):
    if host not in {'arm64', 'x86_64'}:
        raise RuntimeError('QT_HOST_ARCH must be arm64 or x86_64.')
    # Check that this host architecture can execute the selected Qt tool.
    subprocess.run(['arch', '-' + host, str(Path(qt) / 'bin/qmake'), '-v'], check=True)
    qt = str(Path(qt).resolve()).replace('$', '$$').replace('#', '\\#')
    if '\n' in qt or '\r' in qt:
        raise RuntimeError('Qt path cannot contain newlines.')
    Path('config.mk').write_text(
        '# Local machine settings; ignored by git. Command-line values override these.\n'
        f'QT_ROOT := {qt}\nQT_HOST_ARCH := {host}\n')
    print('Saved config.mk. You can now run make without Qt arguments.')


def tools(qt, directory, host):
    if host not in {'arm64', 'x86_64'}:
        raise RuntimeError('QT_HOST_ARCH must be arm64 or x86_64.')
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    # Xcode tools must run natively even when Qt tools run under Rosetta.
    commands = {name: (platform.machine(), Path('/usr/bin') / name)
                for name in ['xcrun', 'otool', 'install_name_tool', 'strip']}
    commands.update({name: (host, Path(qt) / 'libexec' / name)
                     for name in ['moc', 'uic', 'rcc']})
    for name, (arch, executable) in commands.items():
        p = root / name
        p.write_text(f'#!/bin/sh\nexec /usr/bin/arch -{arch} {shlex.quote(str(executable))} "$@"\n')
        p.chmod(0o755)
    # Clang 21 requires the declaration for __yield used in Qt 6.8 headers.
    (root / 'compiler-compat.h').write_text(
        '#if defined(__aarch64__)\n#include <arm_acle.h>\n#endif\n')


def sdk(makefile, sdk_path, qt, tools_dir):
    p = Path(makefile)
    text = p.read_text()
    # New SDKs omit AGL's link stub. QtGui retains its own runtime dependency;
    # QFGraph does not call AGL, so it needs no explicit application-level link.
    if not (Path(sdk_path) / 'System/Library/Frameworks/AGL.framework').exists():
        text = text.replace('-framework AGL', '')
    # qmake resets QMAKE_MOC/UIC when loading Qt features. Wrap the generated
    # commands instead, without changing files in the Qt installation.
    for name in ['moc', 'uic', 'rcc']:
        text = text.replace(str(Path(qt) / 'libexec' / name), str(Path(tools_dir) / name))
    p.write_text(text)


def copy(source, target):
    source, target = Path(source).resolve(), Path(target).resolve()
    if source == target or target.suffix != '.app':
        raise RuntimeError('Package target must be a separate .app directory.')
    if target.exists():
        shutil.rmtree(target)
    subprocess.run(['ditto', str(source), str(target)], check=True)


def verify(directory, *archs):
    app = Path(directory).resolve()
    exe = app / 'Contents/MacOS/QFGraph'
    if not exe.exists():
        raise RuntimeError(f'Missing executable: {exe}')
    files = list(binaries(app))
    for p in files:
        architectures(p, archs)
        for line in run('otool', '-L', str(p)).splitlines():
            if ' (compatibility version ' not in line:
                continue
            dep = line.strip().split(' (compatibility version ')[0]
            if dep.startswith('/') and not dep.startswith(('/System/', '/usr/lib/')):
                raise RuntimeError(f'External dependency in {p}: {dep}')
            if dep.startswith('@rpath/'):
                bundled = app / 'Contents/Frameworks' / dep.removeprefix('@rpath/')
                if not bundled.exists():
                    raise RuntimeError(f'Missing bundled dependency: {dep}')
    if not (app / 'Contents/PlugIns/platforms/libqcocoa.dylib').exists():
        raise RuntimeError('Missing Cocoa platform plugin.')
    print(f'Verified {len(files)} binaries: {", ".join(archs)}; dependencies bundled.')


def smoke(directory, *archs):
    exe = Path(directory).resolve() / 'Contents/MacOS/QFGraph'
    env = {k: v for k, v in os.environ.items() if not k.startswith(('QT_', 'DYLD_'))}
    env['PATH'] = '/usr/bin:/bin:/usr/sbin:/sbin'
    for arch in archs:
        p = subprocess.Popen(['/usr/bin/arch', '-' + arch, str(exe)], env=env,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            out, err = p.communicate(timeout=8)
            raise RuntimeError(f'{arch}: exited with {p.returncode}: {err.decode(errors="replace")}')
        except subprocess.TimeoutExpired:
            p.terminate()
            p.communicate(timeout=10)
            print(f'{arch}: startup passed (8 seconds).')


def clean(directory):
    p = Path(directory).resolve()
    if p == Path.cwd() or p in Path.cwd().parents or p == Path.home():
        raise RuntimeError('Refusing to remove a source or home directory.')
    if p.exists():
        if not (p / '.qmake.stash').exists():
            raise RuntimeError('Refusing to remove a directory without a qmake build marker.')
        shutil.rmtree(p)


if __name__ == '__main__':
    commands = {f.__name__: f for f in (configure, check, tools, sdk, copy, verify, smoke, clean)}
    try:
        commands[sys.argv[1]](*sys.argv[2:])
    except (RuntimeError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
