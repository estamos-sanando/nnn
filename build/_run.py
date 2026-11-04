import sys, importlib, traceback, time
B = r'd:\jeugosnacho\build'
if B not in sys.path:
    sys.path.insert(0, B)


def go(modname, fn='build', *args):
    t = time.time()
    try:
        import common
        importlib.reload(common)
        m = importlib.import_module(modname)
        importlib.reload(m)
        r = getattr(m, fn)(*args)
        msg = 'OK %.1fs %s' % (time.time() - t, r if isinstance(r, (str, int, float)) else '')
    except Exception:
        msg = traceback.format_exc()
    open(B + '\\log.txt', 'w', encoding='utf-8').write(msg)

