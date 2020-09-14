# Determines if a point is contained within a rectangle.
# A rectangle is defined by its (top_left, bottom_right) coordinates.
def is_point_in_rectangle(point, rect):
    point_x, point_y = point[0], point[1]
    rect_left, rect_right = rect[0][0], rect[1][0]
    rect_up, rect_down = rect[0][1], rect[1][1]
    return rect_right >= point_x >= rect_left and rect_up <= point_y <= rect_down


# If a point is not in the rectangle, find out how far away it is.
# The point is we try to find the closest rectangle, and then change the
# word's bounding box to fit inside the rectangle.
def distance_from_box(point, rect):
    point_x, point_y = point[0], point[1]
    rect_left, rect_right = rect[0][0], rect[1][0]
    rect_up, rect_down = rect[0][1], rect[1][1]
    x_dist = y_dist = 0
    if not rect_right >= point_x >= rect_left:
        x_dist = min(abs(rect_right - point_x), abs(rect_left - point_x))
    if not rect_up <= point_y <= rect_down:
        y_dist = min(abs(rect_up - point_y), abs(rect_down - point_y))
    return x_dist + y_dist


# This method adjusts the box of each word to ensure it is contained within a text line.
def adjust_word_bounding_boxes(word_bounding_boxes, text_lines):
    return word_bounding_boxes


# Assigns each word to a text block.
def assign_word_bounding_boxes_to_text_blocks(word_bounding_boxes, text_bounding_boxes):
    bounding_boxes_to_words = {}
    for text_block in text_bounding_boxes:
        bounding_boxes_to_words[text_block] = []
    # TODO: Later, optimize this process by using a 2d Range Tree for searching which
    #   rectangles contain which points.
    for bounding_box in word_bounding_boxes:
        top_left = bounding_box[0][0]
        found_box = False
        for text_block in text_bounding_boxes:
            if is_point_in_rectangle(top_left, text_block):
                bounding_boxes_to_words[text_block].append(bounding_box)
                found_box = True
                break
        if not found_box:
            # Sometimes, tesseract's bounding boxes can be a bit off.
            word = bounding_box[1]
            print(word)
            print('Could not find a text block for box ' + str(bounding_box))
            print('Mapping the box to the nearest bounding box.')
            closest_block = None
            min_distance = None
            for text_block in text_bounding_boxes:
                x_distance = 0
                y_distance = 0
                if not (text_block[0][0] <= top_left[0] <= text_block[1][0]):
                    x_distance = min(abs(text_block[0][0] - top_left[0]), abs(text_block[1][0] - top_left[0]))
                if not (text_block[0][1] <= top_left[1] <= text_block[1][1]):
                    y_distance = min(abs(text_block[0][1] - top_left[1]), abs(text_block[1][1] - top_left[1]))
                if min_distance is None:
                    min_distance = x_distance + y_distance
                    closest_block = text_block
                else:
                    if x_distance + y_distance < min_distance:
                        min_distance = x_distance + y_distance
                        closest_block = text_block
            # Now adjust the text box to fit in the closest block.
            print('The closest block found was:')
            print(closest_block)
            fit_bounding_box_inside_text_box(bounding_box, closest_block)
            bounding_boxes_to_words[closest_block].append(bounding_box)
            print('The new Bounding box is ' + str(bounding_box))

    return bounding_boxes_to_words


def fit_bounding_box_inside_text_box(bounding_box, text_block):
    bounding_box_coordinates = bounding_box[0]
    top_left = bounding_box_coordinates[0]
    bottom_right = bounding_box_coordinates[1]
    if top_left[0] < text_block[0][0]:
        x_adjustment = text_block[0][0] - top_left[0]
    else:
        x_adjustment = min(text_block[1][0] - bottom_right[0], 0)
    if top_left[1] < text_block[0][1]:
        y_adjustment = text_block[0][1] - top_left[1]
    else:
        y_adjustment = min(text_block[1][1] - bottom_right[1], 0)
    bounding_box[0] = ((top_left[0] + x_adjustment, top_left[1] + y_adjustment),
                       (bottom_right[0] + x_adjustment, bottom_right[1] + y_adjustment))
