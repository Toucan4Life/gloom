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
                aoedict[(act,)+tuple(sorted(iinf[3]))].add(frozenset(iinf[4]))
   
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

    gmap = GloomhavenMap(16, 7, monster,figures,contents, initiatives,walls, Rule(1))
    scenario = Solver(Rule(1), gmap)
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

    assert_answers(m, figures,contents,initiatives,walls,({(36, 29), (22, 29)}, {(22, 29): [], (36, 29): []}, {(36, 29): {36}, (22, 29): {22}}, {(36, 29): {29}, (22, 29): {29}}, {(36, 29): {((7.5, 3.4641016151377544), (7.5, 3.4641016151377544))}, (22, 29): {((6.5, 3.4641016151377544), (6.5, 3.4641016151377544))}}, {(36, 29): set(), (22, 29): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(44, 50)}, {(44, 50): []}, {(44, 50): {44}}, {(44, 50): {50}}, {(44, 50): {((11.0, 4.330127018922193), (11.0, 4.330127018922193))}}, {(44, 50): set()}))

# Given equal path distance and proximity, lowest initiative breaks the focus tie
def test_Scenario8():
    m=Monster(action_move=2)
    figures,contents,initiatives,walls = init_test()


    figures[9] = 'C'
    initiatives[9] = 10

    figures[29] = 'C'
    initiatives[29] = 20

    figures[32] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(17, 9)}, {(17, 9): []}, {(17, 9): {17}}, {(17, 9): {9}}, {(17, 9): {((3.0, 6.06217782649107), (3.0, 6.06217782649107))}}, {(17, 9): set()}))

# Given equal path distance, proximity, and initiative; players choose the foc
def test_Scenario9():
    m=Monster(action_move=2)
    figures,contents,initiatives,walls = init_test()


    figures[9] = 'C'
    initiatives[9] = 99

    figures[29] = 'C'
    initiatives[29] = 99

    figures[32] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(17, 9), (30, 29)}, {(17, 9): [], (30, 29): []}, {(17, 9): {17}, (30, 29): {30}}, {(17, 9): {9}, (30, 29): {29}}, {(17, 9): {((3.0, 6.06217782649107), (3.0, 6.06217782649107))}, (30, 29): {((6.5, 3.4641016151377544), (6.5, 3.4641016151377544))}}, {(17, 9): set(), (30, 29): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(45, 51)}, {(45, 51): []}, {(45, 51): {45}}, {(45, 51): {51}}, {(45, 51): {((11.0, 6.06217782649107), (11.0, 6.06217782649107))}}, {(45, 51): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(29, 28)}, {(29, 28): []}, {(29, 28): {29}}, {(29, 28): {28}}, {(29, 28): {((6.5, 1.7320508075688772), (6.5, 1.7320508075688772))}}, {(29, 28): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(29, 28)}, {(29, 28): []}, {(29, 28): {29}}, {(29, 28): {28}}, {(29, 28): {((6.5, 1.7320508075688772), (6.5, 1.7320508075688772))}}, {(29, 28): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(46,)}, {(46,): []}, {(46,): {37}}, {(46,): {30}}, {(46,): set()}, {(46,): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(39,)}, {(39,): []}, {(39,): {45}}, {(39,): {37}}, {(39,): set()}, {(39,): set()}))

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
    assert_answers(m, figures,contents,initiatives,walls,({(43, 36)}, {(43, 36): []}, {(43, 36): {43}}, {(43, 36): {36}}, {(43, 36): {((9.5, 3.4641016151377544), (9.5, 3.4641016151377544))}}, {(43, 36): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(38, 46)}, {(38, 46): []}, {(38, 46): {38}}, {(38, 46): {46}}, {(38, 46): {((9.5, 6.928203230275509), (9.5, 6.928203230275509))}}, {(38, 46): set()}))

# The monster will not move if it can attack without disadvantage from its position
def test_Scenario31():
    m=Monster(action_move=1)
    figures,contents,initiatives,walls = init_test()


    figures[36] = 'C'
    figures[30] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(30, 36)}, {(30, 36): []}, {(30, 36): {30}}, {(30, 36): {36}}, {(30, 36): {((8.0, 4.330127018922193), (8.0, 4.330127018922193))}}, {(30, 36): set()}))

# The monster will not move if in range and line of sight of its foc
def test_Scenario32():
    m=Monster(action_move=3, action_range=4)
    figures,contents,initiatives,walls = init_test()


    figures[29] = 'C'

    figures[25] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(25, 29)}, {(25, 29): []}, {(25, 29): {25}}, {(25, 29): {29}}, {(25, 29): {((6.0, 7.794228634059947), (6.5, 3.4641016151377544))}}, {(25, 29): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(39, 29), (40, 29)}, {(39, 29): [], (40, 29): []}, {(39, 29): {39}, (40, 29): {40}}, {(39, 29): {29}, (40, 29): {29}}, {(39, 29): {((9.0, 7.794228634059947), (7.5, 3.4641016151377544))}, (40, 29): {((9.0, 9.526279441628825), (7.5, 3.4641016151377544))}}, {(39, 29): set(), (40, 29): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(44, 15)}, {(44, 15): []}, {(44, 15): {44}}, {(44, 15): {15}}, {(44, 15): {((9.5, 3.4641016151377544), (5.0, 2.598076211353316))}}, {(44, 15): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(45, 21), (44, 21)}, {(44, 21): [], (45, 21): []}, {(45, 21): {45}, (44, 21): {44}}, {(45, 21): {21}, (44, 21): {21}}, {(45, 21): {((10.5, 5.196152422706632), (6.5, 1.7320508075688772))}, (44, 21): {((9.5, 3.4641016151377544), (6.5, 1.7320508075688772))}}, {(45, 21): set(), (44, 21): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(44, 22)}, {(44, 22): []}, {(44, 22): {44}}, {(44, 22): {22}}, {(44, 22): {((9.5, 3.4641016151377544), (6.0, 2.598076211353316))}}, {(44, 22): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(37, 28)}, {(37, 28): []}, {(37, 28): {37}}, {(37, 28): {28}}, {(37, 28): {((9.5, 5.196152422706632), (8.0, 0.8660254037844386))}}, {(37, 28): set()}))

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
    assert_answers(m, figures,contents,initiatives,walls,({(44, 29), (45, 29)}, {(44, 29): [], (45, 29): []}, {(44, 29): {44}, (45, 29): {45}}, {(44, 29): {29}, (45, 29): {29}}, {(44, 29): {((9.5, 3.4641016151377544), (8.0, 2.598076211353316))}, (45, 29): {((10.5, 5.196152422706632), (8.0, 2.598076211353316))}}, {(44, 29): set(), (45, 29): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(37, 35), (38, 35), (34, 35), (40, 35), (39, 35)}, {(34, 35): [], (37, 35): [], (38, 35): [], (39, 35): [], (40, 35): []}, {(37, 35): {37}, (38, 35): {38}, (39, 35): {39}, (34, 35): {34}, (40, 35): {40}}, {(37, 35): {35}, (38, 35): {35}, (39, 35): {35}, (34, 35): {35}, (40, 35): {35}}, {(37, 35): {((9.5, 5.196152422706632), (9.0, 2.598076211353316))}, (38, 35): {((9.5, 6.928203230275509), (9.0, 2.598076211353316))}, (39, 35): {((9.5, 8.660254037844386), (9.0, 2.598076211353316))}, (34, 35): {((8.0, 11.258330249197702), (9.5, 1.7320508075688772))}, (40, 35): {((9.5, 10.392304845413264), (9.0, 2.598076211353316))}}, {(37, 35): set(), (38, 35): set(), (39, 35): set(), (34, 35): set(), (40, 35): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(33, 36), (26, 36), (32, 36)}, {(26, 36): [], (32, 36): [], (33, 36): []}, {(33, 36): {33}, (26, 36): {26}, (32, 36): {32}}, {(33, 36): {36}, (26, 36): {36}, (32, 36): {36}}, {(33, 36): {((7.5, 8.660254037844386), (9.5, 3.4641016151377544))}, (26, 36): {((6.5, 10.392304845413264), (9.5, 3.4641016151377544))}, (32, 36): {((8.0, 7.794228634059947), (9.5, 3.4641016151377544))}}, {(33, 36): set(), (26, 36): set(), (32, 36): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(32, 42), (33, 42), (26, 42)}, {(26, 42): [], (32, 42): [], (33, 42): []}, {(32, 42): {32}, (33, 42): {33}, (26, 42): {26}}, {(32, 42): {42}, (33, 42): {42}, (26, 42): {42}}, {(32, 42): {((8.0, 7.794228634059947), (10.5, 1.7320508075688772))}, (33, 42): {((7.5, 8.660254037844386), (10.5, 1.7320508075688772))}, (26, 42): {((6.5, 10.392304845413264), (10.5, 1.7320508075688772))}}, {(32, 42): set(), (33, 42): set(), (26, 42): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(18, 43), (5, 43), (11, 43)}, {(5, 43): [], (11, 43): [], (18, 43): []}, {(18, 43): {18}, (5, 43): {5}, (11, 43): {11}}, {(18, 43): {43}, (5, 43): {43}, (11, 43): {43}}, {(18, 43): {((5.0, 7.794228634059947), (10.5, 3.4641016151377544))}, (5, 43): {((2.0, 9.526279441628825), (10.5, 3.4641016151377544))}, (11, 43): {((3.5, 8.660254037844386), (10.5, 3.4641016151377544))}}, {(18, 43): set(), (5, 43): set(), (11, 43): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(3, 44)}, {(3, 44): []}, {(3, 44): {3}}, {(3, 44): {44}}, {(3, 44): {((2.0, 6.06217782649107), (9.5, 5.196152422706632))}}, {(3, 44): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(38, 7), (31, 7)}, {(31, 7): [], (38, 7): []}, {(38, 7): {38}, (31, 7): {31}}, {(38, 7): {7}, (31, 7): {7}}, {(38, 7): {((9.0, 7.794228634059947), (3.0, 2.598076211353316))}, (31, 7): {((6.0, 6.06217782649107), (3.0, 2.598076211353316))}}, {(38, 7): set(), (31, 7): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(38, 15), (31, 15)}, {(31, 15): [], (38, 15): []}, {(38, 15): {38}, (31, 15): {31}}, {(38, 15): {15}, (31, 15): {15}}, {(38, 15): {((9.0, 7.794228634059947), (4.5, 3.4641016151377544))}, (31, 15): {((6.0, 6.06217782649107), (5.0, 2.598076211353316))}}, {(38, 15): set(), (31, 15): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(31, 21)}, {(31, 21): []}, {(31, 21): {31}}, {(31, 21): {21}}, {(31, 21): {((6.0, 6.06217782649107), (5.0, 2.598076211353316))}}, {(31, 21): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(37, 8)}, {(37, 8): []}, {(37, 8): {37}}, {(37, 8): {8}}, {(37, 8): {((8.0, 6.06217782649107), (3.0, 4.330127018922193))}}, {(37, 8): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(37, 16)}, {(37, 16): []}, {(37, 16): {37}}, {(37, 16): {16}}, {(37, 16): {((8.0, 6.06217782649107), (4.5, 5.196152422706632))}}, {(37, 16): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(31, 22), (38, 22)}, {(31, 22): [], (38, 22): []}, {(31, 22): {31}, (38, 22): {38}}, {(31, 22): {22}, (38, 22): {22}}, {(31, 22): {((6.0, 6.06217782649107), (5.0, 4.330127018922193))}, (38, 22): {((9.0, 7.794228634059947), (5.0, 4.330127018922193))}}, {(31, 22): set(), (38, 22): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(37, 9), (44, 9)}, {(37, 9): [], (44, 9): []}, {(37, 9): {37}, (44, 9): {44}}, {(37, 9): {9}, (44, 9): {9}}, {(37, 9): {((8.0, 6.06217782649107), (3.5, 5.196152422706632))}, (44, 9): {((9.5, 5.196152422706632), (3.0, 6.06217782649107))}}, {(37, 9): set(), (44, 9): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(44, 17), (50, 17), (37, 17)}, {(37, 17): [], (44, 17): [], (50, 17): []}, {(44, 17): {44}, (50, 17): {50}, (37, 17): {37}}, {(44, 17): {17}, (50, 17): {17}, (37, 17): {17}}, {(44, 17): {((9.5, 5.196152422706632), (5.0, 6.06217782649107))}, (50, 17): {((11.0, 4.330127018922193), (5.0, 6.06217782649107))}, (37, 17): {((8.0, 6.06217782649107), (5.0, 6.06217782649107))}}, {(44, 17): set(), (50, 17): set(), (37, 17): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(44, 23), (50, 23), (37, 23)}, {(37, 23): [], (44, 23): [], (50, 23): []}, {(44, 23): {44}, (50, 23): {50}, (37, 23): {37}}, {(44, 23): {23}, (50, 23): {23}, (37, 23): {23}}, {(44, 23): {((9.5, 5.196152422706632), (6.0, 6.06217782649107))}, (50, 23): {((11.0, 4.330127018922193), (6.0, 6.06217782649107))}, (37, 23): {((8.0, 6.06217782649107), (6.0, 6.06217782649107))}}, {(44, 23): set(), (50, 23): set(), (37, 23): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(35, 31)}, {(35, 31): []}, {(35, 31): {35}}, {(35, 31): {31}}, {(35, 31): {((9.0, 2.598076211353316), (8.0, 6.06217782649107))}}, {(35, 31): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(49, 76), (50, 76)}, {(49, 76): [], (50, 76): []}, {(49, 76): {49}, (50, 76): {50}}, {(49, 76): {76}, (50, 76): {76}}, {(49, 76): {((12.0, 2.598076211353316), (15.5, 10.392304845413264))}, (50, 76): {((12.5, 3.4641016151377544), (15.5, 10.392304845413264))}}, {(49, 76): set(), (50, 76): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(43, 65)}, {(43, 65): []}, {(43, 65): {43}}, {(43, 65): {65}}, {(43, 65): {((10.5, 3.4641016151377544), (13.5, 5.196152422706632))}}, {(43, 65): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(46, 36), (38, 36)}, {(38, 36): [], (46, 36): []}, {(46, 36): {46}, (38, 36): {38}}, {(46, 36): {36}, (38, 36): {36}}, {(46, 36): {((9.5, 6.928203230275509), (9.5, 3.4641016151377544))}, (38, 36): {((9.0, 6.06217782649107), (9.5, 3.4641016151377544))}}, {(46, 36): set(), (38, 36): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(45, 30)}, {(45, 30): []}, {(45, 30): {45}}, {(45, 30): {30}}, {(45, 30): {((9.0, 6.06217782649107), (7.5, 5.196152422706632))}}, {(45, 30): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(37, 30)}, {(37, 30): []}, {(37, 30): {37}}, {(37, 30): {30}}, {(37, 30): {((7.5, 5.196152422706632), (7.5, 5.196152422706632))}}, {(37, 30): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(37, 30)}, {(37, 30): []}, {(37, 30): {37}}, {(37, 30): {30}}, {(37, 30): {((7.5, 5.196152422706632), (7.5, 5.196152422706632))}}, {(37, 30): set()}))

# The monster will move the additional step to engage both its focus and an extra target
def test_Scenario63():
    m=Monster(action_move=2, action_target=2)
    figures,contents,initiatives,walls = init_test()


    figures[16] = 'C'
    initiatives[16] = 20
    figures[22] = 'C'
    initiatives[22] = 10

    figures[18] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(23, 16, 22)}, {(23, 16, 22): []}, {(23, 16, 22): {23}}, {(23, 16, 22): {16}}, {(23, 16, 22): {((5.0, 4.330127018922193), (5.0, 4.330127018922193)), ((4.5, 5.196152422706632), (4.5, 5.196152422706632))}}, {(23, 16, 22): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(18, 16, 31)}, {(18, 16, 31): []}, {(18, 16, 31): {18}}, {(18, 16, 31): {31}}, {(18, 16, 31): {((5.0, 7.794228634059947), (6.5, 6.928203230275509)), ((3.5, 6.928203230275509), (3.5, 5.196152422706632))}}, {(18, 16, 31): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(30, 16, 31, 35)}, {(30, 16, 31, 35): []}, {(30, 16, 31, 35): {30}}, {(30, 16, 31, 35): {31}}, {(30, 16, 31, 35): {((7.5, 3.4641016151377544), (8.0, 2.598076211353316)), ((7.5, 5.196152422706632), (7.5, 5.196152422706632)), ((6.0, 4.330127018922193), (5.0, 4.330127018922193))}}, {(30, 16, 31, 35): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(22, 16, 31, 35)}, {(22, 16, 31, 35): []}, {(22, 16, 31, 35): {22}}, {(22, 16, 31, 35): {31}}, {(22, 16, 31, 35): {((6.0, 4.330127018922193), (6.5, 5.196152422706632)), ((5.0, 4.330127018922193), (5.0, 4.330127018922193)), ((6.5, 3.4641016151377544), (8.0, 2.598076211353316))}}, {(22, 16, 31, 35): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(22, 15)}, {(22, 15): []}, {(22, 15): {22}}, {(22, 15): {15}}, {(22, 15): {((4.5, 3.4641016151377544), (4.5, 3.4641016151377544))}}, {(22, 15): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(10, 23, 24), (9, 23, 24)}, {(9, 23, 24): [], (10, 23, 24): []}, {(10, 23, 24): {10}, (9, 23, 24): {9}}, {(10, 23, 24): {24}, (9, 23, 24): {24}}, {(10, 23, 24): {((3.5, 6.928203230275509), (4.5, 6.928203230275509)), ((3.5, 6.928203230275509), (5.0, 6.06217782649107))}, (9, 23, 24): {((3.5, 5.196152422706632), (4.5, 5.196152422706632)), ((3.5, 5.196152422706632), (5.0, 6.06217782649107))}}, {(10, 23, 24): set(), (9, 23, 24): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(31, 17, 29)}, {(31, 17, 29): []}, {(31, 17, 29): {31}}, {(31, 17, 29): {29}}, {(31, 17, 29): {((6.5, 5.196152422706632), (6.5, 3.4641016151377544)), ((6.0, 6.06217782649107), (5.0, 6.06217782649107))}}, {(31, 17, 29): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(24, 9, 47)}, {(24, 9, 47): []}, {(24, 9, 47): {24}}, {(24, 9, 47): {9}}, {(24, 9, 47): {((4.5, 6.928203230275509), (3.0, 6.06217782649107)), ((6.5, 6.928203230275509), (9.5, 8.660254037844386))}}, {(24, 9, 47): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(39, 17, 62)}, {(39, 17, 62): []}, {(39, 17, 62): {39}}, {(39, 17, 62): {17}}, {(39, 17, 62): {((9.0, 9.526279441628825), (12.0, 11.258330249197702)), ((7.5, 8.660254037844386), (4.5, 6.928203230275509))}}, {(39, 17, 62): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(37, 17, 57)}, {(37, 17, 57): []}, {(37, 17, 57): {37}}, {(37, 17, 57): {17}}, {(37, 17, 57): {((7.5, 5.196152422706632), (5.0, 6.06217782649107)), ((9.0, 4.330127018922193), (12.0, 2.598076211353316))}}, {(37, 17, 57): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(39, 17, 62), (37, 17, 57)}, {(37, 17, 57): [], (39, 17, 62): []}, {(39, 17, 62): {39}, (37, 17, 57): {37}}, {(39, 17, 62): {17}, (37, 17, 57): {17}}, {(39, 17, 62): {((9.0, 9.526279441628825), (12.0, 11.258330249197702)), ((7.5, 8.660254037844386), (4.5, 6.928203230275509))}, (37, 17, 57): {((7.5, 5.196152422706632), (5.0, 6.06217782649107)), ((9.0, 4.330127018922193), (12.0, 2.598076211353316))}}, {(39, 17, 62): set(), (37, 17, 57): set()}))

# The monster only attacks additional targets if it can do so while still attacking its focus
def test_Scenario74():
    m=Monster(action_move=2,action_target=2)
    figures,contents,initiatives,walls = init_test()


    figures[9] = 'C'
    initiatives[9] = 10

    figures[29] = 'C'
    initiatives[29] = 20

    figures[32] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(17, 9)}, {(17, 9): []}, {(17, 9): {17}}, {(17, 9): {9}}, {(17, 9): {((3.0, 6.06217782649107), (3.0, 6.06217782649107))}}, {(17, 9): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(23, 16, 17, 24, 31), (23, 16, 22, 24, 31)}, {(23, 16, 17, 24, 31): [], (23, 16, 22, 24, 31): []}, {(23, 16, 17, 24, 31): {23}, (23, 16, 22, 24, 31): {23}}, {(23, 16, 17, 24, 31): {16, 24}, (23, 16, 22, 24, 31): {16, 24}}, {(23, 16, 17, 24, 31): {((6.5, 5.196152422706632), (6.5, 5.196152422706632)), ((5.0, 6.06217782649107), (5.0, 6.06217782649107)), ((6.0, 6.06217782649107), (6.0, 6.06217782649107)), ((4.5, 5.196152422706632), (4.5, 5.196152422706632))}, (23, 16, 22, 24, 31): {((6.5, 5.196152422706632), (6.5, 5.196152422706632)), ((6.0, 6.06217782649107), (6.0, 6.06217782649107)), ((5.0, 4.330127018922193), (5.0, 4.330127018922193)), ((4.5, 5.196152422706632), (4.5, 5.196152422706632))}}, {(23, 16, 17, 24, 31): set(), (23, 16, 22, 24, 31): set()}))

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



    assert_answers(m, figures,contents,initiatives,walls,({(23, 16, 22)}, {(23, 16, 22): [17, 22, 16]}, {(23, 16, 22): {23}}, {(23, 16, 22): {16}}, {(23, 16, 22): {((5.0, 4.330127018922193), (5.0, 4.330127018922193)), ((4.5, 5.196152422706632), (4.5, 5.196152422706632))}}, {(23, 16, 22): set()}))

# The monster moves in close to attack an additional target using its AoE
def test_Scenario80():
    m=Monster(action_move=2)
    m.aoe[31] = True
    m.aoe[37] = True
    figures,contents,initiatives,walls = init_test()


    figures[16] = 'C'
    figures[22] = 'C'

    figures[18] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(9, 16, 22)}, {(9, 16, 22): [16, 22]}, {(9, 16, 22): {9}}, {(9, 16, 22): {16}}, {(9, 16, 22): {((3.0, 4.330127018922193), (4.5, 3.4641016151377544)), ((3.5, 5.196152422706632), (3.5, 5.196152422706632))}}, {(9, 16, 22): set()}))

# When deciding how to use its AoE, the monster prioritizes targets based on their ranking as a focus. The monster's first priority is to attack its focus, C30. After that, the next highest priority is C10
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

    assert_answers(m, figures,contents,initiatives,walls,({(23, 8, 16)}, {(23, 8, 16): [16, 8]}, {(23, 8, 16): {23}}, {(23, 8, 16): {16}}, {(23, 8, 16): {((5.0, 4.330127018922193), (3.5, 3.4641016151377544)), ((4.5, 5.196152422706632), (4.5, 5.196152422706632))}}, {(23, 8, 16): set()}))

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



    assert_answers(m, figures,contents,initiatives,walls,({(23, 16, 22), (9, 16, 22)}, {(9, 16, 22): [16, 22], (23, 16, 22): [22, 21]}, {(23, 16, 22): {23}, (9, 16, 22): {9}}, {(23, 16, 22): {16}, (9, 16, 22): {16}}, {(23, 16, 22): {((5.0, 4.330127018922193), (5.0, 4.330127018922193)), ((4.5, 5.196152422706632), (4.5, 5.196152422706632))}, (9, 16, 22): {((3.0, 4.330127018922193), (4.5, 3.4641016151377544)), ((3.5, 5.196152422706632), (3.5, 5.196152422706632))}}, {(23, 16, 22): set(), (9, 16, 22): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(9, 16, 17, 22)}, {(9, 16, 17, 22): [16, 22]}, {(9, 16, 17, 22): {9}}, {(9, 16, 17, 22): {17}}, {(9, 16, 17, 22): {((3.0, 4.330127018922193), (4.5, 3.4641016151377544)), ((3.5, 5.196152422706632), (3.5, 5.196152422706632))}}, {(9, 16, 17, 22): set()}))

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


    assert_answers(m, figures,contents,initiatives,walls,({(17, 15)}, {(17, 15): [16, 15]}, {(17, 15): {17}}, {(17, 15): {15}}, {(17, 15): {((3.5, 5.196152422706632), (3.5, 3.4641016151377544))}}, {(17, 15): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(37, 36)}, {(37, 36): [31, 30, 36]}, {(37, 36): {37}}, {(37, 36): {36}}, {(37, 36): {((9.5, 5.196152422706632), (9.5, 3.4641016151377544))}}, {(37, 36): set()}))

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



    assert_answers(m, figures,contents,initiatives,walls,({(22, 18, 23, 24), (50, 51, 52, 60)}, {(50, 51, 52, 60): [60, 51, 52], (22, 18, 23, 24): [18, 23, 24]}, {(50, 51, 52, 60): {50}, (22, 18, 23, 24): {22}}, {(50, 51, 52, 60): {51}, (22, 18, 23, 24): {23}}, {(22, 18, 23, 24): {((6.0, 4.330127018922193), (6.0, 6.06217782649107)), ((5.0, 4.330127018922193), (4.5, 6.928203230275509)), ((6.0, 4.330127018922193), (6.0, 4.330127018922193))}, (50, 51, 52, 60): {((12.0, 4.330127018922193), (12.5, 6.928203230275509)), ((12.0, 4.330127018922193), (12.0, 6.06217782649107)), ((12.0, 4.330127018922193), (12.0, 4.330127018922193))}}, {(22, 18, 23, 24): set(), (50, 51, 52, 60): set()}))

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



    assert_answers(m, figures,contents,initiatives,walls,({(37, 15, 16, 17), (37, 60, 67, 75)}, {(37, 15, 16, 17): [15, 16, 17], (37, 60, 67, 75): [60, 67, 75]}, {(37, 15, 16, 17): {37}, (37, 60, 67, 75): {37}}, {(37, 15, 16, 17): {16, 17, 15}, (37, 60, 67, 75): {60}}, {(37, 15, 16, 17): {((7.5, 5.196152422706632), (5.0, 4.330127018922193)), ((7.5, 5.196152422706632), (5.0, 6.06217782649107)), ((8.0, 4.330127018922193), (5.0, 2.598076211353316))}, (37, 60, 67, 75): {((9.5, 5.196152422706632), (12.5, 6.928203230275509)), ((9.5, 5.196152422706632), (15.5, 8.660254037844386)), ((9.5, 5.196152422706632), (14.0, 7.794228634059947))}}, {(37, 15, 16, 17): set(), (37, 60, 67, 75): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(38, 10)}, {(38, 10): []}, {(38, 10): {38}}, {(38, 10): {10}}, {(38, 10): {((7.5, 6.928203230275509), (3.5, 6.928203230275509))}}, {(38, 10): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(30,)}, {(30,): []}, {(30,): {16}}, {(30,): {17}}, {(30,): set()}, {(30,): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(32, 29)}, {(32, 29): [29, 30, 36, 37]}, {(32, 29): {32}}, {(32, 29): {29}}, {(32, 29): {((8.0, 7.794228634059947), (7.5, 3.4641016151377544))}}, {(32, 29): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(23, 11, 33, 38)}, {(23, 11, 33, 38): []}, {(23, 11, 33, 38): {23}}, {(23, 11, 33, 38): {11}}, {(23, 11, 33, 38): {((5.0, 6.06217782649107), (3.0, 7.794228634059947)), ((6.5, 5.196152422706632), (8.0, 6.06217782649107)), ((6.0, 6.06217782649107), (6.5, 8.660254037844386))}}, {(23, 11, 33, 38): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(38, 32, 39, 46)}, {(38, 32, 39, 46): []}, {(38, 32, 39, 46): {38}}, {(38, 32, 39, 46): {32}}, {(38, 32, 39, 46): {((9.0, 7.794228634059947), (9.0, 7.794228634059947)), ((8.0, 7.794228634059947), (8.0, 7.794228634059947)), ((9.5, 6.928203230275509), (9.5, 6.928203230275509))}}, {(38, 32, 39, 46): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(24, 25, 32)}, {(24, 25, 32): []}, {(24, 25, 32): {24}}, {(24, 25, 32): {25}}, {(24, 25, 32): {((6.0, 7.794228634059947), (6.0, 7.794228634059947)), ((6.5, 6.928203230275509), (6.5, 6.928203230275509))}}, {(24, 25, 32): set()}))

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



    assert_answers(m, figures,contents,initiatives,walls,({(24, 32, 39)}, {(24, 32, 39): [39, 32]}, {(24, 32, 39): {24}}, {(24, 32, 39): {32}}, {(24, 32, 39): {((6.5, 6.928203230275509), (8.0, 7.794228634059947)), ((6.5, 6.928203230275509), (6.5, 6.928203230275509))}}, {(24, 32, 39): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(38, 32, 39, 46)}, {(38, 32, 39, 46): []}, {(38, 32, 39, 46): {38}}, {(38, 32, 39, 46): {32}}, {(38, 32, 39, 46): {((9.0, 7.794228634059947), (9.0, 7.794228634059947)), ((8.0, 7.794228634059947), (8.0, 7.794228634059947)), ((9.5, 6.928203230275509), (9.5, 6.928203230275509))}}, {(38, 32, 39, 46): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(31,)}, {(31,): []}, {(31,): {45, 53, 46}}, {(31,): {52}}, {(31,): set()}, {(31,): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(31, 23, 24, 30, 32)}, {(31, 23, 24, 30, 32): []}, {(31, 23, 24, 30, 32): {31}}, {(31, 23, 24, 30, 32): {23}}, {(31, 23, 24, 30, 32): {((7.5, 6.928203230275509), (7.5, 6.928203230275509)), ((6.5, 5.196152422706632), (6.5, 5.196152422706632)), ((6.0, 6.06217782649107), (6.0, 6.06217782649107)), ((6.5, 6.928203230275509), (6.5, 6.928203230275509))}}, {(31, 23, 24, 30, 32): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(17, 15, 39, 46)}, {(17, 15, 39, 46): [39, 46]}, {(17, 15, 39, 46): {17}}, {(17, 15, 39, 46): {15}}, {(17, 15, 39, 46): {((5.0, 6.06217782649107), (8.0, 7.794228634059947)), ((3.5, 5.196152422706632), (3.5, 3.4641016151377544)), ((5.0, 6.06217782649107), (9.0, 7.794228634059947))}}, {(17, 15, 39, 46): set()}))

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



    assert_answers(m, figures,contents,initiatives,walls,({(9, 15), (17, 15), (23, 15)}, {(9, 15): [15, 16], (17, 15): [15, 16], (23, 15): [15, 16]}, {(23, 15): {23}, (17, 15): {17}, (9, 15): {9}}, {(23, 15): {15}, (17, 15): {15}, (9, 15): {15}}, {(23, 15): {((5.0, 4.330127018922193), (4.5, 3.4641016151377544))}, (17, 15): {((3.5, 5.196152422706632), (3.5, 3.4641016151377544))}, (9, 15): {((3.0, 4.330127018922193), (3.5, 3.4641016151377544))}}, {(23, 15): set(), (17, 15): set(), (9, 15): set()}))

# The monster will avoid the trap to attack the character
def test_Scenario112():
    m=Monster(action_move=3)
    figures,contents,initiatives,walls = init_test()


    figures[15] = 'C'

    contents[16] = 'T'

    figures[18] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(8, 15), (22, 15)}, {(8, 15): [], (22, 15): []}, {(8, 15): {8}, (22, 15): {22}}, {(8, 15): {15}, (22, 15): {15}}, {(8, 15): {((3.5, 3.4641016151377544), (3.5, 3.4641016151377544))}, (22, 15): {((4.5, 3.4641016151377544), (4.5, 3.4641016151377544))}}, {(8, 15): set(), (22, 15): set()}))

# The jumping monster will avoid the trap to attack the character
def test_Scenario113():
    m=Monster(action_move=3, jumping=True)
    figures,contents,initiatives,walls = init_test()


    figures[15] = 'C'

    contents[16] = 'T'

    figures[18] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(8, 15), (22, 15)}, {(8, 15): [], (22, 15): []}, {(8, 15): {8}, (22, 15): {22}}, {(8, 15): {15}, (22, 15): {15}}, {(8, 15): {((3.5, 3.4641016151377544), (3.5, 3.4641016151377544))}, (22, 15): {((4.5, 3.4641016151377544), (4.5, 3.4641016151377544))}}, {(8, 15): set(), (22, 15): set()}))

# The flying monster will ignore the trap to attack the character
def test_Scenario114():
    m=Monster(action_move=3, flying=True)
    figures,contents,initiatives,walls = init_test()


    figures[15] = 'C'

    contents[16] = 'T'

    figures[18] = 'A'

    assert_answers(m, figures,contents,initiatives,walls,({(16, 15)}, {(16, 15): []}, {(16, 15): {16}}, {(16, 15): {15}}, {(16, 15): {((3.5, 3.4641016151377544), (3.5, 3.4641016151377544))}}, {(16, 15): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(16, 15)}, {(16, 15): []}, {(16, 15): {16}}, {(16, 15): {15}}, {(16, 15): {((3.5, 3.4641016151377544), (3.5, 3.4641016151377544))}}, {(16, 15): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(35, 16, 17, 18)}, {(35, 16, 17, 18): [16, 17, 18]}, {(35, 16, 17, 18): {35}}, {(35, 16, 17, 18): {16}}, {(35, 16, 17, 18): {((8.0, 2.598076211353316), (5.0, 4.330127018922193)), ((8.0, 2.598076211353316), (4.5, 5.196152422706632)), ((8.0, 2.598076211353316), (4.5, 6.928203230275509))}}, {(35, 16, 17, 18): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(35, 16)}, {(35, 16): [16, 23, 31]}, {(35, 16): {35}}, {(35, 16): {16}}, {(35, 16): {((8.0, 2.598076211353316), (5.0, 4.330127018922193))}}, {(35, 16): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(35, 58), (35, 16, 17, 18)}, {(35, 16, 17, 18): [16, 17, 18], (35, 58): [58, 65, 73]}, {(35, 16, 17, 18): {35}, (35, 58): {35}}, {(35, 16, 17, 18): {16}, (35, 58): {58}}, {(35, 58): {((9.5, 1.7320508075688772), (12.5, 3.4641016151377544))}, (35, 16, 17, 18): {((8.0, 2.598076211353316), (5.0, 4.330127018922193)), ((8.0, 2.598076211353316), (4.5, 5.196152422706632)), ((8.0, 2.598076211353316), (4.5, 6.928203230275509))}}, {(35, 58): set(), (35, 16, 17, 18): set()}))

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


    assert_answers(m, figures,contents,initiatives,walls,({(35, 58, 59, 60), (35, 16, 17, 18)}, {(35, 16, 17, 18): [16, 17, 18], (35, 58, 59, 60): [58, 59, 60]}, {(35, 16, 17, 18): {35}, (35, 58, 59, 60): {35}}, {(35, 16, 17, 18): {16}, (35, 58, 59, 60): {58}}, {(35, 58, 59, 60): {((9.0, 2.598076211353316), (12.5, 5.196152422706632)), ((9.0, 2.598076211353316), (12.5, 6.928203230275509)), ((9.5, 1.7320508075688772), (12.5, 3.4641016151377544))}, (35, 16, 17, 18): {((8.0, 2.598076211353316), (5.0, 4.330127018922193)), ((8.0, 2.598076211353316), (4.5, 5.196152422706632)), ((8.0, 2.598076211353316), (4.5, 6.928203230275509))}}, {(35, 58, 59, 60): set(), (35, 16, 17, 18): set()}))

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



    assert_answers(m, figures,contents,initiatives,walls,({(35, 58, 59, 60)}, {(35, 58, 59, 60): [58, 59, 60]}, {(35, 58, 59, 60): {35}}, {(35, 58, 59, 60): {58}}, {(35, 58, 59, 60): {((9.0, 2.598076211353316), (12.5, 5.196152422706632)), ((9.0, 2.598076211353316), (12.5, 6.928203230275509)), ((9.5, 1.7320508075688772), (12.5, 3.4641016151377544))}}, {(35, 58, 59, 60): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(51, 36)}, {(51, 36): []}, {(51, 36): {51}}, {(51, 36): {36}}, {(51, 36): {((11.0, 4.330127018922193), (9.5, 3.4641016151377544))}}, {(51, 36): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(38, 39)}, {(38, 39): []}, {(38, 39): {38}}, {(38, 39): {39}}, {(38, 39): {((9.0, 7.794228634059947), (9.0, 7.794228634059947))}}, {(38, 39): set()}))

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


    assert_answers(m, figures,contents,initiatives,walls,({(32, 39, 47)}, {(32, 39, 47): [39, 47]}, {(32, 39, 47): {32}}, {(32, 39, 47): {39}}, {(32, 39, 47): {((8.0, 7.794228634059947), (8.0, 7.794228634059947)), ((8.0, 7.794228634059947), (9.5, 8.660254037844386))}}, {(32, 39, 47): set()}))

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


    assert_answers(m, figures,contents,initiatives,walls,({(52, 17, 23, 26, 46, 51, 57, 58), (20, 8, 17, 23, 40, 46, 51, 58), (52, 17, 23, 40, 46, 51, 57, 58)}, {(20, 8, 17, 23, 40, 46, 51, 58): [8, 9, 15, 16, 17, 22, 23], (52, 17, 23, 40, 46, 51, 57, 58): [43, 44, 49, 50, 51, 57, 58], (52, 17, 23, 26, 46, 51, 57, 58): [43, 44, 49, 50, 51, 57, 58]}, {(20, 8, 17, 23, 40, 46, 51, 58): {20}, (52, 17, 23, 26, 46, 51, 57, 58): {52}, (52, 17, 23, 40, 46, 51, 57, 58): {52}}, {(20, 8, 17, 23, 40, 46, 51, 58): {51, 46}, (52, 17, 23, 26, 46, 51, 57, 58): {23}, (52, 17, 23, 40, 46, 51, 57, 58): {23}}, {(52, 17, 23, 26, 46, 51, 57, 58): {((12.0, 6.06217782649107), (12.5, 5.196152422706632)), ((11.0, 6.06217782649107), (4.5, 5.196152422706632)), ((10.5, 6.928203230275509), (6.5, 10.392304845413264)), ((12.0, 6.06217782649107), (13.5, 1.7320508075688772)), ((10.5, 6.928203230275509), (10.5, 6.928203230275509)), ((11.0, 6.06217782649107), (11.0, 6.06217782649107))}, (20, 8, 17, 23, 40, 46, 51, 58): {((5.0, 11.258330249197702), (7.5, 10.392304845413264)), ((3.5, 10.392304845413264), (3.5, 6.928203230275509)), ((3.5, 10.392304845413264), (5.0, 6.06217782649107)), ((5.0, 11.258330249197702), (12.5, 5.196152422706632)), ((5.0, 11.258330249197702), (12.0, 6.06217782649107)), ((4.5, 10.392304845413264), (3.5, 3.4641016151377544)), ((5.0, 11.258330249197702), (10.5, 6.928203230275509))}, (52, 17, 23, 40, 46, 51, 57, 58): {((12.0, 6.06217782649107), (12.5, 5.196152422706632)), ((11.0, 6.06217782649107), (4.5, 5.196152422706632)), ((12.0, 6.06217782649107), (13.5, 1.7320508075688772)), ((10.5, 6.928203230275509), (10.5, 6.928203230275509)), ((11.0, 6.06217782649107), (11.0, 6.06217782649107)), ((10.5, 6.928203230275509), (8.0, 9.526279441628825))}}, {(52, 17, 23, 26, 46, 51, 57, 58): set(), (20, 8, 17, 23, 40, 46, 51, 58): set(), (52, 17, 23, 40, 46, 51, 57, 58): set()}))


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
    m=Monster(action_move=1, action_range=1, action_target=2)
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

    assert_answers(m, figures,contents,initiatives,walls,({(37, 44, 45)}, {(37, 44, 45): []}, {(37, 44, 45): {37}}, {(37, 44, 45): {45}}, {(37, 44, 45): {((9.5, 5.196152422706632), (9.5, 5.196152422706632))}}, {(37, 44, 45): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(67, 53, 74, 76)}, {(67, 53, 74, 76): []}, {(67, 53, 74, 76): {67}}, {(67, 53, 74, 76): {53}}, {(67, 53, 74, 76): {((13.5, 8.660254037844386), (12.5, 8.660254037844386)), ((15.0, 9.526279441628825), (15.5, 10.392304845413264)), ((15.5, 8.660254037844386), (15.5, 8.660254037844386))}}, {(67, 53, 74, 76): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(40, 26, 38, 53)}, {(40, 26, 38, 53): []}, {(40, 26, 38, 53): {40}}, {(40, 26, 38, 53): {53}}, {(40, 26, 38, 53): {((9.5, 10.392304845413264), (11.0, 9.526279441628825)), ((7.5, 10.392304845413264), (6.5, 10.392304845413264)), ((8.0, 9.526279441628825), (8.0, 7.794228634059947))}}, {(40, 26, 38, 53): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(39, 26, 38, 53)}, {(39, 26, 38, 53): []}, {(39, 26, 38, 53): {39}}, {(39, 26, 38, 53): {53}}, {(39, 26, 38, 53): {((9.5, 8.660254037844386), (10.5, 8.660254037844386)), ((8.0, 7.794228634059947), (8.0, 7.794228634059947)), ((8.0, 9.526279441628825), (6.5, 10.392304845413264))}}, {(39, 26, 38, 53): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(39, 26, 38, 53)}, {(39, 26, 38, 53): []}, {(39, 26, 38, 53): {39}}, {(39, 26, 38, 53): {53}}, {(39, 26, 38, 53): {((9.5, 8.660254037844386), (10.5, 8.660254037844386)), ((8.0, 7.794228634059947), (8.0, 7.794228634059947)), ((8.0, 9.526279441628825), (6.5, 10.392304845413264))}}, {(39, 26, 38, 53): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(40, 26, 32, 53)}, {(40, 26, 32, 53): []}, {(40, 26, 32, 53): {40}}, {(40, 26, 32, 53): {53}}, {(40, 26, 32, 53): {((9.5, 10.392304845413264), (11.0, 9.526279441628825)), ((7.5, 10.392304845413264), (6.5, 10.392304845413264)), ((8.0, 9.526279441628825), (7.5, 8.660254037844386))}}, {(40, 26, 32, 53): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(52, 32)}, {(52, 32): []}, {(52, 32): {52}}, {(52, 32): {32}}, {(52, 32): {((10.5, 6.928203230275509), (7.5, 6.928203230275509))}}, {(52, 32): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(31, 32)}, {(31, 32): []}, {(31, 32): {31}}, {(31, 32): {32}}, {(31, 32): {((8.0, 6.06217782649107), (8.0, 7.794228634059947))}}, {(31, 32): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(33,)}, {(33,): []}, {(33,): {40, 34, 32, 39}}, {(33,): {75}}, {(33,): set()}, {(33,): set()}))

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

    assert_answers(m, figures,contents,initiatives,walls,({(89,)}, {(89,): []}, {(89,): {80, 94}}, {(89,): {31}}, {(89,): set()}, {(89,): set()}))