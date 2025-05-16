import os
import cv2   # OpenCV for image I/O
import numpy as np
from insightface.app import FaceAnalysis
from sklearn.metrics.pairwise import cosine_similarity
from django.conf import settings
from .models import Person
import pickle

FACE_EMBEDDINGS_PICKLE = 'face_embeddings.pickle'

class FaceRecognizer:
    """
    Wrapper around InsightFace that loads all images under
    MEDIA_ROOT/persons/<person_id>/ and matches incoming frames.
    """
    base_dir = base_dir = os.path.join(settings.MEDIA_ROOT, 'persons')
    
    def __init__(self, model_name='buffalo_m', det_size=(640, 640), threshold=0.35):
        # Initialize InsightFace model
        self.app = FaceAnalysis(name=model_name, providers=['CPUExecutionProvider','CPUExecutionProvider'], root=settings.INSIGHTFACE_MODEL_ROOT)
        self.app.prepare(ctx_id=0, det_size=det_size)
        self.threshold = threshold
        self.embeddings = {}  # maps person_id to list of embeddings
        self.pickle_file_path = os.path.join(settings.BASE_DIR, FACE_EMBEDDINGS_PICKLE)

    def get_embeddings(self, person: Person):
        person_dir = os.path.join(FaceRecognizer.base_dir, str(person.id))
        if not os.path.isdir(person_dir):
            return
        embs = []
        for fname in os.listdir(person_dir):
            if fname.lower().endswith(('.jpg', '.jpeg', '.png')):
                img_path = os.path.join(person_dir, fname)
                img = cv2.imread(img_path)
                if img is None:
                    continue
                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                faces = self.app.get(rgb)
                print(f"Found {len(faces)} faces in {img_path}")
                if not faces:
                    continue
                # pick the largest face in the image
                face = max(faces, key=lambda f: (f.bbox[2]-f.bbox[0]) * (f.bbox[3]-f.bbox[1]))
                print(f"Face detected with bbox: {face.bbox}")
                embs.append(face.normed_embedding)
        return embs
    
    def register_all(self):
        """
        Walk through MEDIA_ROOT/persons/<id>/ for each Person,
        read every image file, compute its embedding, and store it.
        """        
        self.embeddings = pickle.load(open(self.pickle_file_path, 'rb')) if os.path.exists(self.pickle_file_path) else {}
        for person in Person.objects.all():
            if person.id in self.embeddings:
                print(f"Person {person.id} already registered.")
                continue
            embs = self.get_embeddings(person)
            if embs:
                self.embeddings[person.id] = embs
        
        # Save the embeddings to a pickle file
        with open(self.pickle_file_path, 'wb') as f:
            pickle.dump(self.embeddings, f)

    def recognize(self, frame):
        """
        Given a BGR frame array, detect faces and return
        list of matched Person IDs.
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faces = self.app.get(rgb)
        matched_ids = []
        
        for f in faces:
            query_emb = f.normed_embedding.reshape(1, -1)
            for pid, db_embs in self.embeddings.items():
                sims = cosine_similarity(query_emb, np.stack(db_embs))
                # cosine_similarity returns similarity, so threshold it directly
                if np.max(sims) >= self.threshold:
                    matched_ids.append({
                        'id': pid,
                        "coordinates":  list(map(int, f.bbox[:4]))
                    })
                    break

        return matched_ids
