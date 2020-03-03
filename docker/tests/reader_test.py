import unittest
import json

import reader


class TestReader(unittest.TestCase):

    def test_read_json_request(self):
        data = {"tips": ["tip1", "tip2"],
                "usageInfo": {"action_id_1": {"usageCount": 1,
                                              "lastUsedTimestamp": 10},
                              "action_id_2": {"usageCount": 2,
                                              "lastUsedTimestamp": 12}},
                "ideName": "IU",
                "bucket": "2"}
        bucket, user_events, tips = reader.read_request_json(data)
        self.assertEqual(2, bucket)
        self.assertEqual({("actions.action.invoked", "action_id_1"): (10, 1),
                          ("actions.action.invoked", "action_id_2"): (12, 2)}, user_events)
        self.assertEqual(["tip1", "tip2"], tips)

    def test_read_tip_to_event(self):
        file_name = __file__[:-14] + "test_html_to_event.csv"
        tip_to_action_ids_dict, action_id_to_tips_dict = reader.read_tip_to_event(file_name)

        self.assertEqual({"tip1.html": ["action_id_1"], "tip2.html": ["action_id_1", "action_id_3"]}, tip_to_action_ids_dict)
        self.assertEqual({"action_id_1": ["tip1.html", "tip2.html"], "action_id_3": ["tip2.html"]}, action_id_to_tips_dict)


if __name__ == '__main__':
    unittest.main()