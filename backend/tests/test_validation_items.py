import unittest

from app.services.validation.items import transfer_answer


class TransferAnswerTests(unittest.TestCase):
    def test_pending_item_accepts_pronoun_reason_with_goal_item(self):
        output = transfer_answer(
            "I need it to make a bow",
            npc_inventory=["wood"],
            player_inventory=["water", "food"],
            pending_item="wood",
        )

        self.assertIsNotNone(output)
        self.assertEqual(output.intent, "transfer")
        self.assertEqual(output.action, "give_item")
        self.assertEqual(output.item, "wood")


if __name__ == "__main__":
    unittest.main()
