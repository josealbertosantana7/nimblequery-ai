from diffusers import StableDiffusionPipeline
import torch

# Load the public model
pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
).to("cuda" if torch.cuda.is_available() else "cpu")

def generate_image(prompt: str):
    image = pipe(prompt).images[0]
    return image
