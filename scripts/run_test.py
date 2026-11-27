# Runs the tests in tests.json on the test ComfyUI, the way BananaLA would (catalog models, or workflows/<id>.json), and writes one CSV row per run plus a
# small JPEG preview (images) or the GLB itself (3D) into the results folder.
#   <ComfyUI>\python_embeded\python.exe -s run_test.py --catalog ..\..\..\app\src-tauri\catalog\catalog.json
#       --root D:\bla-3070 --port 8398 --tests ..\tests.json --out ..\sonuclar [--only z-image-turbo] [--test t2i-cabin]
# Measures: wall time from submit to done, the card's peak used memory (nvidia-smi, every 0.5 s; other programs
# included, so note the idle value), and the lowest free system RAM (ComfyUI /system_stats).
import argparse, csv, json, os, shutil, subprocess, sys, threading, time, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bla_wf  # noqa: E402


def api(port, path, body=None):
    req = urllib.request.Request(f'http://127.0.0.1:{port}{path}', data=None if body is None else json.dumps(body).encode(),
                                 headers={'content-type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as r:
        t = r.read()
        return json.loads(t) if t else None


class Sampler(threading.Thread):
    """Peak GPU memory (MB) and lowest free RAM (MB) while a run is going."""
    def __init__(self, port):
        super().__init__(daemon=True)
        self.port, self.stop, self.vram, self.ram_free = port, False, 0, None

    def run(self):
        while not self.stop:
            try:
                o = subprocess.run(['nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=5).stdout
                self.vram = max(self.vram, max(int(x) for x in o.split()))
                s = api(self.port, '/system_stats')['system']
                f = s['ram_free'] // (1 << 20)
                self.ram_free = f if self.ram_free is None else min(self.ram_free, f)
            except Exception:
                pass
            time.sleep(0.5)


def find_model(o, cat, mid):
    # A model outside the catalog: workflows/<id>.json, an entry in the catalog's own shape (inputs, params,
    # workflow with {{prompt}} {{width}} {{height}} {{steps}} {{seed}} {{batch}} {{faces}} {{image}} {{prefix}},
    # optional max_inputs / refs / lora_base).
    f = os.path.join(o.workflows, mid + '.json')
    if os.path.exists(f):
        with open(f, encoding='utf-8') as fh:
            m = json.load(fh)
        m.setdefault('id', mid)
        return m
    return bla_wf.model(cat, mid)


def run_one(o, cat, t, mid, extra, writer, last):
    try:
        m = find_model(o, cat, mid)
    except bla_wf.Invalid as e:
        writer.writerow({'test': t['id'], 'model': mid, 'result': f'invalid: {e}'}); return
    images = []
    for k, name in enumerate(t.get('images', [])):
        dst = f'bla3070_{t["id"]}_{k}{os.path.splitext(name)[1]}'
        shutil.copy(os.path.join(o.inputs, name), os.path.join(o.root, 'in', dst))
        images.append(dst)
    loras = [dict(l) for l in t.get('loras', [])]
    tag = '_'.join(str(x) for x in extra.values())
    prefix = f'bla3070/{t["id"]}_{mid}_{tag}'.rstrip('_')
    row = {'test': t['id'], 'model': mid, **{k: extra.get(k, '') for k in ('width', 'height', 'steps', 'faces')}, 'seed': o.seed,
           'loras': '+'.join(f'{l["file"]}@{l["strength"]}' for l in loras), 'inputs': len(images)}
    try:
        w = bla_wf.fill(m, prompt=t.get('prompt', ''), images=images, loras=loras, seed=o.seed, prefix=prefix, batch=1, **extra)
    except bla_wf.Invalid as e:
        writer.writerow({**row, 'result': f'invalid: {e}'}); return
    # BananaLA frees the card when the model changes (one model on the card at a time).
    if last[0] != mid:
        api(o.port, '/free', {'unload_models': True, 'free_memory': True}); time.sleep(2)
        last[0] = mid
    s = Sampler(o.port); s.start()
    t0 = time.time()
    try:
        pid = api(o.port, '/prompt', {'prompt': w})['prompt_id']
    except urllib.error.HTTPError as e:
        s.stop = True
        writer.writerow({**row, 'result': 'rejected: ' + e.read().decode('utf-8', 'replace')[:300]}); return
    h = None
    while time.time() - t0 < o.timeout:
        time.sleep(1)
        h = api(o.port, f'/history/{pid}').get(pid)
        if h and h.get('status', {}).get('completed') is not None:
            break
    s.stop = True; s.join()
    secs = round(time.time() - t0, 1)
    if not h:
        api(o.port, '/interrupt', {}); writer.writerow({**row, 'result': 'timeout', 'seconds': secs}); return
    st = h['status']
    if st.get('status_str') != 'success':
        err = next((m_[1] for m_ in st.get('messages', []) if m_[0] == 'execution_error'), {})
        msg = f'{err.get("node_type", "")}: {str(err.get("exception_message", ""))[:300]}'
        oom = 'out of memory' in msg.lower() or 'allocation' in msg.lower()
        writer.writerow({**row, 'result': ('oom: ' if oom else 'error: ') + msg, 'seconds': secs, 'peak_vram_mb': s.vram, 'min_ram_free_mb': s.ram_free}); return
    files = []
    for node in h['outputs'].values():
        for kind, items in node.items():  # images, 3d, gifs, videos, ...
            for f in items if isinstance(items, list) else []:
                if isinstance(f, dict) and f.get('filename') and f.get('type', 'output') == 'output':
                    files.append(os.path.join(o.root, 'out', f.get('subfolder', ''), f['filename']))
    saved = []
    for f in files:
        base = os.path.join(o.out, 'files', os.path.basename(f))
        os.makedirs(os.path.dirname(base), exist_ok=True)
        if not f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            size = os.path.getsize(f)
            row['out_size'] = f'{size / 1e6:.1f} MB'
            if size <= 10e6:  # GLB / PLY / MP4: the repo takes small ones only
                shutil.copy(f, base); saved.append(base)
        else:
            try:
                from PIL import Image
                im = Image.open(f).convert('RGB'); row['out_size'] = f'{im.width}x{im.height}'
                im.thumbnail((1024, 1024)); jpg = os.path.splitext(base)[0] + '.jpg'; im.save(jpg, quality=88); saved.append(jpg)
            except ImportError:
                shutil.copy(f, base); saved.append(base)
    writer.writerow({**row, 'result': 'ok', 'seconds': secs, 'peak_vram_mb': s.vram, 'min_ram_free_mb': s.ram_free,
                     'files': ' '.join(os.path.relpath(x, o.out) for x in saved)})


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--catalog', required=True); a.add_argument('--root', required=True); a.add_argument('--port', type=int, default=8398)
    a.add_argument('--tests', required=True); a.add_argument('--out', required=True); a.add_argument('--inputs'); a.add_argument('--workflows')
    a.add_argument('--only', action='append'); a.add_argument('--test', action='append'); a.add_argument('--timeout', type=int, default=1800)
    o = a.parse_args()
    cat = bla_wf.load_catalog(o.catalog)
    spec = json.load(open(o.tests, encoding='utf-8'))
    o.seed = spec.get('seed', 7)
    o.inputs = o.inputs or os.path.join(os.path.dirname(os.path.abspath(o.tests)), 'inputs')
    o.workflows = o.workflows or os.path.join(os.path.dirname(os.path.abspath(o.tests)), 'workflows')
    os.makedirs(os.path.join(o.root, 'in'), exist_ok=True); os.makedirs(o.out, exist_ok=True)
    path = os.path.join(o.out, 'sonuclar.csv')
    cols = ['time', 'test', 'model', 'width', 'height', 'steps', 'faces', 'seed', 'loras', 'inputs', 'result', 'seconds', 'peak_vram_mb', 'min_ram_free_mb', 'out_size', 'files']
    new = not os.path.exists(path)
    f = open(path, 'a', newline='', encoding='utf-8')
    w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
    if new:
        w.writeheader()
    class W:
        def writerow(self, r):
            r = {'time': time.strftime('%Y-%m-%d %H:%M'), **r}; w.writerow(r); f.flush()
            print(r['test'], r['model'], r.get('width', ''), r.get('faces', ''), r['result'][:120], r.get('seconds', ''), 's', r.get('peak_vram_mb', ''), 'MB')
    last = [None]
    for t in spec['tests']:
        if o.test and t['id'] not in o.test:
            continue
        for mid in t['models']:
            if o.only and mid not in o.only:
                continue
            for extra in t.get('variants', [{}]):
                run_one(o, cat, t, mid, dict(extra), W(), last)


if __name__ == '__main__':
    main()
