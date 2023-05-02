from flask import Flask, render_template, session, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import SubmitField, IntegerField, HiddenField, StringField, PasswordField, BooleanField, SelectField
from wtforms.validators import InputRequired, Length, NumberRange, ValidationError
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.config['SECRET_KEY'] = 'lily!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.sqlite3'
db = SQLAlchemy(app)
bootstrap = Bootstrap(app)
# initialise main class of flask_login- LoginManager, stored in lm global variable
lm = LoginManager(app)
# needs to know where login page is. Sends login view to endpoint name of login route (name of function that handles that request)
# in this case function is called login
lm.login_view = 'login'
app.app_context().push()

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(1, 16)])
    password = PasswordField('Password', validators=[InputRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Submit')

class SortingForm(FlaskForm):
    order = SelectField('Sort By', choices=[('Name'), ('Price'), ('Environmental Impact')])
    submit = SubmitField('Sort')

class CheckoutForm(FlaskForm):
    # def validate_cardnumber(form, field):
    #     text = str(field.data)
    #     if len(text) != 16:
    #         raise ValidationError('Card number must be 16 digits long')
        
    # def validate_cvc(form, field):
    #     text = str(field.data)
    #     if len(text) != 3:
    #         raise ValidationError('CVC must be 3 digits long')
                
    name = StringField('Name on Card', validators=[InputRequired(), Length(1, 32)])
    cardnumber = IntegerField('Card Number', validators=[InputRequired()])
    expiry_date_month = SelectField('Expiry Month', choices=list(range(1, 13)))
    expiry_date_year = SelectField('Expiry Year', choices=list(range(2023, 2034)))
    cvc = IntegerField('CVC', validators=[InputRequired()])
    #Checkout = SubmitField('Checkout and Pay')



class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(16), index=True, unique=True)
    password_hash = db.Column(db.String(64))


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def register(username, password):
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    def __repr__(self):
        return '<User {0}>'.format(self.username)
    
@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.verify_password(form.password.data):
            return redirect(url_for('login', **request.args))
        login_user(user, form.remember_me.data)
        session['userid']=user.id
        return redirect(request.args.get('next') or url_for('home'))
    return render_template('login.html', form=form, status=current_user.is_authenticated)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


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
    def add_item(name, description, price, image, environmental_impact):
        item = Item(name=name, description=description, price=price, image=image, environmental_impact=environmental_impact)
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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


# method to add item to basket
    def add_item_to_basket(item_id, quantity, current_user):
        exists = db.session.query(db.exists().where((Basket_item.item_id == item_id) & (Basket_item.user_id == current_user))).scalar()
        if exists:
            item = Basket_item.query.filter_by(item_id=item_id, user_id=current_user).first()
            old_quantity = item.quantity
            new_quantity = old_quantity + int(quantity)
            Basket_item.query.filter_by(item_id=item_id, user_id=current_user).delete()
            item = Basket_item(item_id=item_id, quantity=int(new_quantity), user_id = current_user)
            db.session.add(item) 
        else:
            item = Basket_item(item_id=item_id, quantity=int(quantity), user_id = current_user)
            db.session.add(item)

        db.session.commit()
        return item
    

# method to change quantity of items in basket 
    def change_quantity(item_id, quantity, current_user):
        if int(quantity) > 0:
            item = Basket_item.query.filter_by(item_id=item_id, user_id=current_user).first()
            item.quantity = int(quantity)
        else:
            Basket_item.query.filter_by(item_id=item_id, user_id=current_user).delete()

        db.session.commit()


# renders home page with all items from database
# if number entered in form for adding items to bsket it gets the number and prints it
@app.route('/', methods=['GET', 'POST'])
def home():
    form = SortingForm()
    items = Item.query.all()
    if form.validate_on_submit():
        if form.order.data == 'Name':
            items = Item.query.order_by(Item.name).all()
        elif form.order.data == 'Price':
            items = Item.query.order_by(Item.price).all()
        elif form.order.data == 'Environmental Impact':
            items = Item.query.order_by(Item.environmental_impact).all()

    elif request.method == 'POST':
        print(current_user.is_authenticated)
        if current_user.is_authenticated is False:
            return redirect(url_for('login'))
        else:
            quantity = request.form['quantity']
            item_id = request.form['item_id']
            print(f'{quantity} {item_id} added to basket')
            Basket_item.add_item_to_basket(item_id, quantity, session['userid'])
            return redirect(url_for('home')) 
        
    return render_template('home.html',form=form, items=items)


# gets the item that has been clicked on and sends user to item page which is now showing the information specific to that item 
@app.route('/item', methods=['GET', 'POST'])
def item():
    selected_item = request.args.get('type')
    #print(selected_item)
    if request.method == 'POST':
        quantity = request.form['quantity']
        item_id = request.form['item_id']
        print(f'{quantity} {item_id} added to basket')
        Basket_item.add_item_to_basket(item_id, quantity, session['userid'])
        return redirect(url_for('item')) 
    return render_template('item.html', item=Item.query.filter_by(name=selected_item).first())


@app.route('/basket', methods=['GET', 'POST'])
@login_required
def basket():
    if request.method == 'POST':
        item_id = request.form['item_id']
        quantity = request.form['quantity']
        Basket_item.change_quantity(item_id, quantity, session['userid'])
        return redirect(url_for('basket'))
    
    total_price = calculate_total_price()

    return render_template('basket.html', basket=Basket_item.query.filter_by(user_id = session['userid']), Item=Item, total_price=total_price)


@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    form = CheckoutForm()
    if form.validate_on_submit():
        #db.session.query(Basket_item.query.filter_by(user_id = session['userid'])).delete()
        # db.session.query(Basket_item).filter(user_id = session['userid']).delete()

        # db.session.commit


        #Basket_item.query.filter_by(user_id = session['userid']).delete()
        return redirect(url_for('payment_taken'))
        
    

    total_price = calculate_total_price()

    return render_template('checkout.html', total_price=total_price, form=form)


@app.route('/payment_taken', methods=['GET', 'POST'])
@login_required
def payment_taken():

    return render_template('payment_taken.html')


def calculate_total_price():
    basket = Basket_item.query.filter_by(user_id = session['userid']).all()
    total_price = 0
    for item in basket:
        item_price = Item.query.get(item.item_id).price
        item_quantity = item.quantity
        overall_price = item_price * item_quantity
        total_price += overall_price

    return total_price


if __name__ == '__main__':
    db.create_all()
    if Item.query.filter_by(name='table').first() is None:
        Item.add_item('table', 'wooden thing to hold plates', 50, 'table.jpg', 10)
    if Item.query.filter_by(name='chair').first() is None:
        Item.add_item('chair', 'wooden thing to sit on', 100, 'chair.jpg', 5)

    if User.query.filter_by(username='lily').first() is None:
        User.register('lily', 'eye')
    if User.query.filter_by(username='al').first() is None:
        User.register('al', 'cat')
    app.run(debug=True)