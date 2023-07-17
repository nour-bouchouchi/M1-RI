import heapq
import json
import csv
import time

def seekgeq(postings_list, d):
    """
    Fonction pour chercher et retourner la position dans une liste de postings
    où le docnum est supérieur ou égal à la valeur donnée `d`.
    """
    position = 0
    while position < len(postings_list) and postings_list[position][0] < d:
        position += 1
    return position

def argmax(liste):
    """
    Fonction pour récupérer l'argmax (numpy ne fonctionne pas en ssh...)
    """
    max_val = float('-inf')
    max_idx = -1

    for i in range(len(liste)):
        if liste[i][0] > max_val:
            max_val = liste[i][0]
            max_idx = liste[i][1]

    return max_idx

def maxscore(postings_lists, Ut, k, list_splitting=False, dico_corresp=None):
    """
    Algorithme MaxScore pour trouver les k meilleurs documents à partir des listes de postings
    en utilisant les valeurs Ut précalculées pour chaque terme.
    """
    q = len(postings_lists)         # nombre de termes dans la liste des postings
    active = set(range(q))          # termes actifs
    passive = set()                 # termes passifs
    sum_pass = 0                    # somme des valeurs Ut des termes passifs
    heap = []                       # tas des meilleurs documents trouvés jusqu'à présent
    c = [0] * q                     # curseurs pour chaque terme                  
    theta = float('-inf')           # seuil du tas des meilleurs documents

    cpt=0
    while active and cpt<1000000:
        # Sélectionner le prochain document en cherchant la valeur minimale parmi les cursors des termes actifs
        min_postings = [(postings_lists[t][c[t]][0], t) for t in active if c[t] < len(postings_lists[t])]
        if not min_postings:
            break
        d = min(min_postings)[0]
        # Mettre à jour les cursors pour les termes passifs
        for t in passive:
            c[t] = seekgeq(postings_lists[t], d)
        
        # Calculer le score du document en additionnant les impacts scores des postings correspondants
        score = sum(postings_lists[t][c[t]][1] for t in active if c[t] < len(postings_lists[t]) and postings_lists[t][c[t]][0] == d )
        
        # Mettre à jour les cursors pour les termes actifs
        for t in active:                        
            if c[t] < len(postings_lists[t]) and postings_lists[t][c[t]][0] == d:
                c[t] += 1

        # Vérifier le score par rapport au tas des meilleurs documents et mettre à jour si nécessaire
        if score > theta:
            heapq.heappush(heap, (score, d))
            if len(heap) > k:
                heapq.heappop(heap)
                theta = heap[0][0]

        # Expansion de l'ensemble passif si nécessaire
        if cpt%1000==0 : 
            lg_postings = [(len(postings_lists[t]),t) for t in active]
            if lg_postings:
                y = argmax(lg_postings)
                if sum_pass + Ut[y] < theta:
                    active.remove(y)
                    passive.add(y)
                    if list_splitting==True and dico_corresp.get(y)!=None:
                        sum_pass += (Ut[y] - dico_corresp.get(y))
                    else : 
                        sum_pass += Ut[y]
        cpt+=1
        
    return heapq.nlargest(k, heap)

def one_query(query, postings, k):
    postings_query = []
    liste_Ut = []
    for term in query :
        if term in postings :
            postings_query.append(sorted(postings[term]["postings"], key=lambda x: x[1], reverse=False))
            liste_Ut.append(postings[term]["Ut"])
    maxscore(postings_query, liste_Ut, k)

def one_query_postings(query, postings, k):
    postings_query = []
    liste_Ut = []
    for term in query :
        if term in postings :
            if postings[term].get("L")!=None : 
                postings_query.append(sorted(postings[term]["L"]["postings"], key=lambda x: x[1], reverse=False))
                liste_Ut.append(postings[term]["L"]["Ut"])
            if postings[term].get("H")!=None:
                postings_query.append(sorted(postings[term]["H"]["postings"], key=lambda x: x[1], reverse=False))
                liste_Ut.append(postings[term]["H"]["Ut"])
    maxscore(postings_query, liste_Ut, k)

def one_query_list(query, postings, k):
    postings_query = []
    liste_Ut = []
    dico = {} #fait correspondre à l'indice de H avec le score U_L(t)
    for term in query :
        if term in postings :
            if postings[term].get("L")!=None : 
                postings_query.append(sorted(postings[term]["L"]["postings"], key=lambda x: x[1], reverse=False))
                liste_Ut.append(postings[term]["L"]["Ut"])
            if postings[term].get("H")!=None:
                postings_query.append(sorted(postings[term]["H"]["postings"], key=lambda x: x[1], reverse=False))
                liste_Ut.append(postings[term]["H"]["Ut"])
                dico[len(postings_query)-1] = postings[term]["L"]["Ut"]
    maxscore(postings_query, liste_Ut, k, list_splitting=True, dico_corresp=dico)

def all_queries(file, postings_clipping=False, list_splitting=False):
    queries = read_queries()
    with open(file, 'r') as f:
        print("load index")
        postings = json.load(f)
        
        for k in [1000]:
            print("--- k =",k)
            start_time = time.time()
            for query in queries:
                if postings_clipping :
                    one_query_postings(query, postings, k)
                else :
                    if list_splitting:
                        one_query_list(query, postings, k)
                    else : 
                        one_query(query, postings, k)
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
    
