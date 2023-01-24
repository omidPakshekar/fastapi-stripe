from fastapi import FastAPI, Depends, HTTPException, Request, Depends, status, Response, Header
from auth.auth import AuthHandler
from scheme.models import User, Payment
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from auth.auth_bearer import JWTBearer
import  mongoengine as mongo 
import stripe


mongo.connect(db='test', host="my-mongodb", port=27017, username='admin', password='admin')
app = FastAPI()

stripe.api_key =  "sk_test_51MRicJFdWhH1rCkWKjx3OJZrIYshlFEUUwE9tDRKYqOTTAViceHmvHQl13ja7mOZG0YSGICAtYmVttiBSARP7y3y00PIEo7bOL"

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
auth_handler = AuthHandler()

def get_auth_handler():
    return auth_handler

@app.get('/register')
def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post('/register', status_code=201)
async def register(response: Response, request: Request):
    """
        register user it's only work with template
        it's give username and password and create stripe_id and store to db
    """
    form = await request.form()
    username = form.get('username') 
    password = form.get('password')
    errors = []
    if not username:
        errors.append('please enter username')
    if not password:
        errors.append('please enter password')
    if len(errors) > 0:
        return {'error' : errors}

    if any(i.username == username for i in User.objects.all()):
        raise HTTPException(status_code=400, detail='Uesrname is Taken')
    hashed_password = auth_handler.get_password_hash(password)
    customer = stripe.Customer.create(
            description="Demo customer",
    )
    User(username=username, password=hashed_password, stripe_id=customer['id']).save()
    return {'detail' : "it's successful"}


@app.get('/login')
def index(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post('/login')
async def login(response: Response, request: Request):
    """"
        it's only work with form
        if it's successful it store access_token to cookie
    """
    form = await request.form()
    username = form.get('username') 
    password = form.get('password')
    errors = []
    if not username:
        errors.append('please enter username')
    if not password:
        errors.append('please enter password')
    if len(errors) > 0:
        return {'error' : errors}
    user_ = None 
    for x in User.objects.all():
        if x.username == username:
            user_ = x
            break
    if (user_ is None) or (not auth_handler.verify_password(password, user_.password)):
        raise HTTPException(status_code=401, detail='Invalid username and/or password')
    token = auth_handler.encode_token(user_.username)
    msg = "login succssful"
    response = templates.TemplateResponse('login.html', {'request':request, 'msg':msg})

    response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True)
    return response


@app.get('/')
def index(request: Request):
    token = request.cookies.get('access_token')
    if token is None:
        return {'detail' : 'go to /login'}
    return templates.TemplateResponse("index2.html", {"request": request})


@app.get("/success")
async def success(request: Request):
    return templates.TemplateResponse("success.html", {"request": request})


@app.get("/cancel")
async def cancel(request: Request):
    return templates.TemplateResponse("cancel.html", {"request": request})


@app.post("/create-checkout-session")
async def create_checkout_session(request: Request):
    """
        if payment successful it's create session
    """
    data = await request.json()
    print(request.cookies.get('access_token')) 
    token = request.cookies.get('access_token')
    if token is None:
        return templates.TemplateResponse("login.html", {"request": request})
    username = auth_handler.decode_token(token.split(' ')[1])
    user = User.objects.get(username=username)
    
    checkout_session = stripe.checkout.Session.create(
        customer=user.stripe_id,
        success_url="http://176.123.2.161:5022/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="http://176.123.2.161:5022/cancel",
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{
            "price": data["priceId"],
            "quantity": 1
        }],
    )
    return {"sessionId": checkout_session["id"]}


@app.post("/webhook")
async def webhook_received(request: Request, stripe_signature: str = Header(None)):
    """
        it's work with webhook and get information that made after stripe event occure
    """
    webhook_secret = 'whsec_4f257b756ff31b76059e8b9e6364efd8bf0fbd4cafbd82b50505cc478e80e8e4'
    data = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload=data,
            sig_header=stripe_signature,
            secret=webhook_secret
        )
        event_data = event['data']
    except Exception as e:
        return {"error": str(e)}

    event_type = event['type']
    if event_type == 'invoice.paid':
        print('--------' * 4)
        data = event['data']['object']
    
        Payment(stripe_id=data['customer'], email=str(data['customer_email']), subscription=data['subscription'], total=str(data['total'])).save()

        print('--------' * 4)

    if event_type == 'checkout.session.completed':
        print('checkout session completed')
    elif event_type == 'invoice.paid':
        print('invoice paid')
    elif event_type == 'invoice.payment_failed':
        print('invoice payment failed')
    else:
        print(f'unhandled event: {event_type}')

    return {"status": "success"}


@app.get('/get-user-info')
def user_info():
    """
        get all user information that register
    """
    lst = []
    for i in User.objects.all():
        lst.append({
                'username': i.username,
                'stripe_id': i.stripe_id
        })
    return {'data': lst}

@app.get('/get-payment-info')
def get_payment_info():
    """
        get all payment occur
    """
    lst = []
    for i in Payment.objects.all():
        lst.append({
                'stripe_id': i.stripe_id,
                'email': i.email,
                'subscription': i.subscription,
                'total' : i.total
        })
    return {'data': lst}





