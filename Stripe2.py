import os
import stripe
import uvicorn
from fastapi import FastAPI, Request, Header
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

stripe.api_key =  "sk_test_51MRicJFdWhH1rCkWKjx3OJZrIYshlFEUUwE9tDRKYqOTTAViceHmvHQl13ja7mOZG0YSGICAtYmVttiBSARP7y3y00PIEo7bOL"
# This is a terrible idea, only used for demo purposes!
app.state.stripe_customer_id = None


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "hasCustomer": app.state.stripe_customer_id is not None})


@app.get("/success")
async def success(request: Request):
    return templates.TemplateResponse("success.html", {"request": request})


@app.get("/cancel")
async def cancel(request: Request):
    return templates.TemplateResponse("cancel.html", {"request": request})


@app.post("/create-checkout-session")
async def create_checkout_session(request: Request):
    data = await request.json()
    print()
    if not app.state.stripe_customer_id:
        customer = stripe.Customer.create(
            description="Demo customer",
        )
        print('customer_id=', customer['id'])
        app.state.stripe_customer_id = customer["id"]

    checkout_session = stripe.checkout.Session.create(
        customer=app.state.stripe_customer_id,
        success_url="http://localhost:8000/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="http://localhost:8000/cancel",
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{
            "price": data["priceId"],
            "quantity": 1
        }],
    )
    return {"sessionId": checkout_session["id"]}


@app.post("/create-portal-session")
async def create_portal_session():
    session = stripe.billing_portal.Session.create(
        customer=app.state.stripe_customer_id,
        return_url="http://localhost:8000"
    )
    return {"url": session.url}


@app.post("/webhook")
async def webhook_received(request: Request, stripe_signature: str = Header(None)):
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
    # print('--------' * 4)
    # print('event=', event['data']['object'])
    # print('event=', event['data']['object'])
    if event_type == 'invoice.paid':
        print('--------' * 4)
        print(event['data']['object']['customer'])
        print(event['data']['object']['customer_email'])
        print(event['data']['object']['subscription'])
        print(event['data']['object']['total'])

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
# uvicorn myapi:app --reload


# event= {
#   "object": {
#     "account_country": "PL",
#     "account_name": null,
#     "account_tax_ids": null,
#     "amount_due": 500,
#     "amount_paid": 500,
#     "amount_remaining": 0,
#     "application": null,
#     "application_fee_amount": null,
#     "attempt_count": 1,
#     "attempted": true,
#     "auto_advance": false,
#     "automatic_tax": {
#       "enabled": false,
#       "status": null
#     },
#     "billing_reason": "subscription_create",
#     "charge": "ch_3MSHkTFdWhH1rCkW0wSBu2c2",
#     "collection_method": "charge_automatically",
#     "created": 1674210185,
#     "currency": "pln",
#     "custom_fields": null,
#     "customer": "cus_NCh8byPmYjMi4V",
#     "customer_address": null,
#     "customer_email": "omid.pakshekar.est@gmail.com",
#     "customer_name": null,
#     "customer_phone": null,
#     "customer_shipping": null,
#     "customer_tax_exempt": "none",
#     "customer_tax_ids": [],
#     "default_payment_method": null,
#     "default_source": null,
#     "default_tax_rates": [],
#     "description": null,
#     "discount": null,
#     "discounts": [],
#     "due_date": null,
#     "ending_balance": 0,
#     "footer": null,
#     "from_invoice": null,
#     "hosted_invoice_url": "https://invoice.stripe.com/i/acct_1MRicJFdWhH1rCkW/test_YWNjdF8xTVJpY0pGZFdoSDFyQ2tXLF9OQ2g4dWhON0dodVFLQ3FjTTNpVzg3emZPY0xLNHlULDY0NzUwOTg40200JzYoM6xE?s=ap",
#     "id": "in_1MSHkTFdWhH1rCkWwa0ZqiCS",
#     "invoice_pdf": "https://pay.stripe.com/invoice/acct_1MRicJFdWhH1rCkW/test_YWNjdF8xTVJpY0pGZFdoSDFyQ2tXLF9OQ2g4dWhON0dodVFLQ3FjTTNpVzg3emZPY0xLNHlULDY0NzUwOTg40200JzYoM6xE/pdf?s=ap",
#     "last_finalization_error": null,
#     "latest_revision": null,
#     "lines": {
#       "data": [
#         {
#           "amount": 500,
#           "amount_excluding_tax": 500,
#           "currency": "pln",
#           "description": "1 \u00d7 Premium (at 5.00 z\u0142 / month)",
#           "discount_amounts": [],
#           "discountable": true,
#           "discounts": [],
#           "id": "il_1MSHkTFdWhH1rCkWVX1fXirt",
#           "livemode": false,
#           "metadata": {},
#           "object": "line_item",
#           "period": {
#             "end": 1676888585,
#             "start": 1674210185
#           },
#           "plan": {
#             "active": true,
#             "aggregate_usage": null,
#             "amount": 500,
#             "amount_decimal": "500",
#             "billing_scheme": "per_unit",
#             "created": 1674076351,
#             "currency": "pln",
#             "id": "price_1MRivrFdWhH1rCkW2oHGGIDU",
#             "interval": "month",
#             "interval_count": 1,
#             "livemode": false,
#             "metadata": {},
#             "nickname": null,
#             "object": "plan",
#             "product": "prod_NC7ATHu8HqW85O",
#             "tiers_mode": null,
#             "transform_usage": null,
#             "trial_period_days": null,
#             "usage_type": "licensed"
#           },
#           "price": {
#             "active": true,
#             "billing_scheme": "per_unit",
#             "created": 1674076351,
#             "currency": "pln",
#             "custom_unit_amount": null,
#             "id": "price_1MRivrFdWhH1rCkW2oHGGIDU",
#             "livemode": false,
#             "lookup_key": null,
#             "metadata": {},
#             "nickname": null,
#             "object": "price",
#             "product": "prod_NC7ATHu8HqW85O",
#             "recurring": {
#               "aggregate_usage": null,
#               "interval": "month",
#               "interval_count": 1,
#               "trial_period_days": null,
#               "usage_type": "licensed"
#             },
#             "tax_behavior": "unspecified",
#             "tiers_mode": null,
#             "transform_quantity": null,
#             "type": "recurring",
#             "unit_amount": 500,
#             "unit_amount_decimal": "500"
#           },
#           "proration": false,
#           "proration_details": {
#             "credited_items": null
#           },
#           "quantity": 1,
#           "subscription": "sub_1MSHkTFdWhH1rCkWPg5EJurH",
#           "subscription_item": "si_NCh8UhKGZer4gZ",
#           "tax_amounts": [],
#           "tax_rates": [],
#           "type": "subscription",
#           "unit_amount_excluding_tax": "500"
#         }
#       ],
#       "has_more": false,
#       "object": "list",
#       "total_count": 1,
#       "url": "/v1/invoices/in_1MSHkTFdWhH1rCkWwa0ZqiCS/lines"
#     },
#     "livemode": false,
#     "metadata": {},
#     "next_payment_attempt": null,
#     "number": "35EF7C37-0006",
#     "object": "invoice",
#     "on_behalf_of": null,
#     "paid": true,
#     "paid_out_of_band": false,
#     "payment_intent": "pi_3MSHkTFdWhH1rCkW0EuoLijA",
#     "payment_settings": {
#       "default_mandate": null,
#       "payment_method_options": null,
#       "payment_method_types": null
#     },
#     "period_end": 1674210185,
#     "period_start": 1674210185,
#     "post_payment_credit_notes_amount": 0,
#     "pre_payment_credit_notes_amount": 0,
#     "quote": null,
#     "receipt_number": null,
#     "rendering_options": null,
#     "starting_balance": 0,
#     "statement_descriptor": null,
#     "status": "paid",
#     "status_transitions": {
#       "finalized_at": 1674210185,
#       "marked_uncollectible_at": null,
#       "paid_at": 1674210187,
#       "voided_at": null
#     },
#     "subscription": "sub_1MSHkTFdWhH1rCkWPg5EJurH",
#     "subtotal": 500,
#     "subtotal_excluding_tax": 500,
#     "tax": null,
#     "test_clock": null,
#     "total": 500,
#     "total_discount_amounts": [],
#     "total_excluding_tax": 500,
#     "total_tax_amounts": [],
#     "transfer_data": null,
#     "webhooks_delivered_at": null
#   }
# }
