import pytesseract
from pdf2image import convert_from_path, pdfinfo_from_path
import tempfile
import time
import multiprocessing as mp
import cv2
import numpy as np
import tesserocr as tr
from PIL import Image
from ConvertPDF.inserttext import PdfTextInserter
from ConvertPDF.utils import *

filename = "Resources/smalltest.pdf"
filename2 = "Resources/test.pdf"


class PdfParser:
    def __init__(self, file):
        self.pdf = file

    def get_text(self, page, page_number):
        print('Extracting text from page: ' + str(page_number))
        text = str(pytesseract.image_to_string(page))

        # In many PDFs, at line ending, if a word can't
        # be written fully, a 'hyphen' is added.
        # The rest of the word is written in the next line
        # Eg: This is a sample text this word here GeeksF-
        # orGeeks is half on first line, remaining on next.
        # To remove this, we replace every '-\n' to ''.
        text = text.replace('-\n', '')
        return text

    # Sometimes the bounding boxes can be off by a few pixels.
    # To make sure that words on the same row are vertically aligned, we do some manipulation.
    # We try to find the most frequent vertical pixels, then adjust the words that are not already
    # aligned on that level to adjust there.
    def infer_rows(self, data):
        heights = {}

        for box in data:
            height = box[0][0][1]
            if height not in heights:
                heights[height] = 1
            else:
                heights[height] += 1

        row_heights = self.infer_rows_for_group(heights)

        # Now we iterate through each of the bounding boxes and adjust the starting pixel heights.
        for box in data:
            height = box[0][0][1]
            new_height = row_heights[height]
            # Now we need to move the top-left and bottom-right corners to adjust for the new height.
            if new_height != height:
                diff = new_height - height
                box[0] = (box[0][0][0], new_height), (box[0][1][0], box[0][1][1] + diff)
        return data


    def infer_rows_for_group(self, heights_dict):
        heights_to_row_heights = {}
        line_buffer = 10 # this represents the number of pixels that we will use to determine rows.
        # i.e. if we have boxes with heights 89, 90, 91, 102 - we infer that the box on height 102
        # is the beginning of a new row.
        # For the other heights contained within the buffer, we choose the most frequent height as our top.
        heights = sorted(heights_dict.keys())
        heights_in_row = []
        most_frequent_height = None
        highest_frequency = 0
        length = len(heights)
        for index, height in enumerate(heights):
            heights_in_row.append(height)
            if heights_dict[height] >= highest_frequency:
                highest_frequency = heights_dict[height]
                most_frequent_height = height
            if (index == length - 1) or heights[index+1] - height >= line_buffer:
                # the next height is likely on a new row (or we have reached the end).
                for h in heights_in_row:
                    heights_to_row_heights[h] = most_frequent_height
                highest_frequency = 0
                most_frequent_height = None
                heights_in_row = []
        return heights_to_row_heights


    # Get all the text blocks on a page.
    # This is necessary for two reasons:
    # 1. We can find the background color and text color for the entire text block at once.
    # 2. Sometimes, pytesseract bounding boxes can be a bit off.
    #   Pytesseract does a good job with reading words, however, which is why we use it.
    #   On the other hand, tesserocr does a good job with finding bounding boxes, but
    #   a mediocre job at reading words.
    #   We will map each word bounding box to a text_line. We can then adjust the heights
    #       and endpoints of our words' bounding boxes such that they fit inside the textline.
    def get_text_blocks(self, page, text_line = False):
        level = tr.RIL.BLOCK
        if text_line:
            level = tr.RIL.TEXTLINE
        api = tr.PyTessBaseAPI()
        text_block_bounding_boxes = []
        try:
            api.SetImage(page)
            text_blocks = api.GetComponentImages(level, True)
            text = api.GetUTF8Text()
            print(text)
            for (im,box,_,_) in text_blocks:
                x,y,w,h = int(box['x']), int(box['y']), int(box['w']), int(box['h'])
                print(x, y, w, h)
                # Get the top left and bottom right corners.
                text_block_bounding_boxes.append(((x,y), (x+w,y+h)))
                # TODO: Also get the background color and text color of each text block.
        finally:
            api.End()
        return text_block_bounding_boxes

    # This method gets the top left and bottom right corner of each word's bounding box
    # on a given page. It also records the actual word itself.
    def get_word_bounding_boxes(self, page):
        results = []
        boxes = pytesseract.image_to_data(page)
        api = tr.PyTessBaseAPI()
        api.SetImage(page)
        boxes2 = api.GetComponentImages(tr.RIL.WORD, True)
        print(len(boxes2))
        for i, (im, box, _, _) in enumerate(boxes2):
            # im is a PIL image object
            # box is a dict with x, y, w and h keys
            api.SetRectangle(box['x'], box['y'], box['w'], box['h'])
        words = 0
        for x, b in enumerate(boxes.splitlines()):
            if x != 0:
                b = b.split()
                if len(b) == 12:
                    words += 1
                    x, y, w, h, word = int(b[6]), int(b[7]), int(b[8]), int(b[9]), b[11]
                    top_left_corner = (x, y)
                    bottom_right_corner = (w + x, h + y)
                    # page = np.array(page)
                    results.append([(top_left_corner, bottom_right_corner), word])
        return results

    # This method is the wrapper, which gets all the bounding boxes in the pdf, and inserts
    # real text in place of the 'image' of text.
    def pdf_to_bounding_boxes(self):
        results = []
        width = None
        height = None
        with tempfile.TemporaryDirectory() as path:
            images_from_path = convert_from_path(self.pdf, output_folder=path, first_page=0, last_page=2)
            page_num = 0
            all_text_blocks = []
            for image in images_from_path:
                if width is None:
                    width = image.width
                    height = image.height
                text_blocks = self.get_text_blocks(image)
                text_lines = self.get_text_blocks(image, text_line=True)
                page_bounding_boxes = self.get_word_bounding_boxes(image)
                # Clean up the bounding boxes by matching it to a text line.
                page_bounding_boxes = adjust_word_bounding_boxes(page_bounding_boxes, text_lines)
                # For each of the words, assign it to a text block.
                # Also if a word is not in a text block, adjust it so that it fits inside.
                text_block_assignments = \
                    assign_word_bounding_boxes_to_text_blocks(page_bounding_boxes, text_blocks)
                for block in text_blocks:
                    # Align the words vertically.
                    adjusted_height_boxes = self.infer_rows(data=text_block_assignments[block])
                    for box in adjusted_height_boxes:
                        results.append((box[0], box[1], page_num))
                    all_text_blocks.append((block, page_num))
                page_num += 1
        text_inserter = PdfTextInserter(self.pdf)
        text_inserter.insert_text(results, (width,height), all_text_blocks)

    def ingest_pdf(self):
        # First, convert PDF to images.
        with tempfile.TemporaryDirectory() as path:
            page_count = pdfinfo_from_path(self.pdf)["Pages"]
            print(page_count)
            print('Ingesting ' + filename)
            start = time.time()
            pages = []
            page = 1
            all_texts = []
            # Convert the pdf in batches of 10 pages to avoid large memory usage.
            for page_num in range(1, page_count, 10):
                # Convert the pdf pages to jpeg images.
                block = convert_from_path(filename, dpi=200, first_page=page_num,
                                          last_page=min(page_num + 10 - 1, page_count),
                                          output_folder=path, thread_count=4, fmt='jpeg')
                print('Converting Pages ' + str(page_num) + "-" + str(page_num + 9))
                batch_page_numbers = []
                batch_pages = []
                for file in block:
                    print('Ingesting page ' + str(page) + ' of ' + str(page_count))
                    batch_pages.append(file)
                    batch_page_numbers.append(page)
                    page += 1
                # Extract the text from the jpeg images.
                with mp.Pool(mp.cpu_count()) as pool:
                    texts = pool.starmap(self.get_text, zip(batch_pages, batch_page_numbers))
                    all_texts.extend(texts)

            end = time.time()
            print('Finished ingesting pdf in ' + str(end - start) + ' seconds.')

            # Open the file in append mode so that
            # All contents of all images are added to the same file
            # Creating a text file to write the output
            outfile = "out_text2.txt"
            f = open(outfile, "a")
            for text in all_texts:
                f.write(text)
            # Close the file after writing all the text.
            f.close()


p = PdfParser(filename2)
p.pdf_to_bounding_boxes()
