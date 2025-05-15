# core/views.py
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Event
import base64
import numpy as np
import cv2
from django.http import JsonResponse, HttpResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from .models import Event, Person, Attendance
from insightface.app import FaceAnalysis
from django.conf import settings
from .face_recognition import FaceRecognizer


def home(request):
    """
    Renders the admin home page with navigation links
    to Events and Attendance History.
    """
    return render(request, 'core/home.html')
# core/views.py

def events_list(request):
    """
    Lists events for today and the future, ordered by date.
    """
    today = timezone.localdate()
    events = Event.objects.filter(date__gte=today).order_by('date')
    return render(request, 'core/events.html', {'events': events})

def start_attendance(request, pk):
    """
    Renders the page with a <video> element and JS to stream to backend.
    """
    event = get_object_or_404(Event, pk=pk)
    return render(request, 'core/start_attendance.html', {'event': event})

# Initialize and register all known faces once
face_recognizer = FaceRecognizer(model_name='buffalo_l', threshold=0.35)
face_recognizer.register_all()

@csrf_exempt
def stream_frame(request, pk):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    data_uri = request.POST.get('frame')
    if not data_uri:
        return JsonResponse({'status': 'error', 'message': 'No frame data'}, status=400)

    try:
        header, b64 = data_uri.split(',', 1)
        img_bytes = base64.b64decode(b64)
    except Exception:
        return JsonResponse({'status': 'error', 'message': 'Invalid frame format'}, status=400)

    arr = np.frombuffer(img_bytes, dtype=np.uint8)
    if arr.size == 0:
        return JsonResponse({'status': 'error', 'message': 'Empty buffer'}, status=400)

    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        return JsonResponse({'status': 'error', 'message': 'Decode failed'}, status=400)

    # 1) Run detection & recognition
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    faces = face_recognizer.app.get(rgb)

    event = get_object_or_404(Event, pk=pk)
    now = timezone.now()
    marked = []

    matched_ids = face_recognizer.recognize(frame)
    print(f"Matched IDs: {matched_ids}")

    # 4. Mark attendance for each matched person
    event = get_object_or_404(Event, pk=pk)
    print(f"Event: {event}")
    marked = []
    now = timezone.now()
    for p in matched_ids:
        person = Person.objects.get(pk=p['id'])
        attendance_obj, created = Attendance.objects.get_or_create(
            person=person,
            event=event,
            defaults={'timestamp': now}
        )
        x1, y1, x2, y2 = p['coordinates']
        print(f"Coordinates: {x1}, {y1}, {x2}, {y2}")
        # if created:
        marked.append(person.name)
        cv2.putText(frame, person.name, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            # break
    # for f in faces:
        # Draw rectangle on the original BGR frame

        # Recognize

    # 2) Encode annotated frame back to JPEG
    success, jpeg = cv2.imencode('.jpg', frame)
    if not success:
        return JsonResponse({'status': 'error', 'message': 'Encoding failed'}, status=500)

    b64_jpeg = base64.b64encode(jpeg.tobytes()).decode('utf-8')
    annotated_uri = f"data:image/jpeg;base64,{b64_jpeg}"

    return JsonResponse({
        'status': 'ok',
        'annotated_frame': annotated_uri,
        'marked': marked,
        'timestamp': now.isoformat(),
    })


def attendance_history(request):
    """
    Shows live attendance for today's events and history for past events.
    """
    today = timezone.localdate()
    live_events = Event.objects.filter(date=today)
    live_attendances = Attendance.objects.filter(event__in=live_events).select_related('person', 'event')
    past_attendances = Attendance.objects.filter(event__date__lt=today).select_related('person', 'event') \
                          .order_by('-timestamp')[:100]
    return render(request, 'core/attendance.html', {
        'live_attendances': live_attendances,
        'past_attendances': past_attendances,
    })
