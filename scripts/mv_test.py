# Runs the multi-view 3D tests (3d-cok-aci-robot) whose workflows take named views.
# workflows/<id>.json uses {{image1}}..{{image4}} (front, left, back, right) + {{seed}} {{prefix}}.
# Same CSV/logic as run_test.py (GOREV.md: "gerekirse run_test.py'yi düzenle").
#   PY deneme\scripts\mv_test.py --catalog ... --root <test-klasoru> --port 8398 --tests ... --out ... --only hunyuan3d-2-mv-turbo
import argparse, csv, json, os, shutil, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_test  # reuse api(), Sampler()  # noqa: E402


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--catalog', required=True); a.add_argument('--root', required=True); a.add_argument('--port', type=int, default=8398)
    a.add_argument('--tests', required=True); a.add_argument('--out', required=True); a.add_argument('--inputs'); a.add_argument('--workflows')
    a.add_argument('--only', action='append'); a.add_argument('--test', action='append'); a.add_argument('--timeout', type=int, default=1800)
    o = a.parse_args()
    spec = json.load(open(o.tests, encoding='utf-8'))
    o.seed = spec.get('seed', 7)
    here = os.path.dirname(os.path.abspath(o.tests))
    o.inputs = o.inputs or os.path.join(here, 'inputs')
    o.workflows = o.workflows or os.path.join(here, 'workflows')
    os.makedirs(os.path.join(o.root, 'in'), exist_ok=True); os.makedirs(o.out, exist_ok=True)
    path = os.path.join(o.out, 'sonuclar.csv')
    cols = run_test.__dict__  # csv columns are defined inside run_test.main; replicate here
    new = not os.path.exists(path)
    f = open(path, 'a', newline='', encoding='utf-8')
    w = csv.DictWriter(f, fieldnames=['time', 'test', 'model', 'width', 'height', 'steps', 'faces', 'seed', 'loras', 'inputs', 'result', 'seconds', 'peak_vram_mb', 'min_ram_free_mb', 'out_size', 'files'], extrasaction='ignore')
    if new:
        w.writeheader()
    for t in spec['tests']:
        if o.test and t['id'] not in o.test:
            continue
        if not o.test and not t['id'].startswith('3d-cok-aci'):
            continue
        for mid in t['models']:
            if o.only and mid not in o.only:
                continue
            m = json.load(open(os.path.join(o.workflows, mid + '.json'), encoding='utf-8'))
            names = []
            for k, name in enumerate(t.get('images', [])):
                dst = f'mt_{t["id"]}_{k}{os.path.splitext(name)[1]}'
                shutil.copy(os.path.join(o.inputs, name), os.path.join(o.root, 'in', dst))
                names.append(dst)
            wf = json.dumps(m['workflow'])
            for k, n in enumerate(names):
                wf = wf.replace('{{image%d}}' % (k + 1), n)
            wf = wf.replace('{{seed}}', str(o.seed)).replace('{{prefix}}', f'mt/{t["id"]}_{mid}')
            for pk, pv in (('steps', m.get('params', {}).get('steps', {}).get('default', 20)),
                           ('faces', m.get('params', {}).get('faces', {}).get('default', 1))):
                wf = wf.replace('"%s"' % ('{{' + pk + '}}'), str(pv)).replace('{{' + pk + '}}', str(pv))
            wrow = {'test': t['id'], 'model': mid, 'seed': o.seed, 'inputs': len(names)}
            run_test.api(o.port, '/free', {'unload_models': True, 'free_memory': True}); time.sleep(2)
            s = run_test.Sampler(o.port); s.start(); t0 = time.time()
            try:
                pid = run_test.api(o.port, '/prompt', {'prompt': json.loads(wf)})['prompt_id']
            except Exception as e:
                s.stop = True
                body = e.read().decode('utf-8', 'replace')[:300] if hasattr(e, 'read') else str(e)[:300]
                w.writerow({**wrow, 'result': 'rejected: ' + body}); f.flush(); continue
            h = None
            while time.time() - t0 < o.timeout:
                time.sleep(1)
                h = run_test.api(o.port, f'/history/{pid}').get(pid)
                if h and h.get('status', {}).get('completed') is not None:
                    break
            s.stop = True; s.join()
            secs = round(time.time() - t0, 1)
            if not h:
                run_test.api(o.port, '/interrupt', {}); w.writerow({**wrow, 'result': 'timeout', 'seconds': secs}); f.flush(); continue
            st = h['status']
            if st.get('status_str') != 'success':
                err = next((m_[1] for m_ in st.get('messages', []) if m_[0] == 'execution_error'), {})
                msg = f'{err.get("node_type", "")}: {str(err.get("exception_message", ""))[:300]}'
                oom = 'out of memory' in msg.lower() or 'allocation' in msg.lower()
                w.writerow({**wrow, 'result': ('oom: ' if oom else 'error: ') + msg, 'seconds': secs, 'peak_vram_mb': s.vram, 'min_ram_free_mb': s.ram_free}); f.flush(); continue
            files = []
            for node in h['outputs'].values():
                for kind, items in node.items():
                    for fi in items if isinstance(items, list) else []:
                        if isinstance(fi, dict) and fi.get('filename') and fi.get('type', 'output') == 'output':
                            files.append(os.path.join(o.root, 'out', fi.get('subfolder', ''), fi['filename']))
            saved = []
            for fi in files:
                base = os.path.join(o.out, 'files', os.path.basename(fi))
                os.makedirs(os.path.dirname(base), exist_ok=True)
                size = os.path.getsize(fi)
                wrow['out_size'] = f'{size / 1e6:.1f} MB'
                if size <= 10e6:
                    shutil.copy(fi, base); saved.append(base)
            w.writerow({**wrow, 'result': 'ok', 'seconds': secs, 'peak_vram_mb': s.vram, 'min_ram_free_mb': s.ram_free,
                        'files': ' '.join(os.path.relpath(x, o.out) for x in saved)})
            print(t['id'], mid, 'ok', secs, 's', s.vram, 'MB')
            f.flush()


if __name__ == '__main__':
    main()
