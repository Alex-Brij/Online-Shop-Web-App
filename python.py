from flask import Flask, render_template, session, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import SubmitField, IntegerField, HiddenField
from wtforms.validators import InputRequired
from flask_bootstrap import Bootstrap


app = Flask(__name__)
app.config['SECRET_KEY'] = 'lily!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.sqlite3'
db = SQLAlchemy(app)
bootstrap = Bootstrap(app)
app.app_context().push()

# table to hold items
class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)
    price = db.Column(db.Integer)
    environmental_impact = db.Column(db.Integer)
    image = db.Column(db.String)

# method to add an item to the table
    @staticmethod
    def add_item(name, description, price, image):
        item = Item(name=name, description=description, price=price, image=image)
        db.session.add(item)
        db.session.commit()
        return item
    
# method to display item as its name   
    def __repr__(self):
        return f'{self.name}'


class Basket_item(db.Model):
    __tablename__ = 'basket'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'))
    quantity = db.Column(db.Integer)


    def add_item_to_basket(item_id, quantity):
        exists = db.session.query(db.exists().where(Basket_item.item_id == item_id)).scalar()
        if exists:
            item = Basket_item.query.filter_by(item_id=item_id).first()
            old_quantity = item.quantity
            new_quantity = old_quantity + int(quantity)
            Basket_item.query.filter_by(item_id=item_id).delete()
            item = Basket_item(item_id=item_id, quantity=int(new_quantity))
            db.session.add(item) 
        else:
            item = Basket_item(item_id=item_id, quantity=int(quantity))
            db.session.add(item)

        db.session.commit()
        return item
    

    def remove_item_from_basket(item_id):
        #item = Basket_item(item_id = item_id)
        Basket_item.query.filter_by(item_id=item_id).delete()
        db.session.commit()
        #return item



# renders home page with all items from database
# if number entered in form for adding items to bsket it gets the number and prints it
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        quantity = request.form['quantity']
        item_id = request.form['item_id']
        
        print(f'{quantity} {item_id} added to basket')
        Basket_item.add_item_to_basket(item_id, quantity)
        return redirect(url_for('home')) 
    return render_template('home.html', items=Item.query.all())

# gets the item that has been clicked on and sends user to item page which is now showing the information specific to that item 
@app.route('/item', methods=['GET', 'POST'])
def item():
    selected_item = request.args.get('type')
    print(selected_item)
    return render_template('item.html', item=Item.query.filter_by(name=selected_item).first())


@app.route('/basket', methods=['GET', 'POST'])
def basket():
    if request.method == 'POST':
        item_id = request.form['item_id']
        print(f'{item_id} removed from basket')
        Basket_item.remove_item_from_basket(item_id)
        return redirect(url_for('basket'))
    return render_template('basket.html', basket=Basket_item.query.all())


if __name__ == '__main__':
    db.create_all()
    if Item.query.filter_by(name='table').first() is None:
        Item.add_item('table', 'wooden thing to hold plates', 100, 'table.jpg')
    if Item.query.filter_by(name='chair').first() is None:
        Item.add_item('chair', 'wooden thing to sit on', 50, 'chair.jpg')
    app.run(debug=True)