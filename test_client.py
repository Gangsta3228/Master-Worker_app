import unittest
import io
from unittest.mock import patch, MagicMock

import client


class TestClient(unittest.TestCase):

    @patch('http.client.HTTPConnection.request', return_value=MagicMock())
    @patch(
        'http.client.HTTPConnection.getresponse',
        return_value=MagicMock(read=lambda: b'{"word1": 10, "word2": 5}')
    )
    def test_send_request(self, mock_getresponse, mock_request):
        client.send_request(
            'https://github.com/mailcourses/deep_python_spring_2023/blob/main/lesson-06/homework.md'
        )
        mock_request.assert_called_once_with('GET',
                                             'https://github.com/mailcourses/'
                                             'deep_python_spring_2023/blob/main/'
                                             'lesson-06/homework.md',
                                             headers={'Content-Type': 'text/plain; charset=utf-8'}
                                             )
        mock_getresponse.assert_called_once()


if __name__ == '__main__':
    unittest.main()
