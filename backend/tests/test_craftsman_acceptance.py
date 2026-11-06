import unittest
from app.services.craftsman_intent import resolve_craftsman_intent


class CraftsmanAcceptanceTests(unittest.TestCase):
    def intent(self, message, pending=True):
        return resolve_craftsman_intent(message, (), {
            'offer_pending': pending, 'wreck_reported': pending,
            'outing_active': False, 'inspection_complete': False,
        })

    def test_natural_affirmative_replies_accept_the_pending_offer(self):
        for message in ("Sure! That would be helpful.", "Yes, thank you!",
                        "That would be great, thanks.", "I'd appreciate that.",
                        "Absolutely, please do.", "Sounds good to me.",
                        "Okay, let's go.", "yes please", "follow me"):
            with self.subTest(message=message):
                self.assertEqual(self.intent(message), {'command': 'begin_ship_inspection'})

    def test_affirmation_requires_a_pending_offer(self):
        for message in ("Sure! That would be helpful.", "Yes, thank you!", "Sounds good to me."):
            with self.subTest(message=message):
                self.assertEqual(self.intent(message, pending=False), {})

    def test_negated_quoted_hypothetical_and_unrelated_replies_do_not_accept(self):
        for message in ("Sure, but not now.", "That would not be helpful.",
                        "No thanks.", "Sure, I don't want to go.",
                        'He said "Sure! That would be helpful."',
                        "Imagine I said yes.", "Sure, can you make me a bow?",
                        "Sure, the weather is nice.", "Thanks for the offer."):
            with self.subTest(message=message):
                self.assertNotEqual(self.intent(message).get('command'), 'begin_ship_inspection')
