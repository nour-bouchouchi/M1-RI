
import heapq
import csv
import time
import json 

def seek_to_document(postings_list, curseur, d):
    """
    Fait avancer l'itérateur du terme t jusqu'au premier numéro 
    de document supérieur ou égal à d
    """
    for c,posting in enumerate(postings_list[curseur:]):
        if posting[0] >= d:
            return posting, c+curseur
    return None, len(postings_list)


def candidates(cursors, postings_list):
    for i in range(len(cursors)):
        if cursors[i]<len(postings_list[i]):
            return True
    return False

def maj_candidats(curseurs, postings_list):
    candidats = []
    for i in range(len(curseurs)):
        if curseurs[i] < len(postings_list[i]):
            candidats.append(postings_list[i][curseurs[i]])
    return candidats

def WAND(query, index, k, postings_clipping = False, list_splitting=False):
    postings_list = []
    liste_Ut = []
    curseurs = [] 
    candidats = [] #format (doc, score)
    if list_splitting:
        Ht_list_split = [] #pour list splitting (fait correspondre le H(t))
    for term in query :
        if term in index :
            if postings_clipping or list_splitting : 
                if index[term].get("H")!=None :
                    postings_list.append(sorted(index[term]["H"]["postings"], key=lambda x: x[0], reverse=False)) 
                    liste_Ut.append(index[term]["H"]["Ut"])
                    curseurs.append(0)
                    candidats.append(postings_list[-1][0])
                    if list_splitting :
                        Ht_list_split.append(0)
                if index[term].get("L")!=None :
                    postings_list.append(sorted(index[term]["L"]["postings"], key=lambda x: x[0], reverse=False)) 
                    liste_Ut.append(index[term]["L"]["Ut"])
                    curseurs.append(0)
                    candidats.append(postings_list[-1][0])
                    if list_splitting : 
                        if index[term].get("H")!=None :
                            Ht_list_split.append(liste_Ut[-2])
                        else : 
                            Ht_list_split.append(0)
                
            else : 
                #On trie les documents par ordre croissants
                postings_list.append(sorted(index[term]["postings"], key=lambda x: x[0], reverse=False)) 
                liste_Ut.append(index[term]["Ut"])
                curseurs.append(0)
                candidats.append(postings_list[-1][0])
        
    theta = float('-inf')  # Seuil initial
    Ans = []  # k-set of (d, s) values
    # Tant qu'il y a des candidats
    doc_pivot=-1
    while candidates(curseurs, postings_list):
        # Permutation des candidats pour avoir c0 <= c1 <= ... <= c|q|-1 (numéro de doc croissant parmis les candidats)
        candidats = maj_candidats(curseurs, postings_list)
        if list_splitting : 
            candidats, curseurs, postings_list, liste_Ut, Ht_list_split = zip(*sorted(zip(candidats, curseurs, postings_list, liste_Ut, Ht_list_split), key=lambda x: x[0]))
        else :
            candidats, curseurs, postings_list, liste_Ut = zip(*sorted(zip(candidats, curseurs, postings_list, liste_Ut), key=lambda x: x[0]))
        candidats = list(candidats)
        curseurs = list(curseurs)
        postings_list =  list(postings_list)
        liste_Ut = list(liste_Ut)
        if list_splitting : 
            Ht_list_split = list(Ht_list_split)
        
        score_limit = 0
        pivot = 0
        # Recherche du pivot
        while pivot < len(liste_Ut) - 1: 
            tmp_score_lim = score_limit + liste_Ut[pivot]

            if list_splitting :
                tmp_score_lim -= Ht_list_split[pivot]

            if tmp_score_lim > theta:
                break

            score_limit = tmp_score_lim
            pivot += 1
        doc_pivot = candidats[pivot][0]
        if candidats[0][0] == candidats[pivot][0]:
            s = 0  # Score du document cpivot
            t = 0

            while t < len(liste_Ut) and candidats[t][0]==doc_pivot:
                s += candidats[t][1]  # Contribution au score
                curseurs[t] += 1
                if curseurs[t]<len(postings_list[t])-1:
                    candidats[t] = postings_list[t][curseurs[t]]  # Posting suivant pour le terme t
                t+=1
            if s >= theta:  # Réponse possible pour les meilleures k réponses
                heapq.heappush(Ans,(doc_pivot,s))

                if len(Ans) > k:
                    Ans.remove(min(Ans, key=lambda x: x[1]))
                    theta = Ans[0][1]

        else:  # Impossible d'évaluer cpivot pour le moment
            for t in range(pivot):
                candidats[t], curseurs[t] = seek_to_document(postings_list[t], curseurs[t], doc_pivot)  # Déplacer le pointeur au document cpivot ou suivant

    return Ans


def all_queries(file, postings_clipping=False, list_splitting=False):
    queries = read_queries()
    with open(file, 'r') as f:
        print("load index")
        index = json.load(f)
        
        for k in [10,1000]:
            print("--- k =",k)
            start_time = time.time()
            cpt=0
            for query in queries:
                cpt+=1
                print(cpt)
                if postings_clipping :
                    WAND(query, index, k, postings_clipping = True)
                else : 
                    if list_splitting:
                        WAND(query, index, k, list_splitting = True)
                    else : 
                        WAND(query, index, k)
            end_time = time.time()
            total_time = end_time - start_time
            avg_time = total_time / len(queries)
            print("----- Le temps moyen par requête est de : ", avg_time)


def read_queries():
    """
    Permet de lire les 6980 dev queries
    """
    list_queries = []
    with open('queries/msmarco-passage/queries.dev.small.tsv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter='\t')
        for row in reader:
            query_text = row[1]
            query_tokens = query_text.split()
            list_queries.append(query_tokens)
    return list_queries[:100]


if __name__ == '__main__':
    print("==== DeepImpact ====")
    
    print("Index inversé sans traitement : ")
    all_queries("indexes/inverted_index_deepimpact.json")

    print("Postings : ")
    all_queries("indexes/index_postings_deepimpact.json", postings_clipping=True)

    print("List splitting : ")
    all_queries("indexes/index_splitting_deepimpact.json", list_splitting=True)


    print("\n==== BM25 ====")
    
    print("Index inversé sans traitement : ")
    all_queries("indexes/inverted_index_bm25.json")

    print("Postings : ")
    all_queries("indexes/index_postings_bm25.json", postings_clipping=True)


    print("List splitting : ")
    all_queries("indexes/index_splitting_bm25.json", list_splitting=True)
