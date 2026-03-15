import unittest

from qzone_text_exporter import net


class TestJSONP(unittest.TestCase):
    def test_parse_plain_json(self) -> None:
        payload = '{"code":0,"data":{"x":1}}'
        self.assertEqual(net.parse_jsonp(payload)["data"]["x"], 1)

    def test_parse_jsonp_callback(self) -> None:
        payload = "_Callback({\"code\":0,\"data\":{\"x\":1}});"
        self.assertEqual(net.parse_jsonp(payload)["data"]["x"], 1)

    def test_parse_jsonp_with_whitespace(self) -> None:
        payload = "  _Callback(  {\"code\":0,\"data\":{\"x\":2}}  )  ;\\n"
        self.assertEqual(net.parse_jsonp(payload)["data"]["x"], 2)

    def test_parse_invalid_raises(self) -> None:
        with self.assertRaises(ValueError):
            net.parse_jsonp("not jsonp")


if __name__ == "__main__":
    unittest.main()

