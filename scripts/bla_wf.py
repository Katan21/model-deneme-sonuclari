# Builds a ComfyUI API workflow exactly the way BananaLA does (app/src-tauri/src/catalog.rs: fill, add_refs,
# add_loras), from app/src-tauri/catalog/catalog.json. Keep it in step with catalog.rs when that changes.
import json, random

MAX_LORAS = 3


class Invalid(Exception):
    pass


def load_catalog(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def model(cat, mid):
    for m in cat['models']:
        if m['id'] == mid:
            return m
    raise Invalid(f'unknown model {mid}')


def _check(name, v, rng):
    if rng is None:
        return None
    if v is None:
        return rng['default']
    if v < rng['min'] or v > rng['max']:
        raise Invalid(f'{name} must be {rng["min"]}..{rng["max"]}')
    step = rng.get('step')
    if step and (v - rng['min']) % step:
        raise Invalid(f'{name} must be a multiple of {step}')
    return v


def _walk(v, vals):
    if isinstance(v, str) and v.startswith('{{') and v.endswith('}}'):
        return vals.get(v[2:-2], v)
    if isinstance(v, list):
        return [_walk(x, vals) for x in v]
    if isinstance(v, dict):
        return {k: _walk(x, vals) for k, x in v.items()}
    return v


def _add_refs(w, refs, images, size):
    encoders = [refs['node']] + refs.get('also', [])
    for k, v in refs.get('extra', {}).items():
        w[k] = json.loads(json.dumps(v))
    key = refs.get('image_key') or 'images.image_{n}'
    for k, name in enumerate(images):
        nid = str(8101 + k)
        w[nid] = {'class_type': 'LoadImage', 'inputs': {'image': name}}
        src = refs['first'] if (refs.get('first') is not None and k == 0) else [nid, 0]
        for n in encoders:
            w[n]['inputs'][key.replace('{n}', str(k + 1))] = src
    for n in encoders:
        w[n]['inputs']['vae'] = refs['vae']
    if size and 'resolution' in w[refs['node']]['inputs']:
        wd, ht = size
        w[refs['node']]['inputs']['resolution'] = max(512, min(2048, round((wd * ht) ** 0.5 / 32) * 32))
    w[refs['sampler']]['inputs']['latent_image'] = refs['latent']


def _add_loras(w, loras):
    guiders = [k for k, n in w.items() if n['class_type'] == 'CFGGuider']
    samplers = [k for k, n in w.items() if n['class_type'] in ('KSampler', 'KSamplerAdvanced', 'SamplerCustom')]
    target = guiders[0] if guiders else (samplers[0] if samplers else None)
    if target is None or len(guiders) + len(samplers) != 1:
        raise Invalid('this model cannot take a LoRA')
    src = w[target]['inputs']['model']
    for k, l in enumerate(loras):
        nid = str(8201 + k)
        w[nid] = {'class_type': 'LoraLoaderModelOnly', 'inputs': {'model': src, 'lora_name': l['file'], 'strength_model': l['strength']}}
        src = [nid, 0]
    w[target]['inputs']['model'] = src


def fill(m, prompt='', width=None, height=None, steps=None, batch=None, faces=None, seed=None, images=(), loras=(), prefix='test'):
    """loras: [{'file': 'x.safetensors', 'strength': 1.0, 'trigger': 'Pixel art style.'}] (file inside models/loras)."""
    takes_text = 'text' in m['inputs']
    prompt = prompt.strip() if takes_text else ''
    if takes_text and not prompt:
        raise Invalid('prompt is empty')
    if 'image' in m['inputs'] and not takes_text and not images:
        raise Invalid('an input image is required')
    if len(images) > m.get('max_inputs', 0):
        raise Invalid(f'at most {m.get("max_inputs", 0)} input images')
    if loras:
        if not m.get('lora_base'):
            raise Invalid('this model takes no LoRA')
        if len(loras) > MAX_LORAS:
            raise Invalid(f'at most {MAX_LORAS} LoRAs')
    p = m.get('params', {})
    width = _check('width', width, p.get('width'))
    height = _check('height', height, p.get('height'))
    if m.get('max_pixels') and width and height and width * height > m['max_pixels']:
        raise Invalid(f'width x height must be at most {m["max_pixels"]}')
    steps = _check('steps', steps, p.get('steps'))
    batch = _check('batch', batch, p.get('batch'))
    faces = _check('faces', faces, p.get('faces'))
    seed = random.randrange(1 << 50) if seed is None else seed
    trig = [l['trigger'].strip() for l in loras if l.get('trigger', '').strip() and l['trigger'].strip().lower() not in prompt.lower()]
    if trig and prompt:
        prompt = ' '.join(trig) + ' ' + prompt
    vals = {'prompt': prompt, 'seed': seed, 'prefix': prefix}
    for k, v in (('width', width), ('height', height), ('steps', steps), ('batch', batch), ('faces', faces)):
        if v is not None:
            vals[k] = v
    if images:
        vals['image'] = images[0]
    w = _walk(json.loads(json.dumps(m['workflow'])), vals)
    if m.get('refs') and images:
        _add_refs(w, m['refs'], list(images), (width, height) if width and height else None)
    if loras:
        _add_loras(w, list(loras))
    return w
