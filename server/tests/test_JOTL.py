import collections
from solver.monster import Monster
from solver.solver import GloomhavenMap, Rule, Solver

def init_test():
    
    figures:list[str] = [' '] * 16 * 7
    contents:list[str] = [' '] * 16 * 7
    initiatives:list[int] = [0] * 16 * 7
    walls:list[list[bool]] = [[False] * 6 for _ in range(16*7)]

    return figures,contents,initiatives,walls
def map_solution(info: list[tuple[int,int,list[int],tuple[int] | tuple[()],list[int],set[tuple[tuple[float, float], tuple[float, float]]]]])->list[tuple[int, list[int], list[int], set[int], set[tuple[tuple[float, float], tuple[float, float]]], set[int], set[int]]]:
        debug_lines:set[int] = set()
        if info[0][1] ==-1:
            return list({((info[0][0],)):(info[0][0],[],[],set(),set(),set(),set())}.values())
        focusdict:dict[tuple[int]|tuple[int,int],set[int]] = collections.defaultdict(set)
        destdict:dict[tuple[int]|tuple[int,int],set[int]] = collections.defaultdict(set)        
        aoedict:dict[tuple[int]|tuple[int,int],set[int]] = collections.defaultdict(set)       
        for iinf in info:
            for act in iinf[2]:
                destdict[(act,)+tuple(sorted(iinf[3]))].update({iinf[0]})
                focusdict[(act,)+tuple(sorted(iinf[3]))].update({iinf[1]})
                aoedict[(act,)+tuple(sorted(iinf[3]))].update(iinf[4])
   
        solution = list({((act,)+tuple(sorted(iinf[3]))):
            (act,
            sorted(list(iinf[3])),
            aoedict[(act,)+tuple(sorted(iinf[3]))],
            destdict[(act,)+tuple(sorted(iinf[3]))],
            iinf[5],
            debug_lines,
            focusdict[(act,)+tuple(sorted(iinf[3]))])
            for iinf in info for act in iinf[2]}.values())
            
        return solution



def assert_answers(monster:Monster,figures:list[str],contents:list[str],initiatives:list[int],walls:list[list[bool]], correct_answers:set[tuple[int]]):

    gmap = GloomhavenMap(16, 7, monster,figures,contents, initiatives,walls, Rule(2))
    scenario = Solver(Rule(2),gmap)
    scenario.logging=False
    answers = map_solution(scenario.calculate_monster_move())

    test= [(
        (key[0],
            list()if len(key)==1 else list(key[1:]),
            correct_answers[1][key],
            set(correct_answers[3][key]),
            correct_answers[4][key],
            set(),
            set(correct_answers[2][key]))
            ) for key in correct_answers[0]]

    sanswers = sorted(answers)
    stest = sorted(test)
    for i in range(len(sanswers)):
        assert sanswers[i][0]==stest[i][0]
        assert sorted(sanswers[i][1])==sorted(stest[i][1])
        if(len(stest[i][2])>0):
            assert frozenset(stest[i][2]) in sanswers[i][2]
        assert sanswers[i][3]==stest[i][3]
        assert sanswers[i][4]==stest[i][4]
        assert sanswers[i][5]==stest[i][5]
        assert sanswers[i][6]==stest[i][6]
  


# Move towards the character and offer all valid options for the players to choose among
def test_Scenario1():
    m=Monster(action_move=1)
    figures,contents,initiatives,walls = init_test()

    figures[60] = 'C'
    figures[37] = 'M'
    figures[38] = 'M'
    figures[39] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(46,), (47,)}, {(46,): [], (47,): []}, {(46,): {52, 53}, (47,): {53}}, {(46,): {60}, (47,): {60}}, {(46,): set(), (47,): set()}, {(46,): set(), (47,): set()}))

# Online test question #1. Shorten the path to the destinations
def test_Scenario2():
    m=Monster(action_move=1)
    figures,contents,initiatives,walls = init_test()


    figures[35] = 'C'
    figures[36] = 'M'
    figures[37] = 'M'
    figures[38] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(45,), (31,)}, {(45,): [], (31,): []}, {(45,): {43}, (31,): {29}}, {(45,): {35}, (31,): {35}}, {(45,): set(), (31,): set()}, {(45,): set(), (31,): set()}))

# Online test question #2. The monster cannot shorten the path to the destination, so it stays put
def test_Scenario3():
    m=Monster(action_move=1)
    figures,contents,initiatives,walls = init_test()


    figures[35] = 'C'
    figures[37] = 'M'
    figures[38] = 'M'
    figures[39] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(39,)}, {(39,): []}, {(39,): {36}}, {(39,): {35}}, {(39,): set()}, {(39,): set()}))

# Online test question #6. The monster cannot attack the character from the near edge, so it begins the long trek around to the far edge
def test_Scenario4():
    m=Monster(action_move=2)
    figures,contents,initiatives,walls = init_test()

    figures[29] = 'C'

    contents[11] = 'O'
    contents[12] = 'O'
    contents[17] = 'O'
    contents[18] = 'O'
    contents[22] = 'O'
    contents[23] = 'O'
    contents[32] = 'O'
    contents[33] = 'O'
    contents[36] = 'O'
    contents[37] = 'O'
    contents[38] = 'O'
    contents[43] = 'O'

    figures[24] = 'M'
    figures[30] = 'M'

    figures[25] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(34,), (20,)}, {(34,): [], (20,): []}, {(34,): {35}, (20,): {21}}, {(34,): {29}, (20,): {29}}, {(34,): set(), (20,): set()}, {(34,): set(), (20,): set()}))

# When shortening the path to its destination, the monster will move the minimum amount. Players cannot choose a move that puts the monster equally close to its destination, but uses more movement
def test_Scenario5():
    m=Monster(action_move=2)
    figures,contents,initiatives,walls = init_test()


    figures[35] = 'C'
    figures[30] = 'M'
    figures[36] = 'M'
    figures[37] = 'M'
    figures[44] = 'M'
    figures[38] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(45,), (31,)}, {(45,): [], (31,): []}, {(45,): {43}, (31,): {29}}, {(45,): {35}, (31,): {35}}, {(45,): set(), (31,): set()}, {(45,): set(), (31,): set()}))

# When choosing focus, proximity breaks ties in path delta_length. C20 is in closer proximity
def test_Scenario6():
    m=Monster(action_move=2)
    figures,contents,initiatives,walls = init_test()


    figures[50] = 'C'
    initiatives[50] = 10

    figures[29] = 'C'
    initiatives[29] = 20

    contents[30] = 'O'
    figures[31] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(44, 50)}, {(44, 50): []}, {(44, 50): {44}}, {(44, 50): {50}}, {(44, 50): {((10.75, 3.8971143170299736), (10.75, 3.8971143170299736))}}, {(44, 50): set()}))

# When choosing focus, proximity breaks ties in path delta_length, but walls must be pathed around when testing proximity. Proximity is equal here, so initiative breaks the tie
def test_Scenario7():
    m=Monster(action_move=2)
    figures,contents,initiatives,walls = init_test()


    figures[50] = 'C'
    initiatives[50] = 10

    figures[29] = 'C'
    initiatives[29] = 20

    contents[30] = 'X'
    figures[31] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(44, 50)}, {(44, 50): []}, {(44, 50): {44}}, {(44, 50): {50}}, {(44, 50): {((10.75, 3.8971143170299736), (10.75, 3.8971143170299736))}}, {(44, 50): set()}))

# Given equal path distance and proximity, lowest initiative breaks the focus tie
def test_Scenario8():
    m=Monster(action_move=2)
    figures,contents,initiatives,walls = init_test()


    figures[9] = 'C'
    initiatives[9] = 10

    figures[29] = 'C'
    initiatives[29] = 20

    figures[32] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(17, 9)}, {(17, 9): []}, {(17, 9): {17}}, {(17, 9): {9}}, {(17, 9): {((3.25, 5.629165124598851), (3.25, 5.629165124598851))}}, {(17, 9): set()}))

# Given equal path distance, proximity, and initiative; players choose the foc
def test_Scenario9():
    m=Monster(action_move=2)
    figures,contents,initiatives,walls = init_test()


    figures[9] = 'C'
    initiatives[9] = 99

    figures[29] = 'C'
    initiatives[29] = 99

    figures[32] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(17, 9), (30, 29)}, {(17, 9): [], (30, 29): []}, {(17, 9): {17}, (30, 29): {30}}, {(17, 9): {9}, (30, 29): {29}}, {(17, 9): {((3.25, 5.629165124598851), (3.25, 5.629165124598851))}, (30, 29): {((7.0, 3.4641016151377544), (7.0, 3.4641016151377544))}}, {(17, 9): set(), (30, 29): set()}))

# Online test question #4. The monster has a valid path to its destination that does not go through a trap. Even though the monster cannot shorten its path to the destination, it will not go through the trap
def test_Scenario10():
    m=Monster(action_move=2)
    figures,contents,initiatives,walls = init_test()

    contents[70] = 'X'
    contents[77] = 'X'
    contents[84] = 'X'
    contents[91] = 'X'
    contents[98] = 'X'
    contents[105] = 'X'
    contents[106] = 'X'
    contents[107] = 'X'
    contents[108] = 'X'
    contents[109] = 'X'
    contents[102] = 'X'
    contents[95] = 'X'
    contents[88] = 'X'
    contents[81] = 'X'
    contents[74] = 'X'

    contents[85] = 'O'
    contents[93] = 'O'

    contents[87] = 'T'

    figures[86] = 'M'
    figures[92] = 'M'

    figures[79] = 'A'

    figures[99] = 'C'

    assert_answers(m, figures,contents,initiatives,walls,({(79,)}, {(79,): []}, {(79,): {100}}, {(79,): {99}}, {(79,): set()}, {(79,): set()}))

# The monster will shorten its distance to focus, even if it means moving off the shortest path
def test_Scenario11():
    m=Monster(action_move=2)
    figures,contents,initiatives,walls = init_test()


    contents[70] = 'X'
    contents[77] = 'X'
    contents[84] = 'X'
    contents[91] = 'X'
    contents[98] = 'X'
    contents[105] = 'X'
    contents[106] = 'X'
    contents[107] = 'X'
    contents[108] = 'X'
    contents[109] = 'X'
    contents[102] = 'X'
    contents[95] = 'X'
    contents[88] = 'X'
    contents[81] = 'X'
    contents[74] = 'X'

    contents[85] = 'O'
    contents[93] = 'O'

    figures[86] = 'M'
    figures[92] = 'M'

    figures[79] = 'A'

    figures[99] = 'C'

    assert_answers(m, figures,contents,initiatives,walls,({(94,)}, {(94,): []}, {(94,): {100}}, {(94,): {99}}, {(94,): set()}, {(94,): set()}))

# The monster cannot shorten its path to the destination, so it stays put
def test_Scenario12():
    m=Monster(action_move=1)
    figures,contents,initiatives,walls = init_test()


    contents[70] = 'X'
    contents[77] = 'X'
    contents[84] = 'X'
    contents[91] = 'X'
    contents[98] = 'X'
    contents[105] = 'X'
    contents[106] = 'X'
    contents[107] = 'X'
    contents[108] = 'X'
    contents[109] = 'X'
    contents[102] = 'X'
    contents[95] = 'X'
    contents[88] = 'X'
    contents[81] = 'X'
    contents[74] = 'X'

    contents[85] = 'O'
    contents[93] = 'O'

    figures[86] = 'M'
    figures[92] = 'M'

    figures[79] = 'A'

    figures[99] = 'C'

    assert_answers(m, figures,contents,initiatives,walls,({(79,)}, {(79,): []}, {(79,): {100}}, {(79,): {99}}, {(79,): set()}, {(79,): set()}))

# The players choose between the equally close destinations, even thought the monster can make less progress towards one of the two destinations. See this thread (https://boardgamegeek.com/article/28429917#28429917)
def test_Scenario13():
    m=Monster(action_move=2)
    figures,contents,initiatives,walls = init_test()


    figures[33] = 'A'

    figures[24] = 'M'

    contents[30] = 'O'
    contents[31] = 'O'

    figures[29] = 'C'

    assert_answers(m, figures,contents,initiatives,walls,({(25,), (32,), (38,)}, {(38,): [], (25,): [], (32,): []}, {(25,): {22}, (32,): {22}, (38,): {36}}, {(25,): {29}, (32,): {29}, (38,): {29}}, {(25,): set(), (32,): set(), (38,): set()}, {(25,): set(), (32,): set(), (38,): set()}))

# Online test question #5
def test_Scenario14():
    m=Monster(action_move=3)
    figures,contents,initiatives,walls = init_test()


    figures[31] = 'A'

    figures[37] = 'M'
    figures[24] = 'M'

    contents[10] = 'O'
    contents[17] = 'O'
    contents[19] = 'O'
    contents[23] = 'O'
    contents[25] = 'O'
    contents[30] = 'O'
    contents[32] = 'O'
    contents[36] = 'O'
    contents[38] = 'O'
    contents[43] = 'O'
    contents[45] = 'O'
    contents[51] = 'O'

    contents[11] = 'T'

    figures[44] = 'C'

    assert_answers(m, figures,contents,initiatives,walls,({(11,)}, {(11,): []}, {(11,): {50}}, {(11,): {44}}, {(11,): set()}, {(11,): set()}))

# The monster moves towards the character to which it has the stortest path, C20
def test_Scenario15():
    m=Monster(action_move=2)
    figures,contents,initiatives,walls = init_test()


    figures[17] = 'C'
    initiatives[17] = 10

    figures[51] = 'C'
    initiatives[51] = 20

    contents[24] = 'O'
    contents[18] = 'O'
    contents[31] = 'O'

    figures[32] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(45, 51)}, {(45, 51): []}, {(45, 51): {45}}, {(45, 51): {51}}, {(45, 51): {((10.75, 5.629165124598851), (10.75, 5.629165124598851))}}, {(45, 51): set()}))

# The monster chooses its focus based on the shortest path to an attack position, not the shortest path to a character's position. The monster moves towards C20
def test_Scenario16():
    m=Monster(action_move=2)
    figures,contents,initiatives,walls = init_test()


    figures[9] = 'C'
    initiatives[9] = 10

    figures[58] = 'C'
    initiatives[58] = 20

    contents[16] = 'O'
    contents[23] = 'O'
    contents[3] = 'O'
    contents[8] = 'O'
    contents[10] = 'O'

    figures[17] = 'M'

    figures[32] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(45,)}, {(45,): []}, {(45,): {51}}, {(45,): {58}}, {(45,): set()}, {(45,): set()}))

# The monster will choose its destination without consideration for which destination it can most shorten its path to. The destination is chosen based only on which destination is closest. The monster moves as far as it can down the west side of the obstacle
def test_Scenario17():
    m=Monster(action_move=3)
    figures,contents,initiatives,walls = init_test()


    figures[29] = 'C'

    contents[30] = 'O'
    contents[31] = 'O'
    contents[32] = 'O'
    contents[38] = 'O'

    figures[17] = 'M'
    figures[23] = 'M'
    figures[24] = 'M'

    figures[33] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(25,)}, {(25,): []}, {(25,): {22}}, {(25,): {29}}, {(25,): set()}, {(25,): set()}))

# The monster will path around traps if at all possible
def test_Scenario18():
    m=Monster(action_move=2)
    figures,contents,initiatives,walls = init_test()


    figures[28] = 'C'

    contents[31] = 'T'
    contents[24] = 'T'
    contents[25] = 'T'
    contents[38] = 'T'
    contents[39] = 'T'

    figures[32] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(40,), (26,)}, {(26,): [], (40,): []}, {(40,): {35, 29}, (26,): {21, 29}}, {(40,): {28}, (26,): {28}}, {(40,): set(), (26,): set()}, {(40,): set(), (26,): set()}))

# The monster will move through traps if that is its only option
def test_Scenario19():
    m=Monster(action_move=2)
    figures,contents,initiatives,walls = init_test()


    figures[28] = 'C'

    contents[31] = 'T'
    contents[33] = 'T'
    contents[24] = 'T'
    contents[25] = 'T'
    contents[38] = 'T'
    contents[39] = 'T'

    figures[32] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(30,)}, {(30,): []}, {(30,): {29}}, {(30,): {28}}, {(30,): set()}, {(30,): set()}))

# The monster will move through the minimium number of traps possible
def test_Scenario20():
    m=Monster(action_move=3)
    figures,contents,initiatives,walls = init_test()


    figures[28] = 'C'

    contents[17] = 'T'
    contents[23] = 'T'
    contents[24] = 'T'
    contents[25] = 'T'
    contents[30] = 'T'
    contents[31] = 'T'
    contents[33] = 'T'
    contents[37] = 'T'
    contents[38] = 'T'
    contents[39] = 'T'
    contents[45] = 'T'
    contents[18] = 'T'
    contents[19] = 'T'
    contents[34] = 'T'
    contents[40] = 'T'
    contents[47] = 'T'
    contents[46] = 'T'

    figures[32] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(20,)}, {(20,): []}, {(20,): {21, 29}}, {(20,): {28}}, {(20,): set()}, {(20,): set()}))

# Monsters will fly over tra
def test_Scenario21():
    m=Monster(action_move=3,flying=True)
    figures,contents,initiatives,walls = init_test()


    figures[28] = 'C'

    contents[17] = 'T'
    contents[23] = 'T'
    contents[24] = 'T'
    contents[25] = 'T'
    contents[30] = 'T'
    contents[31] = 'T'
    contents[33] = 'T'
    contents[37] = 'T'
    contents[38] = 'T'
    contents[39] = 'T'
    contents[45] = 'T'
    contents[18] = 'T'
    contents[19] = 'T'
    contents[34] = 'T'
    contents[40] = 'T'
    contents[47] = 'T'
    contents[46] = 'T'

    figures[32] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(29, 28)}, {(29, 28): []}, {(29, 28): {29}}, {(29, 28): {28}}, {(29, 28): {((7.0, 1.7320508075688772), (7.0, 1.7320508075688772))}}, {(29, 28): set()}))

# Monsters will jump over tra
def test_Scenario22():
    m=Monster(action_move=3,jumping=True)
    figures,contents,initiatives,walls = init_test()


    figures[28] = 'C'

    contents[17] = 'T'
    contents[23] = 'T'
    contents[24] = 'T'
    contents[25] = 'T'
    contents[30] = 'T'
    contents[31] = 'T'
    contents[33] = 'T'
    contents[37] = 'T'
    contents[38] = 'T'
    contents[39] = 'T'
    contents[45] = 'T'
    contents[18] = 'T'
    contents[19] = 'T'
    contents[34] = 'T'
    contents[40] = 'T'
    contents[47] = 'T'
    contents[46] = 'T'

    figures[32] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(29, 28)}, {(29, 28): []}, {(29, 28): {29}}, {(29, 28): {28}}, {(29, 28): {((7.0, 1.7320508075688772), (7.0, 1.7320508075688772))}}, {(29, 28): set()}))

# Monsters will jump over traps, but not land of them if possible
def test_Scenario23():
    m=Monster(action_move=3,jumping=True)
    figures,contents,initiatives,walls = init_test()


    figures[28] = 'C'

    contents[17] = 'T'
    contents[23] = 'T'
    contents[24] = 'T'
    contents[25] = 'T'
    contents[29] = 'T'
    contents[30] = 'T'
    contents[31] = 'T'
    contents[33] = 'T'
    contents[37] = 'T'
    contents[38] = 'T'
    contents[39] = 'T'
    contents[45] = 'T'
    contents[18] = 'T'
    contents[19] = 'T'
    contents[34] = 'T'
    contents[40] = 'T'
    contents[47] = 'T'
    contents[46] = 'T'

    figures[32] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(36,), (22,)}, {(36,): [], (22,): []}, {(36,): {35}, (22,): {21}}, {(36,): {28}, (22,): {28}}, {(36,): set(), (22,): set()}, {(36,): set(), (22,): set()}))

# The monster will focus on a character that does not require it to move through a trap or hazardous terrain, if possible
def test_Scenario24():
    m=Monster(action_move=2)
    figures,contents,initiatives,walls = init_test()


    figures[8] = 'C'
    initiatives[8] = 10
    figures[80] = 'C'
    initiatives[80] = 20

    contents[17] = 'H'
    contents[18] = 'H'
    contents[23] = 'H'
    contents[25] = 'H'
    contents[30] = 'H'
    contents[33] = 'H'
    contents[37] = 'H'
    contents[39] = 'H'
    contents[44] = 'H'
    contents[47] = 'H'
    contents[51] = 'H'
    contents[53] = 'H'
    contents[61] = 'H'
    contents[67] = 'H'
    contents[75] = 'H'
    contents[81] = 'H'
    contents[88] = 'H'
    contents[87] = 'H'
    contents[79] = 'H'
    contents[72] = 'H'
    contents[65] = 'H'
    contents[58] = 'H'

    figures[24] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(38,)}, {(38,): []}, {(38,): {73, 74}}, {(38,): {80}}, {(38,): set()}, {(38,): set()}))

# Online test question #13
def test_Scenario25():
    m=Monster(action_move=3)
    figures,contents,initiatives,walls = init_test()


    figures[16] = 'C'
    initiatives[16] = 30
    figures[30] = 'C'
    initiatives[30] = 20
    figures[65] = 'C'
    initiatives[65] = 10

    contents[18] = 'T'

    contents[24] = 'O'
    contents[31] = 'O'
    contents[38] = 'O'

    figures[39] = 'M'
    figures[45] = 'M'

    figures[32] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(52,)}, {(52,): []}, {(52,): {59}}, {(52,): {65}}, {(52,): set()}, {(52,): set()}))

# Online test question #20
def test_Scenario26():
    m=Monster(action_move=2)
    figures,contents,initiatives,walls = init_test()


    figures[37] = 'C'
    initiatives[37] = 50
    figures[44] = 'C'
    initiatives[44] = 4

    contents[16] = 'X'
    contents[17] = 'X'
    contents[18] = 'X'
    contents[19] = 'X'
    contents[22] = 'X'
    contents[33] = 'X'
    contents[36] = 'X'
    contents[47] = 'X'
    contents[50] = 'X'
    contents[51] = 'X'
    contents[52] = 'X'
    contents[53] = 'X'

    walls[25][1] = True
    walls[29][1] = True
    walls[39][1] = True
    walls[43][1] = True

    contents[32] = 'T'

    contents[38] = 'O'
    contents[30] = 'O'

    figures[31] = 'M'

    figures[24] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(39,)}, {(39,): []}, {(39,): {45}}, {(39,): {44}}, {(39,): set()}, {(39,): set()}))

# Thin walls block movement. The monster must go around the wall
def test_Scenario27():
    m=Monster(action_move=3)
    figures,contents,initiatives,walls = init_test()


    figures[35] = 'C'

    contents[0] = 'X'
    contents[1] = 'X'
    contents[2] = 'X'
    contents[30] = 'X'
    contents[44] = 'X'
    contents[58] = 'X'
    contents[72] = 'X'
    contents[84] = 'X'
    contents[85] = 'X'
    contents[86] = 'X'
    walls[8][1] = True
    walls[22][1] = True
    walls[36][1] = True
    walls[50][1] = True
    walls[64][1] = True
    walls[78][1] = True

    figures[38] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(16,)}, {(16,): []}, {(16,): {29}}, {(16,): {35}}, {(16,): set()}, {(16,): set()}))

# Thin walls block melee. The monster moves through the doorway
def test_Scenario28():
    m=Monster(action_move=3)
    figures,contents,initiatives,walls = init_test()


    figures[22] = 'C'

    contents[0] = 'X'
    contents[1] = 'X'
    contents[2] = 'X'
    contents[16] = 'X'
    contents[30] = 'X'
    contents[58] = 'X'
    contents[72] = 'X'
    contents[84] = 'X'
    contents[85] = 'X'
    contents[86] = 'X'
    walls[8][1] = True
    walls[22][1] = True
    walls[36][1] = True
    walls[50][1] = True
    walls[64][1] = True
    walls[78][1] = True

    figures[31] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(36,)}, {(36,): []}, {(36,): {29}}, {(36,): {22}}, {(36,): set()}, {(36,): set()}))

# Range follows proximity pathing, even melee attack A melee attack cannot be performed around a thin wall. The monster moves through the door to engage from behind
def test_Scenario29():
    m=Monster(action_move=3)
    figures,contents,initiatives,walls = init_test()


    figures[36] = 'C'

    contents[0] = 'X'
    contents[1] = 'X'
    contents[2] = 'X'
    contents[16] = 'X'
    contents[30] = 'X'
    contents[58] = 'X'
    contents[72] = 'X'
    contents[84] = 'X'
    contents[85] = 'X'
    contents[86] = 'X'
    walls[8][1] = True
    walls[22][1] = True
    walls[36][1] = True
    walls[50][1] = True
    walls[64][1] = True
    walls[78][1] = True

    figures[44] = 'M'
    figures[31] = 'A'
    assert_answers(m, figures,contents,initiatives,walls,({(43, 36)}, {(43, 36): []}, {(43, 36): {43}}, {(43, 36): {36}}, {(43, 36): {((9.25, 3.031088913245535), (9.25, 3.031088913245535))}}, {(43, 36): set()}))

# Range follows proximity pathing, even melee attack A melee attack cannot be performed around a doorway. The monster chooses the focus with the shorter path to an attack location
def test_Scenario30():
    m=Monster(action_move=3)
    figures,contents,initiatives,walls = init_test()


    figures[36] = 'C'
    initiatives[36] = 10
    figures[46] = 'C'
    initiatives[46] = 20

    contents[0] = 'X'
    contents[1] = 'X'
    contents[2] = 'X'
    contents[16] = 'X'
    contents[30] = 'X'
    contents[58] = 'X'
    contents[72] = 'X'
    contents[84] = 'X'
    contents[85] = 'X'
    contents[86] = 'X'
    walls[8][1] = True
    walls[22][1] = True
    walls[36][1] = True
    walls[50][1] = True
    walls[64][1] = True
    walls[78][1] = True

    # figures[44] = 'M'
    figures[31] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(38, 46)}, {(38, 46): []}, {(38, 46): {38}}, {(38, 46): {46}}, {(38, 46): {((9.25, 7.3612159321677275), (9.25, 7.3612159321677275))}}, {(38, 46): set()}))

# The monster will not move if it can attack without disadvantage from its position
def test_Scenario31():
    m=Monster(action_move=1)
    figures,contents,initiatives,walls = init_test()


    figures[36] = 'C'
    figures[30] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(30, 36)}, {(30, 36): []}, {(30, 36): {30}}, {(30, 36): {36}}, {(30, 36): {((7.75, 3.897114317029974), (7.75, 3.897114317029974))}}, {(30, 36): set()}))

# The monster will not move if in range and line of sight of its foc
def test_Scenario32():
    m=Monster(action_move=3, action_range=4)
    figures,contents,initiatives,walls = init_test()


    figures[29] = 'C'

    figures[25] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(25, 29)}, {(25, 29): []}, {(25, 29): {25}}, {(25, 29): {29}}, {(25, 29): {((5.714285714285285, 7.794228634059947), (6.785714285714715, 3.4641016151377544))}}, {(25, 29): set()}))

# The monster will make the minimum move to get within range and line of sight
def test_Scenario33():
    m=Monster(action_move=4, action_range=5)
    figures,contents,initiatives,walls = init_test()


    figures[29] = 'C'

    contents[3] = 'X'
    contents[17] = 'X'
    contents[31] = 'X'
    walls[9][1] = True
    walls[23][1] = True

    figures[26] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(39, 29), (40, 29)}, {(39, 29): [], (40, 29): []}, {(39, 29): {39}, (40, 29): {40}}, {(39, 29): {29}, (40, 29): {29}}, {(39, 29): {((8.761904761904237, 7.794228634059947), (7.548387096774597, 3.3802927050934004))}, (40, 29): {((8.844444444443756, 9.526279441628825), (7.694915254237398, 3.1264984916283756))}}, {(39, 29): set(), (40, 29): set()}))

# Doorway line of sight
def test_Scenario34():
    m=Monster(action_move=6, action_range=7)
    figures,contents,initiatives,walls = init_test()


    figures[15] = 'C'

    contents[0] = 'X'
    contents[1] = 'X'
    contents[2] = 'X'
    contents[16] = 'X'
    contents[30] = 'X'
    contents[58] = 'X'
    contents[72] = 'X'
    contents[84] = 'X'
    contents[85] = 'X'
    contents[86] = 'X'
    walls[8][1] = True
    walls[22][1] = True
    walls[36][1] = True
    walls[50][1] = True
    walls[64][1] = True
    walls[78][1] = True

    figures[3] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(44, 15)}, {(44, 15): []}, {(44, 15): {44}}, {(44, 15): {15}}, {(44, 15): {((9.380952380952118, 3.670298139848789), (4.951612903225403, 2.514267301308962))}}, {(44, 15): set()}))

# Doorway line of sight
def test_Scenario35():
    m=Monster(action_move=6, action_range=7)
    figures,contents,initiatives,walls = init_test()


    figures[21] = 'C'

    contents[0] = 'X'
    contents[1] = 'X'
    contents[2] = 'X'
    contents[16] = 'X'
    contents[30] = 'X'
    contents[58] = 'X'
    contents[72] = 'X'
    contents[84] = 'X'
    contents[85] = 'X'
    contents[86] = 'X'
    walls[8][1] = True
    walls[22][1] = True
    walls[36][1] = True
    walls[50][1] = True
    walls[64][1] = True
    walls[78][1] = True

    figures[3] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(45, 21), (44, 21)}, {(44, 21): [], (45, 21): []}, {(45, 21): {45}, (44, 21): {44}}, {(45, 21): {21}, (44, 21): {21}}, {(45, 21): {((10.202127659574064, 5.196152422706632), (6.414285714285386, 1.8805123053610644))}, (44, 21): {((9.344086021505188, 3.73415254750097), (6.296774193548294, 2.084048229752392))}}, {(45, 21): set(), (44, 21): set()}))

# Doorway line of sight
def test_Scenario36():
    m=Monster(action_move=6, action_range=7)
    figures,contents,initiatives,walls = init_test()


    figures[22] = 'C'

    contents[0] = 'X'
    contents[1] = 'X'
    contents[2] = 'X'
    contents[16] = 'X'
    contents[30] = 'X'
    contents[58] = 'X'
    contents[72] = 'X'
    contents[84] = 'X'
    contents[85] = 'X'
    contents[86] = 'X'
    walls[8][1] = True
    walls[22][1] = True
    walls[36][1] = True
    walls[50][1] = True
    walls[64][1] = True
    walls[78][1] = True

    figures[3] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(44, 22)}, {(44, 22): []}, {(44, 22): {44}}, {(44, 22): {22}}, {(44, 22): {((9.366666666666433, 3.695041722814009), (6.217391304347892, 2.9746089956075332))}}, {(44, 22): set()}))

# Doorway line of sight
def test_Scenario37():
    m=Monster(action_move=6, action_range=7)
    figures,contents,initiatives,walls = init_test()


    figures[28] = 'C'

    contents[0] = 'X'
    contents[1] = 'X'
    contents[2] = 'X'
    contents[16] = 'X'
    contents[30] = 'X'
    contents[58] = 'X'
    contents[72] = 'X'
    contents[84] = 'X'
    contents[85] = 'X'
    contents[86] = 'X'
    walls[8][1] = True
    walls[22][1] = True
    walls[36][1] = True
    walls[50][1] = True
    walls[64][1] = True
    walls[78][1] = True

    figures[3] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(37, 28)}, {(37, 28): []}, {(37, 28): {37}}, {(37, 28): {28}}, {(37, 28): {((9.222222222222276, 4.715027198382036), (7.803921568627343, 1.205643209190287))}}, {(37, 28): set()}))

# Doorway line of sight
def test_Scenario38():
    m=Monster(action_move=6, action_range=7)
    figures,contents,initiatives,walls = init_test()


    figures[29] = 'C'

    contents[0] = 'X'
    contents[1] = 'X'
    contents[2] = 'X'
    contents[16] = 'X'
    contents[30] = 'X'
    contents[58] = 'X'
    contents[72] = 'X'
    contents[84] = 'X'
    contents[85] = 'X'
    contents[86] = 'X'
    walls[8][1] = True
    walls[22][1] = True
    walls[36][1] = True
    walls[50][1] = True
    walls[64][1] = True
    walls[78][1] = True

    figures[3] = 'A'
    assert_answers(m, figures,contents,initiatives,walls,({(44, 29), (45, 29)}, {(44, 29): [], (45, 29): []}, {(44, 29): {44}, (45, 29): {45}}, {(44, 29): {29}, (45, 29): {29}}, {(44, 29): {((9.333333333333167, 3.7527767497328557), (7.833333333333167, 2.8867513459484173))}, (45, 29): {((10.065217391304218, 5.196152422706632), (7.8666666666664335, 2.8290163190295696))}}, {(44, 29): set(), (45, 29): set()}))

# Doorway line of sight
def test_Scenario39():
    m=Monster(action_move=6, action_range=7)
    figures,contents,initiatives,walls = init_test()

    figures[35] = 'C'

    contents[0] = 'X'
    contents[1] = 'X'
    contents[2] = 'X'
    contents[16] = 'X'
    contents[30] = 'X'
    contents[58] = 'X'
    contents[72] = 'X'
    contents[84] = 'X'
    contents[85] = 'X'
    contents[86] = 'X'
    walls[8][1] = True
    walls[22][1] = True
    walls[36][1] = True
    walls[50][1] = True
    walls[64][1] = True
    walls[78][1] = True

    figures[3] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(37, 35), (38, 35), (34, 35), (40, 35), (39, 35)}, {(34, 35): [], (37, 35): [], (38, 35): [], (39, 35): [], (40, 35): []}, {(37, 35): {37}, (38, 35): {38}, (39, 35): {39}, (34, 35): {34}, (40, 35): {40}}, {(37, 35): {35}, (38, 35): {35}, (39, 35): {35}, (34, 35): {35}, (40, 35): {35}}, {(37, 35): {((9.214285714285786, 4.701280763401364), (8.944444444443556, 2.598076211353316))}, (38, 35): {((9.166666666666833, 6.35085296108617), (9.166666666666833, 2.309401076758216))}, (39, 35): {((9.074468085106734, 7.923211141007173), (9.220930232558196, 2.215413823634513))}, (34, 35): {((7.913555992141127, 11.108604835576251), (9.441696113073824, 1.8330361020037638))}, (40, 35): {((8.976190476189524, 9.526279441628825), (9.245762711864417, 2.1724027077982355))}}, {(37, 35): set(), (38, 35): set(), (39, 35): set(), (34, 35): set(), (40, 35): set()}))

# Doorway line of sight
def test_Scenario40():
    m=Monster(action_move=6, action_range=7)
    figures,contents,initiatives,walls = init_test()


    figures[36] = 'C'

    contents[0] = 'X'
    contents[1] = 'X'
    contents[2] = 'X'
    contents[16] = 'X'
    contents[30] = 'X'
    contents[58] = 'X'
    contents[72] = 'X'
    contents[84] = 'X'
    contents[85] = 'X'
    contents[86] = 'X'
    walls[8][1] = True
    walls[22][1] = True
    walls[36][1] = True
    walls[50][1] = True
    walls[64][1] = True
    walls[78][1] = True

    figures[3] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(33, 36), (26, 36), (32, 36)}, {(26, 36): [], (32, 36): [], (33, 36): []}, {(33, 36): {33}, (26, 36): {26}, (32, 36): {32}}, {(33, 36): {36}, (26, 36): {36}, (32, 36): {36}}, {(33, 36): {((7.58000000000034, 8.798818102450484), (9.23076923076927, 3.9304229864062297))}, (26, 36): {((6.316993464052153, 10.075328227034413), (9.233333333333366, 3.925981830489397))}, (32, 36): {((7.803921568627343, 7.454610828654098), (9.222222222222282, 3.94522683946234))}}, {(33, 36): set(), (26, 36): set(), (32, 36): set()}))

# Doorway line of sight
def test_Scenario41():
    m=Monster(action_move=6, action_range=7)
    figures,contents,initiatives,walls = init_test()


    figures[42] = 'C'

    contents[0] = 'X'
    contents[1] = 'X'
    contents[2] = 'X'
    contents[16] = 'X'
    contents[30] = 'X'
    contents[58] = 'X'
    contents[72] = 'X'
    contents[84] = 'X'
    contents[85] = 'X'
    contents[86] = 'X'
    walls[8][1] = True
    walls[22][1] = True
    walls[36][1] = True
    walls[50][1] = True
    walls[64][1] = True
    walls[78][1] = True

    figures[3] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(32, 42), (33, 42), (26, 42)}, {(26, 42): [], (32, 42): [], (33, 42): []}, {(32, 42): {32}, (33, 42): {33}, (26, 42): {26}}, {(32, 42): {42}, (33, 42): {42}, (26, 42): {42}}, {(32, 42): {((7.80952380952369, 7.464314194522812), (10.291666666666083, 1.7320508075688772))}, (33, 42): {((7.594594594594906, 8.824096681804143), (10.233333333332865, 1.7320508075688772))}, (26, 42): {((6.319248826290941, 10.079234629021466), (10.387445887445114, 1.7320508075688772))}}, {(32, 42): set(), (33, 42): set(), (26, 42): set()}))

# Doorway line of sight
def test_Scenario42():
    m=Monster(action_move=6, action_range=7)
    figures,contents,initiatives,walls = init_test()


    figures[43] = 'C'

    contents[0] = 'X'
    contents[1] = 'X'
    contents[2] = 'X'
    contents[16] = 'X'
    contents[30] = 'X'
    contents[58] = 'X'
    contents[72] = 'X'
    contents[84] = 'X'
    contents[85] = 'X'
    contents[86] = 'X'
    walls[8][1] = True
    walls[22][1] = True
    walls[36][1] = True
    walls[50][1] = True
    walls[64][1] = True
    walls[78][1] = True

    figures[3] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(18, 43), (5, 43), (11, 43)}, {(5, 43): [], (11, 43): [], (18, 43): []}, {(18, 43): {18}, (5, 43): {5}, (11, 43): {11}}, {(18, 43): {43}, (5, 43): {43}, (11, 43): {43}}, {(18, 43): {((4.936507936507564, 7.684257154213658), (10.272151898733636, 3.4641016151377544))}, (5, 43): {((1.958041958041542, 9.45360598117067), (10.34431137724482, 3.4641016151377544))}, (11, 43): {((3.4494949494945506, 8.572776724330115), (10.31512605041954, 3.4641016151377544))}}, {(18, 43): set(), (5, 43): set(), (11, 43): set()}))

# Doorway line of sight
def test_Scenario43():
    m=Monster(action_move=6, action_range=7)
    figures,contents,initiatives,walls = init_test()


    figures[44] = 'C'
    contents[0] = 'X'
    contents[1] = 'X'
    contents[2] = 'X'
    contents[16] = 'X'
    contents[30] = 'X'
    contents[58] = 'X'
    contents[72] = 'X'
    contents[84] = 'X'
    contents[85] = 'X'
    contents[86] = 'X'
    walls[8][1] = True
    walls[22][1] = True
    walls[36][1] = True
    walls[50][1] = True
    walls[64][1] = True
    walls[78][1] = True
    figures[3] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(3, 44)}, {(3, 44): []}, {(3, 44): {3}}, {(3, 44): {44}}, {(3, 44): {((1.8977272727269776, 6.239319386356581), (9.438095238094862, 5.088930229856478))}}, {(3, 44): set()}))

# Doorway line of sight
def test_Scenario44():
    m=Monster(action_move=6, action_range=7)
    figures,contents,initiatives,walls = init_test()


    figures[7] = 'C'

    contents[34] = 'X'
    contents[33] = 'X'
    contents[32] = 'X'
    contents[30] = 'X'
    contents[29] = 'X'
    contents[28] = 'X'

    figures[35] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(38, 7), (31, 7)}, {(31, 7): [], (38, 7): []}, {(38, 7): {38}, (31, 7): {31}}, {(38, 7): {7}, (31, 7): {7}}, {(38, 7): {((7.680555555555695, 6.615471834464221), (3.0746527777781285, 2.468773807315449))}, (31, 7): {((6.212797619047693, 5.693601538570778), (3.101438492063789, 2.4223795892556605))}}, {(38, 7): set(), (31, 7): set()}))

# Doorway line of sight
def test_Scenario45():
    m=Monster(action_move=6, action_range=7)
    figures,contents,initiatives,walls = init_test()


    figures[15] = 'C'

    contents[34] = 'X'
    contents[33] = 'X'
    contents[32] = 'X'
    contents[30] = 'X'
    contents[29] = 'X'
    contents[28] = 'X'

    figures[35] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(38, 15), (31, 15)}, {(31, 15): [], (38, 15): []}, {(38, 15): {38}, (31, 15): {31}}, {(38, 15): {15}, (31, 15): {15}}, {(38, 15): {((7.666666666666833, 6.639528095680408), (4.423076923076076, 3.4641016151377544))}, (31, 15): {((6.246666666666673, 5.634938627290736), (4.536666666667093, 3.4005930855261566))}}, {(38, 15): set(), (31, 15): set()}))

# Doorway line of sight
def test_Scenario46():
    m=Monster(action_move=6, action_range=7)
    figures,contents,initiatives,walls = init_test()


    figures[21] = 'C'

    contents[34] = 'X'
    contents[33] = 'X'
    contents[32] = 'X'
    contents[30] = 'X'
    contents[29] = 'X'
    contents[28] = 'X'

    figures[35] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(31, 21)}, {(31, 21): []}, {(31, 21): {31}}, {(31, 21): {21}}, {(31, 21): {((6.217391304347891, 5.685645042236854), (5.266666666667133, 2.598076211353316))}}, {(31, 21): set()}))

# Doorway line of sight
def test_Scenario47():
    m=Monster(action_move=6, action_range=7)
    figures,contents,initiatives,walls = init_test()


    figures[8] = 'C'

    contents[34] = 'X'
    contents[33] = 'X'
    contents[32] = 'X'
    contents[30] = 'X'
    contents[29] = 'X'
    contents[28] = 'X'

    figures[35] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(37, 8)}, {(37, 8): []}, {(37, 8): {37}}, {(37, 8): {8}}, {(37, 8): {((7.851063829787032, 5.804212812597483), (3.085714285714614, 4.1816655211300064))}}, {(37, 8): set()}))

# Doorway line of sight
def test_Scenario48():
    m=Monster(action_move=6, action_range=7)
    figures,contents,initiatives,walls = init_test()


    figures[16] = 'C'

    contents[34] = 'X'
    contents[33] = 'X'
    contents[32] = 'X'
    contents[30] = 'X'
    contents[29] = 'X'
    contents[28] = 'X'

    figures[35] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(37, 16)}, {(37, 16): []}, {(37, 16): {37}}, {(37, 16): {16}}, {(37, 16): {((7.782608695652108, 5.685645042236853), (4.6333333333335665, 4.965212315030378))}}, {(37, 16): set()}))

# Doorway line of sight
def test_Scenario49():
    m=Monster(action_move=6, action_range=7)
    figures,contents,initiatives,walls = init_test()


    figures[22] = 'C'

    contents[34] = 'X'
    contents[33] = 'X'
    contents[32] = 'X'
    contents[30] = 'X'
    contents[29] = 'X'
    contents[28] = 'X'

    figures[35] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(31, 22), (38, 22)}, {(31, 22): [], (38, 22): []}, {(31, 22): {31}, (38, 22): {38}}, {(31, 22): {22}, (38, 22): {22}}, {(31, 22): {((6.2916666666665835, 5.556996340950292), (5.583333333333167, 4.330127018922193))}, (38, 22): {((7.666666666666833, 6.639528095680408), (5.444444444444556, 4.330127018922193))}}, {(31, 22): set(), (38, 22): set()}))

# Doorway line of sight
def test_Scenario50():
    m=Monster(action_move=6, action_range=7)
    figures,contents,initiatives,walls = init_test()


    figures[9] = 'C'

    contents[34] = 'X'
    contents[33] = 'X'
    contents[32] = 'X'
    contents[30] = 'X'
    contents[29] = 'X'
    contents[28] = 'X'

    figures[35] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(37, 9), (44, 9)}, {(37, 9): [], (44, 9): []}, {(37, 9): {37}, (44, 9): {44}}, {(37, 9): {9}, (44, 9): {9}}, {(37, 9): {((7.740407770107581, 5.612550895067299), (3.4045795795792704, 5.361425438954918))}, (44, 9): {((9.454166666666259, 5.116766760692352), (3.186915887850593, 5.738430011991997))}}, {(37, 9): set(), (44, 9): set()}))

# Doorway line of sight
def test_Scenario51():
    m=Monster(action_move=6, action_range=7)
    figures,contents,initiatives,walls = init_test()


    figures[17] = 'C'

    contents[34] = 'X'
    contents[33] = 'X'
    contents[32] = 'X'
    contents[30] = 'X'
    contents[29] = 'X'
    contents[28] = 'X'

    figures[35] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(44, 17), (50, 17), (37, 17)}, {(37, 17): [], (44, 17): [], (50, 17): []}, {(44, 17): {44}, (50, 17): {50}, (37, 17): {37}}, {(44, 17): {17}, (50, 17): {17}, (37, 17): {17}}, {(44, 17): {((9.380952380952118, 4.989955897995598), (4.951612903225403, 6.145986736535424))}, (50, 17): {((10.922222222221878, 4.195411956110684), (4.805084745762602, 6.39978095000045))}, (37, 17): {((7.753333333333327, 5.634938627290736), (4.963333333332907, 5.998669296879473))}}, {(44, 17): set(), (50, 17): set(), (37, 17): set()}))

# Doorway line of sight
def test_Scenario52():
    m=Monster(action_move=6, action_range=7)
    figures,contents,initiatives,walls = init_test()


    figures[23] = 'C'

    contents[34] = 'X'
    contents[33] = 'X'
    contents[32] = 'X'
    contents[30] = 'X'
    contents[29] = 'X'
    contents[28] = 'X'

    figures[35] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(44, 23), (50, 23), (37, 23)}, {(37, 23): [], (44, 23): [], (50, 23): []}, {(44, 23): {44}, (50, 23): {50}, (37, 23): {37}}, {(44, 23): {23}, (50, 23): {23}, (37, 23): {23}}, {(44, 23): {((9.366666666666434, 4.965212315030378), (6.217391304347891, 5.685645042236854))}, (50, 23): {((10.914285714285386, 4.181665521130006), (6.148936170212968, 5.804212812597483))}, (37, 23): {((7.7083333333334165, 5.556996340950292), (6.2916666666665835, 5.556996340950292))}}, {(44, 23): set(), (50, 23): set(), (37, 23): set()}))

# Doorway line of sight
def test_Scenario53():
    m=Monster(action_move=6, action_range=7)
    figures,contents,initiatives,walls = init_test()


    figures[31] = 'C'

    contents[34] = 'X'
    contents[33] = 'X'
    contents[32] = 'X'
    contents[30] = 'X'
    contents[29] = 'X'
    contents[28] = 'X'

    figures[35] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(35, 31)}, {(35, 31): []}, {(35, 31): {35}}, {(35, 31): {31}}, {(35, 31): {((8.733333333332867, 2.598076211353316), (7.782608695652109, 5.685645042236854))}}, {(35, 31): set()}))

# The "V" terrain piece represents an unintuitive line of sight example. The monster does not have line of sight to the character from its initial position. (https://boardgamegeek.com/image/3932301/codenamegreyfox
def test_Scenario54():
    m=Monster(action_move=2, action_range=7)
    figures,contents,initiatives,walls = init_test()


    figures[76] = 'C'

    contents[21] = 'X'
    contents[29] = 'X'
    contents[36] = 'X'
    contents[44] = 'X'
    contents[51] = 'X'
    contents[52] = 'X'
    contents[53] = 'X'
    contents[54] = 'X'
    contents[55] = 'X'
    contents[70] = 'X'
    contents[71] = 'X'
    contents[78] = 'X'
    contents[79] = 'X'
    contents[80] = 'X'
    contents[81] = 'X'
    contents[82] = 'X'
    contents[83] = 'X'
    walls[56][5] = True
    walls[62][1] = True
    walls[63][4] = True
    walls[76][1] = True

    figures[43] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(43, 76)}, {(43, 76): []}, {(43, 76): {43}}, {(43, 76): {76}}, {(43, 76): {((10.973484848484402, 2.6440018009487183), (16.14081632653033, 10.392304845413264))}}, {(43, 76): set()}))

# The monster cannot trace line of sight from the vertex coincident with the tip of the thin wall. The monster must step out to attack. (https://boardgamegeek.com/image/3932321/codenamegreyfox
def test_Scenario55():
    m=Monster(action_move=2, action_range=3)
    figures,contents,initiatives,walls = init_test()


    figures[65] = 'C'

    contents[28] = 'X'
    contents[29] = 'X'
    contents[56] = 'X'
    contents[57] = 'X'
    contents[71] = 'X'
    contents[72] = 'X'
    contents[73] = 'X'
    contents[74] = 'X'
    contents[75] = 'X'
    contents[76] = 'X'
    contents[15] = 'X'
    contents[16] = 'X'
    contents[17] = 'X'
    contents[18] = 'X'
    contents[19] = 'X'
    contents[20] = 'X'
    walls[49][1] = True
    walls[35][1] = True
    walls[63][1] = True
    walls[21][1] = True

    figures[49] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(43, 65)}, {(43, 65): []}, {(43, 65): {43}}, {(43, 65): {65}}, {(43, 65): {((10.655913978494812, 3.194050682774539), (13.703225806451707, 4.844155000523117))}}, {(43, 65): set()}))

# Range is measured by pathing around walls. The character is not within range of the monster's initial position. The monster steps forward
def test_Scenario56():
    m=Monster(action_move=1, action_range=3)
    figures,contents,initiatives,walls = init_test()


    figures[36] = 'C'

    contents[16] = 'X'
    contents[30] = 'X'
    walls[22][1] = True
    walls[36][1] = True

    figures[39] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(46, 36), (38, 36)}, {(38, 36): [], (46, 36): []}, {(46, 36): {46}, (38, 36): {38}}, {(46, 36): {36}, (38, 36): {36}}, {(46, 36): {((9.911111111111289, 6.928203230275509), (9.222222222222276, 3.9452268394623475))}, (38, 36): {((8.944444444443556, 6.06217782649107), (9.214285714285786, 3.9589732744430215))}}, {(46, 36): set(), (38, 36): set()}))

# Online test question #7. The monster's only attack position is over the obstacle north of the character. With no other options, the monster will move through the trap
def test_Scenario57():
    m=Monster(action_move=2, action_range=2)
    figures,contents,initiatives,walls = init_test()


    figures[99] = 'C'

    contents[70] = 'X'
    contents[77] = 'X'
    contents[84] = 'X'
    contents[91] = 'X'
    contents[98] = 'X'
    contents[105] = 'X'
    contents[106] = 'X'
    contents[107] = 'X'
    contents[108] = 'X'
    contents[109] = 'X'
    contents[102] = 'X'
    contents[95] = 'X'
    contents[88] = 'X'
    contents[81] = 'X'
    contents[74] = 'X'

    contents[85] = 'O'
    contents[93] = 'O'
    contents[100] = 'O'

    contents[87] = 'T'

    figures[86] = 'M'
    figures[92] = 'M'

    figures[79] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(94,)}, {(94,): []}, {(94,): {101}}, {(94,): {99}}, {(94,): set()}, {(94,): set()}))

# Even if the monster cannot get to within range of its focus, it will get as close to an attack position as possible
def test_Scenario58():
    m=Monster(action_move=2, action_range=2)
    figures,contents,initiatives,walls = init_test()


    figures[29] = 'C'
    figures[12] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(18,), (25,), (10,)}, {(18,): [], (25,): [], (10,): []}, {(18,): {16, 23, 31}, (25,): {23, 31}, (10,): {16, 23}}, {(18,): {29}, (25,): {29}, (10,): {29}}, {(18,): set(), (25,): set(), (10,): set()}, {(18,): set(), (25,): set(), (10,): set()}))

# Even if the monster cannot get to within range of its focus, it will get as close to the nearest attack position as possible
def test_Scenario59():
    m=Monster(action_move=3, action_range=3)
    figures,contents,initiatives,walls = init_test()


    figures[30] = 'C'

    contents[9] = 'X'
    contents[17] = 'X'
    contents[24] = 'X'
    contents[32] = 'X'
    contents[39] = 'X'
    contents[47] = 'X'

    figures[25] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(3,)}, {(3,): []}, {(3,): {8}}, {(3,): {30}}, {(3,): set()}, {(3,): set()}))

# When using a ranged attack, the monster will step away from its target to avoid disadvantage
def test_Scenario60():
    m=Monster(action_move=3, action_range=4)
    figures,contents,initiatives,walls = init_test()


    figures[30] = 'C'

    contents[23] = 'O'
    contents[31] = 'O'
    contents[38] = 'O'
    contents[46] = 'O'
    contents[36] = 'O'
    contents[44] = 'O'
    contents[51] = 'O'
    contents[59] = 'O'

    figures[37] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(45, 30)}, {(45, 30): []}, {(45, 30): {45}}, {(45, 30): {30}}, {(45, 30): {((9.25, 5.629165124598851), (7.75, 4.7631397208144115))}}, {(45, 30): set()}))

# When using a ranged attack while muddled, the monster will not step away from its target
def test_Scenario61():
    m=Monster(action_move=3, action_range=4, muddled=True)
    figures,contents,initiatives,walls = init_test()


    figures[30] = 'C'

    contents[23] = 'O'
    contents[31] = 'O'
    contents[38] = 'O'
    contents[46] = 'O'
    contents[36] = 'O'
    contents[44] = 'O'
    contents[51] = 'O'
    contents[59] = 'O'

    figures[37] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(37, 30)}, {(37, 30): []}, {(37, 30): {37}}, {(37, 30): {30}}, {(37, 30): {((7.75, 4.7631397208144115), (7.75, 4.763139720814412))}}, {(37, 30): set()}))

# When using a ranged attack, the monster will not step onto a trap to avoid disadvantage
def test_Scenario62():
    m=Monster(action_move=3, action_range=4)
    figures,contents,initiatives,walls = init_test()


    figures[30] = 'C'

    contents[23] = 'O'
    contents[31] = 'O'
    contents[38] = 'O'
    contents[46] = 'O'
    contents[36] = 'O'
    contents[44] = 'O'
    contents[51] = 'O'
    contents[59] = 'O'

    contents[45] = 'T'

    figures[37] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(37, 30)}, {(37, 30): []}, {(37, 30): {37}}, {(37, 30): {30}}, {(37, 30): {((7.75, 4.7631397208144115), (7.75, 4.763139720814412))}}, {(37, 30): set()}))

# The monster will move the additional step to engage both its focus and an extra target
def test_Scenario63():
    m=Monster(action_move=2, action_target=2)
    figures,contents,initiatives,walls = init_test()


    figures[16] = 'C'
    initiatives[16] = 20
    figures[22] = 'C'
    initiatives[22] = 10

    figures[18] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(23, 16, 22)}, {(23, 16, 22): []}, {(23, 16, 22): {23}}, {(23, 16, 22): {16}}, {(23, 16, 22): {((4.75, 4.763139720814412), (4.75, 4.763139720814412)), ((5.5, 4.330127018922193), (5.5, 4.330127018922193))}}, {(23, 16, 22): set()}))

# Online test question #8
def test_Scenario64():
    m=Monster(action_move=2,action_range=2, action_target=3)
    figures,contents,initiatives,walls = init_test()


    figures[16] = 'C'
    initiatives[16] = 10
    figures[31] = 'C'
    initiatives[31] = 20
    figures[35] = 'C'
    initiatives[35] = 30

    contents[22] = 'T'

    figures[24] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(30, 16, 31, 35)}, {(30, 16, 31, 35): []}, {(30, 16, 31, 35): {30}}, {(30, 16, 31, 35): {16}}, {(30, 16, 31, 35): {((7.0, 5.196152422706632), (7.0, 5.196152422706632)), ((6.0000000000005, 4.330127018923059), (4.9999999999995, 4.330127018921327)), ((7.499999999999, 3.4641016151377544), (8.000000000001, 2.598076211353316))}}, {(30, 16, 31, 35): set()}))

# Online test question #9
def test_Scenario65():
    m=Monster(action_move=2,action_range=2, action_target=3, muddled=True)
    figures,contents,initiatives,walls = init_test()


    figures[16] = 'C'
    initiatives[16] = 10
    figures[31] = 'C'
    initiatives[31] = 20
    figures[35] = 'C'
    initiatives[35] = 30

    contents[22] = 'T'

    figures[24] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(30, 16, 31, 35)}, {(30, 16, 31, 35): []}, {(30, 16, 31, 35): {30}}, {(30, 16, 31, 35): {16}}, {(30, 16, 31, 35): {((7.0, 5.196152422706632), (7.0, 5.196152422706632)), ((6.0000000000005, 4.330127018923059), (4.9999999999995, 4.330127018921327)), ((7.499999999999, 3.4641016151377544), (8.000000000001, 2.598076211353316))}}, {(30, 16, 31, 35): set()}))

# Online test question #10
def test_Scenario66():
    m=Monster(action_move=2,action_range=2, action_target=3, flying=True)
    figures,contents,initiatives,walls = init_test()


    figures[16] = 'C'
    initiatives[16] = 10
    figures[31] = 'C'
    initiatives[31] = 20
    figures[35] = 'C'
    initiatives[35] = 30

    contents[22] = 'T'

    figures[24] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(30, 16, 31, 35)}, {(30, 16, 31, 35): []}, {(30, 16, 31, 35): {30}}, {(30, 16, 31, 35): {16}}, {(30, 16, 31, 35): {((7.0, 5.196152422706632), (7.0, 5.196152422706632)), ((6.0000000000005, 4.330127018923059), (4.9999999999995, 4.330127018921327)), ((7.499999999999, 3.4641016151377544), (8.000000000001, 2.598076211353316))}}, {(30, 16, 31, 35): set()}))

# Online test question #11
def test_Scenario67():
    m=Monster(action_move=1,action_range=2)
    figures,contents,initiatives,walls = init_test()


    figures[15] = 'C'
    initiatives[15] = 20
    figures[36] = 'C'
    initiatives[36] = 10

    contents[23] = 'O'
    contents[29] = 'O'

    contents[30] = 'T'

    figures[22] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(22, 36)}, {(22, 36): []}, {(22, 36): {22}}, {(22, 36): {36}}, {(22, 36): {((6.4999999999995, 3.4641016151368884), (7.5000000000005, 3.4641016151386204))}}, {(22, 36): set()}))

# Online test question #12
def test_Scenario68():
    m=Monster(action_move=1,action_range=2,action_target=2)
    figures,contents,initiatives,walls = init_test()


    figures[15] = 'C'
    initiatives[15] = 40
    figures[22] = 'C'
    initiatives[22] = 10
    figures[23] = 'C'
    initiatives[23] = 30
    figures[24] = 'C'
    initiatives[24] = 20

    figures[17] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(9, 22, 24)}, {(9, 22, 24): []}, {(9, 22, 24): {9}}, {(9, 22, 24): {22}}, {(9, 22, 24): {((3.25, 4.763139720814412), (4.75, 3.8971143170299736)), ((3.25, 5.629165124598851), (4.75, 6.49519052838329))}}, {(9, 22, 24): set()}))

# Online test question #14
def test_Scenario69():
    m=Monster(action_move=1,action_range=2,action_target=2)
    figures,contents,initiatives,walls = init_test()


    figures[17] = 'C'
    initiatives[17] = 20
    figures[29] = 'C'
    initiatives[29] = 50
    figures[46] = 'C'
    initiatives[46] = 10

    figures[38] = 'M'

    contents[37] = 'T'

    contents[23] = 'O'

    figures[30] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(31, 17, 29)}, {(31, 17, 29): []}, {(31, 17, 29): {31}}, {(31, 17, 29): {17}}, {(31, 17, 29): {((6.0000000000005, 6.062177826491936), (4.9999999999995, 6.062177826490204)), ((7.0, 5.196152422706632), (7.0, 3.4641016151377544))}}, {(31, 17, 29): set()}))

# The monster prioritizes additional targets based on their rank as a focus. Here C30 is preferred because it is in closer proximity
def test_Scenario70():
    m=Monster(action_move=3,action_range=4,action_target=2)
    figures,contents,initiatives,walls = init_test()


    figures[9] = 'C'
    initiatives[9] = 10
    figures[47] = 'C'
    initiatives[47] = 30
    figures[50] = 'C'
    initiatives[50] = 20

    figures[24] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(24, 9, 50)}, {(24, 9, 50): []}, {(24, 9, 50): {24}}, {(24, 9, 50): {9}}, {(24, 9, 50): {((4.75, 6.49519052838329), (3.25, 5.629165124598851)),  ((6.25, 6.49519052838329), (10.75, 3.897114317029974))}}, {(24, 9, 50): set()}))

# The monster prioritizes additional targets based on their rank as a focus. Here C20 is preferred because of initiative
def test_Scenario71():
    m=Monster(action_move=3,action_range=3,action_target=2)
    figures,contents,initiatives,walls = init_test()


    figures[17] = 'C'
    initiatives[17] = 10
    figures[62] = 'C'
    initiatives[62] = 20
    figures[57] = 'C'
    initiatives[57] = 30

    figures[24] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(39, 17, 62)}, {(39, 17, 62): []}, {(39, 17, 62): {39}}, {(39, 17, 62): {17}}, {(39, 17, 62): {((7.750000000000001, 8.227241335952165), (4.75, 6.495190528383289)), ((9.25, 9.093266739736606), (12.25, 10.825317547305481))}}, {(39, 17, 62): set()}))

# The monster prioritizes additional targets based on their rank as a focus. Here C30 is preferred because the path to attacking it is shorter
def test_Scenario72():
    m=Monster(action_move=3,action_range=3,action_target=2)
    figures,contents,initiatives,walls = init_test()


    figures[17] = 'C'
    initiatives[17] = 10
    figures[62] = 'C'
    initiatives[62] = 20
    figures[57] = 'C'
    initiatives[57] = 30

    contents[32] = 'O'

    figures[24] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(37, 17, 57)}, {(37, 17, 57): []}, {(37, 17, 57): {37}}, {(37, 17, 57): {17}}, {(37, 17, 57): {((7.6000000000003, 5.369357503464039), (4.8999999999997, 5.888972745733663)), ((9.25, 4.763139720814412), (12.25, 3.0310889132455356))}}, {(37, 17, 57): set()}))

# The monster prioritizes additional targets based on their rank as a focus. Here it is a tie, so the players pick
def test_Scenario73():
    m=Monster(action_move=3,action_range=3,action_target=2)
    figures,contents,initiatives,walls = init_test()


    figures[17] = 'C'
    initiatives[17] = 10
    figures[62] = 'C'
    initiatives[62] = 99
    figures[57] = 'C'
    initiatives[57] = 99

    figures[24] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(39, 17, 62), (37, 17, 57)}, {(37, 17, 57): [], (39, 17, 62): []}, {(39, 17, 62): {39}, (37, 17, 57): {37}}, {(39, 17, 62): {17}, (37, 17, 57): {17}}, {(39, 17, 62): {((7.750000000000001, 8.227241335952165), (4.75, 6.495190528383289)), ((9.25, 9.093266739736606), (12.25, 10.825317547305481))}, (37, 17, 57): {((7.6000000000003, 5.369357503464039), (4.8999999999997, 5.888972745733663)), ((9.25, 4.763139720814412), (12.25, 3.0310889132455356))}}, {(39, 17, 62): set(), (37, 17, 57): set()}))

# The monster only attacks additional targets if it can do so while still attacking its focus
def test_Scenario74():
    m=Monster(action_move=2,action_target=2)
    figures,contents,initiatives,walls = init_test()


    figures[9] = 'C'
    initiatives[9] = 10

    figures[29] = 'C'
    initiatives[29] = 20

    figures[32] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(17, 9)}, {(17, 9): []}, {(17, 9): {17}}, {(17, 9): {9}}, {(17, 9): {((3.25, 5.629165124598851), (3.25, 5.629165124598851))}}, {(17, 9): set()}))

# The monster chooses extra targets based on their priority as a focus. On ties, players choose
def test_Scenario75():
    m=Monster(action_move=2,action_target=4)
    figures,contents,initiatives,walls = init_test()


    figures[16] = 'C'
    initiatives[16] = 10
    figures[17] = 'C'
    initiatives[17] = 30
    figures[24] = 'C'
    initiatives[24] = 10
    figures[31] = 'C'
    initiatives[31] = 20
    figures[30] = 'C'
    initiatives[30] = 40
    figures[22] = 'C'
    initiatives[22] = 30

    figures[23] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(23, 16, 17, 24, 31), (23, 16, 22, 24, 31)}, {(23, 16, 17, 24, 31): [], (23, 16, 22, 24, 31): []}, {(23, 16, 17, 24, 31): {23}, (23, 16, 22, 24, 31): {23}}, {(23, 16, 17, 24, 31): {16, 24}, (23, 16, 22, 24, 31): {16, 24}}, {(23, 16, 17, 24, 31): {((4.75, 4.763139720814412), (4.75, 4.763139720814412)), ((5.5, 6.06217782649107), (5.5, 6.06217782649107)), ((6.25, 5.629165124598851), (6.25, 5.629165124598851)), ((4.75, 5.629165124598851), (4.75, 5.629165124598851))}, (23, 16, 22, 24, 31): {((4.75, 4.763139720814412), (4.75, 4.763139720814412)), ((5.5, 6.06217782649107), (5.5, 6.06217782649107)), ((5.5, 4.330127018922193), (5.5, 4.330127018922193)), ((6.25, 5.629165124598851), (6.25, 5.629165124598851))}}, {(23, 16, 17, 24, 31): set(), (23, 16, 22, 24, 31): set()}))

# The monster cannot reach any focus, so it does not move
def test_Scenario76():
    m=Monster(action_move=1)
    figures,contents,initiatives,walls = init_test()


    figures[30] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(30,)}, {(30,): []}, {(30,): {}}, {(30,): {}}, {(30,): set()}, {(30,): set()}))

# The monster cannot reach any focus, so it does not move
def test_Scenario77():
    m=Monster(action_move=2)
    figures,contents,initiatives,walls = init_test()


    figures[9] = 'C'

    contents[22] = 'O'
    contents[23] = 'O'
    contents[24] = 'O'
    contents[29] = 'O'
    contents[32] = 'O'
    contents[35] = 'O'
    contents[39] = 'O'
    contents[43] = 'O'
    contents[46] = 'O'
    contents[50] = 'O'
    contents[51] = 'O'
    contents[52] = 'O'

    figures[37] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(37,)}, {(37,): []}, {(37,): {}}, {(37,): {}}, {(37,): set()}, {(37,): set()}))

# The monster will not step on a trap to attack its focus if it has a trap-free path to attack on future tur
def test_Scenario78():
    m=Monster(action_move=3)
    figures,contents,initiatives,walls = init_test()


    figures[28] = 'C'

    contents[29] = 'T'

    figures[32] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(36,), (22,)}, {(36,): [], (22,): []}, {(36,): {35}, (22,): {21}}, {(36,): {28}, (22,): {28}}, {(36,): set(), (22,): set()}, {(36,): set(), (22,): set()}))

# The monster moves in close to attack additional targets using its AoE
def test_Scenario79():
    m=Monster(action_move=2)
    m.aoe[25] = True
    m.aoe[31] = True
    m.aoe[32] = True
    figures,contents,initiatives,walls = init_test()


    figures[16] = 'C'
    figures[22] = 'C'

    figures[18] = 'A'



    assert_answers(m, figures,contents,initiatives,walls,({(23, 16, 22)}, {(23, 16, 22): [17, 22, 16]}, {(23, 16, 22): {23}}, {(23, 16, 22): {16}}, {(23, 16, 22): {((4.75, 4.763139720814412), (4.75, 4.763139720814412)), ((5.5, 4.330127018922193), (5.5, 4.330127018922193))}}, {(23, 16, 22): set()}))

# The monster moves in close to attack an additional target using its AoE
def test_Scenario80():
    m=Monster(action_move=2)
    m.aoe[31] = True
    m.aoe[37] = True
    figures,contents,initiatives,walls = init_test()


    figures[16] = 'C'
    figures[22] = 'C'

    figures[18] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(9, 16, 22)}, {(9, 16, 22): [16, 22]}, {(9, 16, 22): {9}}, {(9, 16, 22): {16}}, {(9, 16, 22): {((3.25, 4.763139720814412), (4.75, 3.8971143170299736)), ((3.25, 4.763139720814412), (3.25, 4.763139720814412))}}, {(9, 16, 22): set()}))

# WWhen deciding how to use its AoE, the monster prioritizes targets based on their ranking as a focus. The monster's first priority is to attack its focus, C30. After that, the next highest priority is C10
def test_Scenario81():
    m=Monster(action_move=2)
    m.aoe[31] = True
    m.aoe[37] = True
    figures,contents,initiatives,walls = init_test()


    figures[16] = 'C'
    initiatives[16] = 30
    figures[22] = 'C'
    initiatives[22] = 20
    figures[8] = 'C'
    initiatives[8] = 10

    figures[18] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(23, 8, 16)}, {(23, 8, 16): [16, 8]}, {(23, 8, 16): {23}}, {(23, 8, 16): {16}}, {(23, 8, 16): {((4.75, 4.763139720814412), (3.25, 3.8971143170299736)), ((4.75, 4.763139720814412), (4.75, 4.763139720814412))}}, {(23, 8, 16): set()}))

# The monster favors C10 over C20 as its secondary target. Even with an AoE and an added target, the monster is unable to attack all three characters. From one position the monster can use its AoE to attack two targets. From another, the monster can use its additional attack. The player can choose where the monster moves
def test_Scenario82():
    m=Monster(action_move=2,action_target=2)
    m.aoe[31] = True
    m.aoe[37] = True
    figures,contents,initiatives,walls = init_test()


    figures[16] = 'C'
    initiatives[16] = 30
    figures[22] = 'C'
    initiatives[22] = 10
    figures[29] = 'C'
    initiatives[29] = 20

    figures[18] = 'A'



    assert_answers(m, figures,contents,initiatives,walls,({(23, 16, 22), (9, 16, 22)}, {(9, 16, 22): [16, 22], (23, 16, 22): [22, 21]}, {(23, 16, 22): {23}, (9, 16, 22): {9}}, {(23, 16, 22): {16}, (9, 16, 22): {16}}, {(23, 16, 22): {((4.75, 4.763139720814412), (4.75, 4.763139720814412)), ((5.5, 4.330127018922193), (5.5, 4.330127018922193))}, (9, 16, 22): {((3.25, 4.763139720814412), (4.75, 3.8971143170299736)), ((3.25, 4.763139720814412), (3.25, 4.763139720814412))}}, {(23, 16, 22): set(), (9, 16, 22): set()}))

# The monster moves to a position where it can attack all the characters, using both its AoE and its extra attack
def test_Scenario83():
    m=Monster(action_move=2,action_target=2)
    m.aoe[31] = True
    m.aoe[37] = True
    figures,contents,initiatives,walls = init_test()


    figures[16] = 'C'
    figures[17] = 'C'
    figures[22] = 'C'

    figures[18] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(9, 16, 17, 22)}, {(9, 16, 17, 22): [16, 22]}, {(9, 16, 17, 22): {9}}, {(9, 16, 17, 22): {16, 17}}, {(9, 16, 17, 22): {((3.25, 5.629165124598851), (3.25, 5.629165124598851)), ((3.25, 4.763139720814412), (4.75, 3.8971143170299736)), ((3.25, 4.763139720814412), (3.25, 4.763139720814412))}}, {(9, 16, 17, 22): set()}))

# The path to melee range of C10 is shorter than the path to C20. However, the monster can attack C20 over the obstacle with its melee AoE. Thus, the path to an attack position on C20 is shorter. The monster focuses on C20
def test_Scenario84():
    m=Monster(action_move=3)
    m.aoe[31] = True
    m.aoe[37] = True

    figures,contents,initiatives,walls = init_test()


    figures[15] = 'C'
    initiatives[15] = 20
    figures[51] = 'C'
    initiatives[51] = 10

    contents[9] = 'O'
    contents[16] = 'O'
    contents[23] = 'O'

    figures[19] = 'A'


    assert_answers(m, figures,contents,initiatives,walls,({(17, 15)}, {(17, 15): [16, 15]}, {(17, 15): {17}}, {(17, 15): {15}}, {(17, 15): {((4.0, 5.196152422706632), (4.0, 3.4641016151377544))}}, {(17, 15): set()}))

# AoE melee attacks do not require adjacency, nor do they test range. The monster attacks from outside the room. It does not need to step into the room, as would be required to use a non-AoE melee attack
def test_Scenario85():
    m=Monster(action_move=3)
    m.aoe[18] = True
    m.aoe[25] = True
    m.aoe[32] = True
    figures,contents,initiatives,walls = init_test()


    figures[36] = 'C'

    contents[0] = 'X'
    contents[1] = 'X'
    contents[2] = 'X'
    contents[16] = 'X'
    contents[30] = 'X'
    contents[58] = 'X'
    contents[72] = 'X'
    contents[84] = 'X'
    contents[85] = 'X'
    contents[86] = 'X'
    walls[8][1] = True
    walls[22][1] = True
    walls[36][1] = True
    walls[50][1] = True
    walls[64][1] = True
    walls[78][1] = True

    figures[44] = 'M'
    figures[31] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(37, 36)}, {(37, 36): [31, 30, 36]}, {(37, 36): {37}}, {(37, 36): {36}}, {(37, 36): {((9.166666666666833, 4.618802153517293), (9.166666666666833, 4.041451884327093))}}, {(37, 36): set()}))

# The mirrored image of an AoE pattern can be used. The players choose which group of characters the monster attacks. If attacking the second group, the monster uses the mirrored version of its AoE pattern
def test_Scenario86():
    m=Monster(action_move=2)
    m.aoe[20] = True
    m.aoe[25] = True
    m.aoe[26] = True
    figures,contents,initiatives,walls = init_test()


    figures[18] = 'C'
    figures[23] = 'C'
    figures[24] = 'C'

    figures[51] = 'C'
    figures[52] = 'C'
    figures[60] = 'C'

    figures[36] = 'A'



    assert_answers(m, figures,contents,initiatives,walls,({(22, 18, 23, 24), (50, 51, 52, 60)}, {(22, 18, 23, 24): [18, 23, 24], (50, 51, 52, 60): [60, 51, 52]}, {(22, 18, 23, 24): {22}, (50, 51, 52, 60): {50}}, {(22, 18, 23, 24): {24, 23}, (50, 51, 52, 60): {51, 52}}, {(22, 18, 23, 24): {((5.5, 4.330127018922193), (5.5, 6.06217782649107)), ((5.200000000000601, 4.330127018922193), (4.2999999999994, 6.928203230275509)), ((5.5, 4.330127018922193), (5.5, 4.330127018922193))}, (50, 51, 52, 60): {((11.7999999999994, 4.330127018922193), (12.7000000000006, 6.928203230275509)), ((11.5, 4.330127018922193), (11.5, 4.330127018922193)), ((11.5, 4.330127018922193), (11.5, 6.06217782649107))}}, {(22, 18, 23, 24): set(), (50, 51, 52, 60): set()}))

# The monster rotates its ranged AoE pattern as neccessary to attack the maximum number of charcters
def test_Scenario87():
    m=Monster(action_move=2, action_range=3)

    m.aoe[18] = True
    m.aoe[24] = True
    m.aoe[31] = True
    figures,contents,initiatives,walls = init_test()


    figures[15] = 'C'
    figures[16] = 'C'
    figures[17] = 'C'

    figures[60] = 'C'
    figures[67] = 'C'
    figures[75] = 'C'

    figures[37] = 'A'



    assert_answers(m, figures,contents,initiatives,walls,({(37, 15, 16, 17), (37, 60, 67, 75)}, {(37, 60, 67, 75): [60, 67, 75], (37, 15, 16, 17): [15, 16, 17]}, {(37, 60, 67, 75): {37}, (37, 15, 16, 17): {37}}, {(37, 60, 67, 75): {75, 67, 60}, (37, 15, 16, 17): {16, 17, 15}}, {(37, 15, 16, 17): {((7.6000000000003, 5.369357503464039), (4.8999999999997, 5.888972745733663)), ((7.75, 4.763139720814412), (4.75, 3.031088913245535)), ((7.6000000000003, 5.022947341949225), (4.8999999999997, 4.5033320996796))}, (37, 60, 67, 75): {((9.25, 5.629165124598852), (15.25, 9.093266739736604)), ((9.25, 5.629165124598852), (12.25, 7.3612159321677275)), ((9.25, 5.629165124598852), (13.75, 8.227241335952165))}}, {(37, 15, 16, 17): set(), (37, 60, 67, 75): set()}))

# Traps do not block ranged attacks. The monster stands still and attacks the character
def test_Scenario88():
    m=Monster(action_move=3, action_range=4)
    figures,contents,initiatives,walls = init_test()


    figures[10] = 'C'

    contents[22] = 'T'
    contents[23] = 'T'
    contents[24] = 'T'
    contents[25] = 'T'
    contents[26] = 'T'

    figures[38] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(38, 10)}, {(38, 10): []}, {(38, 10): {38}}, {(38, 10): {10}}, {(38, 10): {((7.5000000000005, 6.928203230276375), (3.4999999999995, 6.928203230274643))}}, {(38, 10): set()}))

# The monster focuses on the character it has the shortest path to an attack location for, avoiding traps if possible. The monster moves towards C20
def test_Scenario89():
    m=Monster(action_move=1)
    figures,contents,initiatives,walls = init_test()


    figures[17] = 'C'
    initiatives[17] = 10
    figures[53] = 'C'
    initiatives[53] = 20

    contents[22] = 'T'
    contents[23] = 'T'
    contents[24] = 'T'
    contents[25] = 'T'
    contents[26] = 'T'

    figures[31] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(38,)}, {(38,): []}, {(38,): {46}}, {(38,): {53}}, {(38,): set()}, {(38,): set()}))

# Traps do not block proximity. With both characters at equal pathing distance, the monster focuses on the character in closer proximity, C20
def test_Scenario90():
    m=Monster(action_move=1)
    figures,contents,initiatives,walls = init_test()


    figures[17] = 'C'
    initiatives[17] = 20
    figures[76] = 'C'
    initiatives[76] = 10

    contents[22] = 'T'
    contents[23] = 'T'
    contents[24] = 'T'
    contents[25] = 'T'
    contents[26] = 'T'

    figures[31] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(38,)}, {(38,): []}, {(38,): {68}}, {(38,): {76}}, {(38,): set()}, {(38,): set()}))

# Walls do block proximity. With both characters at equal pathing distance and proximity, the monster focuses on the character with the lower initiative, C10
def test_Scenario91():
    m=Monster(action_move=1)
    figures,contents,initiatives,walls = init_test()


    figures[17] = 'C'
    initiatives[17] = 20
    figures[76] = 'C'
    initiatives[76] = 10

    contents[22] = 'X'
    contents[23] = 'X'
    contents[24] = 'X'
    contents[25] = 'X'
    contents[26] = 'X'

    figures[31] = 'A'
    assert_answers(m, figures,contents,initiatives,walls,({(38,)}, {(38,): []}, {(38,): {68}}, {(38,): {76}}, {(38,): set()}, {(38,): set()}))

# The range of AoE attacks is not affected by walls. The monster attacks the character without moving by placing its AoE on the other side of the thin wall
def test_Scenario92():
    m=Monster(action_move=1, action_range=2)
    m.aoe[24] = True
    m.aoe[25] = True
    m.aoe[18] = True
    m.aoe[32] = True
    figures,contents,initiatives,walls = init_test()


    figures[29] = 'C'

    contents[9] = 'X'
    contents[23] = 'X'
    contents[51] = 'X'
    contents[65] = 'X'
    walls[16][1] = True
    walls[30][1] = True
    walls[44][1] = True
    walls[58][1] = True



    figures[32] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(32, 29)}, {(32, 29): [29, 30, 36, 37]}, {(32, 29): {32}}, {(32, 29): {29}}, {(32, 29): {((7.666666666666834, 7.216878364870611), (7.666666666666833, 3.175426480542653))}}, {(32, 29): set()}))

# Online test question #15
def test_Scenario93():
    m=Monster(action_move=2, action_range=3, action_target=3)
    figures,contents,initiatives,walls = init_test()


    figures[11] = 'C'
    initiatives[11] = 35
    figures[33] = 'C'
    initiatives[33] = 99
    figures[39] = 'C'
    initiatives[39] = 100
    figures[38] = 'C'
    initiatives[38] = 101

    contents[10] = 'O'
    contents[18] = 'O'

    contents[16] = 'T'

    figures[15] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(23, 11, 33, 39)}, {(23, 11, 33, 39): []}, {(23, 11, 33, 39): {23}}, {(23, 11, 33, 39): {11}}, {(23, 11, 33, 39): {((5.799999999999399, 6.06217782649107), (6.700000000000601, 8.660254037844386)), ((4.8999999999997, 5.888972745733663), (3.1000000000003, 7.967433714817354)),  ((6.1000000000003, 5.888972745733663), (7.8999999999997, 7.9674337148173535))}}, {(23, 11, 33, 39): set()}))

# Online test question #16
def test_Scenario94():
    m=Monster(action_move=4, action_target=3)
    figures,contents,initiatives,walls = init_test()


    figures[25] = 'C'
    initiatives[25] = 30
    figures[32] = 'C'
    initiatives[32] = 20
    figures[39] = 'C'
    initiatives[39] = 40
    figures[46] = 'C'
    initiatives[46] = 10

    figures[22] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(38, 32, 39, 46)}, {(38, 32, 39, 46): []}, {(38, 32, 39, 46): {38}}, {(38, 32, 39, 46): {32}}, {(38, 32, 39, 46): {((8.5, 7.794228634059947), (8.5, 7.794228634059947)), ((7.75, 7.361215932167728), (7.75, 7.361215932167728)), ((9.25, 7.3612159321677275), (9.25, 7.3612159321677275))}}, {(38, 32, 39, 46): set()}))

# Online test question #17
def test_Scenario95():
    m=Monster(action_move=4, action_target=3)
    figures,contents,initiatives,walls = init_test()


    figures[25] = 'C'
    initiatives[25] = 20
    figures[32] = 'C'
    initiatives[32] = 40
    figures[39] = 'C'
    initiatives[39] = 30
    figures[46] = 'C'
    initiatives[46] = 10

    figures[22] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(24, 25, 32)}, {(24, 25, 32): []}, {(24, 25, 32): {24}}, {(24, 25, 32): {25}}, {(24, 25, 32): {((5.5, 7.794228634059947), (5.5, 7.794228634059947)), ((6.25, 7.3612159321677275), (6.25, 7.3612159321677275))}}, {(24, 25, 32): set()}))

# Online test question #18
def test_Scenario96():
    m=Monster(action_move=4)
    m.aoe[17] = True
    m.aoe[9] = True
    figures,contents,initiatives,walls = init_test()


    figures[25] = 'C'
    initiatives[25] = 40
    figures[32] = 'C'
    initiatives[32] = 20
    figures[39] = 'C'
    initiatives[39] = 10
    figures[46] = 'C'
    initiatives[46] = 30

    figures[22] = 'A'



    assert_answers(m, figures,contents,initiatives,walls,({(24, 32, 39)}, {(24, 32, 39): [39, 32]}, {(24, 32, 39): {24}}, {(24, 32, 39): {32}}, {(24, 32, 39): {((6.25, 7.3612159321677275), (7.750000000000001, 8.227241335952165)), ((6.25, 7.3612159321677275), (6.25, 7.3612159321677275))}}, {(24, 32, 39): set()}))

# Online test question #19
def test_Scenario97():
    m=Monster(action_move=6, action_target=3)
    figures,contents,initiatives,walls = init_test()


    figures[25] = 'C'
    initiatives[25] = 30
    figures[32] = 'C'
    initiatives[32] = 20
    figures[39] = 'C'
    initiatives[39] = 40
    figures[46] = 'C'
    initiatives[46] = 10

    figures[22] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(38, 32, 39, 46)}, {(38, 32, 39, 46): []}, {(38, 32, 39, 46): {38}}, {(38, 32, 39, 46): {32}}, {(38, 32, 39, 46): {((8.5, 7.794228634059947), (8.5, 7.794228634059947)), ((7.75, 7.361215932167728), (7.75, 7.361215932167728)), ((9.25, 7.3612159321677275), (9.25, 7.3612159321677275))}}, {(38, 32, 39, 46): set()}))

# Difficult terrain requires two movement points to enter. The monster moves only three steps towards the character
def test_Scenario98():
    m=Monster(action_move=4)
    figures,contents,initiatives,walls = init_test()


    figures[52] = 'C'

    contents[24] = 'D'
    contents[23] = 'D'

    contents[29] = 'X'
    contents[30] = 'X'
    contents[32] = 'X'
    contents[33] = 'X'
    contents[34] = 'X'

    figures[10] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(31,)}, {(31,): []}, {(31,): {45, 46}}, {(31,): {52}}, {(31,): set()}, {(31,): set()}))

# Difficult terrain requires two movement points to enter. The monster moves only two steps towards the character
def test_Scenario99():
    m=Monster(action_move=4)
    figures,contents,initiatives,walls = init_test()


    figures[52] = 'C'

    contents[10] = 'D'
    contents[24] = 'D'
    contents[24] = 'D'
    contents[23] = 'D'
    contents[31] = 'D'

    contents[29] = 'X'
    contents[30] = 'X'
    contents[32] = 'X'
    contents[33] = 'X'
    contents[34] = 'X'

    figures[10] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(23,), (24,)}, {(23,): [], (24,): []}, {(23,): {45, 46}, (24,): {45, 46}}, {(23,): {52}, (24,): {52}}, {(23,): set(), (24,): set()}, {(23,): set(), (24,): set()}))

# The path through the difficult terrain and the path around the difficult terrain require equal movement. The players choose
def test_Scenario100():
    m=Monster(action_move=4)
    figures,contents,initiatives,walls = init_test()


    figures[52] = 'C'

    contents[17] = 'D'
    contents[18] = 'D'
    contents[24] = 'D'
    contents[23] = 'D'
    contents[31] = 'D'
    contents[37] = 'D'
    contents[38] = 'D'

    contents[29] = 'X'
    contents[30] = 'X'
    contents[32] = 'X'
    contents[33] = 'X'
    contents[34] = 'X'

    figures[10] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(23,), (24,), (21,)}, {(23,): [], (24,): [], (21,): []}, {(23,): {45, 46}, (24,): {45, 46}, (21,): {51, 45}}, {(23,): {52}, (24,): {52}, (21,): {52}}, {(23,): set(), (24,): set(), (21,): set()}, {(23,): set(), (24,): set(), (21,): set()}))

# The path around the difficult terrain is shorter than the path through the difficult terrain. The moster moves around it
def test_Scenario101():
    m=Monster(action_move=4)
    figures,contents,initiatives,walls = init_test()


    figures[52] = 'C'

    contents[17] = 'D'
    contents[18] = 'D'
    contents[24] = 'D'
    contents[23] = 'D'
    contents[31] = 'D'
    contents[37] = 'D'
    contents[38] = 'D'

    contents[30] = 'X'
    contents[32] = 'X'
    contents[33] = 'X'
    contents[34] = 'X'

    figures[10] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(29,)}, {(29,): []}, {(29,): {51, 45}}, {(29,): {52}}, {(29,): set()}, {(29,): set()}))

# Flying monsters ignore the effects of difficult terrain. The monster moves a full four steps towards the character
def test_Scenario102():
    m=Monster(action_move=4, flying=True)
    figures,contents,initiatives,walls = init_test()


    figures[52] = 'C'

    contents[24] = 'D'
    contents[23] = 'D'
    contents[31] = 'D'

    contents[29] = 'X'
    contents[30] = 'X'
    contents[32] = 'X'
    contents[33] = 'X'
    contents[34] = 'X'

    figures[10] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(37,), (38,)}, {(38,): [], (37,): []}, {(37,): {45}, (38,): {45, 46}}, {(37,): {52}, (38,): {52}}, {(37,): set(), (38,): set()}, {(37,): set(), (38,): set()}))

# Jumping monsters ignore the effects of difficult terrain, except on the last hex of movement. The monster moves a full four steps towards the character
def test_Scenario103():
    m=Monster(action_move=4, jumping=True)
    figures,contents,initiatives,walls = init_test()


    figures[52] = 'C'

    contents[24] = 'D'
    contents[23] = 'D'
    contents[31] = 'D'

    contents[29] = 'X'
    contents[30] = 'X'
    contents[32] = 'X'
    contents[33] = 'X'
    contents[34] = 'X'

    figures[10] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(37,), (38,)}, {(38,): [], (37,): []}, {(37,): {45}, (38,): {45, 46}}, {(37,): {52}, (38,): {52}}, {(37,): set(), (38,): set()}, {(37,): set(), (38,): set()}))

# In Gloomhaven, jumping monsters ignore the effects of difficult terrain, except on the last hex of movement. The monster moves only three steps towards the character
def test_Scenario104():
    m=Monster(action_move=4, jumping=True)
    figures,contents,initiatives,walls = init_test()


    figures[52] = 'C'

    contents[17] = 'D'
    contents[18] = 'D'
    contents[24] = 'D'
    contents[23] = 'D'
    contents[37] = 'D'
    contents[38] = 'D'

    contents[45] = 'D'
    contents[46] = 'D'
    contents[51] = 'D'

    contents[29] = 'X'
    contents[30] = 'X'
    contents[32] = 'X'
    contents[33] = 'X'
    contents[34] = 'X'

    figures[10] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(37,), (38,)}, {(38,): [], (37,): []}, {(37,): {45}, (38,): {45, 46}}, {(37,): {52}, (38,): {52}}, {(37,): set(), (38,): set()}, {(37,): set(), (38,): set()}))

# The monster does not avoid disadvantage when it cannot attack the character. The monster stops adjacent to the character
def test_Scenario105():
    m=Monster(action_move=2, action_range=2)
    figures,contents,initiatives,walls = init_test()


    figures[37] = 'C'

    walls[30][0] = True
    walls[30][5] = True
    walls[37][0] = True
    walls[37][1] = True
    walls[31][5] = True
    walls[44][1] = True

    figures[32] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(45,), (30,)}, {(45,): [], (30,): []}, {(45,): {51}, (30,): {29}}, {(45,): {37}, (30,): {37}}, {(45,): set(), (30,): set()}, {(45,): set(), (30,): set()}))

# There are two destinations that are equally valid assuming infinite movemnet for the jumping monster. THe players can choose either as the monster's destination. Because a jumping monster cannot end its movement on an obstacle, the monster will path around the obsticles. For one of the two destinations, the monster makes less progress towards the destination because the second step of movemnet does not take the monster closer to the destination
def test_Scenario106():
    m=Monster(action_move=2, jumping=True)
    figures,contents,initiatives,walls = init_test()


    figures[37] = 'C'

    contents[31] = 'O'
    contents[38] = 'O'

    figures[25] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(23,), (32,)}, {(32,): [], (23,): []}, {(23,): {30}, (32,): {45}}, {(23,): {37}, (32,): {37}}, {(23,): set(), (32,): set()}, {(23,): set(), (32,): set()}))

# A monster being on an obstacle does not allow its allies to move through it. The monster is blocked by the wall of obsticles. The monster will not move
def test_Scenario107():
    m=Monster(action_move=2)
    figures,contents,initiatives,walls = init_test()


    figures[37] = 'C'

    contents[21] = 'O'
    contents[22] = 'O'
    contents[23] = 'O'
    contents[24] = 'O'
    contents[25] = 'O'
    contents[26] = 'O'
    contents[27] = 'O'

    figures[24] = 'M'

    figures[17] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(17,)}, {(17,): []}, {(17,): {}}, {(17,): {}}, {(17,): set()}, {(17,): set()}))

# The flying monster will path through characters to reach an optimal attack position
def test_Scenario108():
    m=Monster(action_move=3, action_target=4, flying=True)
    figures,contents,initiatives,walls = init_test()


    figures[23] = 'C'
    initiatives[23] = 10
    figures[24] = 'C'
    initiatives[24] = 20
    figures[32] = 'C'
    initiatives[32] = 30
    figures[30] = 'C'
    initiatives[30] = 40

    figures[10] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(31, 23, 24, 30, 32)}, {(31, 23, 24, 30, 32): []}, {(31, 23, 24, 30, 32): {31}}, {(31, 23, 24, 30, 32): {23}}, {(31, 23, 24, 30, 32): {((7.0, 5.196152422706632), (7.0, 5.196152422706632)), ((6.25, 6.49519052838329), (6.25, 6.49519052838329)), ((7.0, 6.928203230275509), (7.0, 6.928203230275509)), ((6.25, 5.629165124598851), (6.25, 5.629165124598851))}}, {(31, 23, 24, 30, 32): set()}))

# The monster will use its extra attack to target its focus, using its aoe on secondary targets, because that targets the most characters
def test_Scenario109():
    m=Monster(action_move=2, action_range=3,action_target=2)
    m.aoe[24] = True
    m.aoe[25] = True
    figures,contents,initiatives,walls = init_test()


    figures[15] = 'C'
    initiatives[15] = 10
    figures[39] = 'C'
    initiatives[39] = 20
    figures[46] = 'C'
    initiatives[46] = 30

    figures[17] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(17, 15, 39, 46)}, {(17, 15, 39, 46): [39, 46]}, {(17, 15, 39, 46): {17}}, {(17, 15, 39, 46): {15}}, {(17, 15, 39, 46): {((4.75, 6.495190528383289), (7.750000000000001, 8.227241335952165)), ((4.0, 5.196152422706632), (4.0, 3.4641016151377544)), ((4.857142857142643, 6.309613656144139), (9.142857142857357, 7.546792804406879))}}, {(17, 15, 39, 46): set()}))

# A monster without an attack will move as if it had a melee attack
def test_Scenario110():
    m=Monster(action_move=2, action_range=3, action_target=0)
    figures,contents,initiatives,walls = init_test()


    figures[15] = 'C'

    figures[18] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(16,)}, {(16,): []}, {(16,): {16}}, {(16,): {15}}, {(16,): set()}, {(16,): set()}))

# The monster will step away to avoid disadvantage when making a range aoe attack
def test_Scenario111():
    m=Monster(action_move=2, action_range=1)
    m.aoe[24] = True
    m.aoe[25] = True
    figures,contents,initiatives,walls = init_test()


    figures[15] = 'C'

    figures[16] = 'A'



    assert_answers(m, figures,contents,initiatives,walls,({(9, 15), (17, 15), (23, 15)}, {(9, 15): [15, 16], (17, 15): [15, 16], (23, 15): [15, 16]}, {(23, 15): {23}, (17, 15): {17}, (9, 15): {9}}, {(23, 15): {15}, (17, 15): {15}, (9, 15): {15}}, {(23, 15): {((4.9999999999995, 4.33012701892306), (4.5000000000005, 3.4641016151368884))}, (17, 15): {((4.0, 5.196152422706632), (4.0, 3.4641016151377544))}, (9, 15): {((2.9999999999990004, 4.330127018922193), (3.5000000000010005, 3.4641016151377544))}}, {(23, 15): set(), (17, 15): set(), (9, 15): set()}))

# The monster will avoid the trap to attack the character
def test_Scenario112():
    m=Monster(action_move=3)
    figures,contents,initiatives,walls = init_test()


    figures[15] = 'C'

    contents[16] = 'T'

    figures[18] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(8, 15), (22, 15)}, {(8, 15): [], (22, 15): []}, {(8, 15): {8}, (22, 15): {22}}, {(8, 15): {15}, (22, 15): {15}}, {(8, 15): {((3.25, 3.031088913245535), (3.25, 3.031088913245535))}, (22, 15): {((4.75, 3.031088913245535), (4.75, 3.031088913245535))}}, {(8, 15): set(), (22, 15): set()}))

# The jumping monster will avoid the trap to attack the character
def test_Scenario113():
    m=Monster(action_move=3, jumping=True)
    figures,contents,initiatives,walls = init_test()


    figures[15] = 'C'

    contents[16] = 'T'

    figures[18] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(8, 15), (22, 15)}, {(8, 15): [], (22, 15): []}, {(8, 15): {8}, (22, 15): {22}}, {(8, 15): {15}, (22, 15): {15}}, {(8, 15): {((3.25, 3.031088913245535), (3.25, 3.031088913245535))}, (22, 15): {((4.75, 3.031088913245535), (4.75, 3.031088913245535))}}, {(8, 15): set(), (22, 15): set()}))

# The flying monster will ignore the trap to attack the character
def test_Scenario114():
    m=Monster(action_move=3, flying=True)
    figures,contents,initiatives,walls = init_test()


    figures[15] = 'C'

    contents[16] = 'T'

    figures[18] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(16, 15)}, {(16, 15): []}, {(16, 15): {16}}, {(16, 15): {15}}, {(16, 15): {((4.0, 3.4641016151377544), (4.0, 3.4641016151377544))}}, {(16, 15): set()}))

# With no other option, the monster will move onto the trap to attack the character
def test_Scenario115():
    m=Monster(action_move=3)
    figures,contents,initiatives,walls = init_test()


    figures[15] = 'C'

    contents[16] = 'T'
    contents[8] = 'T'
    contents[7] = 'T'
    contents[14] = 'T'
    contents[21] = 'T'
    contents[22] = 'T'

    figures[18] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(16, 15)}, {(16, 15): []}, {(16, 15): {16}}, {(16, 15): {15}}, {(16, 15): {((4.0, 3.4641016151377544), (4.0, 3.4641016151377544))}}, {(16, 15): set()}))

# AoE attacks require line of site. The monster will move around the wall
def test_Scenario116():
    m=Monster(action_move=3)
    m.aoe[25] = True
    figures,contents,initiatives,walls = init_test()


    figures[31] = 'C'

    contents[24] = 'X'
    contents[38] = 'X'
    walls[31][1] = True

    figures[32] = 'A'



    assert_answers(m, figures,contents,initiatives,walls,({(45,), (17,)}, {(45,): [], (17,): []}, {(45,): {37}, (17,): {23}}, {(45,): {31}, (17,): {31}}, {(45,): set(), (17,): set()}, {(45,): set(), (17,): set()}))

# The closest character with the lowest initiative is the monster's focus. The monster will place its AoE to attack its focus
def test_Scenario117():
    m=Monster(action_move=2, action_range=3)
    m.aoe[18] = True
    m.aoe[24] = True
    m.aoe[31] = True
    figures,contents,initiatives,walls = init_test()


    figures[16] = 'C'
    initiatives[16] = 10
    figures[17] = 'C'
    initiatives[17] = 20
    figures[18] = 'C'
    initiatives[18] = 30

    figures[58] = 'C'
    initiatives[58] = 70
    figures[59] = 'C'
    initiatives[59] = 10
    figures[60] = 'C'
    initiatives[60] = 10

    figures[35] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(35, 58, 59, 60), (35, 16, 17, 18)}, {(35, 16, 17, 18): [16, 17, 18], (35, 58, 59, 60): [58, 59, 60]}, {(35, 16, 17, 18): {35}, (35, 58, 59, 60): {35}}, {(35, 16, 17, 18): {16}, (35, 58, 59, 60): {59, 60}}, {(35, 58, 59, 60): {((9.25, 2.165063509461097), (12.25, 3.897114317029973)), ((9.142857142857357, 2.3506403817002486), (12.357142857142643, 5.4435882523596995)), ((9.062500000000375, 2.4898230358796125), (12.437499999999625, 7.036456405749211))}, (35, 16, 17, 18): {((7.75, 2.165063509461097), (4.75, 3.8971143170299736)), ((7.937499999999625, 2.4898230358796125), (4.562500000000375, 7.036456405749213)), ((7.857142857142644, 2.3506403817002486), (4.642857142857356, 5.4435882523596995))}}, {(35, 58, 59, 60): set(), (35, 16, 17, 18): set()}))

# The closest character with the lowest initiative is the monster's focus. The monster will place its AoE to attack its focus, even if other placements hit more targets
def test_Scenario118():
    m=Monster(action_move=2, action_range=3)
    m.aoe[18] = True
    m.aoe[24] = True
    m.aoe[31] = True
    figures,contents,initiatives,walls = init_test()


    figures[16] = 'C'
    initiatives[16] = 10

    figures[58] = 'C'
    initiatives[58] = 70
    figures[59] = 'C'
    initiatives[59] = 10
    figures[60] = 'C'
    initiatives[60] = 10

    figures[35] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(35, 16), (35, 58, 59, 60)}, {(35, 16): [16, 23, 31], (35, 58, 59, 60): [58, 59, 60]}, {(35, 16): {35}, (35, 58, 59, 60): {35}}, {(35, 16): {16}, (35, 58, 59, 60): {59, 60}}, {(35, 58, 59, 60): {((9.25, 2.165063509461097), (12.25, 3.897114317029973)), ((9.142857142857357, 2.3506403817002486), (12.357142857142643, 5.4435882523596995)), ((9.062500000000375, 2.4898230358796125), (12.437499999999625, 7.036456405749211))}, (35, 16): {((7.75, 2.165063509461097), (4.75, 3.8971143170299736))}}, {(35, 58, 59, 60): set(), (35, 16): set()}))

# There are two equally good focuses, so the players can choose which group the monster attacks. This is true even though choosing one of the focuses allows the monster to attack more targets
def test_Scenario119():
    m=Monster(action_move=2, action_range=3)
    m.aoe[18] = True
    m.aoe[24] = True
    m.aoe[31] = True
    figures,contents,initiatives,walls = init_test()


    figures[16] = 'C'
    initiatives[16] = 10
    figures[17] = 'C'
    initiatives[17] = 20
    figures[18] = 'C'
    initiatives[18] = 30

    figures[58] = 'C'
    initiatives[58] = 10

    figures[35] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(35, 58), (35, 16, 17, 18)}, {(35, 16, 17, 18): [16, 17, 18], (35, 58): [58, 65, 73]}, {(35, 16, 17, 18): {35}, (35, 58): {35}}, {(35, 16, 17, 18): {16}, (35, 58): {58}}, {(35, 58): {((9.25, 2.165063509461097), (12.25, 3.897114317029973))}, (35, 16, 17, 18): {((7.75, 2.165063509461097), (4.75, 3.8971143170299736)), ((7.937499999999625, 2.4898230358796125), (4.562500000000375, 7.036456405749213)), ((7.857142857142644, 2.3506403817002486), (4.642857142857356, 5.4435882523596995))}}, {(35, 58): set(), (35, 16, 17, 18): set()}))

# There are two equally good focuses, so the players can choose which group the monster attacks. This is true even though choosing one of the focuses allows the monster to attack more favorable targets
def test_Scenario120():
    m=Monster(action_move=2, action_range=3)
    m.aoe[18] = True
    m.aoe[24] = True
    m.aoe[31] = True
    figures,contents,initiatives,walls = init_test()


    figures[16] = 'C'
    initiatives[16] = 10
    figures[17] = 'C'
    initiatives[17] = 20
    figures[18] = 'C'
    initiatives[18] = 30

    figures[58] = 'C'
    initiatives[58] = 10
    figures[59] = 'C'
    initiatives[59] = 80
    figures[60] = 'C'
    initiatives[60] = 90

    figures[35] = 'A'


    assert_answers(m, figures,contents,initiatives,walls,({(35, 58, 59, 60), (35, 16, 17, 18)}, {(35, 16, 17, 18): [16, 17, 18], (35, 58, 59, 60): [58, 59, 60]}, {(35, 16, 17, 18): {35}, (35, 58, 59, 60): {35}}, {(35, 16, 17, 18): {16}, (35, 58, 59, 60): {58}}, {(35, 58, 59, 60): {((9.25, 2.165063509461097), (12.25, 3.897114317029973)), ((9.142857142857357, 2.3506403817002486), (12.357142857142643, 5.4435882523596995)), ((9.062500000000375, 2.4898230358796125), (12.437499999999625, 7.036456405749211))}, (35, 16, 17, 18): {((7.75, 2.165063509461097), (4.75, 3.8971143170299736)), ((7.937499999999625, 2.4898230358796125), (4.562500000000375, 7.036456405749213)), ((7.857142857142644, 2.3506403817002486), (4.642857142857356, 5.4435882523596995))}}, {(35, 58, 59, 60): set(), (35, 16, 17, 18): set()}))

# The monster will place its AoE to hit its focus and the most favorable set of additional targets
def test_Scenario121():
    m=Monster(action_move=2, action_range=3)
    m.aoe[18] = True
    m.aoe[24] = True
    m.aoe[31] = True
    figures,contents,initiatives,walls = init_test()


    figures[58] = 'C'
    initiatives[58] = 10
    figures[59] = 'C'
    initiatives[59] = 20
    figures[60] = 'C'
    initiatives[60] = 30
    figures[64] = 'C'
    initiatives[64] = 40
    figures[71] = 'C'
    initiatives[71] = 50

    figures[35] = 'A'



    assert_answers(m, figures,contents,initiatives,walls,({(35, 58, 59, 60)}, {(35, 58, 59, 60): [58, 59, 60]}, {(35, 58, 59, 60): {35}}, {(35, 58, 59, 60): {58}}, {(35, 58, 59, 60): {((9.25, 2.165063509461097), (12.25, 3.897114317029973)), ((9.142857142857357, 2.3506403817002486), (12.357142857142643, 5.4435882523596995)), ((9.062500000000375, 2.4898230358796125), (12.437499999999625, 7.036456405749211))}}, {(35, 58, 59, 60): set()}))

# A monster with an AoE attack and a target count of zero will move as if it had a melee attack and not attack
def test_Scenario122():
    m=Monster(action_move=2, action_range=3, action_target=0)

    m.aoe[18] = True
    m.aoe[25] = True
    m.aoe[32] = True
    figures,contents,initiatives,walls = init_test()


    figures[59] = 'C'

    figures[36] = 'A'


    assert_answers(m, figures,contents,initiatives,walls,({(51,)}, {(51,): []}, {(51,): {51}}, {(51,): {59}}, {(51,): set()}, {(51,): set()}))

# All of vertices of the monster's starting hex are touching walls, so the monster does not have line of sight to any other hex. It will step forward to gain los and attack the character
def test_Scenario123():
    m=Monster(action_move=2, action_range=4)
    figures,contents,initiatives,walls = init_test()


    figures[36] = 'C'

    contents[52] = 'X'
    contents[66] = 'X'
    contents[58] = 'X'

    figures[59] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(59, 36)}, {(59, 36): []}, {(59, 36): {59}}, {(59, 36): {36}}, {(59, 36): {((12.25, 5.629165124598851), (9.25, 3.897114317029974))}}, {(59, 36): set()}))

# If a monster can attack its focus this turn, it will move to do so. That is true even when there is a more optimal attack location, if it cannot reach that more optimal location this turn
def test_Scenario124():
    m=Monster(action_move=2, action_target=2)
    figures,contents,initiatives,walls = init_test()


    figures[26] = 'C'
    figures[39] = 'C'

    contents[29] = 'O'
    contents[22] = 'O'
    contents[16] = 'O'
    contents[17] = 'O'
    contents[18] = 'O'
    contents[19] = 'O'
    contents[20] = 'O'
    contents[35] = 'O'
    contents[43] = 'O'
    contents[44] = 'O'
    contents[45] = 'O'
    contents[46] = 'O'
    contents[47] = 'O'
    contents[27] = 'O'
    contents[34] = 'O'
    contents[40] = 'O'
    contents[31] = 'O'
    contents[32] = 'O'

    figures[36] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(38, 39)}, {(38, 39): []}, {(38, 39): {38}}, {(38, 39): {39}}, {(38, 39): {((8.5, 7.794228634059947), (8.5, 7.794228634059947))}}, {(38, 39): set()}))

# If a monster cannot attack its focus this turn, it will move towards the most optimal attack location. That is true even if there is a closer attack location that is less optimal
def test_Scenario125():
    m=Monster(action_move=1, action_target=2)
    figures,contents,initiatives,walls = init_test()


    figures[26] = 'C'
    figures[39] = 'C'

    contents[29] = 'O'
    contents[22] = 'O'
    contents[16] = 'O'
    contents[17] = 'O'
    contents[18] = 'O'
    contents[19] = 'O'
    contents[20] = 'O'
    contents[35] = 'O'
    contents[43] = 'O'
    contents[44] = 'O'
    contents[45] = 'O'
    contents[46] = 'O'
    contents[47] = 'O'
    contents[27] = 'O'
    contents[34] = 'O'
    contents[40] = 'O'
    contents[31] = 'O'
    contents[32] = 'O'

    figures[36] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(30,)}, {(30,): []}, {(30,): {33}}, {(30,): {39}}, {(30,): set()}, {(30,): set()}))

# If the monster has multiple attack options that target its focus plus a maximum number of additional charcters, it will favor additional targets that are closest in proximty first, then it will favor targets that have lower initiative. In this case, C20 is favored over C30 due to initiative. Note that if secondary targets were instead ranked based on their quality as a focus, C30 would have been favored. That is because only two steps are required to attack C30 individually, while three steps are required to attack C20 due to the obstacle. See this ruling (https://boardgamegeek.com/article/29431623#29431623). Still looking for full clarity (https://boardgamegeek.com/article/29455803#29455803)
def test_Scenario126():
    m=Monster(action_move=3)

    m.aoe[25] = True
    m.aoe[26] = True
    figures,contents,initiatives,walls = init_test()


    figures[33] = 'C'
    initiatives[33] = 30
    figures[39] = 'C'
    initiatives[39] = 10
    figures[47] = 'C'
    initiatives[47] = 20

    contents[45] = 'O'

    figures[36] = 'A'


    assert_answers(m, figures,contents,initiatives,walls,({(32, 39, 47)}, {(32, 39, 47): [39, 47]}, {(32, 39, 47): {32}}, {(32, 39, 47): {39}}, {(32, 39, 47): {((7.75, 8.227241335952165), (9.25, 9.093266739736604)), ((7.750000000000001, 8.227241335952165), (7.750000000000001, 8.227241335952165))}}, {(32, 39, 47): set()}))

# The players can choose either of the monster's two desintations, including the destination on difficult terrain, even though the monster can make less progress towards that destinatino. See ruling here (https://boardgamegeek.com/thread/2014493/monster-movement-question)
def test_Scenario127():
    m=Monster(action_move=2)
    figures,contents,initiatives,walls = init_test()


    figures[39] = 'C'

    contents[38] = 'D'

    figures[36] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(45,), (31,), (37,)}, {(45,): [], (31,): [], (37,): []}, {(45,): {46}, (31,): {32}, (37,): {38}}, {(45,): {39}, (31,): {39}, (37,): {39}}, {(45,): set(), (31,): set(), (37,): set()}, {(45,): set(), (31,): set(), (37,): set()}))

# The players can choose either of the monster's two desintations, even though the monster can only make progress towards one of them. See ruling here (https://boardgamegeek.com/thread/2014493/monster-movement-question)
def test_Scenario128():
    m=Monster(action_move=1)
    figures,contents,initiatives,walls = init_test()


    figures[39] = 'C'
    figures[31] = 'M'

    contents[38] = 'O'

    figures[37] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(45,), (37,)}, {(37,): [], (45,): []}, {(45,): {46}, (37,): {32}}, {(45,): {39}, (37,): {39}}, {(45,): set(), (37,): set()}, {(45,): set(), (37,): set()}))

# The players can choose any of the monster's three desintations, even though the monster can only make progress towards two of them. See ruling here (https://boardgamegeek.com/thread/2014493/monster-movement-question)
def test_Scenario129():
    m=Monster(action_move=1)
    figures,contents,initiatives,walls = init_test()


    figures[40] = 'C'
    figures[31] = 'M'

    contents[38] = 'O'

    figures[37] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(45,), (37,)}, {(37,): [], (45,): []}, {(45,): {47, 39}, (37,): {33}}, {(45,): {40}, (37,): {40}}, {(45,): set(), (37,): set()}, {(45,): set(), (37,): set()}))

# With only a single destination, the monster takes the best path to that destination. The players cannot choose to have the monster take the path along which the monster cannot make progress. Compare to scenario #129
def test_Scenario130():
    m=Monster(action_move=1)
    figures,contents,initiatives,walls = init_test()


    figures[40] = 'C'
    figures[31] = 'M'

    contents[33] = 'O'
    contents[38] = 'O'
    contents[47] = 'O'

    figures[37] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(45,)}, {(45,): []}, {(45,): {39}}, {(45,): {40}}, {(45,): set()}, {(45,): set()}))

# Large number of walls and characters, high target attack, large range and move, and a large aoe to use when timing optimizations
def test_Scenario131():
    m=Monster(action_move=7,action_range=7, action_target=5)
    m.aoe[17] = True
    m.aoe[18] = True
    m.aoe[23] = True
    m.aoe[24] = True
    m.aoe[25] = True
    m.aoe[31] = True
    m.aoe[32] = True
    figures,contents,initiatives,walls = init_test()

    figures[8] = 'C'
    figures[17] = 'C'
    figures[23] = 'C'
    figures[26] = 'C'
    figures[40] = 'C'
    figures[46] = 'C'
    figures[51] = 'C'
    figures[54] = 'C'
    figures[57] = 'C'
    figures[58] = 'C'
    figures[68] = 'C'
    figures[80] = 'C'
    figures[90] = 'C'
    figures[92] = 'C'
    figures[94] = 'C'
    figures[102] = 'C'

    contents[9] = 'X'
    contents[25] = 'X'
    contents[30] = 'X'
    contents[38] = 'X'
    contents[44] = 'X'
    contents[47] = 'X'
    contents[50] = 'X'
    contents[53] = 'X'
    contents[64] = 'X'
    contents[65] = 'X'
    contents[75] = 'X'
    contents[76] = 'X'
    contents[78] = 'X'
    contents[88] = 'X'
    contents[89] = 'X'
    contents[93] = 'X'
    contents[99] = 'X'
    contents[104] = 'X'

    figures[37] = 'A'

    gmap = GloomhavenMap(16, 7, m,figures,contents, initiatives,walls, Rule(2))
    scenario = Solver(Rule(2),gmap)
    scenario.logging=False
    scenario.calculate_monster_move()
    assert 1==1
  
# The monster will take a longer path to avoid traps. That is true even if it means not being able to attack its focus this turn
def test_Scenario132():
    m=Monster(action_move=2)
    figures,contents,initiatives,walls = init_test()


    figures[24] = 'C'

    contents[22] = 'T'

    contents[30] = 'O'
    contents[31] = 'O'
    contents[33] = 'O'

    contents[28] = 'O'
    contents[21] = 'O'
    contents[15] = 'O'
    contents[16] = 'O'
    contents[17] = 'O'
    contents[18] = 'O'
    contents[25] = 'O'
    contents[35] = 'O'
    contents[43] = 'O'
    contents[44] = 'O'
    contents[45] = 'O'
    contents[46] = 'O'
    contents[39] = 'O'

    figures[29] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(37,)}, {(37,): []}, {(37,): {32}}, {(37,): {24}}, {(37,): set()}, {(37,): set()}))

# The monster first uses proximity to rank secondary targets, before initiative. Because of the wall line between the monster and C10, C10 is two proximity steps away. Thus, the monster prefers C30 as its second target
def test_Scenario133():
    m=Monster(action_move=1, action_range=2, action_target=2)
    figures,contents,initiatives,walls = init_test()


    figures[38] = 'C'
    initiatives[38] = 10
    figures[44] = 'C'
    initiatives[44] = 30
    figures[45] = 'C'
    initiatives[45] = 20

    contents[59] = 'X'
    contents[73] = 'X'
    contents[31] = 'X'
    contents[17] = 'X'

    walls[23][1] = True
    walls[37][1] = True
    walls[51][1] = True
    walls[65][1] = True

    figures[30] = 'M'
    figures[36] = 'M'

    figures[37] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({ ( 37, 38, 45 )}, { ( 37, 38, 45 ): []}, {( 37, 38, 45 ): {37}}, { ( 37, 38, 45 ): {38}}, { ( 37, 38, 45 ): {((9.166666666666833, 5.77350269189597), (9.166666666666833, 6.35085296108617)), ((9.297619047618953, 5.546686514714784), (9.297619047618953, 5.546686514714784))}}, { ( 37, 38, 45 ): set()}))

# Have clarification. Must measure range around thin wall. This answer is wrong. Waiting for clarification. See https://boardgamegeek.com/thread/2020826/question-about-measuring-range-aoe-attacks and https://boardgamegeek.com/thread/2020622/ranged-aoe-and-wall-hexe
def test_Scenario134():
    m=Monster(action_move=0, action_range=2)
    m.aoe[25] = True
    m.aoe[24] = True
    m.aoe[31] = True
    figures,contents,initiatives,walls = init_test()


    figures[47] = 'C'

    contents[59] = 'X'
    contents[73] = 'X'
    contents[31] = 'X'
    contents[17] = 'X'

    walls[23][1] = True
    walls[37][1] = True
    walls[51][1] = True
    walls[65][1] = True

    figures[36] = 'A'



    assert_answers(m, figures,contents,initiatives,walls,({(36,)}, {(36,): []}, {(36,): {44, 37}}, {(36,): {47}}, {(36,): set()}, {(36,): set()}))

# Have clarification. Cannot use wall as target point for aoe. This answer is wrong. Waiting for clarification. See https://boardgamegeek.com/thread/2020826/question-about-measuring-range-aoe-attacks and https://boardgamegeek.com/thread/2020622/ranged-aoe-and-wall-hexe
def test_Scenario135():
    m=Monster(action_move=0,action_range=2)
    m.aoe[25] = True
    m.aoe[24] = True
    m.aoe[31] = True
    figures,contents,initiatives,walls = init_test()


    figures[47] = 'C'

    contents[59] = 'X'
    contents[73] = 'X'
    contents[31] = 'X'
    contents[17] = 'X'
    contents[38] = 'X'

    walls[23][1] = True
    walls[51][1] = True
    walls[65][1] = True

    figures[36] = 'A'



    assert_answers(m, figures,contents,initiatives,walls,({(36,)}, {(36,): []}, {(36,): {44, 37}}, {(36,): {47}}, {(36,): set()}, {(36,): set()}))

# Have clarification. Cannot use wall as target point for aoe. This answer is wrong. Waiting for clarification. See https://boardgamegeek.com/thread/2020826/question-about-measuring-range-aoe-attacks and https://boardgamegeek.com/thread/2020622/ranged-aoe-and-wall-hexe
def test_Scenario136():
    m=Monster(action_move=0,action_range=2)
    m.aoe[25] = True
    m.aoe[24] = True
    m.aoe[31] = True
    figures,contents,initiatives,walls = init_test()


    figures[47] = 'C'

    contents[59] = 'X'
    contents[73] = 'X'
    contents[31] = 'X'
    contents[17] = 'X'
    contents[38] = 'X'
    contents[37] = 'X'

    walls[23][1] = True
    walls[51][1] = True
    walls[65][1] = True

    figures[36] = 'A'



    assert_answers(m, figures,contents,initiatives,walls,({(36,)}, {(36,): []}, {(36,): {44}}, {(36,): {47}}, {(36,): set()}, {(36,): set()}))

# https://boardgamegeek.com/article/29498431#2949843
def test_Scenario137():
    m=Monster(action_move=5,action_range=2, action_target=3)
    figures,contents,initiatives,walls = init_test()


    figures[53] = 'C'
    initiatives[53] = 10
    figures[34] = 'C'
    initiatives[34] = 50
    figures[24] = 'C'
    initiatives[24] = 40
    figures[76] = 'C'
    initiatives[76] = 30
    figures[74] = 'C'
    initiatives[74] = 20

    figures[49] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(67, 53, 74, 76)}, {(67, 53, 74, 76): []}, {(67, 53, 74, 76): {67}}, {(67, 53, 74, 76): {53}}, {(67, 53, 74, 76): {((15.000000000000501, 9.526279441627958), (15.4999999999995, 10.39230484541413)), ((13.500000000000501, 8.660254037845252), (12.499999999999499, 8.660254037843519)), ((15.25, 8.227241335952165), (15.25, 8.227241335952165))}}, {(67, 53, 74, 76): set()}))

# Monsters are willing to move farther to avoid disadvantage against secondary targets
def test_Scenario138():
    m=Monster(action_move=6,action_range=2, action_target=3)
    figures,contents,initiatives,walls = init_test()


    figures[53] = 'C'
    initiatives[53] = 10
    figures[38] = 'C'
    initiatives[38] = 30
    figures[26] = 'C'
    initiatives[26] = 20

    figures[49] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(40, 26, 38, 53)}, {(40, 26, 38, 53): []}, {(40, 26, 38, 53): {40}}, {(40, 26, 38, 53): {53}}, {(40, 26, 38, 53): {((9.25, 9.959292143521044), (10.75, 9.093266739736606)), ((8.5, 9.526279441628825), (8.5, 7.794228634059947)), ((7.500000000000501, 10.392304845414131), (6.499999999999499, 10.392304845412397))}}, {(40, 26, 38, 53): set()}))

# Monsters are willing to move farther to avoid disadvantage against secondary targets; but this one is muddled
def test_Scenario139():
    m=Monster(action_move=6,action_range=2, action_target=3, muddled=True)
    figures,contents,initiatives,walls = init_test()


    figures[53] = 'C'
    initiatives[53] = 10
    figures[38] = 'C'
    initiatives[38] = 30
    figures[26] = 'C'
    initiatives[26] = 20

    figures[49] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(39, 26, 38, 53)}, {(39, 26, 38, 53): []}, {(39, 26, 38, 53): {39}}, {(39, 26, 38, 53): {53}}, {(39, 26, 38, 53): {((8.5, 7.794228634059947), (8.5, 7.794228634059947)), ((7.75, 9.093266739736606), (6.25, 9.959292143521044)), ((9.499999999999499, 8.660254037843519), (10.500000000000501, 8.660254037845252))}}, {(39, 26, 38, 53): set()}))

# Monsters are willing to move farther to avoid disadvantage against secondary targets; but this one is muddled
def test_Scenario140():
    m=Monster(action_move=5,action_range=2, action_target=3)
    figures,contents,initiatives,walls = init_test()


    figures[53] = 'C'
    initiatives[53] = 10
    figures[38] = 'C'
    initiatives[38] = 30
    figures[26] = 'C'
    initiatives[26] = 20

    figures[49] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(39, 26, 38, 53)}, {(39, 26, 38, 53): []}, {(39, 26, 38, 53): {39}}, {(39, 26, 38, 53): {53}}, {(39, 26, 38, 53): {((8.5, 7.794228634059947), (8.5, 7.794228634059947)), ((7.75, 9.093266739736606), (6.25, 9.959292143521044)), ((9.499999999999499, 8.660254037843519), (10.500000000000501, 8.660254037845252))}}, {(39, 26, 38, 53): set()}))

# Monster picks his secondary targets based on how far it must move to attack them, then proximity, then initiative. Here both groups can be attacked in five steps. It picks the left targets due to proximty. It ends up moving six steps to avoid disadvantage, even though it could have attacked the right targets without disadvantage in five moves. That is because targets are picked based on distance to attack. Only after picking targets does the monster adjust its destination based on avoiding disadvantage
def test_Scenario141():
    m=Monster(action_move=6,action_range=2, action_target=3)
    figures,contents,initiatives,walls = init_test()


    figures[53] = 'C'
    initiatives[53] = 10
    figures[32] = 'C'
    initiatives[32] = 30
    figures[26] = 'C'
    initiatives[26] = 20
    figures[81] = 'C'
    initiatives[81] = 30
    figures[82] = 'C'
    initiatives[82] = 20

    figures[49] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(67, 53, 81, 82 )}, {(67, 53, 81, 82 ): []}, {(67, 53, 81, 82 ): {67}}, {(67, 53, 81, 82 ): {53}}, {(67, 53, 81, 82 ): {  ((15.25, 9.093266739736606), (16.75, 9.959292143521044)),  ((13.500000000000501, 8.660254037845252), (12.499999999999499, 8.660254037843519)),  ((15.499999999999499, 8.660254037843519), (16.5000000000005, 8.660254037845252))}}, {(67, 53, 81, 82 ): set()}))

# Tests a bug in the line-line collision detection causing all colinear line segments to report as colliding
def test_Scenario142():
    m=Monster(action_move=0,action_range=3,)
    figures,contents,initiatives,walls = init_test()


    figures[32] = 'C'

    contents[23] = 'X'
    contents[24] = 'X'
    contents[25] = 'X'
    contents[33] = 'X'
    contents[39] = 'X'
    contents[47] = 'X'
    contents[51] = 'X'
    contents[53] = 'X'

    figures[52] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(52, 32)}, {(52, 32): []}, {(52, 32): {52}}, {(52, 32): {32}}, {(52, 32): {((10.536666666667093, 6.991711759887107), (7.746666666666673, 7.355442429475843))}}, {(52, 32): set()}))

# Monster does not suffer disadvantage against an adjacent target if the range to that target is two
def test_Scenario143():
    m=Monster(action_move=2,action_range=2)
    figures,contents,initiatives,walls = init_test()


    figures[32] = 'C'

    contents[23] = 'X'
    contents[24] = 'X'
    contents[25] = 'X'
    contents[51] = 'X'
    contents[52] = 'X'
    contents[53] = 'X'

    walls[31][1] = True
    walls[45][1] = True

    figures[31] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(31, 32)}, {(31, 32): []}, {(31, 32): {31}}, {(31, 32): {32}}, {(31, 32): {((7.666666666666834, 6.639528095680407), (7.666666666666833, 7.2168783648706105))}}, {(31, 32): set()}))

# trap test
def test_Scenario144():
    m=Monster(action_move=2)
    figures,contents,initiatives,walls = init_test()


    figures[37] = 'C'

    contents[2] = 'X'
    contents[3] = 'X'
    contents[8] = 'X'
    contents[10] = 'X'
    contents[15] = 'X'
    contents[18] = 'X'
    contents[28] = 'X'
    contents[33] = 'X'
    contents[35] = 'X'
    contents[36] = 'X'
    contents[38] = 'X'
    contents[39] = 'X'
    contents[44] = 'X'
    contents[45] = 'X'

    contents[16] = 'T'
    contents[17] = 'T'
    contents[21] = 'T'
    contents[22] = 'T'
    contents[23] = 'T'
    contents[24] = 'T'
    contents[25] = 'T'
    contents[29] = 'T'
    contents[30] = 'T'
    contents[31] = 'T'
    contents[32] = 'T'

    walls[25][1] = True
    walls[25][2] = True
    walls[21][3] = True
    walls[21][4] = True

    figures[9] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(23,), (24,), (22,)}, {(22,): [], (23,): [], (24,): []}, {(23,): {30, 31}, (24,): {31}, (22,): {30}}, {(23,): {37}, (24,): {37}, (22,): {37}}, {(23,): set(), (24,): set(), (22,): set()}, {(23,): set(), (24,): set(), (22,): set()}))

# The monster will choose to close the distance to its destination along a path that minimizes the number of traps it will trigger
def test_Scenario145():
    m=Monster(action_move=3)
    figures,contents,initiatives,walls = init_test()


    figures[34] = 'C'

    contents[28] = 'X'
    contents[21] = 'X'
    contents[15] = 'X'
    contents[16] = 'X'
    contents[17] = 'X'
    contents[18] = 'X'
    contents[19] = 'X'
    contents[20] = 'X'
    contents[27] = 'X'
    contents[35] = 'X'
    contents[43] = 'X'
    contents[44] = 'X'
    contents[45] = 'X'
    contents[46] = 'X'
    contents[47] = 'X'
    contents[48] = 'X'
    contents[31] = 'X'
    contents[32] = 'X'
    contents[41] = 'X'

    contents[23] = 'T'
    contents[25] = 'T'
    contents[39] = 'T'

    figures[29] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(38,)}, {(38,): []}, {(38,): {40, 33}}, {(38,): {34}}, {(38,): set()}, {(38,): set()}))

# Monster values traps triggered on later turns equal to those triggered on this turn
def test_Scenario146():
    m=Monster(action_move=3)
    figures,contents,initiatives,walls = init_test()


    figures[32] = 'C'

    contents[8] = 'X'
    contents[9] = 'X'
    contents[10] = 'X'
    contents[11] = 'X'
    contents[19] = 'X'
    contents[23] = 'X'
    contents[24] = 'X'
    contents[15] = 'X'
    contents[21] = 'X'
    contents[28] = 'X'
    contents[35] = 'X'
    contents[43] = 'X'
    contents[50] = 'X'
    contents[31] = 'X'
    contents[37] = 'X'
    contents[38] = 'X'
    contents[39] = 'X'
    contents[51] = 'X'

    contents[25] = 'T'
    contents[18] = 'T'
    contents[36] = 'T'
    contents[44] = 'T'

    figures[30] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(17,)}, {(17,): []}, {(17,): {25}}, {(17,): {32}}, {(17,): set()}, {(17,): set()}))

# Tests los angles from vertices with walls
def test_Scenario147():
    m=Monster(action_move=0, action_range=4)
    figures,contents,initiatives,walls = init_test()


    figures[18] = 'C'

    walls[12][4] = True
    walls[12][5] = True

    figures[12] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(12,)}, {(12,): []}, {(12,): {13, 20, 5, 6}}, {(12,): {18}}, {(12,): set()}, {(12,): set()}))

# Simple test of Frosthaven hex to hex (not vertex to vertex) line of sight
def test_Scenario148():
    m=Monster(action_move=0,action_range=6)
    figures,contents,initiatives,walls = init_test()


    figures[75] = 'C'

    walls[47][2] = True
    walls[47][5] = True

    figures[33] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(33, 75)}, {(33, 75): []}, {(33, 75): {33}}, {(33, 75): {75}}, {(33, 75): {((7.876190476190224, 9.311835055929384), (15.276190476190424, 10.004655378957281))}}, {(33, 75): set()}))

# Test Frosthaven hex-to-hex los algorithm for walls that are parallel to the sightline
def test_Scenario149():
    m=Monster(action_move=0,action_range=6)
    figures,contents,initiatives,walls = init_test()


    figures[11] = 'C'

    walls[33][4] = True
    walls[33][5] = True
    walls[32][2] = True

    figures[53] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(53,)}, {(53,): []}, {(53,): {46, 52, 54, 47}}, {(53,): {11}}, {(53,): set()}, {(53,): set()}))

# Line-of-sight test that is very close to fully blocked
def test_Scenario150():
    m=Monster(action_move=0,action_range=9)
    figures,contents,initiatives,walls = init_test()


    figures[31] = 'C'

    contents[32] = 'X'
    contents[52] = 'X'
    contents[61] = 'X'
    contents[66] = 'X'
    contents[88] = 'X'

    figures[89] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(89, 31)}, {(89, 31): []}, {(89, 31): {89}}, {(89, 31): {31}}, {(89, 31): {((18.256983240223448, 9.971387470389518), (7.555555555555945, 6.831978185409897))}}, {(89, 31): set()}))

# Monsters slide along icy terrain
def test_Scenario151():
    m=Monster(action_move=1)
    figures,contents,initiatives,walls = init_test()

    figures[38] = 'C'
    initiatives[38] = 1
    contents[19] = 'I'
    contents[25] = 'I'

    figures[12] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(32, 38)}, {(32, 38): []}, {(32, 38): {32}}, {(32, 38): {38}}, {(32, 38): {((7.75, 7.361215932167728), (7.75, 7.361215932167728))}}, {(32, 38): set()}))

# Flying monsters do not slide
def test_Scenario152():
    m=Monster(action_move=1,flying=True)
    figures,contents,initiatives,walls = init_test()
    figures[38] = 'C'
    initiatives[38] = 1
    contents[19] = 'I'
    contents[25] = 'I'

    figures[12] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(19,)}, {(19,): []}, {(19,): {32}}, {(19,): {38}}, {(19,): set()}, {(32, 38): set()}))

# Sliding stops at figures
def test_Scenario153():
    m=Monster(action_move=2)
    figures,contents,initiatives,walls = init_test()
    figures[38] = 'C'
    initiatives[38] = 1
    contents[19] = 'I'
    contents[25] = 'I'
    contents[32] = 'I'
    figures[12] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(32, 38)}, {(32, 38): []}, {(32, 38): {32}}, {(32, 38): {38}}, {(32, 38): {((7.75, 7.361215932167728), (7.75, 7.361215932167728))}}, {(32, 38): set()}))

# Monster uses ice to reach target then moves out of disadvantage
def test_Scenario154():
    m=Monster(action_move=2,action_range=2)
    figures,contents,initiatives,walls = init_test()
    figures[38] = 'C'
    initiatives[38] = 1
    contents[19] = 'I'
    contents[25] = 'I'
    contents[32] = 'I'
    contents[33] = 'I'
    contents[39] = 'I'
    figures[12] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(24, 38),(47, 38)}, {(24, 38): [],(47, 38): []}, {(24, 38): {24},(47, 38): {47}}, {(24, 38): {38},(47, 38): {38}}, {(24, 38): {((6.4999999999995, 6.928203230274643), (7.5000000000005, 6.928203230276375))},(47, 38): {((9.499999999999499, 8.660254037845252), (9.0000000000005, 7.794228634059082))}}, {(24, 38): set(),(24, 47): set()}))

# Monster uses ice to minimize distance to target
def test_Scenario155():
    m=Monster(action_move=3)
    figures,contents,initiatives,walls = init_test()

    figures[21] = 'C'
    initiatives[21] = 1

    contents[18] = 'I'
    contents[19] = 'I'
    contents[37] = 'I'
    contents[38] = 'I'
    contents[39] = 'I'

    figures[27] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(23,),(16,),(36,)}, {(23,): [],(16,): [],(36,): []}, {(23,): {22},(16,): {22, 15},(36,): {29}}, {(23,): {21},(16,): {21},(36,): {21}}, {(23,): set(),(16,): set(),(36,): set()}, {(23, ): set(),(16, ): set(),(36, ): set()}))


# Monster anticipates future use of ice when determining path to focus
def test_Scenario156():
    m=Monster(action_move=2)
    figures,contents,initiatives,walls = init_test()

    figures[21] = 'C'
    initiatives[21] = 1

    contents[37] = 'I'
    contents[38] = 'I'
    contents[39] = 'I'

    figures[27] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(40,)}, {(40,): []}, {(40,): {29}}, {(40,): {21}}, {(40,): set()}, {(40): set()}))
# Monster anticipates future use of ice, including accounting for a slide-stopping wall, when determining path to focus
def test_Scenario157():
    m=Monster(action_move=2)
    figures,contents,initiatives,walls = init_test()

    figures[45] = 'C'
    initiatives[45] = 1

    contents[26] = 'I'
    contents[33] = 'I'
    contents[39] = 'I'
    walls[46][2] = True
    figures[12] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(39,)}, {(39,): []}, {(39,): {38}}, {(39,): {45}}, {(39,): set()}, {(39): set()}))

# Monster anticipates future use of ice, including accounting for a slide-stopping wall, when determining path to focus
def test_Scenario158():
    m=Monster(action_move=2)
    figures,contents,initiatives,walls = init_test()

    figures[51] = 'C'
    initiatives[45] = 1

    contents[24] = 'I'
    contents[31] = 'I'
    contents[37] = 'I'
    walls[30][1] = True
    figures[12] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(18,)}, {(18,): []}, {(18,): {44}}, {(18,): {51}}, {(18,): set()}, {(39): set()}))

# Sliding onto difficult terrain does not costs an extra move
def test_Scenario159():
    m=Monster(action_move=2)
    figures,contents,initiatives,walls = init_test()

    figures[12] = 'A'
    figures[38] = 'C'

    contents[19] = 'I'
    contents[25] = 'D'

    assert_answers(m, figures,contents,initiatives,walls,({(32,38)}, {(32,38): []}, {(32,38): {32}}, {(32,38): {38}}, {(32,38):  {((7.75, 7.361215932167728), (7.75, 7.361215932167728))}}, {(32,38): set()}))

# Sliding onto difficult terrain does not costs an extra move
def test_Scenario160():
    m=Monster(action_move=2)
    figures,contents,initiatives,walls = init_test()

    figures[6] = 'A'
    figures[38] = 'C'

    contents[33] = 'I'
    contents[39] = 'D'

    assert_answers(m, figures,contents,initiatives,walls,({(19,), (20,)},{(19,): [], (20,): []},{(19,): {32, 39}, (20,): {39}},{(19,): {38}, (20,): {38}},{(19,): set(), (20,): set()},{(19,): {32}, (20,): {32}}))

# Monsters teleport through walls
def test_Scenario161():
    m=Monster(action_move=2, teleport=True)
    figures,contents,initiatives,walls = init_test()

    figures[17] = 'A'
    figures[31] = 'C'

    contents[22] = 'X'
    contents[23] = 'X'
    contents[24] = 'X'
    contents[25] = 'X'

    assert_answers(m, figures,contents,initiatives,walls,({(32,31), (30,31)},{(32,31): [], (30,31): []},{(32,31): {32}, (30,31): {30}},{(32,31): {31}, (30,31): {31}},{(32,31): {((7.095238095237905, 6.928203230275509), (7.095238095237905, 6.928203230275509))},(30,31): {((7.095238095237905, 5.196152422706632), (7.095238095237905, 5.196152422706632))}},{(32,31): {32}, (30,31): {32}}))
    
# Flying monsters teleport onto obstacles and traps
def test_Scenario162():
    m=Monster(action_move=2, teleport=True, flying=True)
    figures,contents,initiatives,walls = init_test()

    figures[17] = 'A'
    figures[31] = 'C'

    contents[22] = 'X'
    contents[23] = 'X'
    contents[24] = 'X'
    contents[25] = 'X'
    contents[30] = 'T'
    contents[32] = 'O'

    assert_answers(m, figures,contents,initiatives,walls,({(32,31), (30,31)},{(32,31): [], (30,31): []},{(32,31): {32}, (30,31): {30}},{(32,31): {31}, (30,31): {31}},{(32,31): {((7.095238095237905, 6.928203230275509), (7.095238095237905, 6.928203230275509))},(30,31): {((7.095238095237905, 5.196152422706632), (7.095238095237905, 5.196152422706632))}},{(32,31): {32}, (30,31): {32}}))
#Online test question #21
def test_Scenario163():
    m=Monster(action_move=2, jumping=True)
    figures,contents,initiatives,walls = init_test()

    figures[22] = 'A'
    figures[26] = 'C'

    contents[24] = 'D'

    assert_answers(m, figures,contents,initiatives,walls,({(24,)},{(24,): []},{(24,): {25}},{(24,): {26},},{(24,): set()},{(24,): {32}}))
    
#Online test question #22
def test_Scenario164():
    m=Monster(action_move=2, jumping=True)
    figures,contents,initiatives,walls = init_test()

    figures[22] = 'A'
    figures[25] = 'C'

    contents[24] = 'D'

    assert_answers(m, figures,contents,initiatives,walls,({(24,25)},{(24,25): []},{(24,25): {24}},{(24,25): {25},},{(24,25): {((5.5, 7.794228634059947), (5.5, 7.794228634059947))}},{(24,25): {32}}))
    
#Online test question #23
def test_Scenario165():
    m=Monster(action_move=2, jumping=True)
    figures,contents,initiatives,walls = init_test()

    figures[29] = 'A'
    figures[33] = 'C'

    contents[17] = 'X'
    contents[18] = 'X'
    contents[19] = 'X'
    contents[24] = 'X'
    contents[31] = 'T'
    contents[38] = 'X'
    contents[45] = 'X'
    contents[46] = 'X'
    contents[47] = 'X'

    assert_answers(m, figures,contents,initiatives,walls,({(30,)},{(30,): []},{(30,): {32}},{(30,): {33},},{(30,): set()},{(30,): {32}}))
    
#Online test question #24
def test_Scenario166():
    m=Monster(action_move=2,action_range=3,action_target=3, jumping=True)
    figures,contents,initiatives,walls = init_test()


    figures[24] = 'A'
    figures[30] = 'C'
    initiatives[30] = 1
    figures[32] = 'C'
    initiatives[32] = 2
    figures[44] = 'C'
    initiatives[44] = 4
    figures[46] = 'C'
    initiatives[46] = 3

    assert_answers(m, figures,contents,initiatives,walls,({( 24, 30, 32, 46 )},{( 24, 30, 32, 46 ): []},{( 24, 30, 32, 46 ): {24}},{( 24, 30, 32, 46 ): {30},},{( 24, 30, 32, 46 ): {((6.25, 7.3612159321677275), (6.25, 7.3612159321677275)),((6.3999999999997, 7.101408311032916), (9.1000000000003, 7.62102355330254)),((5.999999999999, 6.06217782649107), (6.500000000001, 5.196152422706632))}},{( 24, 30, 32, 46 ): {32}}))
    
#Online test question #25
def test_Scenario167():
    m=Monster(action_move=4, action_target=2)
    figures,contents,initiatives,walls = init_test()

    figures[11] = 'C'
    initiatives[11] = 3
    figures[22] = 'A'
    figures[26] = 'C'
    initiatives[26] = 1
    figures[39] = 'C'
    initiatives[39] = 2

    contents[32] = 'O'
    contents[38] = 'O'
    assert_answers(m, figures,contents,initiatives,walls,({( 33, 26, 39 )},{( 33, 26, 39 ): []},{( 33, 26, 39 ): {33}},{( 33, 26, 39 ): {26}},{( 33, 26, 39 ): {((7.75, 9.093266739736606), (7.75, 9.093266739736606)),((6.25, 9.959292143521044), (6.25, 9.959292143521044))}},{( 33, 26, 39 ): {32}}))
    
#Monsters measure proximity around walls
def test_Scenario168():
    m=Monster(action_move=4)
    figures,contents,initiatives,walls = init_test()

    figures[15] = 'C'
    initiatives[15] = 1
    figures[17] = 'A'
    figures[48] = 'C'
    initiatives[48] = 1

    contents[8] = 'X'
    contents[16] = 'X'
    contents[23] = 'X'
    contents[31] = 'X'
    contents[38] = 'X'
    contents[46] = 'X'

    assert_answers(m, figures,contents,initiatives,walls,({( 40, 48 ), ( 47, 48 ), ( 7, 15 )},{( 40, 48 ): [], ( 47, 48 ): [], ( 7, 15 ): []},{(40, 48 ):{40}, (47, 48 ): {47}, ( 7, 15 ): {7}},{(40, 48 ):{48}, (47, 48 ): {48}, ( 7, 15 ): {15}},{(40, 48 ):{ ((9.25, 10.825317547305483), (9.25, 10.825317547305483))},(47, 48 ):{((10.0, 10.392304845413264), (10.0, 10.392304845413264))},( 7, 15 ):{((3.2976190476189524, 2.082584899577029), (3.2976190476189524, 2.082584899577029))}},{(40, 48 ):{15}, (47, 48 ): {15}, ( 7, 15 ): {33}}))
    
#Even teleporting monsters measure proximity around walls
def test_Scenario169():
    m=Monster(action_move=4, teleport=True)
    figures,contents,initiatives,walls = init_test()

    figures[24] = 'A'
    figures[30] = 'C'
    initiatives[30] = 1
    figures[47] = 'C'
    initiatives[47] = 2

    contents[8] = 'X'
    contents[16] = 'X'
    contents[23] = 'X'
    contents[31] = 'X'
    contents[38] = 'X'
    contents[46] = 'X'

    assert_answers(m, figures,contents,initiatives,walls,({(37, 30), ( 22, 30 ) },{(37, 30): [], ( 22, 30 ): []},{(37, 30):{37}, ( 22, 30 ): {22}},{(37, 30):{30}, ( 22, 30 ): {30}},{(37, 30):{ ((7.797619047618952, 4.680661110930345), (7.797619047618952, 4.680661110930345))},( 22, 30 ):{((6.297619047618952, 3.8146357071459063), (6.297619047618952, 3.8146357071459063))}},{(37, 30):{15}, ( 22, 30 ): {15}}))
        
#Monsters do not measure proximity around obstacles
def test_Scenario170():
    m=Monster(action_move=4, teleport=True)
    figures,contents,initiatives,walls = init_test()

    figures[24] = 'A'
    figures[30] = 'C'
    initiatives[30] = 1
    figures[47] = 'C'
    initiatives[47] = 2

    contents[8] = 'X'
    contents[16] = 'X'
    contents[23] = 'X'
    contents[31] = 'O'
    contents[38] = 'X'
    contents[46] = 'X'

    assert_answers(m, figures,contents,initiatives,walls,({(37, 30), ( 22, 30 ) },{(37, 30): [], ( 22, 30 ): []},{(37, 30):{37}, ( 22, 30 ): {22}},{(37, 30):{30}, ( 22, 30 ): {30}},{(37, 30):{ ((7.75, 4.7631397208144115), (7.75, 4.763139720814412))},( 22, 30 ):{((6.297619047618952, 3.8146357071459063), (6.297619047618952, 3.8146357071459063))}},{(37, 30):{15}, ( 22, 30 ): {15}}))
    
#Monsters do not slide through other monsters
def test_Scenario171():
    m=Monster(action_move=1)
    figures,contents,initiatives,walls = init_test()

    figures[9] = 'A'
    figures[32] = 'M'
    figures[54] = 'C'
    initiatives[54] = 1

    contents[17] = 'I'
    contents[24] = 'I'
    contents[32] = 'I'
    contents[39] = 'I'

    assert_answers(m, figures,contents,initiatives,walls,({(24, )},{(24, ): []},{(24, ):{47}},{(24, ):{54}},{(24, ):set()},{(24, ):{15}}))

#Monsters can step through other monsters that are on icy terrain
def test_Scenario172():
    m=Monster(action_move=1)
    figures,contents,initiatives,walls = init_test()

    figures[9] = 'A'
    figures[32] = 'M'
    figures[54] = 'C'
    initiatives[54] = 1

    contents[17] = 'I'
    contents[24] = 'I'
    contents[32] = 'I'
    contents[39] = 'I'

    assert_answers(m, figures,contents,initiatives,walls,({(24, )},{(24, ): []},{(24, ):{47}},{(24, ):{54}},{(24, ):set()},{(24, ):{15}}))
    
#Monsters will slide into a blocking monster to move closer to their focus
def test_Scenario173():
    m=Monster(action_move=1)
    figures,contents,initiatives,walls = init_test()

    figures[9] = 'A'
    figures[39] = 'M'
    figures[54] = 'C'
    initiatives[54] = 1

    contents[17] = 'I'
    contents[24] = 'I'
    contents[32] = 'I'
    contents[39] = 'I'

    assert_answers(m, figures,contents,initiatives,walls,({(32, )},{(32, ): []},{(32, ):{47}},{(32, ):{54}},{(32, ):set()},{(32, ):{15}}))
    
#Monsters will slide into a blocking monster to move closer to their focus
def test_Scenario174():
    m=Monster(action_move=1)
    figures,contents,initiatives,walls = init_test()

    figures[9] = 'A'
    figures[47] = 'M'
    figures[54] = 'C'
    initiatives[54] = 1

    contents[17] = 'I'
    contents[24] = 'I'
    contents[32] = 'I'
    contents[39] = 'I'

    assert_answers(m, figures,contents,initiatives,walls,({(39, )},{(39, ): []},{(39, ):{53, 48}},{(39, ):{54}},{(39, ):set()},{(39, ):{15}}))
    
#Monsters will slide into a blocking monster to move closer to their focus
def test_Scenario175():
    m=Monster(action_move=1)
    figures,contents,initiatives,walls = init_test()

    figures[9] = 'A'
    figures[32] = 'M'
    figures[39] = 'M'
    figures[54] = 'C'
    initiatives[54] = 1

    contents[17] = 'I'
    contents[24] = 'I'
    contents[32] = 'I'
    contents[39] = 'I'

    assert_answers(m, figures,contents,initiatives,walls,({(24,)},{(24,): []},{(24,):{47}},{(24,):{54}},{(24,):set()},{(24,):{15}}))
    
#Monsters will slide into a blocking monster to move closer to their focus
def test_Scenario176():
    m=Monster(action_move=1)
    figures,contents,initiatives,walls = init_test()

    figures[9] = 'A'
    figures[39] = 'M'
    figures[54] = 'C'
    initiatives[54] = 1

    contents[17] = 'I'
    contents[24] = 'I'
    contents[32] = 'I'

    assert_answers(m, figures,contents,initiatives,walls,({(32,)},{(32,): []},{(32,):{47}},{(32,):{54}},{(32,):set()},{(32,):{15}}))
    
#Monsters will step through a blocking monster on icy terrain to move closer to their focus
def test_Scenario177():
    m=Monster(action_move=2)
    figures,contents,initiatives,walls = init_test()

    figures[9] = 'A'
    figures[24] = 'M'
    figures[39] = 'M'
    figures[54] = 'C'
    initiatives[54] = 1

    contents[17] = 'I'
    contents[24] = 'I'
    contents[32] = 'I'
    contents[39] = 'I'

    assert_answers(m, figures,contents,initiatives,walls,({(32,)},{(32,): []},{(32,):{47}},{(32,):{54}},{(32,):set()},{(32,):{15}}))
    
#Monsters do not slide through characters
def test_Scenario178():
    m=Monster(action_move=3, action_target=2)
    figures,contents,initiatives,walls = init_test()

    figures[9] = 'A'
    figures[39] = 'C'
    initiatives[39] = 1
    figures[54] = 'C'
    initiatives[54] = 1

    contents[17] = 'I'
    contents[24] = 'I'
    contents[32] = 'I'
    contents[39] = 'I'

    assert_answers(m, figures,contents,initiatives,walls,({( 32,39 ) },{( 32,39 ) : []},{( 32,39) :{32}},{( 32,39 ) :{39}},{( 32,39) :{ ((7.750000000000001, 8.227241335952165), (7.750000000000001, 8.227241335952165))}},{( 32,39) :{15}}))
    
#Monsters do not slide through characters
def test_Scenario179():
    m=Monster(action_move=4, action_target=2)
    figures,contents,initiatives,walls = init_test()

    figures[9] = 'A'
    figures[39] = 'C'
    initiatives[39] = 1
    figures[54] = 'C'
    initiatives[54] = 1

    contents[17] = 'I'
    contents[24] = 'I'
    contents[32] = 'I'
    contents[39] = 'I'

    assert_answers(m, figures,contents,initiatives,walls,({( 47, 39, 54 ) },{( 47, 39, 54 ) : []},{( 47, 39, 54 ) :{47}},{( 47, 39, 54 ) :{39}},{( 47, 39, 54 ) :{((9.25, 9.093266739736606), (9.25, 9.093266739736606)),((10.75, 9.959292143521044), (10.75, 9.959292143521044))}},{( 47, 39, 54 ) :{15}}))
#In Frosthaven, if a monster with multiple attacks cannot make an attack this turn, it moves towards the closest hex that allows it to attack its focus. In Gloomhaven, the monster moves towards the hex that maximizes its attack
def test_Scenario180():
    m=Monster(action_move=1, action_target=2)
    figures,contents,initiatives,walls = init_test()

    figures[12] = 'A'
    figures[23] = 'C'
    initiatives[23] = 1
    figures[30] = 'C'
    initiatives[30] = 2

    contents[18] = 'X'
    contents[24] = 'X'

    m.aoe[17] = True
    m.aoe[23] = True

    assert_answers(m, figures,contents,initiatives,walls,({( 19, ) },{( 19, ) : []},{( 19,) :{31}},{( 19, ) :{23}},{( 19,) :set()},{( 19, ) :{15}}))

#In Frosthaven, if a monster with AoE cannot make an attack this turn, it moves towards the closest hex that allows it to attack its focus. In Gloomhaven, the monster moves towards the hex that maximizes its attack
def test_Scenario181():
    m=Monster(action_move=1, action_target=1)
    figures,contents,initiatives,walls = init_test()

    figures[12] = 'A'
    figures[23] = 'C'
    initiatives[23] = 1
    figures[30] = 'C'
    initiatives[30] = 2

    contents[18] = 'X'
    contents[24] = 'X'

    m.aoe[17] = True
    m.aoe[23] = True

    assert_answers(m, figures,contents,initiatives,walls,({( 19, ) },{( 19, ) : []},{( 19,) :{31}},{( 19, ) :{23}},{( 19,) :set()},{( 19, ) :{15}}))

#In Frosthaven, if a monster with multiple attacks cannot make an attack this turn, it moves towards the closest hex that allows it to attack its focus. In Gloomhaven, the monster moves towards the hex that maximizes its attack
def test_Scenario182():
    m=Monster(action_move=1, action_target=2, action_range=2)
    figures,contents,initiatives,walls = init_test()

    figures[11] = 'C'
    initiatives[11] = 1
    figures[22] = 'A'
    figures[39] = 'C'
    initiatives[39] = 2

    contents[18] = 'X'
    contents[24] = 'X'

    assert_answers(m, figures,contents,initiatives,walls,({( 23, ),( 30, ) },{( 23, ) : [],( 30, ) : []},{( 23,) :{25},( 30,) :{25}},{( 23, ) :{11},( 30, ) :{11}},{( 23,) :set(),( 30,) :set()},{( 23, ) :{15},( 30, ) :{15}}))