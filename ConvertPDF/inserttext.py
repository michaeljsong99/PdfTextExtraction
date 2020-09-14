from PyPDF2 import PdfFileWriter, PdfFileReader
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import fitz
from PIL import ImageFont

class PdfTextInserter:

    def __init__(self, file):
        self.pdf = file

    def insert_text(self, text_area_pagenum, dimensions, text_blocks):
        doc = fitz.open(self.pdf)
        width = dimensions[0]
        height = dimensions[1]

        # TODO: Fitz resizes the page differently. We need to convert the bounding box rectangles.
        # i.e. pytesseract is 1700 by 2200, fitz is 612 by 792, etc.
        zoom = 1
        try:
            page_size = doc[0].MediaBoxSize
            x = page_size.x
            y = page_size.y
            zoomx = max(width, x) / min(width, x)
            zoomy = max(height, y) / min(height, y)
            assert zoomx == zoomy
            zoom = zoomx
        except:
            print("Could not find the first page.")
        purple = (0.5, 0.5, 1.0)
        white = (1, 1, 1)
        save = False
        print("*****************************************************************************************")
        for block in text_blocks:
            area = block[0]
            page_num = block[1]
            scaled_area = ((area[0][0]/zoom, area[0][1]/zoom), (area[1][0]/zoom, area[1][1]/zoom))
            rect = fitz.Rect(*scaled_area)
            page = doc[page_num]
            # TODO: Later, extract the background color of the text box. For now, everything is just white.
            page.drawRect(rect, color = white, fill=white)
        for tup in text_area_pagenum:
            area = tup[0]
            scaled_area = ((area[0][0]/zoom, area[0][1]/zoom), (area[1][0]/zoom, area[1][1]/zoom))
            text = tup[1]
            page_num = tup[2]
            print(area, text)
            print(scaled_area, text)
            rect = fitz.Rect(*scaled_area)
            page = doc[page_num]
            page.insertTextbox(rect, text, fill=purple, align=0, fontsize=4)
        doc.save("result.pdf")
        print('New pdf saved at "result.pdf')

font = ImageFont.truetype('times.ttf', 12)
size = font.getsize('Hello Worly')
print(size)


