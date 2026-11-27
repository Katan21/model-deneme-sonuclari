# P-H3-Image workflow (from the ComfyUI templates). usage: ph3.py out.json prefix W H request [image] [--noup]
# W=H=0 with an image: size follows the image (template scales it to 0.95 MP first). Prompt upsampler on unless --noup.
import json,sys
from math import gcd
a=[x for x in sys.argv[1:] if not x.startswith('--')]; up='--noup' not in sys.argv
out,pre,w,h,req=a[0],a[1],int(a[2]),int(a[3]),a[4]; img=a[5] if len(a)>5 else None
W={}
def n(k,c,i): W[k]={"class_type":c,"inputs":i}
n("1","UNETLoader",{"unet_name":"minimax_h3_fl2va_pruned_int8_convrot.safetensors","weight_dtype":"default"})
n("2","CLIPLoader",{"clip_name":"p-h3-image_text_encoder_int8_convrot.safetensors","type":"minimax","device":"default"})
n("3","VAELoader",{"vae_name":"p-h3-image_vae_int8_convrot.safetensors"})
n("19","LoraLoaderModelOnly",{"model":["1",0],"lora_name":"p-h3-image_lora_bf16.safetensors","strength_model":1})
n("18","MiniMaxH3SigmaShift",{"model":["19",0],"shift_video":1,"shift_audio":1})
if w: g=gcd(w,h); ar=f"{w//g}:{h//g}"
else: ar="auto"
p=f"Aspect ratio: {ar}\nRequest: {req}" if w else f"Request: {req}"
cond={"clip":["2",0],"vae":["3",0],"width":w,"height":h}
if img:
    n("26","LoadImage",{"image":img})
    n("6","ImageScaleToTotalPixels",{"image":["26",0],"upscale_method":"lanczos","megapixels":0.95,"resolution_steps":32})
    cond["images.image_1"]=["6",0]
    if not w:
        n("27","GetImageSize",{"image":["6",0]}); cond["width"]=["27",0]; cond["height"]=["27",1]
if up:
    n("4","CLIPLoader",{"clip_name":"p-h3-image_prompt_upsampler_w4a8.safetensors","type":"minimax","device":"default"})
    t={"clip":["4",0],"prompt":p,"max_length":1536,"sampling_mode":"off","thinking":True,"use_default_template":True,"mtp":"auto"}
    if img: t["images.image1"]=["6",0]
    n("29","TextGenerateV2",t); cond["prompt"]=["29",0]
    n("8","PreviewAny",{"source":["29",0]})
else: cond["prompt"]=p
n("9","PH3ImageConditioning",cond)
n("10","BasicGuider",{"model":["18",0],"conditioning":["9",0]})
n("11","KSamplerSelect",{"sampler_name":"er_sde"})
n("12","RandomNoise",{"noise_seed":7})
n("13","ManualSigmas",{"sigmas":"1.0, 0.984753, 0.967905, 0.951688, 0.925372, 0.881923, 0.810083, 0.528718, 0.0"})
n("14","SamplerCustomAdvanced",{"noise":["12",0],"guider":["10",0],"sampler":["11",0],"sigmas":["13",0],"latent_image":["9",1]})
n("15","VAEDecode",{"samples":["14",0],"vae":["3",0]})
n("16","SaveImage",{"images":["15",0],"filename_prefix":"night/"+pre})
json.dump(W,open(out,"w"))
