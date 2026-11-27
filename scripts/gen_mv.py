# Generates the multiview robot inputs (left/back/right) with an edit model, using a
# deneme/workflows/<id>.json workflow, and copies them into deneme/inputs/.
#   PY gen_mv.py --root <test-klasoru> --port 8398 --wf mage-flow-edit-turbo [--seed 7]
import argparse, json, os, shutil, sys, time, urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import bla_wf  # noqa: E402

VIEWS = [("mv_robot_left.jpg", "Show the same robot from its left side (profile view), same lighting, plain light grey background"),
         ("mv_robot_back.jpg", "Show the same robot from directly behind, same lighting, plain light grey background"),
         ("mv_robot_right.jpg", "Show the same robot from its right side (profile view), same lighting, plain light grey background")]


def api(port, path, body=None):
    req = urllib.request.Request(f'http://127.0.0.1:{port}{path}', data=None if body is None else json.dumps(body).encode(),
                                 headers={'content-type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as r:
        t = r.read()
        return json.loads(t) if t else None


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--root', required=True); a.add_argument('--port', type=int, default=8398)
    a.add_argument('--wf', required=True); a.add_argument('--seed', type=int, default=7)
    a.add_argument('--repo', default=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
    o = a.parse_args()
    here = os.path.join(o.repo, 'deneme')
    m = json.load(open(os.path.join(here, 'workflows', o.wf + '.json'), encoding='utf-8'))
    src = 'g_robot.jpg'
    shutil.copy(os.path.join(here, 'inputs', src), os.path.join(o.root, 'in', 'mt_mv_src.jpg'))
    api(o.port, '/free', {'unload_models': True, 'free_memory': True})
    for out_name, prompt in VIEWS:
        w = bla_wf.fill(m, prompt=prompt, images=['mt_mv_src.jpg'], seed=o.seed, prefix='mt/mv')
        pid = api(o.port, '/prompt', {'prompt': w})['prompt_id']
        h = None
        for _ in range(1800):
            time.sleep(1)
            h = api(o.port, f'/history/{pid}').get(pid)
            if h and h.get('status', {}).get('completed') is not None:
                break
        if not h or h['status'].get('status_str') != 'success':
            print('FAIL', out_name, str(h and h.get('status'))[:200]); return
        f = next(i for n in h['outputs'].values() for i in n.get('images', []) if i.get('type') == 'output')
        srcf = os.path.join(o.root, 'out', f.get('subfolder', ''), f['filename'])
        shutil.copy(srcf, os.path.join(here, 'inputs', out_name))
        print('ok', out_name, f['filename'])
    shutil.copy(os.path.join(here, 'inputs', src), os.path.join(here, 'inputs', 'mv_robot_front.jpg'))
    print('ok mv_robot_front.jpg (kopya)')


if __name__ == '__main__':
    main()
