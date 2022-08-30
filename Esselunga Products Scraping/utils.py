keys = {
    # PERMANENT INFO
    'email': '----',
    'password': '----',
    'scrap_categ' : 'https://www.esselungaacasa.it/ecommerce/nav/auth/supermercato/home.html#!/negozio/menu/',
    'menu_categ': {
        'frutta_verdura': 300000000002314,
        'pesce': 300000000002027,
        'carne': 300000000002007,
        'latticini' : 300000000002343,
        'alimenti_veg' : 300000000006876,
        'pane_pasticceria' : 300000000002050,
        'gastronomia': 300000000002033,
        'colazione' : 300000000011197,
        'snack': 300000000019692,
        'confezionati' : 300000000002399,
        'surgelati': 300000000002075,
        'bibite' : 300000000002062,
        'alcolici' : 300000000002081,
    }

}

class Product():
    def __init__(self,prod_id,prod_name,discounted,prod_price):
        self.id = prod_id
        self.name = prod_name
        self.discounted = discounted
        self.price = prod_price

