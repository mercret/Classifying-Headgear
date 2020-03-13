import sys
import json

if __name__=='__main__':
    input1 = sys.argv[1]
    f1 = open(input1, 'r')
    sorted_players = json.load(f1)
    f1.close()
    input2 = sys.argv[2]
    f2 = open(input2, 'r')
    scored_players = json.load(f2)
    f2.close()

    scores = {'GRYFFINDOR': 0, 'RAVENCLAW': 0, 'SLYTHERIN': 0, 'HUFFLEPUFF': 0}
    nr_of_players = {'GRYFFINDOR': 0, 'RAVENCLAW': 0, 'SLYTHERIN': 0, 'HUFFLEPUFF': 0}
    for p1, p2 in zip(sorted_players['players'], scored_players['players']):
        # double check
        assert(p1['name'] == p2['name'])
        assert(p1['playerId'] == p2['playerId'])
        scores[p1['house']] += p2['score']
        nr_of_players[p1['house']] += 1
    for s in scores:
        scores[s] = round(scores[s] / nr_of_players[s]) 
    f = open('scores.json', 'w')
    json.dump(scores, f)
    f.close()

    

