import tempfile
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
import os
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from docx import Document

# # Specify the path to Tesseract executable
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Adjust this path as needed

# # Specify the path to Poppler binaries
# poppler_path = r'C:\Program Files\poppler-24.02.0\Library\bin'  # Adjust this path as needed


pytesseract.pytesseract.tesseract_cmd = os.environ.get('TESSERACT_PATH', 'tesseract')
poppler_path = os.path.join(settings.BASE_DIR, 'poppler-24.02.0', 'Library', 'bin')


def home(request):
    return render(request,"home.html")

def preprocess_image(image):
    """ Preprocess the image for better OCR accuracy """
    image = image.convert('L')  # Convert to grayscale
    image = image.filter(ImageFilter.SHARPEN)  # Sharpen the image
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)  # Enhance the contrast
    return image

def extract_text_from_image(image):
    """ Extract text from a single image using Tesseract OCR """
    processed_image = preprocess_image(image)
    return pytesseract.image_to_string(processed_image)

def pdf_to_images(pdf_path):
    """ Convert PDF pages to images using pdf2image """
    return convert_from_path(pdf_path, poppler_path=poppler_path)

def extract_text_from_pdf(pdf_path):
    """ Extract text from a PDF, using OCR if necessary """
    images = pdf_to_images(pdf_path)
    full_text = ""

    for image in images:
        ocr_text = extract_text_from_image(image)
        full_text += ocr_text + "\n"

    return full_text

def extract_text_from_docx(docx_path):
    """ Extract text from a DOCX file """
    doc = Document(docx_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

def extract(request):
    if request.method == 'POST':
        if 'file' not in request.FILES:
            return JsonResponse({"error": "No file part"}, status=400)

        file = request.FILES['file']
        if not file.name:
            return JsonResponse({"error": "No selected file"}, status=400)

        file_extension = request.POST.get('extension')
        if file_extension not in ['image', 'pdf', 'doc', 'ppt']:
            return JsonResponse({"error": "Invalid file extension"}, status=400)

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name

        try:
            if file_extension == 'pdf':
                text = extract_text_from_pdf(temp_file_path)
            elif file_extension == 'image':
                image = Image.open(temp_file_path)
                text = extract_text_from_image(image)
            elif file_extension == 'doc':
                text = extract_text_from_docx(temp_file_path)
            else:
                # Handle other file types (e.g., PPT)
                text = "File type not supported"

            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

            return JsonResponse({"text": text}, status=200)
        except Exception as e:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)
