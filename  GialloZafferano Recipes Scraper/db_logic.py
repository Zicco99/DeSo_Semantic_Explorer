from sqlalchemy.sql.functions import func
from sqlalchemy.sql.schema import ForeignKey, MetaData
from sqlalchemy import create_engine,Column, String, Integer,inspect, update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('postgresql://zicco:chilledpanda@localhost:5432/appspesa')
Base = declarative_base()
session = None 

r=None

class Recipe(Base):
    __tablename__ = 'recipe'
    
    name = Column(String, primary_key=True)
    link = Column(String)
    presentation = Column(String)
    difficulty = Column(Integer)
    time = Column(Integer)
    doses = Column(String)

    def __str__(self):
        return ' : ID: {self.name}\n '.format(self=self)
    
    def __init__(self,rec_name,rec_link,pres,diff,time,doses):
        self.name = rec_name
        self.link = rec_link
        self.presentation = pres
        self.difficulty = diff
        self.time = time
        self.doses = doses

class Ingredient(Base):
    __tablename__ = 'ingredient'

    name = Column(String, primary_key=True)
    
    def __init__(self,ingr_name):
        self.name = ingr_name
        self.n = 1

def recipe_exits(rec_name):
    recipe_check = session.query(Recipe).filter_by(name=rec_name).first()
    return recipe_check is not None

def insert_recipe(rec_name,rec_link,pres,infos,ingredients,steps):
    #fare un controllo se manca un informazione
    if (infos == []):
        return
    check_ingredients(ingredients)
    diff,time,doses = info_parser(infos)

    r = Recipe(rec_name,rec_link,diff,time,doses,pres)

    try:
        session.add(r)
        session.commit()
    except:
        session.rollback()

    #Aggiungi al database

def db_init():
    global session
    Session = sessionmaker(bind=engine) 
    session = Session()
    #Uncomment if you want to clean database

    Recipe.__table__.drop(engine)
    Ingredient.__table__.drop(engine)
    
    #Create tables that are not in database
    if(not inspect(engine).has_table("recipe")):
        Recipe.__table__.create(engine)
    
    if(not inspect(engine).has_table("ingredient")):
        Ingredient.__table__.create(engine)

    
def info_parser(infos):
    time = 0
    diff = 0
    for info in infos:
        type_value = info.split(':')
        match type_value[0]:
            case "Difficoltà":
                match type_value[1][1:]:
                    case "Molto facile":
                        diff = 0
                    case "Facile":
                        diff = 1
                    case "Media":
                        diff = 2
                    case "Difficile":
                        diff = 3
                    case default:
                        print(type_value)
            
            case "Costo":
                match type_value[1][1:]:
                    case "Molto basso":
                        diff = 0
                    case "Basso":
                        diff = 1
                    case "Medio":
                        diff = 2
                    case "Elevato":
                        diff = 3
                    case default:
                        print(type_value)

            case "Preparazione":
                time+= int([int(s) for s in type_value[1].split() if s.isdigit()][0])

            case "Cottura":
                time+= int([int(s) for s in type_value[1].split() if s.isdigit()][0])

            case "Dosi per":
                doses = type_value[1]

            case default:
                print(type_value)
    
    return diff,time,doses

def check_ingredients(ingrs):
    for ingr in ingrs:
        #Extract ingr
        ingr.index



        recipe_check = session.query(Ingredient).filter_by(name=ingr).first()
        if(recipe_check is not None):
            session.query(Ingredient).\
            filter(Ingredient.name == ingr).\
            update({'n': Ingredient.n + 1})
            session.commit()
        else:
            i = Ingredient(ingr)
            try:
                session.add(i)
                session.commit()
            except:
                session.rollback()

