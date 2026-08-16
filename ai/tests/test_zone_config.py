from pipeline.utils.zone_config import filter_detections_by_zones


FRAME_WIDTH = 100
FRAME_HEIGHT = 100

TOP_LEFT_QUADRANT = [
    [0.0, 0.0], [0.5, 0.0], [0.5, 0.5], [0.0, 0.5]
]


def detection(x, y, width=10, height=10):
    return([x, y, width, height], 0.90, "HUMAN_PRESENCE")


def test_no_zones_keeps_every_detection():

    detections = [detection(10, 10), detection(70, 70)]

    result = filter_detections_by_zones(detections, [], FRAME_WIDTH, FRAME_HEIGHT)

    assert result == detections


def test_keeps_detection_with_center_inside_a_zone():
    inside = detection(10, 10)

    result = filter_detections_by_zones([inside], [TOP_LEFT_QUADRANT], FRAME_WIDTH, FRAME_HEIGHT)

    assert result == [inside]


def test_discards_detection_with_center_outside_all_zones():
    outside = detection(70, 70)

    result = filter_detections_by_zones([outside], [TOP_LEFT_QUADRANT], FRAME_WIDTH, FRAME_HEIGHT)

    assert result == []


def test_keeps_detection_inside_any_of_multiple_zones():

    bottom_right_quadrant = [
        [0.5, 0.5],
        [1.0, 0.5],
        [1.0, 1.0],
        [0.5, 1.0],
    ]

    inside_second_zone = detection(70, 70)

    result = filter_detections_by_zones([inside_second_zone], [TOP_LEFT_QUADRANT, bottom_right_quadrant], FRAME_WIDTH, FRAME_HEIGHT)



    assert result == [inside_second_zone]