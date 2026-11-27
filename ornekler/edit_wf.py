# Edit workflows for the night comparison. usage: edit_wf.py out.json model prefix prompt img1 [img2] [--fast] [--seed N]
# model: q2511 (Qwen-Image-Edit-2511 int8) | q21 (Qwen-Image-2.1, catalog) | mm (MiniMax H3, 4 MP like the template)
import json,sys
a=[x for x in sys.argv[1:] if not x.startswith('--')]; fast='--fast' in sys.argv
out,model,pre,prompt,imgs=a[0],a[1],a[2],a[3],a[4:]
W={}
def n(k,c,i): W[k]={"class_type":c,"inputs":i}
for j,f in enumerate(imgs): n(str(8101+j),"LoadImage",{"image":f})
if model=="q2511":
    n("1","UNETLoader",{"unet_name":"qwen_image_edit_2511_int8_convrot.safetensors","weight_dtype":"default"})
    n("2","CLIPLoader",{"clip_name":"qwen_2.5_vl_7b_fp8_scaled.safetensors","type":"qwen_image","device":"default"})
    n("3","VAELoader",{"vae_name":"qwen_image_vae.safetensors"})
    n("4","ModelSamplingAuraFlow",{"model":["1",0],"shift":3.1})
    n("5","CFGNorm",{"model":["4",0],"strength":1})
    m=["5",0]
    if fast: n("6","LoraLoaderModelOnly",{"model":m,"lora_name":"Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors","strength_model":1}); m=["6",0]
    n("10","FluxKontextImageScale",{"image":["8101",0]})
    ims={"image1":["10",0]}
    for j in range(1,len(imgs)): ims[f"image{j+1}"]=[str(8101+j),0]
    n("11","TextEncodeQwenImageEditPlus",dict(clip=["2",0],vae=["3",0],prompt=prompt,**ims))
    n("12","TextEncodeQwenImageEditPlus",dict(clip=["2",0],vae=["3",0],prompt="",**ims))
    n("13","FluxKontextMultiReferenceLatentMethod",{"conditioning":["11",0],"reference_latents_method":"index_timestep_zero"})
    n("14","FluxKontextMultiReferenceLatentMethod",{"conditioning":["12",0],"reference_latents_method":"index_timestep_zero"})
    n("15","VAEEncode",{"pixels":["10",0],"vae":["3",0]})
    n("16","KSampler",{"model":m,"positive":["13",0],"negative":["14",0],"latent_image":["15",0],"seed":7,"steps":4 if fast else 40,"cfg":1 if fast else 4,"sampler_name":"euler","scheduler":"simple","denoise":1})
    n("17","VAEDecode",{"samples":["16",0],"vae":["3",0]})
    n("18","SaveImage",{"images":["17",0],"filename_prefix":"night/"+pre})
elif model=="q21":
    n("1","UNETLoader",{"unet_name":"qwen_image_2.1_int8_convrot.safetensors","weight_dtype":"default"})
    n("2","QwenImage21Cache",{"model":["1",0],"device":"auto","dtype":"default"})
    n("3","CLIPLoader",{"clip_name":"qwen3vl_8b_int8_convrot.safetensors","type":"qwen_image","device":"default"})
    n("4","VAELoader",{"vae_name":"qwen_image_2.1_vae_bf16.safetensors"})
    i={"clip":["3",0],"prompt":prompt,"negative_prompt":"","resolution":1024,"vae":["4",0]}
    for j in range(len(imgs)): i[f"images.image_{j+1}"]=[str(8101+j),0]
    n("5","TextEncodeQwenImage21",i)
    n("7","KSampler",{"model":["2",0],"positive":["5",0],"negative":["5",1],"latent_image":["5",2],"seed":7,"steps":25,"cfg":1,"sampler_name":"euler","scheduler":"simple","denoise":1})
    n("8","VAEDecode",{"samples":["7",0],"vae":["4",0]})
    n("9","SaveImage",{"images":["8",0],"filename_prefix":"night/"+pre})
elif model=="mm":
    n("1","UNETLoader",{"unet_name":"minimax_h3_image_pruned_int8_convrot.safetensors","weight_dtype":"default"})
    n("2","CLIPLoader",{"clip_name":"qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors","type":"minimax","device":"default"})
    n("3","VAELoader",{"vae_name":"minimax_h3_image_vae_fp16.safetensors"})
    n("20","ImageScaleToTotalPixels",{"image":["8101",0],"upscale_method":"area","megapixels":4,"resolution_steps":32})
    n("21","GetImageSize",{"image":["20",0]})
    i={"prompt":prompt,"width":["21",0],"height":["21",1],"clip":["2",0],"vae":["3",0],"images.image_1":["20",0]}
    for j in range(1,len(imgs)): i[f"images.image_{j+1}"]=[str(8101+j),0]
    n("5","MiniMaxH3ImageConditioning",i)
    n("6","ConditioningZeroOut",{"conditioning":["5",0]})
    n("7","KSampler",{"seed":7,"steps":6,"cfg":1,"sampler_name":"euler","scheduler":"simple","denoise":1,"model":["1",0],"positive":["5",0],"negative":["6",0],"latent_image":["5",1]})
    n("8","VAEDecode",{"samples":["7",0],"vae":["3",0]})
    n("9","SaveImage",{"images":["8",0],"filename_prefix":"night/"+pre})
elif model=="fibo":
    n("1","UNETLoader",{"unet_name":"fibo2_edit_turbo_int8_convrot.safetensors","weight_dtype":"default"})
    n("2","CLIPLoader",{"clip_name":"qwen3vl_4b_bf16.safetensors","type":"fibo2","device":"default"})
    n("3","VAELoader",{"vae_name":"flux2-vae.safetensors"})
    i={"clip":["2",0],"prompt":prompt,"negative_prompt":"","width":0,"height":0,"batch_size":1,"vae":["3",0]}
    for j in range(len(imgs)): i[f"images.image_{j+1}"]=[str(8101+j),0]
    n("4","TextEncodeFibo2",i)
    n("5","KSampler",{"model":["1",0],"positive":["4",0],"negative":["4",1],"latent_image":["4",2],"seed":7,"steps":4,"cfg":1,"sampler_name":"euler","scheduler":"simple","denoise":1})
    n("6","VAEDecode",{"samples":["5",0],"vae":["3",0]})
    n("7","SaveImage",{"images":["6",0],"filename_prefix":"night/"+pre})
elif model=="flux2":
    n("1","UNETLoader",{"unet_name":"flux2_dev_fp8mixed.safetensors","weight_dtype":"default"})
    n("2","CLIPLoader",{"clip_name":"mistral_3_small_flux2_fp8.safetensors","type":"flux2","device":"default"})
    n("3","VAELoader",{"vae_name":"flux2-vae.safetensors"})
    m=["1",0]
    if fast: n("4","LoraLoaderModelOnly",{"model":m,"lora_name":"Flux2TurboComfyv2.safetensors","strength_model":1}); m=["4",0]
    n("5","CLIPTextEncode",{"clip":["2",0],"text":prompt})
    n("6","FluxGuidance",{"conditioning":["5",0],"guidance":4}); c=["6",0]
    for j in range(len(imgs)):
        n(f"{20+j}","ImageScaleToTotalPixels",{"image":[str(8101+j),0],"upscale_method":"area","megapixels":1,"resolution_steps":1})
        n(f"{30+j}","VAEEncode",{"pixels":[f"{20+j}",0],"vae":["3",0]})
        n(f"{40+j}","ReferenceLatent",{"conditioning":c,"latent":[f"{30+j}",0]}); c=[f"{40+j}",0]
    n("50","GetImageSize",{"image":["20",0]})
    n("51","EmptyFlux2LatentImage",{"width":["50",0],"height":["50",1],"batch_size":1})
    n("52","Flux2Scheduler",{"steps":8 if fast else 20,"width":["50",0],"height":["50",1]})
    n("53","BasicGuider",{"model":m,"conditioning":c})
    n("54","KSamplerSelect",{"sampler_name":"euler"})
    n("55","RandomNoise",{"noise_seed":7})
    n("56","SamplerCustomAdvanced",{"noise":["55",0],"guider":["53",0],"sampler":["54",0],"sigmas":["52",0],"latent_image":["51",0]})
    n("57","VAEDecode",{"samples":["56",0],"vae":["3",0]})
    n("58","SaveImage",{"images":["57",0],"filename_prefix":"night/"+pre})
json.dump(W,open(out,"w"))
