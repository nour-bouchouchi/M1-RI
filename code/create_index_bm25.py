import os
import json

def create_index(folder):
    inverted_index = {}
    # On parcourt tous les fichiers pour indexer les 1 000 000 de passages
    # qu'on avait indexé avec deeimpact
    nb_passages = 0
    for filename in os.listdir(folder):
        if filename.endswith('jsonl') :
            with open(os.path.join(folder, filename),'r') as f:
                print("start indexing : ", filename)
                # On récupère les objets (passages) du fichier json
                for line in f : 
                    passage = json.loads(line)
                    # On ne récupère que les passages utilisés avec deepimpact
                    if int(passage["id"])<1000000:
                        nb_passages+=1
                        if nb_passages%10000==0:
                            print("---"+str(nb_passages)+"/1000000")
                        for word, score in passage['vector'].items():
                            if word not in inverted_index:
                                inverted_index[word] = {'postings': [], 'Ut': None}
                            inverted_index[word]['postings'].append((int(passage['id']), int(score))) 
                f.close()

    # On ajoute le champ Ut pour chaque word
    print("add Ut")
    cpt = 0
    nb_mots = len(inverted_index)
    for word in inverted_index:
        cpt+=1
        if cpt%10000==0:
            print("---"+str(cpt)+"/"+str(nb_mots))
        postings = inverted_index[word]['postings']
        ut = max(postings, key=lambda x: x[1])[1]
        inverted_index[word]['Ut'] = ut
        

    print("write index")
    with open('indexes/inverted_index_bm25.json', 'w') as f:
        json.dump(inverted_index, f)
        

     
    
if __name__ == '__main__':
    create_index('collections/msmarco-passage-bm25-b8')
