import json
import base64
import numpy as np
import cv2
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from .models import Event, Person, Attendance
from insightface.app import FaceAnalysis

# Initialize once (sync to async)
face_app = FaceAnalysis(name='buffalo_m')
face_app.prepare(ctx_id=0, det_size=(640, 640))

class AttendanceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.event_id = self.scope['url_route']['kwargs']['event_id']
        await self.accept()

    async def disconnect(self, close_code):
        pass  # clean-up if needed

    async def receive(self, text_data=None, bytes_data=None):
        """
        Expect JSON: {"frame": "data:image/jpeg;base64,/9j/..."}
        """
        data = json.loads(text_data)
        frame_uri = data.get('frame', '')
        try:
            header, b64 = frame_uri.split(',', 1)
            img_bytes = base64.b64decode(b64)
            arr = np.frombuffer(img_bytes, dtype=np.uint8)
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if frame is None:
                raise ValueError("decode failed")

            # Face Recognition Logic
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            faces = face_app.get(rgb)
            marked = []
            event = Event.objects.get(pk=self.event_id)
            for f in faces:
                emb = f.normed_embedding.reshape(1, -1)
                for person in Person.objects.all():
                    # assume person.embedding preloaded
                    dist = np.linalg.norm(person.embedding - emb)
                    if dist < 0.35:
                        Attendance.objects.get_or_create(person=person, event=event)
                        marked.append(person.name)

            # Send back which names were marked this frame
            await self.send(text_data=json.dumps({
                'status': 'ok',
                'marked': marked,
                'timestamp': timezone.now().isoformat(),
            }))
        except Exception as e:
            # send error back
            await self.send(text_data=json.dumps({
                'status': 'error',
                'message': str(e)
            }))
