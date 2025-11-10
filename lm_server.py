import re

from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer
from sentence_transformers import util
import torch

app = Flask(__name__)
app.config['global_model']=SentenceTransformer('sentence-transformers/msmarco-distilbert-base-tas-b')
@app.route('/flip', methods=['POST'])
def flip_string():
    data = request.get_json()
    string_to_flip = data.get('string', '')
    flipped_string = string_to_flip[::-1]
    return jsonify({'flipped': flipped_string})

def retrieve_top_docs(query, docs, model, width=3):
    query_emb = model.encode(query)
    doc_emb = model.encode(docs,)
    scores = util.dot_score(query_emb, doc_emb)[0].tolist()
    # scores = util.dot_score(query_emb, doc_emb)[0].cpu().tolist()

    doc_score_pairs = sorted(list(zip(docs, scores)), key=lambda x: x[1], reverse=True)

    top_docs = [pair[0] for pair in doc_score_pairs[:width]]
    top_scores = [pair[1] for pair in doc_score_pairs[:width]]

    return top_docs, top_scores


def retrieve_top_docs_cos_chunk(query, docs, model, width=3, chunk_size=1024):
    query_emb = model.encode(query)
    doc_embeddings = []

    for doc in docs:
        # Split document into chunks
        chunks = [doc[i:i + chunk_size] for i in range(0, len(doc), chunk_size)]
        chunk_embeddings = model.encode(chunks)
        # Average the embeddings of the chunks
        chunk_embeddings_tensor = torch.from_numpy(chunk_embeddings)
        doc_emb = torch.mean(chunk_embeddings_tensor, dim=0)
        doc_embeddings.append(doc_emb)
    if not doc_embeddings:
        print(query)
        print(docs)
        return [], []
    doc_embeddings = torch.stack(doc_embeddings)
    scores = util.cos_sim(query_emb, doc_embeddings)[0].tolist()

    doc_score_pairs = sorted(list(zip(docs, scores)), key=lambda x: x[1], reverse=True)

    top_docs = [pair[0] for pair in doc_score_pairs[:width]]
    top_scores = [pair[1] for pair in doc_score_pairs[:width]]

    return top_docs, top_scores

def retrieve_top_docs_cos(same_part,query, docs, model, width=3):
    """
    Retrieve the topn most relevant documents for the given query.

    Parameters:
    - query (str): The input query.
    - docs (list of str): The list of documents to search from.
    - model_name (str): The name of the SentenceTransformer model to use.
    - width (int): The number of top documents to return.

    Returns:
    - list of float: A list of scores for the topn documents.
    - list of str: A list of the topn documents.
    """

    query_emb = model.encode(query)
    doc_emb = model.encode(docs)
    scores = util.cos_sim(query_emb, doc_emb)[0].tolist()
    # scores = util.dot_score(query_emb, doc_emb)[0].cpu().tolist()

    doc_score_pairs = sorted(list(zip(docs, scores)), key=lambda x: x[1], reverse=True)

    top_docs = [pair[0] for pair in doc_score_pairs[:width]]
    top_scores = [pair[1] for pair in doc_score_pairs[:width]]

    return top_docs, top_scores


def calculate_score(query, docs, model):
    query_emb = model.encode(query)
    doc_emb = model.encode(docs)
    scores = util.cos_sim(query_emb, doc_emb)[0].tolist()
    return scores


@app.route('/sentence_transformer', methods=['POST'])
def sentence_transformer():
    model=app.config['global_model']
    data = request.get_json()
    width = int(data.get('width', ''))
    question=data.get('question', '')
    total_relations=data.get('total_relations', '')
    total_relations_list = total_relations.split('&;& ') if total_relations else []
    total_relations_list = [rel.strip() for rel in total_relations_list]

    topn_relations, topn_scores = retrieve_top_docs(question, total_relations_list, model, width)
    return jsonify({'topn_relations': topn_relations,'topn_scores': topn_scores})

@app.route('/sentence_transformer_cos_list', methods=['POST'])
def sentence_transformer_cos_list():
    model=app.config['global_model']
    data = request.get_json()
    width = int(data.get('width', ''))
    question=data.get('question', '')
    total_relations=data.get('total_relations', '')
    same_part=data.get('same_part', '')

    question=re.sub(same_part, "&*&", question, flags=re.IGNORECASE)
    total_relations=re.sub(same_part, "&*&", total_relations, flags=re.IGNORECASE)

    total_relations_list = total_relations.split('&;& ') if total_relations else []
    total_relations_list = [rel.strip() for rel in total_relations_list]
    try:
        topn_relations, topn_scores = retrieve_top_docs_cos(same_part, question, total_relations_list, model, width)
    except:
        topn_relations, topn_scores = retrieve_top_docs_cos_chunk(question, total_relations_list, model, width)
    return jsonify({'topn_relations': topn_relations,'topn_scores': topn_scores})


@app.route('/sentence_transformer_cos', methods=['POST'])
def sentence_transformer_cos():
    model=app.config['global_model']
    data = request.get_json()
    width = int(data.get('width', ''))
    question=data.get('question', '')
    relation=data.get('relation', '')
    # print(relation)
    cos_score=calculate_score(question, relation, model)
    return jsonify({'cos_score': cos_score})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)




