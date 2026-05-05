# Model notes

The default segmentation model is `nvidia/segformer-b2-finetuned-ade-512-512`.

The model is loaded with Hugging Face Transformers and PyTorch. It is a pretrained ADE20K semantic segmentation model, so it does not require training for this technical assessment. Aerial imagery can still create domain-shift errors because ADE20K is not exclusively a drone dataset.

The service resizes large images before inference to protect free CPU memory. The default `MAX_INFERENCE_SIDE` is 1280. Increase it only when the deployment hardware is stronger.
