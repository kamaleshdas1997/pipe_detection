import os
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
import cv2
import numpy as np
import base64

class PipeCountAPI(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def count_and_mark_pipes(self, image_path):
        # Load the image
        image = cv2.imread(image_path)

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply GaussianBlur to reduce noise
        blurred = cv2.GaussianBlur(gray, (7, 7), 2)
        cv2.imwrite("gray_image.png", gray)
        cv2.imwrite("blurred_image.png", blurred)
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=50,  # Increase to avoid overlapping circles
            param1=100,  # Increase for stricter edge detection
            param2=50,   # Increase to detect only strong circles
            minRadius=10, # Adjust based on pipe size
            maxRadius=100
        )

        # If circles are detected, mark them on the image
        pipe_count = 0
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            for (x, y, r) in circles:
                cv2.circle(image, (x, y), r, (0, 255, 0), 4)  # Draw the circle
                cv2.rectangle(image, (x - 5, y - 5), (x + 5, y + 5), (255, 0, 0), -1)  # Draw the center
            pipe_count = len(circles)

        # Encode the marked image as Base64
        _, buffer = cv2.imencode('.png', image)
        marked_image_base64 = base64.b64encode(buffer).decode('utf-8')

        return pipe_count, marked_image_base64

    def post(self, request, *args, **kwargs):
        file = request.FILES.get('image')

        if not file:
            return Response({"error": "No image file provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Save the file temporarily to the local filesystem
        temp_file_path = os.path.join(settings.MEDIA_ROOT, file.name)
        with open(temp_file_path, 'wb') as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)

        # Count the pipes and generate the marked image
        try:
            count, marked_image_base64 = self.count_and_mark_pipes(temp_file_path)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

        return Response({
            "pipe_count": count,
            "marked_image": marked_image_base64
        }, status=status.HTTP_200_OK)
