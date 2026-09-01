from evaluation.metrics import Detection, iou_xyxy, score_class


def det(box, confidence=1.0):
    return Detection(class_id=0, bbox_xyxy=box, confidence=confidence)


def test_iou_for_identical_boxes_is_one():
    assert iou_xyxy((0, 0, 10, 10), (0, 0, 10, 10)) == 1.0


def test_iou_for_disjoint_boxes_is_zero():
    assert iou_xyxy((0, 0, 10, 10), (20, 20, 30, 30)) == 0.0


def test_one_matching_prediction_is_one_true_positive():
    result = score_class([det((0, 0, 10, 10))], [det((0, 0, 10, 10))])
    assert (result["tp"], result["fp"], result["fn"]) == (1, 0, 0)
    assert result["precision"] == result["recall"] == result["f1"] == 1.0


def test_unmatched_prediction_is_false_positive():
    result = score_class([det((20, 20, 30, 30))], [det((0, 0, 10, 10))])
    assert (result["tp"], result["fp"], result["fn"]) == (0, 1, 1)


def test_unmatched_ground_truth_is_false_negative():
    result = score_class([], [det((0, 0, 10, 10))])
    assert (result["tp"], result["fp"], result["fn"]) == (0, 0, 1)


def test_two_predictions_cannot_claim_one_ground_truth():
    result = score_class(
        [det((0, 0, 10, 10), 0.9), det((0, 0, 10, 10), 0.8)],
        [det((0, 0, 10, 10))],
    )
    assert (result["tp"], result["fp"], result["fn"]) == (1, 1, 0)