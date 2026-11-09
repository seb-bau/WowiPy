import inspect
import logging
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from wowipy.exceptions import WowiPyException
from wowipy.models import Result
from wowipy.rest_adapter import RestAdapter
from wowipy.wowipy import WowiPy


class TicketConversationTests(unittest.TestCase):
    def setUp(self):
        self.client = WowiPy.__new__(WowiPy)
        self.client._rest_adapter = Mock(spec=RestAdapter)
        self.result = Result(200, 'OK', {'Id': 42, 'IdNum': '00123', 'CommentId': 91})
        self.client._rest_adapter.post.return_value = self.result

    def test_only_ticket_id_is_required(self):
        signature = inspect.signature(WowiPy.create_ticket_conversation)
        required = [
            name for name, parameter in signature.parameters.items()
            if parameter.default is inspect.Parameter.empty
        ]
        self.assertEqual(required, ['self', 'ticket_id'])
        result = self.client.create_ticket_conversation(ticket_id=42)
        self.client._rest_adapter.post.assert_called_once_with(
            endpoint='CommunicationEdit/Ticket/AddConversation',
            data={'TicketId': 42},
        )
        self.assertIs(result, self.result)

    def test_all_conversation_fields_are_sent(self):
        created_at = datetime(2026, 11, 9, 14, 30, 15, 123456, tzinfo=timezone(timedelta(hours=1)))
        self.client.create_ticket_conversation(
            ticket_id=42,
            content='Rückmeldung zur Beauftragung',
            ticket_source_id=7,
            person_id=11,
            user_id=13,
            created_at=created_at,
            location='Lünen',
        )
        self.client._rest_adapter.post.assert_called_once_with(
            endpoint='CommunicationEdit/Ticket/AddConversation',
            data={
                'TicketId': 42,
                'TicketSourceId': 7,
                'PersonId': 11,
                'UserId': 13,
                'CreatedAt': '2026-11-09T14:30:15.123456+01:00',
                'Location': 'Lünen',
                'Content': 'Rückmeldung zur Beauftragung',
            },
        )

    def test_explicit_none_values_are_omitted(self):
        self.client.create_ticket_conversation(
            ticket_id=42,
            content=None,
            ticket_source_id=None,
            person_id=None,
            user_id=None,
            created_at=None,
            location=None,
        )
        self.assertEqual(self.client._rest_adapter.post.call_args.kwargs['data'], {'TicketId': 42})

    def test_empty_strings_and_zero_values_are_preserved(self):
        self.client.create_ticket_conversation(
            ticket_id=42, content='', ticket_source_id=0, person_id=0, user_id=0, location='',
        )
        self.assertEqual(self.client._rest_adapter.post.call_args.kwargs['data'], {
            'TicketId': 42, 'Content': '', 'TicketSourceId': 0, 'PersonId': 0, 'UserId': 0, 'Location': '',
        })

    def test_legacy_signature_and_delegation_are_unchanged(self):
        signature = inspect.signature(WowiPy.create_ticket_comment)
        self.assertEqual(list(signature.parameters), ['self', 'ticket_id', 'content'])
        self.client.create_ticket_conversation = Mock(return_value=self.result)
        for arguments, keywords in [((42, 'Antwort'), {}), ((), {'ticket_id': 42, 'content': 'Antwort'})]:
            with self.subTest(arguments=arguments, keywords=keywords):
                result = self.client.create_ticket_comment(*arguments, **keywords)
                self.client.create_ticket_conversation.assert_called_with(ticket_id=42, content='Antwort')
                self.assertIs(result, self.result)
        self.client._rest_adapter.post.assert_not_called()

    def test_api_errors_propagate_to_legacy_callers(self):
        self.client._rest_adapter.post.side_effect = WowiPyException('400: Bad Request')
        with self.assertRaisesRegex(WowiPyException, '400: Bad Request'):
            self.client.create_ticket_comment(ticket_id=42, content='Antwort')
        self.assertEqual(self.client._rest_adapter.post.call_count, 1)

    def test_legacy_calls_preserve_both_application_response_contracts(self):
        adapter = RestAdapter.__new__(RestAdapter)
        adapter.api_key = 'test-api-key'
        adapter.url = 'https://example.invalid/openwowi/v1.2/'
        adapter.user_agent = 'test-client'
        adapter.access_token = 'test-access-token'
        adapter._logger = logging.getLogger(__name__)
        self.client._rest_adapter = adapter
        original_post = adapter.post
        adapter.post = Mock(wraps=original_post)
        for status_code in (200, 201):
            for response_data in (
                {'Id': 42, 'IdNum': '00123', 'CommentId': 91},
                [{'Id': 42, 'IdNum': '00123', 'CommentId': 91}],
            ):
                with self.subTest(status_code=status_code, response_data=response_data):
                    response = Mock(status_code=status_code, reason='OK', text='test-response')
                    response.json.return_value = response_data
                    with patch('wowipy.rest_adapter.requests.request', return_value=response) as request:
                        result = self.client.create_ticket_comment(ticket_id=42, content='Antwort')
                    request.assert_called_once_with(
                        method='POST',
                        url='https://example.invalid/openwowi/v1.2/CommunicationEdit/Ticket/AddConversation',
                        headers={
                            'User-Agent': 'test-client', 'Accept': 'text/plain',
                            'Authorization': 'Bearer test-access-token',
                        },
                        params={'apiKey': 'test-api-key'},
                        json={'TicketId': 42, 'Content': 'Antwort'},
                    )
                    self.assertIn(result.status_code, (200, 201))
                    self.assertEqual(result.message, 'OK')
                    self.assertIs(result.data, response_data)
                    comment_data = result.data[0] if isinstance(result.data, list) else result.data
                    self.assertEqual(comment_data['CommentId'], 91)
        self.assertEqual(adapter.post.call_count, 4)


if __name__ == '__main__':
    unittest.main()
