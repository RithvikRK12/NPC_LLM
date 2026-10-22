"""Reproduce the original typed rejection without provider, DB or player save."""
import json
from pathlib import Path
from pydantic import ValidationError
from app.services.conversation import contracts as c
from app.services.llm.structured import _json_arrays_to_tuples
OUT=Path(__file__).resolve().parent
sample=json.loads((OUT.parent/'wreck-reaction/live-samples.json').read_text())[0]
raw=json.loads(sample['provider_calls'][0]['output'])
try:
    c.CandidateReply.model_validate(_json_arrays_to_tuples(raw),strict=True)
    raise AssertionError('original invalid metadata was unexpectedly accepted')
except ValidationError as error:
    fields=[{'path':'.'.join(map(str,item['loc'])),'type':item['type']} for item in error.errors()]
unknown=sorted({value for segment in raw['segments'] for value in segment.get('addressed_concern_ids',())})
report={'valid_json':True,'typed_rejections':fields,'admitted_concern_ids':[],
        'invented_concern_ids':unknown,
        'conclusion':'Server-owned metadata must not be generated; speech alone must not invent structural references.'}
(OUT/'original-rejection.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
