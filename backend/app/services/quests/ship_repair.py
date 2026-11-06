"""Inspection establishes the quest. Deliveries and repair are deliberately absent."""
from app.models.ship_repair_quest import ShipRepairQuest
PHASES = ('not_started', 'gathering_materials', 'ready_for_repair', 'repairing', 'completed')
RECIPE = [('ship_plank', 'Sound timber plank', 12), ('rope', 'Coil of rope', 3),
          ('sailcloth_bundle', 'Bundle of sailcloth', 2), ('pitch_pot', 'Pot of pitch', 2)]

PLURALS = {'ship_plank':'sound timber planks','rope':'coils of rope','sailcloth_bundle':'bundles of sailcloth','pitch_pot':'pots of pitch'}

def material_list(materials, remaining=False):
    pieces=[f"{m['remaining' if remaining else 'required']} {PLURALS[m['item']]}" for m in materials]
    return ', '.join(pieces[:-1])+', and '+pieces[-1]

def ship_snapshot(db, player):
    quest = db.get(ShipRepairQuest, player.id)
    if quest and quest.game_scope != player.game_scope:
        quest = None
    counts = quest.contributions if quest else {}
    materials = [dict(item=item, name=name, required=quantity, contributed=counts.get(item, 0),
                      remaining=max(0, quantity-counts.get(item, 0))) for item, name, quantity in RECIPE]
    return dict(id='ship_repair', title='A Way Home', category='Main story', recipe_version=1,
                phase=quest.phase if quest else 'not_started', materials=materials,
                requirement_text='Bring me ' + material_list(materials) + '. That should give us a start.',
                objective='Gather the materials and bring them to the Craftsman’s workshop.',
                availability_note='Material gathering and ship repair will be added in a later update.')
