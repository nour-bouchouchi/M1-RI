import os
import sys
import json

def postings_clipping(folder, bm25=False):
    new_index = {}

    with open(folder,'r') as f:
        index = json.load(f)

        # pour chaque terme dans l'index
        cpt = 0
        nb_mots = len(index)
        for word, data in index.items():
            cpt+=1
            if cpt%1000==0:
                print("---"+str(cpt)+"/"+str(nb_mots))

            postings = data["postings"]

            # Si le terme de l'index a plus de 256 postings (sinon on met tout dans L)
            if len(postings) > 256:
                # On ordonne les postings par ordre décroissants
                postings = sorted(postings, key=lambda x: x[1], reverse=True)

                # Nombre de postings dans H au max (de façon à ce que le plus bas score de H soit supérieur au meilleur de L)
                len_H = len(postings) // 64
                min_score_H = postings[len_H][1] 
                max_score_L = postings[len_H+1][1] 
                while not min_score_H > max_score_L and len_H>0: 
                    len_H -=1
                    min_score_H = postings[len_H][1] 
                    max_score_L = postings[len_H+1][1] 

                if len_H<=1:
                    new_index[word] = {'L': {'postings' : postings, 'Ut' : data["Ut"]}}
                else : 
                    # On crée les listes L et H
                    postings_L = []
                    postings_H = []

                    for doc, score in postings:
                        if score > max_score_L:
                            postings_H.append((doc, score-max_score_L))
                        postings_L.append((doc, min(score, max_score_L)))
                    
                    # On calcule les valeurs Ut pour L et H
                    Ut_L = postings_L[0][1]
                    Ut_H = postings_H[0][1] 
                    
                    # On ajoute les termes dans le nouvel index :
                    new_index[word] = {'L': {'postings' : postings_L, 'Ut' : Ut_L}, 'H': {'postings' : postings_H, 'Ut' : Ut_H}}
            else :
                new_index[word] = {'L': {'postings' : postings, 'Ut' : data["Ut"]}}
    
    f.close()
    
    print("write index")
    if bm25==True :
        with open('indexes/index_postings_bm25.json', 'w') as f:
            json.dump(new_index, f)
    else :
        with open('indexes/index_postings_deepimpact.json', 'w') as f:
            json.dump(new_index, f)
    print("done")

if __name__ == '__main__':

    if len(sys.argv) > 1:
        print("BM25")
        file_path = 'indexes/inverted_index_bm25.json' 
        postings_clipping('indexes/inverted_index_bm25.json', True)
    else:
        print("DeepImpact")
        file_path = 'indexes/inverted_index_deepimpact.json'  
        postings_clipping('indexes/inverted_index_deepimpact.json')
