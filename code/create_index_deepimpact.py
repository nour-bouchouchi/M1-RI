import os
import json

def create_index(folder):
    inverted_index = {}
    # On n'indexe que les deux premiers fichiers (1 000 000 de passages)
    for filename in os.listdir(folder):
        if filename.endswith('.json') and int(filename[-7:-5])<2:
            with open(os.path.join(folder, filename),'r') as f:
                print("start indexing : ", filename)
                # On récupère les objets (passages) du fichier json
                for line in f : 
                    passage = json.loads(line)                
                    for word, score in passage['vector'].items():
                        if word not in inverted_index:
                            inverted_index[word] = {'postings': [], 'Ut': None}
                        inverted_index[word]['postings'].append((passage['id'], score)) 
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
    with open('indexes/inverted_index_deepimpact.json', 'w') as f:
        json.dump(inverted_index, f)
        

     
    
if __name__ == '__main__':
    create_index('collections/msmarco-passage-deepimpact')

