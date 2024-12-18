import pytest
import json
from app import app
from flask import testing


@pytest.fixture()
def client():
    return app.test_client()


@pytest.fixture()
def runner():
    return app.test_cli_runner()


def test_isAlive(client: 'testing.FlaskClient'):
    response = client.get("/isAlive")
    assert b"ok" in response.data


def test_views(client: 'testing.FlaskClient'):
    response = client.put(
        "/views", data=b'{"scenario_id":18,"solve_view":2,"range":5,"target":2,"game_rules":0,"width":29,"height":25,"map":{"walls":[115],"thin_walls":[[43,1],[44,2],[68,0],[69,0],[69,2],[70,2],[94,0],[95,2]]},"viewpoints":[42,46,68,95,71]}')
    p = json.loads(response.data)["sight"]
    q = json.loads(response.data)["reach"]
    r = json.loads(response.data)["scenario_id"]
    assert json.dumps(p) == '[[[0, 42], [43, 69], [70, 95], [96, 115], [116, 122], [123, 148], [149, 187], [188, 260], [261, 332], [333, 405], [406, 477], [478, 550], [551, 725]], [[0, 46], [47, 69], [70, 91], [95, 114], [120, 136], [144, 159], [169, 181], [193, 204], [218, 226], [241, 250], [266, 275], [290, 300], [315, 325], [339, 350], [364, 375], [388, 400], [412, 425], [436, 450], [461, 475], [485, 500], [510, 525], [534, 550], [559, 575], [582, 600], [607, 625], [631, 650], [656, 675], [680, 700], [705, 725]], [[0, 68], [75, 95], [100, 115], [116, 123], [125, 138], [139, 162], [163, 185], [186, 209], [210, 232], [233, 256], [257, 279], [280, 303], [304, 326], [327, 350], [351, 725]], [[17, 25], [43, 50], [70, 75], [96, 100], [120, 125], [143, 150], [167, 175], [190, 200], [214, 225], [237, 250], [261, 275], [284, 300], [308, 325], [331, 350], [355, 375], [378, 400], [402, 725]], [[0, 50], [70, 71], [72, 75], [95, 100], [120, 125], [144, 150], [169, 175], [192, 200], [217, 225], [241, 250], [266, 275], [289, 300], [314, 325], [338, 350], [363, 375], [386, 400], [411, 425], [435, 450], [460, 475], [483, 500], [508, 525], [532, 550], [557, 575], [580, 600], [605, 625], [629, 650], [654, 675], [677, 700], [702, 725]]]'
    assert json.dumps(q) == '[[[13, 23], [37, 42], [43, 48], [63, 69], [70, 73], [88, 95], [96, 97], [114, 115], [116, 122], [139, 146], [165, 171]], [[17, 25], [41, 46], [47, 50], [67, 69], [70, 75], [95, 100], [120, 125], [144, 150], [170, 175]], [[14, 23], [38, 48], [63, 68], [88, 95], [114, 115], [116, 123], [139, 147], [165, 172], [190, 196]], [[17, 25], [43, 50], [70, 75], [96, 100], [120, 125], [143, 150], [168, 175], [193, 199], [219, 224]], [[17, 25], [41, 50], [70, 71], [72, 75], [95, 100], [120, 125], [144, 150], [169, 175], [194, 199]]]'
    assert r == 18


def test_solve_thin_los(client: 'testing.FlaskClient'):
    response = client.put(
        "/solve", data=b'{"scenario_id":3,"solve_view":2,"active_figure":42,"move":0,"range":5,"target":2,"flying":1,"teleport":0,"muddled":0,"game_rules":0,"aoe":[23,24,32],"width":29,"height":25,"map":{"characters":[145,169],"monsters":[42],"walls":[115],"obstacles":[96],"traps":[117],"hazardous":[40,216],"difficult":[168],"icy":[],"initiatives":[4,3],"thin_walls":[[43,1],[44,2],[68,0],[69,0],[69,2],[70,2],[94,0],[95,2]]}}')
    p = json.loads(response.data)["actions"]
    q = json.loads(response.data)["reach"]
    r = json.loads(response.data)["scenario_id"]
    s = json.loads(response.data)["sight"]
    
    assert json.dumps(p) == '[{"aoe": [145, 171, 195], "attacks": [145, 169], "destinations": [42], "focuses": [169], "move": 42, "sightlines": [[[3.3796296296293704, 31.385402133447602], [7.932870370370006, 35.623313484374414]], [[3.333333333333166, 31.46558967083489], [9.166666666666833, 33.486315612998006]]]}]'
    assert json.dumps(
        q) == '[[[13, 23], [37, 42], [43, 48], [63, 69], [70, 73], [88, 95], [96, 97], [114, 115], [116, 122], [139, 146], [165, 171]]]'
    assert r == 3
    assert json.dumps(
        s) == '[[[0, 42], [43, 69], [70, 95], [96, 115], [116, 122], [123, 148], [149, 187], [188, 260], [261, 332], [333, 405], [406, 477], [478, 550], [551, 725]]]'


def test_solve_sight(client: 'testing.FlaskClient'):
    response = client.put(
        "/solve", data=b'{"scenario_id":18,"solve_view":2,"active_figure":44,"move":2,"range":5,"target":2,"flying":1,"teleport":0,"muddled":1,"game_rules":0,"aoe":[23,24,32],"width":29,"height":25,"map":{"characters":[145,169],"monsters":[44],"walls":[115],"obstacles":[96],"traps":[117],"icy":[],"hazardous":[40,191],"difficult":[168],"initiatives":[4,3],"thin_walls":[[43,1],[44,2],[68,0],[69,0],[69,2],[70,2],[94,0],[95,2]]}}')
    p = json.loads(response.data)["actions"]
    q = json.loads(response.data)["reach"]
    r = json.loads(response.data)["scenario_id"]
    s = json.loads(response.data)["sight"]
    
    assert json.dumps(p) == '[{"aoe": [145, 171, 195], "attacks": [145, 169], "destinations": [68], "focuses": [145], "move": 68, "sightlines": [[[4.787202380952307, 32.41151622794452], [7.898561507936211, 35.68273817725964]], [[4.893939393939105, 32.22664229840324], [9.161616161616339, 33.49506334434935]]]}, {"aoe": [145, 171, 195], "attacks": [145, 169], "destinations": [71], "focuses": [145], "move": 71, "sightlines": [[[4.96153846153804, 37.172475023977476], [7.673076923077074, 36.672844983333604]], [[4.779069767441802, 37.62175475044967], [9.648936170213478, 34.64101615137754]]]}, {"aoe": [145, 171, 195], "attacks": [145, 169], "destinations": [42], "focuses": [145], "move": 42, "sightlines": [[[3.3796296296293704, 31.385402133447602], [7.932870370370006, 35.623313484374414]], [[3.333333333333166, 31.46558967083489], [9.166666666666833, 33.486315612998006]]]}, {"aoe": [169, 170, 193], "attacks": [145, 169], "destinations": [46], "focuses": [145], "move": 46, "sightlines": [[[3.3915492957743663, 37.917275636679875], [7.690845070422656, 36.703620317292525]], [[3.333333333333165, 38.3937929011104], [9.833333333333675, 34.64101615137754]]]}, {"aoe": [145, 171, 195], "attacks": [145, 169], "destinations": [95], "focuses": [145], "move": 95, "sightlines": [[[6.299999999999902, 36.71947712046037], [7.631944444444681, 36.60160144050106]], [[6.272727272727226, 36.766714869757614], [9.384722222221955, 34.441349183282334]]]}]'
    assert q.sort() == [[[13, 23], [37, 42], [43, 48], [63, 69], [70, 73], [88, 95], [96, 97], [114, 115], [116, 122], [139, 146], [165, 171]], [[17, 25], [41, 46], [47, 50], [67, 69], [70, 75], [95, 100], [120, 125], [144, 150], [170, 175]], [[14, 23], [38, 48], [63, 68], [88, 95], [114, 115], [116, 123], [139, 147], [165, 172], [190, 196]], [[17, 25], [41, 50], [70, 71], [72, 75], [95, 100], [120, 125], [144, 150], [169, 175], [194, 199]], [[17, 25], [43, 50], [70, 75], [96, 100], [120, 125], [143, 150], [168, 175], [193, 199], [219, 224]]].sort()
    assert r == 18
    assert s.sort() == [[[0, 42], [43, 69], [70, 95], [96, 115], [116, 122], [123, 148], [149, 187], [188, 260], [261, 332], [333, 405], [406, 477], [478, 550], [551, 725]], [[0, 46], [47, 69], [70, 91], [95, 114], [120, 136], [144, 159], [169, 181], [193, 204], [218, 226], [241, 250], [266, 275], [290, 300], [315, 325], [339, 350], [364, 375], [388, 400], [412, 425], [436, 450], [461, 475], [485, 500], [510, 525], [534, 550], [559, 575], [582, 600], [607, 625], [631, 650], [656, 675], [680, 700], [705, 725]], [[0, 68], [75, 95], [100, 115], [116, 123], [125, 138], [139, 162], [163, 185], [186, 209], [210, 232], [233, 256], [257, 279], [280, 303], [304, 326], [327, 350], [351, 725]], [[0, 50], [70, 71], [72, 75], [95, 100], [120, 125], [144, 150], [169, 175], [192, 200], [217, 225], [241, 250], [266, 275], [289, 300], [314, 325], [338, 350], [363, 375], [386, 400], [411, 425], [435, 450], [460, 475], [483, 500], [508, 525], [532, 550], [557, 575], [580, 600], [605, 625], [629, 650], [654, 675], [677, 700], [702, 725]], [[17, 25], [43, 50], [70, 75], [96, 100], [120, 125], [143, 150], [167, 175], [190, 200], [214, 225], [237, 250], [261, 275], [284, 300], [308, 325], [331, 350], [355, 375], [378, 400], [402, 725]]].sort()

def test_solve_multiple_destination(client: 'testing.FlaskClient'):
    response = client.put(
        "/solve", data=b'{"scenario_id":8,"solve_view":0,"active_figure":217,"move":2,"range":0,"target":1,"flying":0,"teleport":0,"muddled":0,"game_rules":0,"aoe":[],"width":29,"height":25,"map":{"characters":[314],"monsters":[217],"walls":[265,266,345],"obstacles":[],"traps":[],"hazardous":[],"difficult":[],"icy":[],"initiatives":[1],"thin_walls":[]}}')

    p = json.loads(response.data)["actions"]
    r = json.loads(response.data)["scenario_id"]

    assert json.dumps(p) == '[{"aoe": [], "attacks": [], "destinations": [289, 315], "focuses": [314], "move": 267, "sightlines": []}, {"aoe": [], "attacks": [], "destinations": [288, 289], "focuses": [314], "move": 215, "sightlines": []}, {"aoe": [], "attacks": [], "destinations": [288, 289], "focuses": [314], "move": 240, "sightlines": []}]'
    assert r == 8