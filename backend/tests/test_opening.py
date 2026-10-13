import json
import unittest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.database.base import Base
from app.models import Player
from app.database.seed import seed_world, reset_world
from app.api.routes.world import world

class OpeningTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://')
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        seed_world(self.db)
    def tearDown(self):
        self.db.close()
        self.engine.dispose()
    def test_new_run_pending_and_checkpoint_repeat_does_not_teleport(self):
        from app.services.opening import complete_opening, HANDOFF
        p=self.db.get(Player,1)
        self.assertEqual(p.opening_state,'pending')
        from app.services.island import MAP_VERSION
        self.assertEqual(p.map_version,MAP_VERSION)
        scope=p.game_scope
        complete_opening(self.db,scope,1)
        self.assertEqual(p.position,HANDOFF)
        p.position={'x':10.125,'y':4400.25}
        self.db.commit()
        complete_opening(self.db,scope,1)
        self.assertEqual(p.position,{'x':10.125,'y':4400.25})
        self.assertEqual(world(self.db)['opening_state'],'complete')
    def test_stale_run_and_version_rejected(self):
        from app.services.opening import complete_opening
        scope=self.db.get(Player,1).game_scope
        reset_world(self.db)
        self.db.commit()
        for old,version in [(scope,1),(self.db.get(Player,1).game_scope,2)]:
            with self.assertRaises(HTTPException) as error: complete_opening(self.db,old,version)
            self.assertEqual(error.exception.status_code,409)
        self.assertEqual(self.db.get(Player,1).opening_state,'pending')
    def test_salvage_atomic_repeat_reload_and_distance_validation(self):
        from app.services.opening import complete_opening, collect_salvage
        p=self.db.get(Player,1)
        with self.assertRaises(HTTPException): collect_salvage(self.db,p.game_scope,160,3600)
        self.db.rollback()
        complete_opening(self.db,p.game_scope,1)
        with self.assertRaises(HTTPException): collect_salvage(self.db,p.game_scope,0,0)
        self.db.rollback()
        collect_salvage(self.db,p.game_scope,160,3600)
        self.db.expire_all()
        collect_salvage(self.db,p.game_scope,160,3600)
        self.assertEqual(p.inventory.count('rope'),1)
        self.assertEqual(p.salvage_ids,['southern_rope'])
        reset_world(self.db)
        self.db.commit()
        self.assertEqual(p.salvage_ids,[])
        self.assertEqual(p.inventory,['water','food'])
    def test_legacy_migration_preserves_progress_and_interiors(self):
        from app.database.opening_migration import upgrade_opening_schema
        engine=create_engine('sqlite://')
        with engine.begin() as c:
            c.execute(text('CREATE TABLE players (id INTEGER PRIMARY KEY, position JSON, inventory JSON, current_location TEXT)'))
            for id,pos in [(1,{'x':30.125,'y':50.875}),(2,{'x':10064.25,'y':10032.125}),(3,{'x':50000,'y':9000})]:
                c.execute(text('INSERT INTO players VALUES (:id,:pos,:items,\'saved\')'),{'id':id,'pos':json.dumps(pos),'items':'["bow"]'})
        upgrade_opening_schema(engine)
        with engine.connect() as c:
            rows=list(c.execute(text('SELECT position,inventory,opening_state,map_version FROM players ORDER BY id')))
        self.assertEqual(json.loads(rows[0][0]),{'x':30.125,'y':50.875})
        self.assertEqual(json.loads(rows[1][0]),{'x':10064.25,'y':10032.125})
        self.assertNotEqual(json.loads(rows[2][0]),{'x':50000,'y':9000})
        self.assertTrue(all(r[1]=='["bow"]' and r[2]=='complete' and r[3]==2 for r in rows))
        upgrade_opening_schema(engine)
        with engine.connect() as c: self.assertEqual(list(c.execute(text('SELECT position,inventory,opening_state,map_version FROM players ORDER BY id'))),rows)
        engine.dispose()

    def test_position_saves_update_arrival_location_for_future_conversations(self):
        from app.services.opening import complete_opening
        from app.api.routes.world import save_position, PlayerPosition
        p=self.db.get(Player,1)
        complete_opening(self.db,p.game_scope,1)
        for x,y,location in [(10064,10032,'workshop'),(0,0,'village_square'),(-650,70,'forest_edge')]:
            save_position(PlayerPosition(x=x,y=y,game_scope=p.game_scope),self.db)
            self.assertEqual(p.current_location,location)

    def test_server_mask_matches_godot_for_every_authoring_cell(self):
        import hashlib
        from app.services.island import land_cell, LAYOUT
        mask=bytes(int(land_cell(x,y)) for y in range(-192,192) for x in range(-256,256))
        self.assertEqual(hashlib.sha256(mask).hexdigest(),LAYOUT['mask_sha256'])

    def test_second_pass_route_and_existing_run_migration(self):
        from app.services.island import LAYOUT, MAP_VERSION, BEACH, exterior_walkable
        from app.database.opening_migration import upgrade_opening_schema
        import math
        route=LAYOUT['routes'][0]
        distance=sum(math.dist(a,b) for a,b in zip(route,route[1:]))
        self.assertGreaterEqual(distance/180,18)
        self.assertLessEqual(distance/180,22)
        self.assertEqual(MAP_VERSION,2)
        for a,b in zip(route,route[1:]):
            steps=math.ceil(math.dist(a,b)/8)
            for i in range(steps+1):
                t=i/steps
                self.assertTrue(exterior_walkable(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t))
        p=self.db.get(Player,1)
        for state,position in [('complete',{'x':0,'y':4560}),('pending',{'x':0,'y':4752}),('complete',{'x':30.125,'y':50.875})]:
            p.opening_state=state; p.opening_version=1; p.map_version=1
            p.position=position; p.inventory=['water','bow']; self.db.commit()
            upgrade_opening_schema(self.engine); self.db.expire_all()
            self.assertEqual(p.opening_state,state)
            self.assertEqual(p.opening_version,1)
            self.assertEqual(p.inventory,['water','bow'])
            self.assertEqual(p.map_version,2)
            self.assertTrue(exterior_walkable(**p.position))
            if position['y']<100: self.assertEqual(p.position,position)
            else: self.assertEqual(p.position,dict(zip(('x','y'),BEACH['markers']['ControlHandoff'])))
