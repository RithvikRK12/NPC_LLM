# Reviewer 1 results: current-turn and grounding replay

The submitted form is `human-calibration-reviewer_1-completed.json`. Its guidance and policy provenance match this replay, and all 24 candidate texts match the replay output. The same reviewer scored the same 24 sample references and dimensions in T06, enabling a within-reviewer comparison. This is one reviewer’s paired assessment, not independent agreement or a release-quality estimate.

| Dimension | T06 | Current replay | Change |
| --- | ---: | ---: | ---: |
| Directness | 4.00 | 3.25 | -0.75 |
| Coverage | 3.50 | 2.25 | -1.25 |
| Continuity | 2.75 | 4.00 | +1.25 |
| Character consistency | 4.50 | 2.75 | -1.75 |
| Grounding | 4.25 | 3.75 | -0.50 |
| Naturalness | 5.00 | 3.75 | -1.25 |
| **Overall mean (24 scores)** | **4.00** | **3.29** | **-0.71** |

Continuity improved most: the reviewer accepted the Craftsman clock-tower recall and later change-of-view answer. However, the Gatherer incorrectly answered a recall question with “quiet attentive company” instead of the prior fruit detail. Coverage is the lowest dimension. On practical rope/wood turns, answers acknowledge worry but fail to explain the requested safe/useful guidance; a follow-up about whether to wait received a repeated answer or generic waiting advice. The reviewer specifically questioned an offer to demonstrate rope use, which may promise an affordance the game does not implement.

Character consistency fell to 2.75. The Craftsman response says his father passed away, while the authored profile explicitly does not establish that the father is dead. The Gatherer’s answer to the day-going-well question repeated an earlier answer instead of addressing the new question. Grounding concerns include an unsupported weather forecast and claims about changing forest layout. Naturalness comments also note irrelevant anecdotes and replies that restate context without answering the question.

## Suggested next revision

1. Require the first sentence to answer the practical or personal question actually asked. Keep empathy brief, and omit unrelated anecdotes and echoed question text.
2. Permit offers such as “I can show you” or “let’s inspect it” only when supplied capabilities support that action. Keep conversational guidance separate from playable actions.
3. Keep backstory bounded by authored canon: a historical mention of the Craftsman’s father does not authorize adding his death or whereabouts. Likewise, do not invent current weather or forest events without supplied evidence.
4. Retain the improved continuity behavior for actual recall and changed-opinion questions, while testing that recall references the correct prior detail.

This evidence argues against accepting the current prompt change as an overall quality improvement. Keep the 600-character ceiling; the separate replay still had four responses at the ceiling without sentence-final punctuation. Obtain Reviewer 2’s scores for this exact replay before making a broader quality claim.
