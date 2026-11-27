# Downloads a catalog model's files (or any Hugging Face file) into the test folder, resumable, SHA-256 checked.
#   python -I download.py --catalog ..\..\..\app\src-tauri\catalog\catalog.json --root <test-klasoru> z-image-turbo flux2-klein-4b
#   python -I download.py --root <test-klasoru> --url loras https://huggingface.co/.../x.safetensors
# --dry prints sizes only (say the size before a big download). Needs curl (in Windows 10+).
import argparse, hashlib, http.client, json, os, subprocess, sys, time, urllib.parse


def head(u, tok=None):
    hdrs = {'Authorization': f'Bearer {tok}'} if tok else {}
    for _ in range(8):
        p = urllib.parse.urlparse(u)
        c = http.client.HTTPSConnection(p.netloc, timeout=30)
        c.request('HEAD', p.path + ('?' + p.query if p.query else ''), headers=hdrs)
        r = c.getresponse()
        h = {k.lower(): v for k, v in r.getheaders()}
        if 'x-linked-size' in h:
            return int(h['x-linked-size']), h.get('x-linked-etag', '').strip('"')
        if r.status in (301, 302, 303, 307, 308):
            u = urllib.parse.urljoin(u, h['location'])
            continue
        if r.status == 200 and 'content-length' in h:
            return int(h['content-length']), ''
        raise SystemExit(f'HEAD {u}: HTTP {r.status} (gated repo? log in on huggingface.co and accept the licence)')
    raise SystemExit(f'too many redirects: {u}')


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 24), b''):
            h.update(b)
    return h.hexdigest()


def get(root, d, url, size=None, sha=None, log=print, tok=None):
    name = url.rsplit('/', 1)[1].split('?')[0]
    dst = os.path.join(root, 'models', d, name)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if size is None:
        size, sha = head(url, tok)
    if os.path.exists(dst) and os.path.getsize(dst) == size:
        log(f'have {d}/{name}')
        return dst
    log(f'start {d}/{name} {size / 1e9:.2f} GB')
    t = time.time()
    cmd = ['curl', '-sSL', '--retry', '5', '-C', '-', '-o', dst + '.part']
    if tok:
        cmd += ['-H', f'Authorization: Bearer {tok}']
    for _ in range(30):
        subprocess.run(cmd + [url])
        if os.path.exists(dst + '.part') and os.path.getsize(dst + '.part') >= size:
            break
        time.sleep(10)
    else:
        raise SystemExit(f'download failed: {name}')
    if sha and len(sha) == 64 and sha256(dst + '.part') != sha:
        os.remove(dst + '.part')
        raise SystemExit(f'SHA-256 mismatch: {name} (deleted, run again)')
    os.replace(dst + '.part', dst)
    log(f'done {d}/{name} {size / 1e6 / max(time.time() - t, 1):.1f} MB/s')
    return dst


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--catalog')
    a.add_argument('--root', required=True)
    a.add_argument('--url', nargs=2, action='append', metavar=('DIR', 'URL'), default=[])
    a.add_argument('--dry', action='store_true')
    a.add_argument('--token', help='HF token string, or a path to a file containing it')
    a.add_argument('ids', nargs='*')
    o = a.parse_args()
    tok = None
    if o.token:
        tok = o.token.strip()
        if os.path.exists(tok):
            tok = open(tok, encoding='utf-8').read().strip()
    elif os.environ.get('HF_TOKEN'):
        tok = os.environ['HF_TOKEN'].strip()
    jobs = []
    if o.ids:
        cat = json.load(open(o.catalog, encoding='utf-8'))
        for mid in o.ids:
            m = next((x for x in cat['models'] if x['id'] == mid), None)
            if not m:
                raise SystemExit(f'unknown model {mid}')
            jobs += [(f['dir'], f['url'], f['size'], f['sha256']) for f in m['files']]
    jobs += [(d, u, None, None) for d, u in o.url]
    seen, total = set(), 0
    for d, u, s, h in jobs:
        if u in seen:
            continue
        seen.add(u)
        s = s or head(u, tok)[0]
        total += s
        print(f'{s / 1e9:7.2f} GB  {d}/{u.rsplit("/", 1)[1]}')
    print(f'{total / 1e9:7.2f} GB in all (files already there are skipped)')
    if o.dry:
        return
    logf = open(os.path.join(o.root, 'download.log'), 'a', encoding='utf-8', buffering=1)
    log = lambda s: (print(s), logf.write(time.strftime('%Y-%m-%d %H:%M ') + s + '\n'))
    done = set()
    for d, u, s, h in jobs:
        if u not in done:
            done.add(u)
            get(o.root, d, u, s, h, log, tok)


if __name__ == '__main__':
    main()
