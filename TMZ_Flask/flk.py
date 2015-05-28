from flask import Flask
from flask import render_template
#from models import db
from flask_sqlalchemy import SQLAlchemy

from alchemyapi import AlchemyAPI
from collections import defaultdict

 
 
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db'

db = SQLAlchemy(app)
       
class Entities(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer)
    name = db.Column(db.String)
    type = db.Column(db.String)
    relevance = db.Column(db.Float)
    sentiment = db.Column(db.String)
    sentiment_score = db.Column(db.Float)

    def __init__(self, article_id, name, type, relevance, sentiment, sentiment_score):
        self.article_id = article_id
        self.name = name
        self.type = type
        self.relevance = relevance
        self.sentiment = sentiment
        self.sentiment_score = sentiment_score

class Cooccurrences(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entity1 = db.Column(db.String)
    entity2 = db.Column(db.String)
    count = db.Column(db.Integer)

    def __init__(self, entity1, entity2, count):
        self.entity1 = entity1
        self.entity2 = entity2
        self.count = count
 
@app.route("/")
def hello():
    return "Welcome to the hater score"
 
@app.route('/extract_entities')
def extract_entities():
         
    #####Get Alchemy Response######
    demo_urls = ['http://www.nhl.com/ice/news.htm?id=758474&navid=nhl:topheads','http://www.nhl.com/gamecenter/en/recap?id=2014030227&navid=nhl:topheads']
    for article_id,demo_url in enumerate(demo_urls):
        # Create the AlchemyAPI Object
        alchemyapi = AlchemyAPI()
        response = alchemyapi.text('url', demo_url)
            
        #Article text
        if response['status'] == 'OK':
            footer_line_start = "NHL.com is the official web site of the National Hockey League" 
            demo_text = response['text'].encode('utf-8') #save text here and make text calls instead of url calls later on
            demo_text = demo_text.split(footer_line_start)[0] 
            
        #Perform entity extraction
        response = alchemyapi.entities('text', demo_text, {'sentiment': 1}) #can replace with 'text', demo_text
            
        if response['status'] == 'OK':
            for id,entity in enumerate(response['entities']):
                entity_name = entity['text'].encode('utf-8')
                entity_type = entity['type']
                entity_relevance =  entity['relevance']
                entity_sentiment = entity['sentiment']['type']
                if 'score' in entity['sentiment']:
                    entity_score = entity['sentiment']['score']
                else:
                    entity_score = 0 #it has no entity score if it is neutral so just give it a zero score for consistency in db
            
                #Store entities in db
                e = Entities(article_id,entity_name, entity_type, entity_relevance,entity_sentiment,entity_score)
                db.session.add(e)
            db.session.commit() #before it was in loop, see if it works outside of looop
    
    return "Entities successfully extracted"    

@app.route('/retrieve_entities')
def retrieve_entities():
    avg_sentiment_scores = []
    all_entities = Entities.query.all()
    unique_entities_names = []
    [unique_entities_names.append(ent.name) for ent in all_entities if ent.name not in unique_entities_names]
    for unique_entities_name in unique_entities_names:
        sentiment_scores = [entity.sentiment_score for entity in all_entities if entity.name == unique_entities_name] 
        avg_sentiment_score = sum(sentiment_scores)/len(sentiment_scores)
        avg_sentiment_scores.append((unique_entities_name,avg_sentiment_score))
    return render_template('avg_entity_scores.html', title='Average sentiment scores per entity', scores = avg_sentiment_scores )
     
@app.route('/calculate_cooccurrences')
def calculate_cooccurrences():
    #default dict enters value in dictionary if it doesn't exist instead of return an error
    #it also looks like we have a nested dictionary here
    num_articles = 2
    matrix = defaultdict(lambda : defaultdict(int))
    ### Two entities co-occur together if they are present in the same article
    ### So for each article
    for article_id in range(num_articles): 
        ###Retrieve a list of entities in the article
        entities = Entities.query.filter_by(article_id = article_id).all()
        ###Remove any duplicate entities
        unique_entities_names = []
        [unique_entities_names.append(ent.name) for ent in entities if ent.name not in unique_entities_names]
        
        #populate the co-occurrence matrix  
        for i in range(len(unique_entities_names)):
            for j in range(i,len(unique_entities_names)):
                if i != j: #so that we don't calculate co-occurrence with itself
                    entity1, entity2 = [unique_entities_names[i],unique_entities_names[j]]
                    matrix[entity1][entity2] +=1
                    matrix[entity2][entity1] +=1
                    
                
    #Store the co-occurence matrix in the db
    for entity1 in matrix.iterkeys():
        for k, entity2 in enumerate(matrix[entity1].keys()):
            cooccurrence_count = matrix[entity1].values()[k]
            c = Cooccurrences(entity1,entity2,cooccurrence_count) 
            db.session.add(c)
    db.session.commit()            
    
    return "Co-occurrences calculated"

@app.route('/retrieve_cooccurrences')
def retrieve_cooccurrences():
    cooccurences = Cooccurrences.query.order_by(Cooccurrences.count.desc()).all()
    return render_template('occurrences.html', title='Entity cooccurences', cooccurences = cooccurences)

#calculate_cooccurrences()

#when debugging, comment out the line below 
if __name__ == "__main__":
    app.run()


