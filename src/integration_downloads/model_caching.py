import torch
import clip
import open_clip
from transformers import AutoFeatureExtractor, AutoTokenizer, ClapModel, AutoProcessor, AutoModel
from sentence_transformers import SentenceTransformer

device = "cuda" if torch.cuda.is_available() else "cpu"

class ModelCache:
    models = {}
    def __init__(self):
        #self.models = {}
        pass

    def get_model(self, model_name, model_loader):
        if model_name not in self.models:
            print("Loading:", model_name, "in memory for query embeddings")
            self.models[model_name] = model_loader()
        else:
            print("Loading cached:", model_name, "for query embeddings")
        return self.models[model_name]
    
    def load_clip_vit_b_32(self):
        model, preprocess = clip.load("ViT-B/32", device=device)
        return model, preprocess


    def load_open_clip_vit_l_14(self):
        model, _, preprocess = open_clip.create_model_and_transforms('ViT-L-14', pretrained='datacomp_xl_s13b_b90k', device=device)
        tokenizer = open_clip.get_tokenizer('ViT-L-14')
        return model, preprocess, tokenizer


    def load_siglip_base_16_224(self):
        model = AutoModel.from_pretrained("google/siglip-base-patch16-224").to(device)
        tokenizer = AutoTokenizer.from_pretrained("google/siglip-base-patch16-224")
        processor = AutoProcessor.from_pretrained("google/siglip-base-patch16-224")
        return model, tokenizer, processor


    def load_larger_clap_general(self):
        model = ClapModel.from_pretrained("laion/larger_clap_general").to(device)
        audio_feature_extractor = AutoFeatureExtractor.from_pretrained("laion/larger_clap_general")
        audio_text_tokenizer = AutoTokenizer.from_pretrained("laion/larger_clap_general")
        return model, audio_feature_extractor, audio_text_tokenizer


    def load_all_minilm_l6_v2(self):
        return SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')