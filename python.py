from flask import Flask, render_template, session, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import SubmitField, IntegerField, HiddenField, StringField, PasswordField, BooleanField, SelectField
from wtforms.validators import InputRequired, Length, NumberRange, ValidationError, Regexp
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# INITIALISATION

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lily!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.sqlite3'
db = SQLAlchemy(app)
bootstrap = Bootstrap(app)
lm = LoginManager(app)
lm.login_view = 'login'
app.app_context().push()


# FUNCTIONS AND OTHER CODE

# formats all the prices so they include commas
@app.template_filter('format')
def format_price(value):
    return '{:,.0f}'.format(value)

# calculates total price of basket of current user 
def calculate_total_price():
    basket = Basket_item.query.filter_by(user_id = session['userid']).all()
    total_price = 0
    for item in basket:
        item_price = Item.query.get(item.item_id).price
        item_quantity = item.quantity
        overall_price = item_price * item_quantity
        total_price += overall_price

    return total_price


# FLASK FORMS

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(1, 16)])
    password = PasswordField('Password', validators=[InputRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Login')

class SortingForm(FlaskForm):
    order = SelectField('Sort By', choices=[('Name'), ('Price'), ('Environmental Impact')], render_kw={"class": "select_form"})

class CheckoutForm(FlaskForm):               
    name = StringField('Name on Card', validators=[InputRequired(), Length(1, 32)])
    cardnumber = StringField('Card Number', validators=[Regexp(r'^[0-9]{16}$', message='Please Enter a 16 Digit Numer')])
    expiry_date_month = SelectField('Expiry Month', choices=list(range(1, 13)), render_kw={"class": "select_form"})
    expiry_date_year = SelectField('Expiry Year', choices=list(range(2023, 2034)), render_kw={"class": "select_form"})
    cvc = StringField('CVC', validators=[Regexp(r'^[0-9]{3}$', message='Please Enter a 3 Digit Numer')])

class SignupForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(1, 10)])
    password = PasswordField('Password', validators=[InputRequired(), Length(1, 32)])
    submit = SubmitField('Sign up')


# DATABASES / MODELS

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
    

# returns a user when given an id
@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)
    price = db.Column(db.Integer)
    environmental_impact = db.Column(db.Integer)
    image = db.Column(db.String)

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
    
    # method to change quantity of items in basket, also used to delete items if quantity set to zero 
    def change_quantity(item_id, quantity, current_user):
        if int(quantity) > 0:
            item = Basket_item.query.filter_by(item_id=item_id, user_id=current_user).first()
            item.quantity = int(quantity)
        else:
            Basket_item.query.filter_by(item_id=item_id, user_id=current_user).delete()

        db.session.commit()


class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer)
    username = db.Column(db.String, db.ForeignKey('users.username'))
    review = db.Column(db.String)

    def write_review(username, item_id, review):
        review = Review(username=username, item_id=item_id, review=review)
        db.session.add(review)
        db.session.commit()


# ROUTES

# signs user up and redirects to loging page unless user already exists, then it displays message saying user exists
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        if User.query.filter_by(username=username).first() is None:
            User.register(username, password)
            return redirect(url_for('login'))

        else:
            return render_template('signup.html', form=form, exists=True)

    return render_template('signup.html', form=form)


# allows signed up user to login if password is correct and sets userid in session to the users id, redirects to home page
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


# renders home page with all items from database, allows user to click on item to view more info or add a quantity of the item to the basket
# also allows items to be sorted by different properties
@app.route('/', methods=['GET', 'POST'])
def home():
    form = SortingForm()
    items = Item.query.all()
    if form.validate_on_submit():
        if form.order.data == 'Name':
            items = Item.query.order_by(Item.name).all()
        elif form.order.data == 'Price':
            items = Item.query.order_by(Item.price.desc()).all()
        elif form.order.data == 'Environmental Impact':
            items = Item.query.order_by(Item.environmental_impact.desc()).all()

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
# also allows item to be added to basket and allows users to write and read reviews if they are logged in, else ridirects to login
@app.route('/item', methods=['GET', 'POST'])
def item():
    selected_item = request.args.get('type')
    item=Item.query.filter_by(name=selected_item).first()
    item_id = item.id

    if request.method == 'POST':
        if current_user.is_authenticated:
            review = request.form['review']
            user_id = session['userid']
            user = User.query.filter_by(id=user_id).first()
            username = user.username
            Review.write_review(username, item_id, review)
        else:
            return redirect(url_for('login'))

    return render_template('item.html', item=Item.query.filter_by(name=selected_item).first(), reviews=Review.query.filter_by(item_id=item_id).all())


# displays all items in users basket, allows to add items to basket or delete items by setting there quantity to zero
# diisplays the total price of items in the basket and allows user to checkout
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


# has a form to enter to checkout that includes error messages if the wrong informtion is entered and pop hints when hovering over inputs
# if the form validates sends user to payment_taken page and removes all items from users basket
@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    form = CheckoutForm()
    if form.validate_on_submit():
        basket = Basket_item.query.filter_by(user_id = session['userid'])
        for item in basket:
            Basket_item.change_quantity(item.item_id, 0, session['userid'])      
        return redirect(url_for('payment_taken'))
    
    total_price = calculate_total_price()
    return render_template('checkout.html', total_price=total_price, form=form)


@app.route('/payment_taken', methods=['GET', 'POST'])
@login_required
def payment_taken():
    return render_template('payment_taken.html')



# MAIN

# starts website and fills item database with items in the shop
if __name__ == '__main__':
    db.create_all()

    if Item.query.filter_by(name='Porsche Carrera GT').first() is None:
        Item.add_item('Porsche Carrera GT', 'The Porsche Carrera GT is a mid engined V10 sports car that was manufactured by Porsche in very limmited quantities '
                    'between 2004 and 2006. It is widely considered one of the best drivers cars every made due to its chasis, V10 engine and 6-speed manual gearbox '
                    'The carrera GT makes 603 hp and 435 lbs ft of torque, can do 0-60 mph in 3.5 seconds and has a top speed of 205mph.', 1149995, 'carrera_gt.png', 10)
    if Item.query.filter_by(name='Renault Clio V6').first() is None:
        Item.add_item('Renault Clio V6', 'The Renault Clio V6 is a rear wheel drive hot hatch that was produced by Renault from 2001 to 2005 and (the phase 2) was at the time '
                      'the most powerful production hot hatch in the world, making 252 bhp from its rear mid-mounted 2.9 litre V6 through a 6-speed manual gearbox. It had a reputation '
                      'for tricky handling due to its short wheel base and the postion of the engine.', 59995, 'clio_v6.png', 20)
    if Item.query.filter_by(name='BMW E30 M3').first() is None:
        Item.add_item('BMW E30 M3', 'The E30 M3 is widely considered to be the best looking M3 ever and was the first M3- being manufactured by BMW from 1986 to 1991- meaning it birthed '
                      'one of the best lines of sports cars ever. It had an inline 4 engine that made between 192 and 235 bhp depending on the model and was built as a homologation car to allow '
                      'BMW to go racing in the DTM and Group A touring series. 18,000 E30 M3s were built and the race cars won over 1400 races.', 77950, 'e30_m3.png', 19)   
    if Item.query.filter_by(name='Mitsubishi Pajero Evolution').first() is None:
        Item.add_item('Mitsubishi Pajero Evolution', 'The Mitsubishi Pajero Evolution is a homologation car that was built by Mitsubishi from 1997 to 1999 to allow it to race a race version in the Dakar Rally '
                      '(A Rally form Paris in France to Dakar in Senegal), which it ended up winning the most times out of any car at a staggering 12. The road car made 275 bhp from its 3.5 litre V6 and featured '
                      'a spoiler, hood scoop, skid plate and mudflaps; inherited from the offroad version.', 25848, 'pajero.png', 16)      
    if Item.query.filter_by(name='Audi Quattro Rally').first() is None:
        Item.add_item('Audi Quattro Rally', 'The Audi Quattro is a 4 wheel drive homolgation car made by Audi from 1980 to 1991, and which became one of the most famous rally cars of all time. There were many different '
                      'versions of the Quattro (which translates to four in Italian- and represents the cars 4 wheel drive), but they used a verion of Audis inline 5, paired with a 6-speed manual transmission. Rally versions '
                      'of the car competed in Group B rallies and have won 23 world champioship rallies.', 127232, 'quattro.png', 18)   
    
    app.run(debug=True)