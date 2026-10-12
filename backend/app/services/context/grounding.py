"""Exact public knowledge and current facts. Model selects; server renders.

Catalog locations are usual locations, never an observation of Godot positions.
No other NPC's private inventory, emotions or memories enter this directory.
"""
from pathlib import Path
import re

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select

from app.models import Conversation, NPC


class Person(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str
    name: str
    role: str
    usual_place: str
    work: str
    source: str


class Place(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str
    name: str


class Route(BaseModel):
    model_config = ConfigDict(extra='forbid')
    origin: str
    destination: str
    directions: str = Field(min_length=1, max_length=140)
    source: str = Field(min_length=1)


class Catalog(BaseModel):
    model_config = ConfigDict(extra='forbid')
    people: list[Person] = Field(max_length=8)
    places: list[Place] = Field(max_length=12)
    routes: list[Route] = Field(max_length=12)
    source: str

    @model_validator(mode='after')
    def references(self):
        ids = [p.id for p in self.people + self.places]
        places = {p.id for p in self.places}
        if len(set(ids)) != len(ids) or any(p.usual_place not in places for p in self.people):
            raise ValueError('Catalog requires unique IDs and known usual places')
        if any(r.origin not in places or r.destination not in places for r in self.routes):
            raise ValueError('Routes require known endpoints and map evidence in source')
        return self


CATALOG = Catalog.model_validate_json(Path(__file__).with_name('village.json').read_text())


def resolve_location_reference(question, focus, facts):
    """Bind locative queries to catalog entities, not model-invented subjects.

    None means no binding; False means an explicit unsupported target. This is
    a small query adapter over catalog data, not a table of question/reply pairs.
    Model selection continues to handle other factual topics and social prose.
    """
    text = question.lower().strip(' ?!.')
    navigation = bool(re.search(r'\b(?:directions|way)\b|\bhow\b.*\b(?:get|go|reach|travel|walk)\b', text))
    if not navigation and not re.search(r'\bwhere\b', text):
        return None
    target = re.search(r"\b(?:where (?:is|are)|where's|find|locate|reach|visit|(?:get|go|travel|walk) to)\s+(?:the\s+)?(.+)", text)
    target_text = target.group(1) if target else text
    labels = [(p.id, p.name.lower()) for p in CATALOG.people + CATALOG.places]
    subject = next((identity for identity, label in labels if re.search(
        (r'^(?:wood )?' if target else r'\b') + re.escape(label) + r'\b', target_text)), None)
    if subject is None:
        if re.fullmatch(r'(?:he|she|him|her|them|it|there|here)(?: (?:now|please))?', target_text) or (
                not target and re.search(r'\b(?:he|she|him|her|them|it|there)\b', text)):
            subject = focus.get('subject')
        elif target:
            # Material-source questions remain model-selected from quest facts.
            if re.search(r'\b(?:wood|string|bow)\b', target_text):
                return None
            return False
    if not subject:
        return None
    identity = subject + ('.route' if navigation else '.location')
    return identity if any(f['id'] == identity for f in facts) else False


def build_facts(db, npc, player, quest, now):
    facts = []

    def add(identity, subject, facet, text, source, status='current'):
        facts.append(dict(id=identity, subject=subject, facet=facet, text=text,
                          source=source, status=status, as_of=now if status == 'current' else None))

    places = {p.id: p.name for p in CATALOG.places}
    routes = {r.destination: r for r in CATALOG.routes}

    def route_fact(identity, subject, destination):
        route = routes.get(destination)
        text = (f"From the {places[route.origin]} to the {places[destination]}: {route.directions}"
                if route else f"I don't have verified directions to the {places[destination]}.")
        add(identity, subject, 'route', text, route.source if route else CATALOG.source,
            'public' if route else 'unknown')

    for person in CATALOG.people:
        add(person.id + '.location', person.id, 'location',
            f"{person.name} is usually at the {places[person.usual_place]}. I don't have an observed current position.",
            person.source, 'usual')
        add(person.id + '.work', person.id, 'work', person.work, person.source, 'public')
        route_fact(person.id + '.route', person.id, person.usual_place)
    for place in CATALOG.places:
        route_fact(place.id + '.route', place.id, place.id)
    craftsman = db.scalar(select(NPC).where(NPC.role == 'craftsman'))
    consumed = quest['phase'] in {'crafting', 'completed'}
    missing = [item for item in ('wood', 'string') if not craftsman or item not in (craftsman.inventory or [])]
    progress = ('Both materials have been consumed for this bow.' if consumed else
                'Still needed: ' + (', '.join(missing) or 'nothing') + '.')
    add('quest.bow.requirements', 'quest.bow', 'requirements',
        'The bow requires wood and string delivered to the Craftsman. ' + progress +
        ' Ask the Gatherer for wood; string is a ground pickup near the well.',
        'services/quests/bow.py; Craftsman quest material stock', 'current')
    add('quest.bow.phase', 'quest.bow', 'phase',
        f"Get a bow: {quest['objective']}", 'BowQuest snapshot')
    # Delivery history is verified execution, not a remembered player claim. It
    # survives consumption. Retained quest stock also survives clearing chat.
    delivered = []
    if craftsman:
        delivered = list(db.scalars(select(Conversation.validated_output['item'].as_string()).where(
            Conversation.npc_id == craftsman.id,
            Conversation.validated_output['action'].as_string() == 'receive_item',
            Conversation.validated_output['item'].as_string().in_(['wood', 'string']),
        ).distinct()))
        delivered.extend(item for item in ('wood', 'string') if item in (craftsman.inventory or []))
    if consumed:
        delivered = ['wood', 'string']  # service only advances after consuming both
    delivered_text = ', '.join(sorted(set(delivered))) or 'no materials recorded'
    add('quest.bow.delivered', 'quest.bow', 'delivered',
        f"Verified bow materials delivered to the Craftsman: {delivered_text}.", 'Conversation executed transfers; BowQuest')
    add('player.inventory', 'player', 'inventory',
        'Your satchel currently contains: ' + (', '.join(player.inventory or []) or 'nothing') + '.', 'Player.inventory')
    add('self.inventory', 'person.' + npc.role, 'inventory',
        'I currently carry: ' + (', '.join(npc.inventory or []) or 'nothing') + '.', 'NPC.inventory (speaker only)')
    return facts


def render_answer(output, facts):
    """IDs never authorize free prose. Replace the entire factual answer."""
    if output.answer_kind == 'clarify':
        return "I don't have verified information about that. Which known villager, place or bow requirement do you mean?"
    by_id = {fact['id']: fact for fact in facts}
    if not 1 <= len(output.fact_ids) <= 2 or len(set(output.fact_ids)) != len(output.fact_ids):
        raise ValueError('Answer requires one or two distinct facts')
    if any(identity not in by_id for identity in output.fact_ids):
        raise ValueError('Unknown or private fact reference')
    return ' '.join(by_id[identity]['text'] for identity in output.fact_ids)
