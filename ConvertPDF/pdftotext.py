import pytesseract
from pdf2image import convert_from_path, pdfinfo_from_path
import tempfile
import time
import multiprocessing as mp
import cv2
import numpy as np
from ConvertPDF.inserttext import PdfTextInserter

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
            page_num = box[2]
            if page_num not in heights:
                heights[page_num] = {}
            if height not in heights[page_num]:
                heights[page_num][height] = 1
            else:
                heights[page_num][height] += 1
            print(page_num, height)

        row_heights = {}
        for page_num in heights.keys():
            row_heights[page_num] = self.infer_rows_for_single_page(heights[page_num])

        # Now we iterate through each of the bounding boxes and adjust the starting pixel heights.
        for box in data:
            height = box[0][0][1]
            page_num = box[2]
            new_height = row_heights[page_num][height]
            # Now we need to move the top-left and bottom-right corners to adjust for the new height.
            if new_height != height:
                diff = new_height - height
                box[0] = (box[0][0][0], new_height), (box[0][1][0], box[0][1][1] + diff)
        return data


    def infer_rows_for_single_page(self, heights_dict):
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



    def get_word_bounding_boxes(self, page, page_num):
        results = []
        boxes = pytesseract.image_to_data(page)
        for x, b in enumerate(boxes.splitlines()):
            if x != 0:
                b = b.split()
                if len(b) == 12:
                    x, y, w, h, word = int(b[6]), int(b[7]), int(b[8]), int(b[9]), b[11]
                    top_left_corner = (x, y)
                    bottom_right_corner = (w + x, h + y)
                    page = np.array(page)
                    # print(word)
                    results.append([(top_left_corner, bottom_right_corner), word, page_num])
        return results


    def pdf_to_bounding_boxes(self):
        results = []
        width = None
        height = None
        with tempfile.TemporaryDirectory() as path:
            images_from_path = convert_from_path(self.pdf, output_folder=path, first_page=0, last_page=2)
            page_num = 0
            for image in images_from_path:
                if width is None:
                    width = image.width
                    height = image.height
                page_bounding_boxes = self.get_word_bounding_boxes(image, page_num)
                results.extend(page_bounding_boxes)
                page_num += 1
        results = self.infer_rows(results)
        text_inserter = PdfTextInserter(self.pdf)
        text_inserter.insert_text(results, (width,height))

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
