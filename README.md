# Aban Tether Code Challenge
This is intended to be a very brief introduction to the code challenge for Aban Tether Interview.by Alireza Shamsaei.

# Notes

* For the sake of simplicity, We will keep using sqlite db.
* The system fulfils client orders (although no model is implemented for orders) by deducting the USD value and adding the corresponding amount in the target currency to their balance.
* There is a treasury containing the balance for each currency. this balance can become negative. when this balance becomes smaller (more negative) than a certain threshold (configurable via settings), then a (mock) request is sent to a (imaginary) Exchange, simulating a purchase from an external Exchange, increasing the amount of stored currency, "settling" accumulated "debt" for that currency.
* There was no mention of any type of authentication method/system  being required. There has been no efforts done in improving/ implementing user authentication & authorization. everything is how it is out of the box with django & DRF.  (a good Idea would be to implement oauth / token authentication)
* A video preview of the service is available [Here](https://drive.google.com/file/d/1-Csw4-X3eqp6fcZgpeU_5rh_v0bQUgKL/view?usp=sharing).

## Browsable API
This project is implemented using [Django Rest Framework](https://www.django-rest-framework.org/), therefore It comes with a browsable API which can be used to use and test the service.

## Models
 - **User Model:** default django model, used for authentication & authorization
 - **Currency:**  a ~~tradeable~~ buyable currency.
 - **Balance:** Abstract Model, for keeping tabs on currencies available in an account
 - **TreasuryBalance:** Inherited from **Balance**, keeps track of the available amount of a currency in Treasury.
 - **UserBalance:** Inherited from **Balance**, keeps track of the available amount of a currency in user account.
 - **Exchange:** Representing an external exchange. 


## Routes
- **Root**: provides a list of routes implemented.
- **users**: allows admin users to view, edit, add and remove currencies 
- **currencies**: allows admin users to view, edit, add and remove currencies 
- - **buy**: allows authenticated users to buy currencies with USD

## Tests
There are some tests. run `python manage.py test`

# Setup
## Dev environment
1. `clone` the project
2. install dependencies `pip install -r requirements`
3. copy `.env.sample` and rename to `.env`. fill with appropriate values.
4. create and initialize the db:
	-  `python manage.py migrate`
5. create a superuser:
	- `python manage.py createsuperuser`
6. populate the db using initial data: 
	- `python manage.py loaddata db.json`
	- This will create 3 users, each of them having 100 USD initial funds, three 
7. run `python manage.py runserver`
8. browse to the api root (via browser), login with credentials.
9. Browse !

## Test Environment
This project is dockerised, but never deployed using docker yet :(
