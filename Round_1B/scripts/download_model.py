from sentence_transformers import SentenceTransformer
import os

def download_and_save_model():
   
    model_name = 'sentence-transformers/multi-qa-MiniLM-L6-cos-v1'
    save_path = os.path.join(os.path.dirname(__file__), '..', 'models', os.path.basename(model_name))

    if not os.path.exists(save_path):
        print(f"Downloading model: {model_name}...")
        model = SentenceTransformer(model_name)
        model.save(save_path)
        print(f"Model successfully downloaded and saved to: {save_path}")
    else:
        print(f"Model '{model_name}' already exists at {save_path}. Skipping download.")

if __name__ == "__main__":
    models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
    os.makedirs(models_dir, exist_ok=True)
    download_and_save_model()